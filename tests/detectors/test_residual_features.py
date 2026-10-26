"""Run when KS-02 is available; no teammate source is copied into this branch."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sentinel.config import DetectorConfig
from sentinel.contracts import ContractError, Observation, Prediction
from sentinel.data.io import read_observations
from sentinel.detectors.residual import ResidualDetector
from sentinel.detectors.rolling import RollingMADStarter
from sentinel.pipeline import prediction_record, process_stream

features = pytest.importorskip(
    "sentinel.data.features",
    reason="KS-02 is unmerged; run the pinned published-extractor compatibility check",
)
START = datetime(2026, 1, 1, tzinfo=UTC)
FIXTURES = Path(__file__).parents[1] / "fixtures"


def observation(index: int, value: float, series: str = "s") -> Observation:
    return Observation(series, START + timedelta(seconds=index), value)


def make_detector(
    *,
    use_seasonal: bool = True,
    window_size: int = 3,
    min_history: int = 2,
    scale_floor: float = 0.5,
    period: int | None = 3,
) -> ResidualDetector:
    config = DetectorConfig(
        window_size=window_size, min_history=min_history, scale_floor=scale_floor
    )
    extractor = features.RollingFeatureExtractor(
        window_size=window_size,
        min_history=min_history,
        scale_floor=scale_floor,
        seasonal_period=period,
    )
    return ResidualDetector(config, extractor, use_seasonal=use_seasonal)


def replay(detector: ResidualDetector, values: list[float]) -> list[Prediction]:
    return [detector.process(observation(i, value)) for i, value in enumerate(values)]


def test_real_hand_trace_and_seasonal_unavailability_match_independent_arithmetic() -> None:
    results = replay(make_detector(), [1, 3, 9, 7])
    assert [p.ready for p in results] == [False, False, True, True]
    third = results[2]
    assert third.evidence.baseline == 2
    assert third.evidence.scale == pytest.approx(1.4826)
    assert third.evidence.residual == 7
    assert third.evidence.component_scores == pytest.approx(
        {"level": 7 / 1.4826, "change": 4 / 1.4826}
    )
    assert third.score == pytest.approx(7 / 1.4826)
    assert third.evidence.reason.endswith("seasonal=unavailable")
    fourth = results[3]
    assert fourth.evidence.baseline == 3
    assert fourth.evidence.scale == pytest.approx(2.9652)
    assert fourth.evidence.component_scores == pytest.approx(
        {"level": 4 / 2.9652, "change": 6 / 2.9652, "seasonal": 6 / 2.9652}
    )
    assert fourth.score == pytest.approx(6 / 2.9652)
    assert "change=abs(-2.0 - 4.0)" in fourth.evidence.reason
    assert "seasonal=abs(7.0 - 1.0)" in fourth.evidence.reason


def test_real_seasonal_component_exposes_a_missing_synthetic_peak() -> None:
    # Period 4 is declared only for this hand-built trace, not fitted to test labels.
    values = [0, 0, 10, 0] * 3 + [0, 0, 0]
    enabled = replay(make_detector(window_size=4, period=4), values)[-1]
    disabled = replay(make_detector(window_size=4, period=4, use_seasonal=False), values)[-1]
    assert disabled.evidence.component_scores == {"level": 0, "change": 0}
    assert disabled.label == "NORMAL"
    assert enabled.evidence.component_scores == {"level": 0, "change": 0, "seasonal": 20}
    assert enabled.label == "ANOMALOUS"
    assert enabled.score == 20


def test_real_level_component_agrees_with_mad_on_existing_synthetic_fixture() -> None:
    config = DetectorConfig()
    residual = make_detector(
        window_size=config.window_size,
        min_history=config.min_history,
        scale_floor=config.scale_floor,
        period=None,
        use_seasonal=False,
    )
    mad = RollingMADStarter(config)
    for current in read_observations(FIXTURES / "synthetic_stream.csv"):
        result, baseline = residual.process(current), mad.process(current)
        assert result.ready == baseline.ready
        if result.ready:
            assert result.evidence.baseline == baseline.evidence.baseline
            assert result.evidence.scale == pytest.approx(baseline.evidence.scale)
            assert result.evidence.component_scores["level"] == pytest.approx(baseline.score)
            assert result.score == max(result.evidence.component_scores.values())


def test_real_future_suffix_cannot_revise_prefix_evidence() -> None:
    values = [1, 3, 9, 7, 2, 3, 8, 1000, -1000, 7]
    detector = make_detector()
    prefix = replay(detector, values[:7])
    snapshot = json.dumps([prediction_record(p, 0) for p in prefix], allow_nan=False)
    for i in range(7, len(values)):
        detector.process(observation(i, values[i]))
    assert prefix == replay(make_detector(), values)[:7]
    assert snapshot == json.dumps([prediction_record(p, 0) for p in prefix], allow_nan=False)


def test_real_interleaved_pipeline_matches_independent_replays() -> None:
    left = [observation(i, value, "a") for i, value in enumerate([1, 3, 9, 7, 2])]
    right = [observation(i, value, "b") for i, value in enumerate([100, 100, 150, 100, 110])]
    mixed = [item for pair in zip(left, right, strict=True) for item in pair]
    predictions = [p for p, _ in process_stream(mixed, make_detector)]
    for series, observations in (("a", left), ("b", right)):
        expected = [p for p, _ in process_stream(observations, make_detector)]
        assert [p for p in predictions if p.series_id == series] == expected


def test_real_scoring_failure_requires_reset_and_replays_cleanly() -> None:
    detector = make_detector(scale_floor=1e-308, period=None, use_seasonal=False)
    replay(detector, [0, 0])
    with pytest.raises(ContractError, match="overflow"):
        detector.process(observation(2, 1e308))
    with pytest.raises(ContractError, match="requires reset and replay"):
        detector.process(observation(3, 0))
    detector.reset()
    expected = make_detector(scale_floor=1e-308, period=None, use_seasonal=False)
    assert replay(detector, [0, 0, 0]) == replay(expected, [0, 0, 0])


@pytest.mark.parametrize("window", [3, 8])
@pytest.mark.parametrize("period", [None, 3])
def test_real_affine_scale_and_offset_transform_preserves_decisions(
    window: int, period: int | None
) -> None:
    values = [1, 2, 3, 0, 4, 3, 9, 5, 4, 3, 2, 1] * 2
    original = replay(make_detector(window_size=window, period=period, scale_floor=0.5), values)
    transformed = replay(
        make_detector(window_size=window, period=period, scale_floor=4),
        [100 + 8 * value for value in values],
    )
    for left, right in zip(original, transformed, strict=True):
        assert left.ready == right.ready
        assert left.label == right.label
        assert left.score == pytest.approx(right.score)
        assert left.evidence.component_scores == pytest.approx(right.evidence.component_scores)


@pytest.mark.parametrize("window", [2, 32, 64])
def test_real_constant_stream_preserves_finite_zero_scores_and_bounded_history(window: int) -> None:
    results = replay(make_detector(window_size=window, period=None), [10] * 96)
    assert not results[0].ready
    assert not results[1].ready
    assert all(result.ready and result.score == 0 for result in results[2:])
    assert all(result.label == "NORMAL" for result in results)
    assert results[-1].evidence.history_size == window
    assert all(result.evidence.history_size <= window for result in results)
    json.dumps([prediction_record(p, 0) for p in results], allow_nan=False)
