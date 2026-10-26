"""Execute against the exact published MN-02/KS-02 modules before their merge."""

from datetime import UTC, datetime, timedelta

import pytest

from sentinel.config import DetectorConfig
from sentinel.contracts import Detector, Observation, Prediction
from sentinel.detectors.calibrated import CalibratedDetector
from sentinel.detectors.thresholds import PriorScoreQuantile, QuantileThresholdConfig

features = pytest.importorskip("sentinel.data.features", reason="Published KS-02 is unmerged")
residual = pytest.importorskip("sentinel.detectors.residual", reason="Published MN-02 is unmerged")
START = datetime(2026, 1, 1, tzinfo=UTC)


def inputs() -> list[Observation]:
    return [
        Observation("s", START + timedelta(minutes=i), float((i * 7) % 19 + (i // 11) * 3))
        for i in range(48)
    ]


def base_detector() -> Detector:
    return residual.ResidualDetector(
        DetectorConfig(window_size=4, min_history=2, scale_floor=0.5),
        features.RollingFeatureExtractor(
            window_size=4, min_history=2, scale_floor=0.5, seasonal_period=3
        ),
        use_seasonal=True,
    )


def model() -> CalibratedDetector:
    return CalibratedDetector(
        base_detector(),
        PriorScoreQuantile(
            QuantileThresholdConfig(window_size=3, min_history=2, quantile=1, threshold_floor=0.01)
        ),
    )


def replay(points: list[Observation]) -> list[Prediction]:
    detector = model()
    return [detector.process(point) for point in points]


def test_published_residual_combined_score_is_calibrated_without_changing_components() -> None:
    raw, calibrated = base_detector(), model()
    previous: list[float] = []
    for point in inputs():
        before = raw.process(point)
        after = calibrated.process(point)
        expected = 4 if len(previous) < 2 else max(0.01, *previous[-3:])
        assert after.threshold == expected
        assert after.score == before.score
        assert after.ready == before.ready
        assert after.evidence.component_scores == before.evidence.component_scores
        assert after.evidence.reason.startswith(before.evidence.reason + "; calibration=")
        if before.ready:
            assert before.score == max(before.evidence.component_scores.values())
            assert after.label == ("ANOMALOUS" if before.score >= expected else "NORMAL")
            previous.append(before.score)


@pytest.mark.parametrize("lookback", [7, 9])
def test_full_feature_plus_calibration_support_replays_target_predictions(lookback: int) -> None:
    points = inputs()
    full = replay(points)
    target_start, target_stop = 20, 30
    restarted = replay(points[target_start - lookback : target_stop])
    assert restarted[lookback:] == full[target_start:target_stop]


def test_feature_only_context_does_not_reproduce_the_prior_score_buffer() -> None:
    points = inputs()
    full = replay(points)
    target_start, target_stop, lookback = 20, 30, 4
    restarted = replay(points[target_start - lookback : target_stop])
    first_target = restarted[lookback]
    assert first_target.ready
    assert "prior_scores=2" in first_target.evidence.reason
    assert "prior_scores=3" in full[target_start].evidence.reason
    assert first_target != full[target_start]
