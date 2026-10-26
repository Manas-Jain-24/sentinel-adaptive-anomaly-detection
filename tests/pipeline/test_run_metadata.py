import hashlib
import itertools
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from sentinel import pipeline
from sentinel.cli import main
from sentinel.config import DetectorConfig
from sentinel.contracts import ContractError, Prediction, parse_timestamp
from sentinel.evaluation.reference import evaluate_run
from sentinel.pipeline import run_file

FIXTURES = Path(__file__).parents[1] / "fixtures"


def semantic_records(path: Path) -> list[dict[str, Any]]:
    return [
        {key: value for key, value in json.loads(line).items() if key != "elapsed_ns"}
        for line in (path / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def independent_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def test_manifest_hashes_timing_regions_and_existing_evaluator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = itertools.count(0, 10)
    monkeypatch.setattr(pipeline, "perf_counter_ns", lambda: next(clock))
    destination = tmp_path / "run"
    config = DetectorConfig()
    manifest = run_file(
        FIXTURES / "synthetic_stream.csv", destination, config, "synthetic_smoke", "fixture"
    )
    assert json.loads((destination / "run.json").read_text()) == manifest
    provenance = manifest["provenance"]
    assert provenance["version"] == "1.0"
    assert provenance["config_sha256"] == independent_digest(config.to_dict())
    assert provenance["environment_sha256"] == independent_digest(provenance["environment"])
    assert provenance["dependencies_sha256"] == independent_digest(
        provenance["environment"]["dependencies"]
    )
    assert provenance["split_manifest_sha256"] is provenance["split_manifest_artifact"] is None
    assert provenance["split_validation"] == "not_supplied"
    assert parse_timestamp(provenance["started_at_utc"]) <= parse_timestamp(
        provenance["prepared_at_utc"]
    )
    timings = manifest["profiling"]
    populations = timings["distributions"]
    for name, count in {
        "all_process": 16,
        "ready_process": 8,
        "warmup_process": 8,
        "cold_process": 1,
        "warm_process": 15,
    }.items():
        assert populations[name]["count"] == count
        assert populations[name]["p50_upper_bound_ns"] == 10
        assert populations[name]["p95_upper_bound_ns"] == 10
    assert populations["all_process"]["total_ns"] == manifest["detector_total_ns"] == 160
    assert timings["prepublication_elapsed_ns"] > timings["end_to_end_replay_ns"] > 160
    assert "factory" in timings["process_region"]
    assert "construction" in timings["cold_region"]
    assert "run.json" in timings["prepublication_region"]
    workload = manifest["workload"]
    assert workload["observations"] == 16
    assert workload["series_count"] == 1
    assert workload["window_size"] == config.window_size
    assert sum(item["observations"] for item in workload["series"].values()) == 16
    metrics = evaluate_run(destination, FIXTURES / "synthetic_windows.json")
    assert metrics["tp"] == 1 and metrics["fp"] == metrics["fn"] == 0
    assert metrics["official_metric"] is False


def test_opaque_split_snapshot_and_profiling_do_not_change_predictions(tmp_path: Path) -> None:
    split = tmp_path / "split.manifest"
    raw = b"opaque synthetic split; labels must never feed inference\r\n"
    split.write_bytes(raw)
    plain, with_split = tmp_path / "plain", tmp_path / "split-run"
    run_file(
        FIXTURES / "synthetic_stream.csv", plain, DetectorConfig(), "synthetic_smoke", "fixture"
    )
    result = run_file(
        FIXTURES / "synthetic_stream.csv",
        with_split,
        DetectorConfig(),
        "synthetic_smoke",
        "fixture",
        split_manifest_path=split,
    )
    provenance = result["provenance"]
    assert provenance["split_validation"] == "checksum_only"
    assert provenance["split_manifest_sha256"] == hashlib.sha256(raw).hexdigest()
    assert (with_split / provenance["split_manifest_artifact"]).read_bytes() == raw
    assert semantic_records(plain) == semantic_records(with_split)


def test_interleaved_workload_and_empty_ready_population(tmp_path: Path) -> None:
    source = tmp_path / "interleaved.csv"
    source.write_text(
        "series_id,timestamp,value\n"
        "a,2026-01-01T00:00:00Z,1\nb,2026-01-01T00:00:00Z,5\n"
        "a,2026-01-01T00:01:00Z,1\nb,2026-01-01T00:02:00Z,5\n",
        encoding="utf-8",
    )
    result = run_file(source, tmp_path / "run", DetectorConfig(), "synthetic_smoke", "interleaved")
    workload = result["workload"]
    assert workload["series_count"] == 2
    assert workload["warmup_observations"] == 4
    assert workload["series"]["a"]["last_timestamp"] == "2026-01-01T00:01:00Z"
    assert workload["series"]["b"]["last_timestamp"] == "2026-01-01T00:02:00Z"
    populations = result["profiling"]["distributions"]
    assert populations["cold_process"]["count"] == populations["warm_process"]["count"] == 2
    assert populations["ready_process"]["count"] == 0
    assert populations["ready_process"]["p95_upper_bound_ns"] is None


def test_input_mutation_during_replay_cannot_publish_stale_checksum(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "input.csv"
    source.write_bytes((FIXTURES / "synthetic_stream.csv").read_bytes())
    real_process_stream = pipeline.process_stream

    def mutating_stream(*args: Any, **kwargs: Any) -> Iterator[tuple[Prediction, int]]:
        yield from real_process_stream(*args, **kwargs)
        source.write_bytes(source.read_bytes() + b"\n")

    monkeypatch.setattr(pipeline, "process_stream", mutating_stream)
    with pytest.raises(ContractError, match="Input changed"):
        run_file(source, tmp_path / "run", DetectorConfig(), "synthetic_smoke", "fixture")
    assert not (tmp_path / "run").exists()
    assert not list(tmp_path.glob(".sentinel-*"))


def test_split_cli_and_missing_split_cleanup(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    split = tmp_path / "split.json"
    destination = tmp_path / "run"
    args = [
        "run",
        "--input",
        str(FIXTURES / "synthetic_stream.csv"),
        "--config",
        "configs/starter.json",
        "--output-dir",
        str(destination),
        "--dataset-id",
        "fixture",
        "--scope",
        "synthetic_smoke",
        "--split-manifest",
        str(split),
    ]
    assert main(args) == 2
    assert not destination.exists()
    assert not list(tmp_path.glob(".sentinel-*"))
    split.write_text('{"scope":"synthetic_smoke"}\n', encoding="utf-8")
    assert main(args) == 0
    manifest = json.loads(capsys.readouterr().out)
    assert manifest["provenance"]["split_manifest_artifact"] == "split-manifest.snapshot"
