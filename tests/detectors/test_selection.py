"""Validate configuration boundaries and real detector factory state isolation."""

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sentinel.config import DetectorConfig
from sentinel.contracts import ContractError, Observation
from sentinel.detectors.selection import ModelConfig, create_detector, load_model_config
from sentinel.detectors.thresholds import QuantileThresholdConfig
from sentinel.pipeline import process_stream


@pytest.mark.parametrize(
    "text,match",
    [
        ("[]", "JSON object"),
        ('{"labels":[]}', "Unknown model"),
        ('{"detector":"mad","detector":"zscore"}', "Duplicate"),
        ('{"calibration":{"quantile":0.5,"quantile":0.8}}', "Duplicate"),
        ('{"calibration":{"labels":[]}}', "Unknown calibration"),
        ('{"calibration":[]}', "object or null"),
        ('{"calibration":false}', "object or null"),
        ('{"detector":"chronos"}', "detector must"),
        ('{"detector":null}', "detector must"),
        ('{"calibration":{"quantile":NaN}}', "Nonfinite"),
        ('{"calibration":{"fallback_threshold":1e400}}', "finite"),
        ('{"calibration":{"window_size":true}}', "integers"),
        ('{"calibration":{"min_history":0}}', "Require"),
        ('{"use_seasonal":1}', "boolean"),
        ('{"detector":"residual","use_seasonal":true}', "explicit lag"),
        ('{"detector":"residual","seasonal_period":4}', "explicit lag"),
        ('{"use_seasonal":true,"seasonal_period":4}', "only by the residual"),
        ('{"seasonal_period":true}', "positive observation lag"),
        ('{"seasonal_period":0}', "positive observation lag"),
    ],
)
def test_invalid_or_ambiguous_model_settings_reject(tmp_path: Path, text: str, match: str) -> None:
    path = tmp_path / "model.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ContractError, match=match):
        load_model_config(path)


def test_seasonal_period_must_fit_the_actual_base_window() -> None:
    model = ModelConfig(detector="residual", use_seasonal=True, seasonal_period=4)
    with pytest.raises(ContractError, match="base window_size"):
        create_detector(DetectorConfig(window_size=3, min_history=2), model)


def test_empty_model_preserves_defaults_and_canonical_settings_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "model.json"
    path.write_text("{}", encoding="utf-8")
    assert load_model_config(path) == ModelConfig()
    model = ModelConfig(
        detector="residual",
        use_seasonal=True,
        seasonal_period=4,
        calibration=QuantileThresholdConfig(window_size=8, min_history=2, quantile=0.75),
    )
    path.write_text(json.dumps(model.to_dict()), encoding="utf-8")
    assert load_model_config(path) == model


@pytest.mark.parametrize("detector", ["mad", "zscore", "residual"])
@pytest.mark.parametrize("adaptive", [False, True])
def test_factory_keeps_series_and_calibration_state_independent(
    detector: str, adaptive: bool
) -> None:
    model = ModelConfig(
        detector=detector,
        calibration=QuantileThresholdConfig(window_size=3, min_history=2) if adaptive else None,
    )
    cfg = DetectorConfig(window_size=4, min_history=2)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    left = [Observation("a", start + timedelta(seconds=i), float(i % 7)) for i in range(20)]
    right = [replace(p, series_id="b", value=100 + 3 * p.value) for p in left]
    mixed = [p for pair in zip(left, right, strict=True) for p in pair]

    def factory():
        return create_detector(cfg, model)

    combined = [p for p, _ in process_stream(mixed, factory)]
    for series, inputs in (("a", left), ("b", right)):
        independent = [p for p, _ in process_stream(inputs, factory)]
        assert [p for p in combined if p.series_id == series] == independent


def test_direct_constructor_rejects_unvalidated_calibrator() -> None:
    with pytest.raises(ContractError, match="QuantileThresholdConfig"):
        ModelConfig(calibration={})
