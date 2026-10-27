"""Hand-derived arithmetic and causal lifecycle checks; all data are synthetic."""

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone
from math import isfinite, sqrt
from pathlib import Path

import pytest

from sentinel.config import DetectorConfig
from sentinel.contracts import ContractError, Detector, Observation, Prediction
from sentinel.data.io import read_observations, read_windows
from sentinel.detectors.rolling import RollingMADStarter
from sentinel.detectors.zscore import RollingZScoreDetector
from sentinel.evaluation.reference import event_metrics
from sentinel.pipeline import prediction_record, process_stream

Factory = Callable[[DetectorConfig], Detector]
BASELINES = (RollingMADStarter, RollingZScoreDetector)
START = datetime(2026, 1, 1, tzinfo=UTC)
FIXTURES = Path(__file__).parents[1] / "fixtures"


def observation(index: int, value: float, series: str = "s") -> Observation:
    return Observation(series, START + timedelta(minutes=index), value)


def replay(detector: Detector, values: list[float], series: str = "s") -> list[Prediction]:
    return [detector.process(observation(i, value, series)) for i, value in enumerate(values)]


@pytest.mark.parametrize(
    ("history", "value", "baseline", "scale", "score"),
    [
        ([2, 4, 4, 4, 5, 5, 7, 9], 11, 5, 2, 3),
        ([-2, -4, -4, -4, -5, -5, -7, -9], -11, -5, 2, 3),
        ([0, 0, 0, 4], 4, 1, sqrt(3), sqrt(3)),
    ],
)
def test_zscore_matches_population_reference(
    history: list[float], value: float, baseline: float, scale: float, score: float
) -> None:
    detector = RollingZScoreDetector(
        DetectorConfig(window_size=len(history), min_history=len(history), threshold=3)
    )
    replay(detector, history)
    result = detector.process(observation(len(history), value))
    assert result.ready
    assert result.evidence.baseline == pytest.approx(baseline)
    assert result.evidence.scale == pytest.approx(scale)
    assert result.evidence.residual == pytest.approx(value - baseline)
    assert result.score == pytest.approx(score)
    assert result.evidence.component_scores == {"level": result.score}
    assert result.evidence.reason == "rolling_z_deviation"


@pytest.mark.parametrize(
    ("history", "value", "baseline", "scale"),
    [
        ([1, 2, 3, 4, 5], 6, 3, 1.4826),
        ([1, 2, 4, 9], 7, 3, 2.2239),
        ([0, 0, 0, 100, 100], 2, 0, 0.25),
    ],
)
def test_mad_starter_matches_hand_derived_odd_even_and_contaminated_history(
    history: list[float], value: float, baseline: float, scale: float
) -> None:
    detector = RollingMADStarter(
        DetectorConfig(window_size=len(history), min_history=len(history), scale_floor=0.25)
    )
    replay(detector, history)
    result = detector.process(observation(len(history), value))
    assert result.evidence.baseline == baseline
    assert result.evidence.scale == pytest.approx(scale)
    assert result.evidence.residual == value - baseline
    assert result.score == pytest.approx(abs(value - baseline) / scale)
    assert result.evidence.reason == "rolling_mad_deviation"
    assert result.evidence.component_scores == {"level": result.score}


@pytest.mark.parametrize("factory", BASELINES)
@pytest.mark.parametrize("minimum", [2, 5])
def test_warmup_uses_only_preceding_observations(factory: Factory, minimum: int) -> None:
    detector = factory(
        DetectorConfig(window_size=5, min_history=minimum, threshold=4, scale_floor=0.5)
    )
    for i in range(minimum):
        result = detector.process(observation(i, 10))
        assert not result.ready
        assert result.score is None
        assert result.label == "NORMAL"
        assert result.evidence.baseline == (None if i == 0 else 10)
        assert result.evidence.scale is None
        assert result.evidence.residual is None
        assert result.evidence.history_size == i
        assert result.evidence.component_scores == {}
        assert result.evidence.reason == "warmup"
    spike = detector.process(observation(minimum, 12))
    assert spike.ready
    assert spike.evidence.baseline == 10
    assert spike.evidence.history_size == minimum
    assert spike.score == 4
    assert spike.label == "ANOMALOUS"


@pytest.mark.parametrize("factory", BASELINES)
@pytest.mark.parametrize(("value", "score"), [(8, 4), (12, 4), (9, 2), (11, 2), (10, 0)])
def test_absolute_score_orientation_and_inclusive_threshold(
    factory: Factory, value: float, score: float
) -> None:
    detector = factory(DetectorConfig(min_history=2, threshold=4, scale_floor=0.5))
    replay(detector, [10, 10])
    result = detector.process(observation(2, value))
    assert result.score == score
    assert result.threshold == 4
    assert result.label == ("ANOMALOUS" if score >= 4 else "NORMAL")


@pytest.mark.parametrize("factory", BASELINES)
def test_floor_applies_to_small_nonzero_scale(factory: Factory) -> None:
    detector = factory(DetectorConfig(min_history=2, scale_floor=0.5))
    replay(detector, [-0.1, 0.1])
    result = detector.process(observation(2, 1))
    assert result.evidence.baseline == 0
    assert result.evidence.scale == 0.5
    assert result.score == 2


@pytest.mark.parametrize(
    ("factory", "expected_scale"), [(RollingMADStarter, 1.4826), (RollingZScoreDetector, 1)]
)
def test_window_evicts_old_values(factory: Factory, expected_scale: float) -> None:
    detector = factory(DetectorConfig(window_size=2, min_history=2))
    results = replay(detector, [100, 0, 2, 3])
    latest = results[-1]
    assert latest.evidence.history_size == 2
    assert latest.evidence.baseline == 1
    assert latest.evidence.scale == pytest.approx(expected_scale)
    assert latest.score == pytest.approx(2 / expected_scale)


@pytest.mark.parametrize("factory", BASELINES)
@pytest.mark.parametrize(
    ("index", "series", "error"),
    [(1, "s", "strictly increasing"), (0, "s", "strictly increasing"), (2, "other", "one series")],
)
def test_invalid_sequence_does_not_update_state(
    factory: Factory, index: int, series: str, error: str
) -> None:
    detector = factory(DetectorConfig(min_history=2))
    control = factory(DetectorConfig(min_history=2))
    replay(detector, [1, 3])
    replay(control, [1, 3])
    with pytest.raises(ContractError, match=error):
        detector.process(observation(index, 999, series))
    assert detector.process(observation(2, 5)) == control.process(observation(2, 5))


@pytest.mark.parametrize("factory", BASELINES)
def test_reset_clears_history_series_and_timestamp(factory: Factory) -> None:
    detector = factory(DetectorConfig(min_history=2))
    replay(detector, [1, 3, 99])
    detector.reset()
    fresh = factory(DetectorConfig(min_history=2))
    assert replay(detector, [10, 10, 12], "new") == replay(fresh, [10, 10, 12], "new")


@pytest.mark.parametrize("factory", BASELINES)
def test_isolated_spike_is_flagged_before_update_and_history_recovers(factory: Factory) -> None:
    detector = factory(DetectorConfig(window_size=5, min_history=5, scale_floor=0.5))
    results = replay(detector, [10] * 8 + [14] + [10] * 10)
    assert results[8].label == "ANOMALOUS"
    assert results[8].evidence.baseline == 10
    assert results[8].score == 8
    assert all(result.label == "NORMAL" for result in results[9:])
    assert results[-1].evidence.baseline == 10
    assert results[-1].score == 0


@pytest.mark.parametrize("factory", BASELINES)
def test_persistent_shift_is_eventually_absorbed_without_guard(factory: Factory) -> None:
    detector = factory(DetectorConfig(window_size=4, min_history=4, scale_floor=0.5))
    results = replay(detector, [10] * 8 + [14] * 8 + [10] * 8)
    assert results[8].label == "ANOMALOUS"
    assert results[8].score == 8
    assert results[12].evidence.baseline == 14
    assert results[12].score == 0
    assert results[12].label == "NORMAL"
    assert results[16].label == "ANOMALOUS"
    assert results[16].score == 8
    assert results[20].evidence.baseline == 10
    assert results[20].score == 0


@pytest.mark.parametrize("factory", BASELINES)
def test_future_suffix_cannot_change_prefix_decisions_or_evidence(factory: Factory) -> None:
    config = DetectorConfig(window_size=4, min_history=3)
    values = [2, 4, 4, 4, 5, 5, 7, 9, 1000, -1000, 4, 5]
    detector = factory(config)
    prefix = replay(detector, values[:8])
    snapshot = json.dumps([prediction_record(p, 0) for p in prefix], allow_nan=False)
    for i in range(8, len(values)):
        detector.process(observation(i, values[i]))
    assert prefix == replay(factory(config), values)[:8]
    assert snapshot == json.dumps([prediction_record(p, 0) for p in prefix], allow_nan=False)


@pytest.mark.parametrize("factory", BASELINES)
def test_affine_value_transforms_with_scaled_floor_preserve_scores(factory: Factory) -> None:
    values = [2, 4, 4, 4, 5, 5, 7, 9, 11, 5, 4, 4]
    original = replay(factory(DetectorConfig(min_history=3, scale_floor=0.25)), values)
    transformed = replay(
        factory(DetectorConfig(min_history=3, scale_floor=2)), [100 + 8 * value for value in values]
    )
    for left, right in zip(original, transformed, strict=True):
        assert left.ready == right.ready
        assert left.label == right.label
        assert left.score == pytest.approx(right.score)


@pytest.mark.parametrize("factory", BASELINES)
def test_interleaved_pipeline_matches_independent_series(factory: Factory) -> None:
    config = DetectorConfig(window_size=4, min_history=2)
    series_a = [observation(i, value, "a") for i, value in enumerate([1, 1, 8, 1, 1])]
    series_b = [observation(i, value, "b") for i, value in enumerate([100, 100, 100, 150, 100])]
    mixed = [item for pair in zip(series_a, series_b, strict=True) for item in pair]
    predictions = [p for p, _ in process_stream(mixed, lambda: factory(config))]
    for series, observations in (("a", series_a), ("b", series_b)):
        independent = [p for p, _ in process_stream(observations, lambda: factory(config))]
        assert [p for p in predictions if p.series_id == series] == independent


@pytest.mark.parametrize(
    ("history", "value", "baseline", "scale"),
    [([1e308, 1e308], 1e308, 1e308, 0.1), ([-1e308, 1e308], 0, 0, 1e308)],
)
def test_zscore_large_finite_statistics_do_not_overflow_intermediate_sum(
    history: list[float], value: float, baseline: float, scale: float
) -> None:
    detector = RollingZScoreDetector(DetectorConfig(min_history=2))
    replay(detector, history)
    result = detector.process(observation(2, value))
    assert result.evidence.baseline == baseline
    assert result.evidence.scale == scale
    assert result.score == 0
    json.dumps(prediction_record(result, 0), allow_nan=False)


@pytest.mark.parametrize(
    ("history", "bad_value", "valid_value", "floor"),
    [([1e308, 1e308], -1e308, 1e308, 0.1), ([0, 0], 1e308, 0, 1e-308)],
)
def test_zscore_numeric_overflow_is_explicit_and_does_not_update_state(
    history: list[float], bad_value: float, valid_value: float, floor: float
) -> None:
    config = DetectorConfig(min_history=2, scale_floor=floor)
    detector = RollingZScoreDetector(config)
    control = RollingZScoreDetector(config)
    replay(detector, history)
    replay(control, history)
    with pytest.raises(ContractError, match="overflow.*rescale"):
        detector.process(observation(2, bad_value))
    assert detector.process(observation(2, valid_value)) == control.process(
        observation(2, valid_value)
    )


def test_zscore_normalizes_direct_offset_observations_to_utc() -> None:
    detector = RollingZScoreDetector(DetectorConfig(min_history=2))
    timestamp = START.astimezone(timezone(timedelta(hours=5, minutes=30)))
    result = detector.process(Observation("s", timestamp, 1))
    assert result.timestamp == START
    assert result.timestamp.tzinfo == UTC


def test_zscore_fixture_replays_and_serializes_through_existing_public_interfaces() -> None:
    config = DetectorConfig()
    results = list(
        process_stream(
            read_observations(FIXTURES / "synthetic_stream.csv"),
            lambda: RollingZScoreDetector(config),
            config.max_series,
        )
    )
    records = [prediction_record(prediction, elapsed) for prediction, elapsed in results]
    assert len(records) == 16
    assert sum(prediction.ready for prediction, _ in results) == 8
    assert all(elapsed >= 0 for _, elapsed in results)
    assert all(
        prediction.score is None or (isfinite(prediction.score) and prediction.score >= 0)
        for prediction, _ in results
    )
    json.dumps(records, allow_nan=False)
    metrics = event_metrics(records, read_windows(FIXTURES / "synthetic_windows.json"))
    assert metrics["metric_id"] == "provisional_event_trigger_f1_v0"
    assert not metrics["official_metric"]
    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (1, 0, 0)
