"""Ayush owns orchestration and the CLI; the detector is replaceable via Protocol."""

import hashlib
import json
import platform
import shutil
import tempfile
from collections.abc import Callable, Iterable, Iterator
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter_ns, sleep
from typing import Any

from sentinel import __version__
from sentinel.config import DetectorConfig
from sentinel.contracts import (
    SCHEMA_VERSION,
    ContractError,
    Detector,
    EvaluationScope,
    Observation,
    Prediction,
    timestamp_text,
)
from sentinel.data.io import read_observations
from sentinel.detectors.selection import ModelConfig, create_detector
from sentinel.profiling import ReplayProfile
from sentinel.provenance import canonical_sha256, environment_snapshot, source_state


def process_stream(
    observations: Iterable[Observation], factory: Callable[[], Detector], max_series: int = 100
) -> Iterator[tuple[Prediction, int]]:
    detectors: dict[str, Detector] = {}
    for observation in observations:
        if observation.series_id not in detectors:
            if len(detectors) >= max_series:
                raise ContractError("Maximum active series exceeded")
            detectors[observation.series_id] = factory()
        start = perf_counter_ns()
        prediction = detectors[observation.series_id].process(observation)
        yield prediction, perf_counter_ns() - start


def prediction_record(prediction: Prediction, elapsed_ns: int) -> dict[str, Any]:
    payload = asdict(prediction)
    payload["timestamp"] = timestamp_text(prediction.timestamp)
    payload["schema_version"] = SCHEMA_VERSION
    payload["elapsed_ns"] = elapsed_ns
    return payload


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _publish_run(temporary: Path, output_dir: Path) -> None:
    """Bound Windows sharing/access-denied retries without hiding persistent errors.

    Files have been closed before this call. A short-lived filesystem reader can
    still prevent a directory rename on Windows. No retry for other error types,
    no overwrite of an existing destination, and at most 310 ms total backoff.
    This remains single-process publication, not a multiwriter transaction.
    """
    delays = (0.0, 0.01, 0.02, 0.04, 0.08, 0.16)
    for attempt, delay in enumerate(delays):
        if delay:
            sleep(delay)
        if output_dir.exists():
            raise ContractError(f"Output directory already exists: {output_dir}")
        try:
            temporary.rename(output_dir)
            return
        except PermissionError as exc:
            if getattr(exc, "winerror", None) not in (5, 32) or attempt == len(delays) - 1:
                raise


def run_file(
    input_path: Path,
    output_dir: Path,
    config: DetectorConfig,
    scope: EvaluationScope,
    dataset_id: str,
    *,
    split_manifest_path: Path | None = None,
    model_config: ModelConfig | None = None,
) -> dict[str, Any]:
    started_ns = perf_counter_ns()
    started_at = timestamp_text(datetime.now(UTC))
    if scope not in ("synthetic_smoke", "development_validation"):
        raise ContractError("Starter supports synthetic_smoke or development_validation only")
    if not dataset_id.strip():
        raise ContractError("dataset_id is required")
    selection = model_config if model_config is not None else ModelConfig()
    model_metadata = selection.metadata(config)
    if output_dir.exists():
        raise ContractError(
            f"Output directory already exists: {output_dir}; use a new run directory"
        )
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".sentinel-", dir=output_dir.parent))
    try:
        input_sha256 = sha256_file(input_path)
        environment = environment_snapshot()
        source = source_state(Path(__file__))
        split_artifact = None
        split_sha256 = None
        if split_manifest_path is not None:
            split_artifact = "split-manifest.snapshot"
            shutil.copyfile(split_manifest_path, temporary / split_artifact)
            split_sha256 = sha256_file(temporary / split_artifact)
        profile = ReplayProfile()
        count = ready_count = alerts = total_ns = 0
        replay_started_ns = perf_counter_ns()
        with (temporary / "predictions.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
            for prediction, elapsed in process_stream(
                read_observations(input_path),
                lambda: create_detector(config, selection),
                config.max_series,
            ):
                stream.write(
                    json.dumps(prediction_record(prediction, elapsed), allow_nan=False) + "\n"
                )
                count += 1
                ready_count += int(prediction.ready)
                alerts += int(prediction.label == "ANOMALOUS")
                total_ns += elapsed
                profile.record(prediction, elapsed)
        replay_elapsed_ns = perf_counter_ns() - replay_started_ns
        if sha256_file(input_path) != input_sha256:
            raise ContractError("Input changed during replay; no run was published")
        metadata: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "package_version": __version__,
            "algorithm": selection.algorithm,
            "evaluation_scope": scope,
            "dataset_id": dataset_id,
            "input_sha256": input_sha256,
            "predictions_sha256": sha256_file(temporary / "predictions.jsonl"),
            "config": config.to_dict(),
            "model": model_metadata,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "observations": count,
            "ready_observations": ready_count,
            "anomalous_points": alerts,
            "detector_total_ns": total_ns,
            "runtime_note": (
                "process() only, includes warmup; excludes parsing/writing; not a benchmark"
            ),
            "official_submission_ready": False,
            "provenance": {
                "version": "1.0",
                "source": source,
                "config_sha256": canonical_sha256(config.to_dict()),
                "model_config_sha256": canonical_sha256(model_metadata),
                "run_config_sha256": canonical_sha256(
                    {"config": config.to_dict(), "model": model_metadata}
                ),
                "environment": environment,
                "environment_sha256": canonical_sha256(environment),
                "dependencies_sha256": canonical_sha256(environment["dependencies"]),
                "split_manifest_sha256": split_sha256,
                "split_manifest_artifact": split_artifact,
                "split_validation": "checksum_only" if split_artifact else "not_supplied",
                "started_at_utc": started_at,
            },
            "profiling": {
                **profile.timings(),
                "end_to_end_replay_ns": replay_elapsed_ns,
                "replay_region": (
                    "predictions file open through close; includes CSV open/read, parsing, "
                    "detector construction, routing, process, serialization, writing and profiling"
                ),
                "prepublication_region": (
                    "run_file entry through metadata preparation, including provenance and hashes; "
                    "excludes final run.json write/rename, CLI startup and evaluation"
                ),
            },
            "workload": {
                **profile.workload(),
                "observations": count,
                "ready_observations": ready_count,
                "warmup_observations": count - ready_count,
                "window_size": config.window_size,
                "min_history": config.min_history,
                "max_series": config.max_series,
            },
        }
        metadata["provenance"]["prepared_at_utc"] = timestamp_text(datetime.now(UTC))
        metadata["profiling"]["prepublication_elapsed_ns"] = perf_counter_ns() - started_ns
        (temporary / "run.json").write_text(
            json.dumps(metadata, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n"
        )
        _publish_run(temporary, output_dir)
        return metadata
    except BaseException:
        shutil.rmtree(temporary)
        raise
