"""Independent forecast-origin, arithmetic, lifecycle and composition checks."""

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from sys import maxsize

import pytest

from sentinel.contracts import ContractError, Observation
from sentinel.detectors.calibrated import CalibratedDetector
from sentinel.detectors.forecast import (
    ForecastDetectorConfig,
    ForecastInterval,
    ForecastIntervalDetector,
)
from sentinel.detectors.thresholds import PriorScoreQuantile, QuantileThresholdConfig
from sentinel.pipeline import prediction_record, process_stream

START = datetime(2026, 1, 1, tzinfo=UTC)


class RecordingModel:
    def __init__(self) -> None:
        self.calls: list[tuple[tuple[float, ...], int]] = []

    def forecast(self, history: tuple[float, ...], horizon: int) -> list[ForecastInterval]:
        self.calls.append((history, horizon))
        return [ForecastInterval(history[-1] - 1, history[-1], history[-1] + 1)] * horizon


def point(i: int, value: float, series: str = "s") -> Observation:
    return Observation(series, START + timedelta(seconds=i), value)


def config(**changes: object) -> ForecastDetectorConfig:
    return replace(ForecastDetectorConfig(context_window=4, min_history=2, horizon=3), **changes)


@pytest.mark.parametrize("stride", [1, 3])
def test_forecast_sees_only_past_bounded_values_with_exact_origins(stride: int) -> None:
    model = RecordingModel()
    detector = ForecastIntervalDetector(config(refresh_stride=stride), model)
    results = [detector.process(point(i, float(i))) for i in range(9)]
    assert [(p.ready, p.score) for p in results[:2]] == [(False, None), (False, None)]
    refresh_indices = range(2, 9, stride)
    assert model.calls == [
        (tuple(float(j) for j in range(max(0, i - 4), i)), 3) for i in refresh_indices
    ]
    for i, prediction in enumerate(results[2:], 2):
        age = (i - 2) % stride + 1
        origin = i - age
        assert (
            f"origin={(START + timedelta(seconds=origin)).isoformat().replace('+00:00', 'Z')}"
            in (prediction.evidence.reason)
        )
        assert f"age_points={age}" in prediction.evidence.reason
        assert prediction.evidence.baseline == origin
        assert prediction.score == max(0, age - 1) / 2


def test_hand_computed_interval_score_floor_equality_and_frozen_evidence() -> None:
    class FlatModel:
        def forecast(self, history: tuple[float, ...], horizon: int) -> list[ForecastInterval]:
            return [ForecastInterval(10, 10, 10)] * horizon

    detector = ForecastIntervalDetector(config(scale_floor=0.5, threshold=4), FlatModel())
    detector.process(point(0, 10))
    detector.process(point(1, 10))
    hit = detector.process(point(2, 12))
    assert (hit.score, hit.label) == (4, "ANOMALOUS")
    assert (hit.evidence.baseline, hit.evidence.scale, hit.evidence.residual) == (10, 0.5, 2)
    assert hit.evidence.component_scores == {"interval_exceedance": 4}
    frozen = json.dumps(prediction_record(hit, 0), allow_nan=False)
    detector.process(point(3, -100))
    assert frozen == json.dumps(prediction_record(hit, 0), allow_nan=False)


@pytest.mark.parametrize("stride", [1, 3])
def test_prefix_reset_and_appended_future_do_not_revise_predictions(stride: int) -> None:
    detector = ForecastIntervalDetector(config(refresh_stride=stride), RecordingModel())
    points = [point(i, float(i % 7)) for i in range(15)]
    prefix = [detector.process(p) for p in points[:9]]
    [detector.process(p) for p in points[9:]]
    detector.reset()
    assert [detector.process(p) for p in points][:9] == prefix


def test_frozen_block_does_not_observe_spike_early_or_refresh_mid_block() -> None:
    model = RecordingModel()
    detector = ForecastIntervalDetector(config(refresh_stride=3), model)
    results = [detector.process(point(i, v)) for i, v in enumerate([0, 0, 100, 0, 0, 0])]
    assert model.calls == [((0, 0), 3), ((0, 100, 0, 0), 3)]
    assert results[2].score == 49.5
    assert results[3].score == 0
    assert "age_points=2" in results[3].evidence.reason


@pytest.mark.parametrize("bad", [0, -1, True, 2.5])
@pytest.mark.parametrize("field", ["context_window", "min_history", "horizon"])
def test_invalid_sizes_are_rejected(field: str, bad: object) -> None:
    with pytest.raises(ContractError):
        config(**{field: bad})


@pytest.mark.parametrize("field", ["context_window", "horizon"])
def test_unrepresentable_container_sizes_reject_with_contract_error(field: str) -> None:
    with pytest.raises(ContractError):
        config(**{field: maxsize + 1})


@pytest.mark.parametrize("actual,expected", [(8, 0.5), (9, 0), (10, 0), (11, 0), (12, 0.5)])
def test_both_interval_endpoints_are_inclusive(actual: float, expected: float) -> None:
    class FixedModel:
        def forecast(self, history: tuple[float, ...], horizon: int) -> list[ForecastInterval]:
            return [ForecastInterval(9, 10, 11)] * horizon

    detector = ForecastIntervalDetector(config(), FixedModel())
    detector.process(point(0, 10))
    detector.process(point(1, 10))
    result = detector.process(point(2, actual))
    assert result.score == expected


def test_restarting_block_from_short_context_does_not_prove_forecast_phase_parity() -> None:
    points = [point(i, float(i)) for i in range(20)]

    def replay(items: list[Observation]) -> list[object]:
        detector = ForecastIntervalDetector(config(refresh_stride=3), RecordingModel())
        return [detector.process(p) for p in items]

    full = replay(points)
    restarted = replay(points[5:])
    assert restarted[4] != full[9]  # Both ready with four past values, different origin phase.


def test_timezone_ordering_is_by_instant_and_output_is_utc() -> None:
    detector = ForecastIntervalDetector(config(), RecordingModel())
    detector.process(point(0, 0))
    shifted = datetime.fromisoformat("2026-01-01T05:30:01+05:30")
    assert detector.process(Observation("s", shifted, 1)).timestamp == point(1, 1).timestamp
    with pytest.raises(ContractError):
        detector.process(Observation("s", shifted, 1))
    assert detector.process(point(2, 2)).ready


@pytest.mark.parametrize("field", ["threshold", "scale_floor"])
@pytest.mark.parametrize("bad", [0, -1, True, "1", float("nan"), float("inf")])
def test_invalid_numeric_config_is_rejected(field: str, bad: object) -> None:
    with pytest.raises(ContractError):
        config(**{field: bad})


@pytest.mark.parametrize("stride", [0, 2, -1, True, 1.0])
def test_only_fresh_or_full_block_strides_are_supported(stride: object) -> None:
    with pytest.raises(ContractError):
        config(refresh_stride=stride)


@pytest.mark.parametrize(
    "values", [(2, 1, 3), (1, 3, 2), (0, float("nan"), 1), (-1e308, 0, 1e308), (False, 0, 1)]
)
def test_invalid_forecast_intervals_reject(values: tuple[float, float, float]) -> None:
    with pytest.raises(ContractError):
        ForecastInterval(*values)


@pytest.mark.parametrize("failure", ["short", "wrong_type", "raise", "overflow"])
def test_model_failure_requires_reset_and_propagates_programming_errors(failure: str) -> None:
    class BadModel(RecordingModel):
        def forecast(self, history: tuple[float, ...], horizon: int) -> list[ForecastInterval]:
            if failure == "raise":
                raise RuntimeError("model defect")
            if failure == "short":
                return []
            if failure == "wrong_type":
                return [None] * horizon  # type: ignore[list-item]
            return [ForecastInterval(-1e308, -1e308, -1e308)] * horizon

    model = BadModel()
    detector = ForecastIntervalDetector(config(), model)
    detector.process(point(0, 0))
    detector.process(point(1, 0))
    with pytest.raises(RuntimeError if failure == "raise" else ContractError):
        detector.process(point(2, 1e308))
    with pytest.raises(ContractError, match="requires reset"):
        detector.process(point(3, 0))
    detector.reset()
    assert not detector.process(point(0, 0)).ready


def test_order_and_series_fail_before_model_call_without_poisoning_context() -> None:
    model = RecordingModel()
    detector = ForecastIntervalDetector(config(), model)
    detector.process(point(0, 0))
    detector.process(point(1, 1))
    for bad in (point(1, 9), point(2, 9, "other")):
        with pytest.raises(ContractError):
            detector.process(bad)
    assert model.calls == []
    assert detector.process(point(2, 2)).ready
    assert model.calls == [((0, 1), 3)]


def test_calibration_wraps_forecast_score_and_retains_interval_evidence() -> None:
    base = ForecastIntervalDetector(config(), RecordingModel())
    detector = CalibratedDetector(
        base,
        PriorScoreQuantile(QuantileThresholdConfig(window_size=3, min_history=2, quantile=1)),
    )
    results = [detector.process(point(i, v)) for i, v in enumerate([0, 0, 10, 0, 20])]
    assert [p.score for p in results] == [None, None, 4.5, 4.5, 9.5]
    assert results[-1].threshold == 4.5
    assert results[-1].label == "ANOMALOUS"
    assert "q10=-1.0; q50=0.0; q90=1.0" in results[-1].evidence.reason
    assert "prior_scores=2" in results[-1].evidence.reason


def test_interleaved_series_equal_isolated_forecasts() -> None:
    shared_model = RecordingModel()

    def factory() -> ForecastIntervalDetector:
        return ForecastIntervalDetector(config(refresh_stride=3), shared_model)

    left = [point(i, float(i), "a") for i in range(8)]
    right = [point(i, 100 + float(i), "b") for i in range(8)]
    mixed = [p for pair in zip(left, right, strict=True) for p in pair]
    combined = [p for p, _ in process_stream(mixed, factory)]
    for series, stream in (("a", left), ("b", right)):
        assert [p for p in combined if p.series_id == series] == [
            p for p, _ in process_stream(stream, factory)
        ]
