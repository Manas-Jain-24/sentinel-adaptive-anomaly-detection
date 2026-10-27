"""Exercise actual CLI -> factory -> saved predictions/profiling -> evaluator."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from sentinel import pipeline
from sentinel.cli import main
from sentinel.config import DetectorConfig
from sentinel.contracts import AnomalyWindow, ContractError, Detector, parse_timestamp
from sentinel.data.features import RollingFeatureExtractor
from sentinel.data.io import read_observations
from sentinel.detectors.calibrated import CalibratedDetector
from sentinel.detectors.residual import ResidualDetector
from sentinel.detectors.rolling import RollingMADStarter
from sentinel.detectors.selection import ModelConfig
from sentinel.detectors.thresholds import PriorScoreQuantile, QuantileThresholdConfig
from sentinel.detectors.zscore import RollingZScoreDetector
from sentinel.evaluation.reference import evaluate_run, event_metrics
from sentinel.pipeline import prediction_record, run_file

FIXTURES = Path(__file__).parents[1] / "fixtures"


def records(path: Path) -> list[dict[str, Any]]:
    return [
        {key: value for key, value in json.loads(line).items() if key != "elapsed_ns"}
        for line in (path / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def args(source: Path, destination: Path) -> list[str]:
    return [
        "run",
        "--input",
        str(source),
        "--config",
        "configs/starter.json",
        "--output-dir",
        str(destination),
        "--dataset-id",
        "synthetic-fixture-v1",
        "--scope",
        "synthetic_smoke",
    ]


@pytest.mark.parametrize(
    "name,adaptive,seasonal,algorithm",
    [
        ("mad", False, False, "rolling_mad_starter"),
        ("zscore", False, False, "rolling_zscore"),
        ("residual", False, False, "residual_max"),
        ("residual", False, True, "residual_max_seasonal"),
        ("mad", True, False, "rolling_mad_starter_prior_quantile"),
        ("zscore", True, False, "rolling_zscore_prior_quantile"),
        ("residual", True, False, "residual_max_prior_quantile"),
        ("residual", True, True, "residual_max_seasonal_prior_quantile"),
    ],
)
def test_cli_records_actual_selected_model_and_matches_independent_composition(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    name: str,
    adaptive: bool,
    seasonal: bool,
    algorithm: str,
) -> None:
    quantile = QuantileThresholdConfig(
        window_size=3, min_history=2, quantile=1, threshold_floor=0.01
    )
    selection = ModelConfig(
        detector=name,
        use_seasonal=seasonal,
        seasonal_period=4 if seasonal else None,
        calibration=quantile if adaptive else None,
    )
    model_path = tmp_path / "model.json"
    model_path.write_text(json.dumps(selection.to_dict()), encoding="utf-8")
    split = tmp_path / "split.snapshot"
    split.write_bytes(b"opaque provenance only: no inferred partition permissions")
    destination = tmp_path / "run"
    assert (
        main(
            args(FIXTURES / "synthetic_stream.csv", destination)
            + [
                "--model-config",
                str(model_path),
                "--split-manifest",
                str(split),
            ]
        )
        == 0
    )
    manifest = json.loads(capsys.readouterr().out)
    assert manifest == json.loads((destination / "run.json").read_text())
    assert manifest["algorithm"] == algorithm
    assert manifest["official_submission_ready"] is False
    assert manifest["config"] == DetectorConfig().to_dict()
    model = manifest["model"]
    assert {k: model[k] for k in selection.to_dict()} == selection.to_dict()
    assert model["reference_update_policy"] == "include_all_observations"
    assert model["replay_context"]["saturated_raw_lookback"] == 32 + (3 if adaptive else 0)
    assert (model["features"] is not None) == (name == "residual")
    if name == "residual":
        assert model["features"]["scale_floor"] == 0.1
        assert model["features"]["seasonal_period"] == (4 if seasonal else None)
    provenance = manifest["provenance"]
    assert provenance["config_sha256"] == digest(manifest["config"])
    assert provenance["model_config_sha256"] == digest(model)
    assert provenance["run_config_sha256"] == digest({"config": manifest["config"], "model": model})
    assert provenance["split_validation"] == "checksum_only"
    assert (destination / "split-manifest.snapshot").read_bytes() == split.read_bytes()
    assert manifest["profiling"]["distributions"]["all_process"]["count"] == 16
    assert manifest["profiling"]["distributions"]["ready_process"]["count"] == 8

    # Instantiate the existing public classes independently of the new selector.
    base: Detector
    if name == "mad":
        base = RollingMADStarter(DetectorConfig())
    elif name == "zscore":
        base = RollingZScoreDetector(DetectorConfig())
    else:
        base = ResidualDetector(
            DetectorConfig(),
            RollingFeatureExtractor(seasonal_period=4 if seasonal else None),
            use_seasonal=seasonal,
        )
    if adaptive:
        base = CalibratedDetector(base, PriorScoreQuantile(quantile))
    expected = []
    for point in read_observations(FIXTURES / "synthetic_stream.csv"):
        record = prediction_record(base.process(point), 0)
        record.pop("elapsed_ns")
        expected.append(record)
    assert records(destination) == expected
    metric = evaluate_run(destination, FIXTURES / "synthetic_windows.json")
    assert metric["metric_id"] == "provisional_event_trigger_f1_v0"
    assert metric["official_metric"] is False


def test_legacy_default_matches_explicit_mad_and_preserves_old_config_hash(tmp_path: Path) -> None:
    source = FIXTURES / "synthetic_stream.csv"
    default = run_file(source, tmp_path / "default", DetectorConfig(), "synthetic_smoke", "s")
    explicit = run_file(
        source,
        tmp_path / "explicit",
        DetectorConfig(),
        "synthetic_smoke",
        "s",
        model_config=ModelConfig(detector="mad"),
    )
    assert records(tmp_path / "default") == records(tmp_path / "explicit")
    assert default["algorithm"] == explicit["algorithm"] == "rolling_mad_starter"
    assert default["provenance"]["run_config_sha256"] == explicit["provenance"]["run_config_sha256"]
    assert default["provenance"]["config_sha256"] == digest(DetectorConfig().to_dict())


@pytest.mark.parametrize("name", ["mad", "zscore", "residual"])
def test_simple_detector_flag_is_a_real_saved_run(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    name: str,
) -> None:
    assert (
        main(args(FIXTURES / "synthetic_stream.csv", tmp_path / "run") + ["--detector", name]) == 0
    )
    manifest = json.loads(capsys.readouterr().out)
    assert manifest["model"]["detector"] == name
    assert manifest["model"]["calibration"] is None


def test_no_selector_is_silently_overridden(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as failure:
        main(
            args(FIXTURES / "synthetic_stream.csv", tmp_path / "run")
            + [
                "--detector",
                "zscore",
                "--model-config",
                "configs/residual-quantile.model.json",
            ]
        )
    assert failure.value.code == 2
    assert not (tmp_path / "run").exists()


@pytest.mark.parametrize(
    "content",
    [
        '{"guard":"quarantine"}',
        '{"detector":"chronos"}',
        '{"detector":"residual","use_seasonal":true,"seasonal_period":64}',
        '{"calibration":{"window_size":0}}',
        '{"labels":[]}',
        '{"detector":NaN}',
    ],
)
def test_invalid_model_cli_fails_without_output_or_partial_directory(
    tmp_path: Path, content: str
) -> None:
    model = tmp_path / "model.json"
    model.write_text(content, encoding="utf-8")
    assert (
        main(
            args(FIXTURES / "synthetic_stream.csv", tmp_path / "run")
            + ["--model-config", str(model)]
        )
        == 2
    )
    assert not (tmp_path / "run").exists()
    assert not list(tmp_path.glob(".sentinel-*"))


def test_model_failure_and_collision_preserve_existing_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Broken:
        def process(self, observation):
            raise ContractError("deliberate model failure")

        def reset(self):
            pass

    destination = tmp_path / "run"
    monkeypatch.setattr(pipeline, "create_detector", lambda *_: Broken())
    with pytest.raises(ContractError, match="deliberate model failure"):
        run_file(
            FIXTURES / "synthetic_stream.csv",
            destination,
            DetectorConfig(),
            "synthetic_smoke",
            "s",
            model_config=ModelConfig(detector="residual"),
        )
    assert not destination.exists()
    assert not list(tmp_path.glob(".sentinel-*"))
    destination.mkdir()
    (destination / "keep.txt").write_text("original")
    with pytest.raises(ContractError, match="already exists"):
        run_file(
            FIXTURES / "synthetic_stream.csv", destination, DetectorConfig(), "synthetic_smoke", "s"
        )
    assert (destination / "keep.txt").read_text() == "original"


def test_model_changes_have_distinct_run_identity_even_with_identical_base_config(
    tmp_path: Path,
) -> None:
    identities = set()
    base_hashes = set()
    for name in ("mad", "zscore", "residual"):
        manifest = run_file(
            FIXTURES / "synthetic_stream.csv",
            tmp_path / name,
            DetectorConfig(),
            "synthetic_smoke",
            "s",
            model_config=ModelConfig(detector=name),
        )
        identities.add(manifest["provenance"]["run_config_sha256"])
        base_hashes.add(manifest["provenance"]["config_sha256"])
    assert len(identities) == 3
    assert len(base_hashes) == 1


def test_entire_input_hash_does_not_leak_suffix_values_into_saved_prefix(tmp_path: Path) -> None:
    rows = (FIXTURES / "synthetic_stream.csv").read_text(encoding="utf-8").splitlines()
    prefix = tmp_path / "prefix.csv"
    prefix.write_text("\n".join(rows[:13]) + "\n", encoding="utf-8")
    model = ModelConfig(
        detector="residual",
        use_seasonal=True,
        seasonal_period=4,
        calibration=QuantileThresholdConfig(window_size=3, min_history=2, quantile=1),
    )
    short = run_file(
        prefix,
        tmp_path / "short",
        DetectorConfig(),
        "synthetic_smoke",
        "fixture",
        model_config=model,
    )
    full = run_file(
        FIXTURES / "synthetic_stream.csv",
        tmp_path / "full",
        DetectorConfig(),
        "synthetic_smoke",
        "fixture",
        model_config=model,
    )
    assert short["input_sha256"] != full["input_sha256"]
    assert records(tmp_path / "short") == records(tmp_path / "full")[:12]


@pytest.mark.parametrize("content", [None, "{bad json", '{"detector":"mad","detector":"residual"}'])
def test_missing_malformed_or_duplicate_model_file_is_an_actionable_cli_error(
    tmp_path: Path,
    content: str | None,
) -> None:
    model = tmp_path / "model.json"
    if content is not None:
        model.write_text(content, encoding="utf-8")
    assert (
        main(
            args(FIXTURES / "synthetic_stream.csv", tmp_path / "run")
            + [
                "--model-config",
                str(model),
            ]
        )
        == 2
    )
    assert not (tmp_path / "run").exists()


def test_default_quantile_ties_can_start_an_episode_before_a_real_synthetic_spike(
    tmp_path: Path,
) -> None:
    # Regression for the measured 96-point CLI smoke. Preserve the observed
    # limitation rather than tune the threshold/metric to conceal its miss.
    from datetime import UTC, datetime, timedelta

    start = datetime(2026, 1, 1, tzinfo=UTC)
    rows = ["series_id,timestamp,value"]
    for i in range(96):
        value = 25 if i == 64 else (10.0, 10.1, 10.0, 9.9)[i % 4]
        rows.append(f"s,{(start + timedelta(seconds=i)).isoformat()},{value}")
    source = tmp_path / "stream.csv"
    source.write_text("\n".join(rows) + "\n", encoding="utf-8")
    destination = tmp_path / "run"
    run_file(
        source,
        destination,
        DetectorConfig(),
        "synthetic_smoke",
        "quantile-tie-regression",
        model_config=ModelConfig(detector="residual", calibration=QuantileThresholdConfig()),
    )
    predictions = records(destination)
    assert predictions[39]["label"] == "NORMAL"
    assert predictions[40]["label"] == "ANOMALOUS"
    assert predictions[40]["score"] == predictions[40]["threshold"]
    assert all(row["label"] == "ANOMALOUS" for row in predictions[40:65])
    assert predictions[65]["label"] == "NORMAL"
    event_time = parse_timestamp(predictions[64]["timestamp"])
    metric = event_metrics(predictions, [AnomalyWindow("s", event_time, event_time)])
    assert (metric["tp"], metric["fp"], metric["fn"]) == (0, 1, 1)
