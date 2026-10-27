"""MN-02 consumer tests with deterministic, deliberately simple extractor doubles."""

import json
from collections import deque
from dataclasses import replace
from datetime import UTC, datetime, timedelta, tzinfo
from pathlib import Path
from typing import Any, cast

import pytest

from sentinel.config import DetectorConfig
from sentinel.contracts import ContractError, FeatureFrame, Observation, Prediction
from sentinel.data.io import read_observations, read_windows
from sentinel.detectors.residual import ResidualDetector
from sentinel.evaluation.reference import event_metrics
from sentinel.pipeline import prediction_record, process_stream

START = datetime(2026, 1, 1, tzinfo=UTC)
FIXTURES = Path(__file__).parents[1] / "fixtures"


def observation(index: int = 0, value: float = 16, series: str = "s") -> Observation:
    return Observation(series, START + timedelta(seconds=index), value)


def feature_frame(**changes: Any) -> FeatureFrame:
    return replace(FeatureFrame("s", START, 10.0, 1.0, 2.0, 5.0, None, 8, True), **changes)


class ScriptedExtractor:
    """Return supplied frames/errors; consume one entry before consumer validation."""

    def __init__(self, frames: list[FeatureFrame | Exception]) -> None:
        self.frames = frames
        self.calls: list[Observation] = []
        self.resets = 0
        self.index = 0

    def reset(self) -> None:
        self.index = 0
        self.resets += 1

    def process(self, value: Observation) -> FeatureFrame:
        self.calls.append(value)
        result = self.frames[self.index]
        self.index += 1
        if isinstance(result, Exception):
            raise result
        return result


class LagExtractor:
    """Test double: previous-value expectation, fixed unit scale, zero expected delta."""

    def __init__(self) -> None:
        self.calls = 0
        self.reset()

    def reset(self) -> None:
        self.history: deque[float] = deque(maxlen=2)

    def process(self, value: Observation) -> FeatureFrame:
        self.calls += 1
        ready = len(self.history) == 2
        previous = self.history[-1] if self.history else None
        frame = FeatureFrame(
            value.series_id,
            value.timestamp,
            previous if ready else None,
            0.0 if ready else None,
            1.0 if ready else None,
            value.value - previous if previous is not None else None,
            self.history[0] if ready else None,
            len(self.history),
            ready,
        )
        self.history.append(value.value)
        return frame


def replay(detector: ResidualDetector, values: list[float]) -> list[Prediction]:
    return [detector.process(observation(i, value)) for i, value in enumerate(values)]


@pytest.mark.parametrize(
    ("value", "changes", "components", "formulas"),
    [
        (
            16,
            {},
            {"level": 3, "change": 2},
            ["level=abs(16.0 - 10.0) / 2.0", "change=abs(5.0 - 1.0) / 2.0"],
        ),
        (
            12,
            {"delta": 9.0},
            {"level": 1, "change": 4},
            ["level=abs(12.0 - 10.0) / 2.0", "change=abs(9.0 - 1.0) / 2.0"],
        ),
        (
            14,
            {"expected_level": 12.0, "delta": 2.0, "expected_delta": 0.0, "seasonal_expected": 4.0},
            {"level": 1, "change": 1, "seasonal": 5},
            ["seasonal=abs(14.0 - 4.0) / 2.0"],
        ),
        (
            6,
            {"delta": -5.0},
            {"level": 2, "change": 3},
            ["level=abs(6.0 - 10.0) / 2.0", "change=abs(-5.0 - 1.0) / 2.0"],
        ),
    ],
)
def test_hand_derived_components_and_explanations_reproduce_combined_score(
    value: float, changes: dict[str, Any], components: dict[str, float], formulas: list[str]
) -> None:
    extractor = ScriptedExtractor([feature_frame(**changes)])
    result = ResidualDetector(
        DetectorConfig(threshold=3), extractor, use_seasonal="seasonal" in components
    ).process(observation(value=value))
    assert result.ready
    assert result.evidence.component_scores == components
    assert result.score == max(components.values())
    assert result.label == "ANOMALOUS"
    assert result.evidence.baseline == changes.get("expected_level", 10.0)
    assert result.evidence.residual == value - result.evidence.baseline
    assert result.evidence.scale == 2
    assert result.evidence.reason.startswith("residual_max: max(")
    assert all(formula in result.evidence.reason for formula in formulas)
    assert len(extractor.calls) == 1
    json.dumps(prediction_record(result, 0), allow_nan=False)


@pytest.mark.parametrize(
    ("threshold", "label"), [(2.9, "ANOMALOUS"), (3, "ANOMALOUS"), (3.1, "NORMAL")]
)
def test_fixed_threshold_is_inclusive(threshold: float, label: str) -> None:
    result = ResidualDetector(
        DetectorConfig(threshold=threshold), ScriptedExtractor([feature_frame()])
    ).process(observation())
    assert result.score == 3
    assert result.threshold == threshold
    assert result.label == label


def test_detector_floor_clamps_a_positive_feature_scale() -> None:
    result = ResidualDetector(
        DetectorConfig(scale_floor=0.5), ScriptedExtractor([feature_frame(scale=0.01)])
    ).process(observation())
    assert result.evidence.scale == 0.5
    assert result.evidence.component_scores == {"level": 12, "change": 8}
    assert result.score == 12
    assert " / 0.5" in result.evidence.reason


@pytest.mark.parametrize("seasonal_expected", [None, 0.0, 1e308])
def test_disabled_seasonal_branch_cannot_change_prediction(seasonal_expected: float | None) -> None:
    reference = ResidualDetector(DetectorConfig(), ScriptedExtractor([feature_frame()])).process(
        observation()
    )
    result = ResidualDetector(
        DetectorConfig(), ScriptedExtractor([feature_frame(seasonal_expected=seasonal_expected)])
    ).process(observation())
    assert result == reference


def test_missing_seasonal_reference_falls_back_without_delaying_readiness() -> None:
    result = ResidualDetector(
        DetectorConfig(), ScriptedExtractor([feature_frame()]), use_seasonal=True
    ).process(observation())
    assert result.ready
    assert result.score == 3
    assert result.evidence.component_scores == {"level": 3, "change": 2}
    assert result.evidence.reason.endswith("; seasonal=unavailable")


@pytest.mark.parametrize("size", [0, 1, 8])
def test_extractor_controls_warmup_even_if_statistics_are_present(size: int) -> None:
    result = ResidualDetector(
        DetectorConfig(), ScriptedExtractor([feature_frame(ready=False, history_size=size)])
    ).process(observation())
    assert not result.ready
    assert result.score is None
    assert result.label == "NORMAL"
    assert result.evidence.baseline == 10
    assert result.evidence.scale is None
    assert result.evidence.residual is None
    assert result.evidence.component_scores == {}
    assert result.evidence.reason == "warmup"


def test_null_warmup_values_are_supported() -> None:
    frame = feature_frame(
        ready=False,
        history_size=0,
        expected_level=None,
        expected_delta=None,
        delta=None,
        scale=None,
    )
    result = ResidualDetector(DetectorConfig(), ScriptedExtractor([frame])).process(observation())
    assert result.evidence.baseline is None
    assert result.score is None


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"series_id": "wrong"}, "series_id"),
        ({"timestamp": START + timedelta(seconds=1)}, "timestamp"),
        ({"timestamp": START.replace(tzinfo=None)}, "timestamp"),
        ({"ready": 1}, "boolean"),
        ({"history_size": True}, "history_size"),
        ({"history_size": -1}, "history_size"),
        ({"history_size": 1.5}, "history_size"),
        ({"history_size": 1}, "two preceding"),
        ({"expected_level": None}, "ready requires"),
        ({"expected_delta": None}, "ready requires"),
        ({"delta": None}, "ready requires"),
        ({"scale": None}, "ready requires"),
        ({"scale": 0}, "positive"),
        ({"scale": -1}, "positive"),
        ({"expected_level": True}, "finite number"),
        ({"scale": "2"}, "finite number"),
        ({"expected_delta": 10**400}, "finite"),
    ],
)
def test_malformed_feature_frame_fails_visibly(changes: dict[str, Any], message: str) -> None:
    detector = ResidualDetector(DetectorConfig(), ScriptedExtractor([feature_frame(**changes)]))
    with pytest.raises(ContractError, match=message):
        detector.process(observation())


@pytest.mark.parametrize(
    "field", ["expected_level", "expected_delta", "delta", "scale", "seasonal_expected"]
)
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_all_present_features_are_finite_even_when_branch_disabled(
    field: str, value: float
) -> None:
    detector = ResidualDetector(
        DetectorConfig(), ScriptedExtractor([feature_frame(**{field: value})])
    )
    with pytest.raises(ContractError, match="finite"):
        detector.process(observation())


@pytest.mark.parametrize("value", [1, 0, "false", None])
def test_seasonal_option_rejects_non_boolean_values(value: Any) -> None:
    extractor = ScriptedExtractor([feature_frame()])
    with pytest.raises(ContractError, match="boolean"):
        ResidualDetector(DetectorConfig(), extractor, use_seasonal=value)
    assert extractor.resets == 0


def test_invalid_frame_requires_reset_then_allows_replay() -> None:
    extractor = ScriptedExtractor([feature_frame(scale=0)])
    detector = ResidualDetector(DetectorConfig(), extractor)
    with pytest.raises(ContractError, match="positive"):
        detector.process(observation())
    with pytest.raises(ContractError, match="requires reset and replay"):
        detector.process(observation(1))
    assert len(extractor.calls) == 1
    extractor.frames[0] = feature_frame()
    detector.reset()
    assert extractor.resets == 2
    assert detector.process(observation()).score == 3


@pytest.mark.parametrize(
    "failure", [ContractError("feature failure"), RuntimeError("programming failure")]
)
def test_extractor_errors_propagate_and_require_reset(failure: Exception) -> None:
    extractor = ScriptedExtractor([failure])
    detector = ResidualDetector(DetectorConfig(), extractor)
    with pytest.raises(type(failure), match=str(failure)):
        detector.process(observation())
    with pytest.raises(ContractError, match="requires reset and replay"):
        detector.process(observation(1))
    assert len(extractor.calls) == 1
    extractor.frames[0] = feature_frame()
    detector.reset()
    assert detector.process(observation()).ready


def test_wrong_extractor_return_type_is_an_explicit_contract_error() -> None:
    detector = ResidualDetector(DetectorConfig(), ScriptedExtractor([cast(FeatureFrame, None)]))
    with pytest.raises(ContractError, match="must return FeatureFrame"):
        detector.process(observation())


@pytest.mark.parametrize(
    ("value", "changes", "floor", "branch"),
    [
        (-1e308, {"expected_level": 1e308}, 0.1, "level"),
        (16, {"delta": 1e308, "expected_delta": -1e308}, 0.1, "change"),
        (1e308, {"expected_level": 1e308, "seasonal_expected": -1e308}, 0.1, "seasonal"),
        (1e308, {"expected_level": 0, "scale": 1e-308}, 1e-308, "level"),
        (0, {"delta": 10**308, "expected_delta": -(10**308)}, 0.1, "change"),
    ],
)
def test_residual_and_division_overflow_fail_closed(
    value: float, changes: dict[str, Any], floor: float, branch: str
) -> None:
    extractor = ScriptedExtractor([feature_frame(**changes)])
    detector = ResidualDetector(DetectorConfig(scale_floor=floor), extractor, use_seasonal=True)
    with pytest.raises(ContractError, match=f"overflow in {branch}"):
        detector.process(observation(value=value))
    with pytest.raises(ContractError, match="requires reset and replay"):
        detector.process(observation(1))
    assert len(extractor.calls) == 1


@pytest.mark.parametrize(("index", "series"), [(1, "s"), (0, "s"), (2, "wrong")])
def test_sequence_errors_are_checked_before_calling_extractor(index: int, series: str) -> None:
    extractor = LagExtractor()
    detector = ResidualDetector(DetectorConfig(), extractor)
    control = ResidualDetector(DetectorConfig(), LagExtractor())
    replay(detector, [1, 3])
    replay(control, [1, 3])
    with pytest.raises(ContractError):
        detector.process(observation(index, 999, series))
    assert extractor.calls == 2
    assert detector.process(observation(2, 5)) == control.process(observation(2, 5))


def test_reset_clears_both_extractor_and_detector_identity_history_and_time() -> None:
    detector = ResidualDetector(DetectorConfig(), LagExtractor(), use_seasonal=True)
    replay(detector, [1, 3, 5, 100])
    detector.reset()
    fresh = ResidualDetector(DetectorConfig(), LagExtractor(), use_seasonal=True)
    for i, value in enumerate([100, 100, 120]):
        current = observation(i - 10, value, "new")
        assert detector.process(current) == fresh.process(current)


def test_future_suffix_preserves_prefix_and_previous_evidence() -> None:
    values = [1, 1, 2, 3, 20, 2, 3, 5, 1000, -1000, 1]
    detector = ResidualDetector(DetectorConfig(), LagExtractor(), use_seasonal=True)
    prefix = replay(detector, values[:8])
    snapshot = json.dumps([prediction_record(p, 0) for p in prefix], allow_nan=False)
    for i in range(8, len(values)):
        detector.process(observation(i, values[i]))
    fresh = ResidualDetector(DetectorConfig(), LagExtractor(), use_seasonal=True)
    assert prefix == replay(fresh, values)[:8]
    assert json.dumps([prediction_record(p, 0) for p in prefix], allow_nan=False) == snapshot


class FoldTimezone(tzinfo):
    """Small DST-fold test zone, independent of a host's zoneinfo database."""

    def utcoffset(self, value: datetime | None) -> timedelta:
        return -timedelta(hours=5 if value is not None and value.fold else 4)

    def dst(self, value: datetime | None) -> timedelta:
        return timedelta(0)


def test_same_zone_fold_order_uses_utc_instants_and_normalizes_output() -> None:
    detector = ResidualDetector(DetectorConfig(), LagExtractor())
    zone = FoldTimezone()
    first = datetime(2026, 11, 1, 1, 45, tzinfo=zone, fold=0)
    second = datetime(2026, 11, 1, 1, 15, tzinfo=zone, fold=1)
    detector.process(Observation("s", first, 10))
    result = detector.process(Observation("s", second, 12))
    assert result.timestamp == datetime(2026, 11, 1, 6, 15, tzinfo=UTC)
    assert result.timestamp.tzinfo == UTC


def test_interleaved_pipeline_preserves_per_series_state() -> None:
    config = DetectorConfig()
    left = [observation(i, v, "a") for i, v in enumerate([1, 1, 2, 10, 1])]
    right = [observation(i, v, "b") for i, v in enumerate([100, 100, 100, 150, 100])]
    mixed = [item for pair in zip(left, right, strict=True) for item in pair]
    factory = lambda: ResidualDetector(config, LagExtractor(), use_seasonal=True)  # noqa: E731
    predictions = [p for p, _ in process_stream(mixed, factory)]
    for series, observations in (("a", left), ("b", right)):
        independent = [p for p, _ in process_stream(observations, factory)]
        assert [p for p in predictions if p.series_id == series] == independent


def test_fixture_predictions_work_with_existing_serializer_and_provisional_evaluator() -> None:
    config = DetectorConfig()
    results = list(
        process_stream(
            read_observations(FIXTURES / "synthetic_stream.csv"),
            lambda: ResidualDetector(config, LagExtractor()),
            config.max_series,
        )
    )
    records = [prediction_record(prediction, elapsed) for prediction, elapsed in results]
    assert len(records) == 16
    json.dumps(records, allow_nan=False)
    metrics = event_metrics(records, read_windows(FIXTURES / "synthetic_windows.json"))
    assert metrics["metric_id"] == "provisional_event_trigger_f1_v0"
    assert not metrics["official_metric"]
    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (1, 0, 0)
