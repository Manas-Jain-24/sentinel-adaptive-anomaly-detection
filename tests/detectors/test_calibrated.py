"""Contract, causality and lifecycle checks for the calibration wrapper."""

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

import pytest

from sentinel.config import DetectorConfig
from sentinel.contracts import ContractError, Evidence, Observation, Prediction
from sentinel.data.io import read_observations, read_windows
from sentinel.detectors.calibrated import CalibratedDetector
from sentinel.detectors.rolling import RollingMADStarter
from sentinel.detectors.thresholds import PriorScoreQuantile, QuantileThresholdConfig
from sentinel.evaluation.reference import event_metrics
from sentinel.pipeline import prediction_record, process_stream

START = datetime(2026, 1, 1, tzinfo=UTC)
FIXTURES = Path(__file__).parents[1] / "fixtures"


def observation(index: int, value: float = 1, series: str = "s") -> Observation:
    return Observation(series, START + timedelta(seconds=index), value)


def quantile() -> PriorScoreQuantile:
    return PriorScoreQuantile(
        QuantileThresholdConfig(window_size=3, min_history=2, quantile=1, threshold_floor=0.01)
    )


class ScriptedDetector:
    def __init__(self, scores: list[float | None | Exception]) -> None:
        self.scores = scores
        self.index = 0
        self.resets = 0
        self.calls: list[Observation] = []
        self.last_prediction: Prediction | None = None

    def reset(self) -> None:
        self.index = 0
        self.resets += 1
        self.last_prediction = None

    def process(self, current: Observation) -> Prediction:
        self.calls.append(current)
        index = self.index
        score = self.scores[index]
        self.index += 1
        if isinstance(score, Exception):
            raise score
        self.last_prediction = Prediction(
            current.series_id,
            current.timestamp,
            current.value,
            score,
            9,
            "ANOMALOUS" if score is not None and score >= 9 else "NORMAL",
            score is not None,
            Evidence(
                0,
                1,
                score,
                index,
                "warmup" if score is None else "scripted_score",
                {} if score is None else {"combined": score},
            ),
        )
        return self.last_prediction


def test_ready_scores_keep_fallback_until_prior_score_minimum_then_relabel() -> None:
    base = ScriptedDetector([None, None, 1, 2, 3])
    calibration = quantile()
    model = CalibratedDetector(base, calibration)
    predictions = [model.process(observation(i)) for i in range(5)]
    assert [p.ready for p in predictions] == [False, False, True, True, True]
    assert [p.score for p in predictions] == [None, None, 1, 2, 3]
    assert [p.threshold for p in predictions] == [4, 4, 4, 4, 2]
    assert [p.label for p in predictions] == ["NORMAL"] * 4 + ["ANOMALOUS"]
    assert "calibration=fallback; prior_scores=0" in predictions[2].evidence.reason
    assert "calibration=nearest_rank; prior_scores=2" in predictions[-1].evidence.reason
    assert "quantile=1; rank=2" in predictions[-1].evidence.reason
    assert predictions[-1].evidence.history_size == 4
    assert predictions[-1].evidence.component_scores == {"combined": 3}
    assert calibration.threshold_state().history_size == 3
    assert len(base.calls) == 5
    assert base.last_prediction is not None
    assert base.last_prediction.label == "NORMAL"
    assert base.last_prediction.threshold == 9
    assert base.last_prediction.evidence.reason == "scripted_score"


def test_intermittent_warmup_does_not_enter_or_erase_prior_scores() -> None:
    calibration = quantile()
    model = CalibratedDetector(ScriptedDetector([1, 2, None, 3]), calibration)
    first = [model.process(observation(i)) for i in range(3)]
    assert first[-1].score is None
    assert not first[-1].ready
    assert first[-1].threshold == 2
    assert first[-1].label == "NORMAL"
    assert calibration.threshold_state().history_size == 2
    assert model.process(observation(3)).threshold == 2


def test_constructor_and_reset_clear_exclusive_base_and_calibration_state() -> None:
    base, calibration = ScriptedDetector([None, 1, 2, 10]), quantile()
    calibration.process(100)
    model = CalibratedDetector(base, calibration)
    assert base.resets == 1
    assert calibration.threshold_state().history_size == 0
    for i in range(4):
        model.process(observation(i))
    model.reset()
    fresh = CalibratedDetector(ScriptedDetector([None, 1, 2, 10]), quantile())
    assert base.resets == 2
    for i in range(4):
        current = observation(i - 10, series="new")
        assert model.process(current) == fresh.process(current)


@pytest.mark.parametrize(("index", "series"), [(1, "s"), (0, "s"), (2, "wrong")])
def test_sequence_errors_do_not_advance_base_or_calibration(index: int, series: str) -> None:
    base, calibration = ScriptedDetector([1, 2, 3]), quantile()
    model = CalibratedDetector(base, calibration)
    control = CalibratedDetector(ScriptedDetector([1, 2, 3]), quantile())
    for i in range(2):
        assert model.process(observation(i)) == control.process(observation(i))
    before = calibration.threshold_state()
    with pytest.raises(ContractError):
        model.process(observation(index, series=series))
    assert len(base.calls) == 2
    assert calibration.threshold_state() == before
    assert model.process(observation(2)) == control.process(observation(2))


@pytest.mark.parametrize("failure", [ContractError("base failure"), RuntimeError("bug")])
def test_base_failures_propagate_then_require_reset_and_replay(failure: Exception) -> None:
    base, calibration = ScriptedDetector([1, failure]), quantile()
    model = CalibratedDetector(base, calibration)
    model.process(observation(0))
    with pytest.raises(type(failure), match=str(failure)):
        model.process(observation(1))
    assert calibration.threshold_state().history_size == 1
    with pytest.raises(ContractError, match="requires reset and replay"):
        model.process(observation(2))
    assert len(base.calls) == 2
    base.scores[1] = 2
    model.reset()
    assert calibration.threshold_state().history_size == 0
    assert model.process(observation(0)).threshold == 4
    assert model.process(observation(1)).threshold == 4


class MalformedDetector(ScriptedDetector):
    def __init__(self, changes: dict[str, Any]) -> None:
        super().__init__([1])
        self.changes = changes

    def process(self, current: Observation) -> Prediction:
        return replace(super().process(current), **self.changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"series_id": "wrong"},
        {"value": 999},
        {"value": True},
        {"timestamp": START.replace(tzinfo=None)},
        {"timestamp": START + timedelta(seconds=1)},
        {"ready": 1},
        {"score": None},
        {"score": -1},
        {"score": True},
        {"score": float("nan")},
        {"score": float("inf")},
        {"score": 10**400},
        {"ready": False},
        {"threshold": 0},
        {"threshold": float("inf")},
        {"threshold": True},
        {"label": "ANOMALOUS"},
        {"evidence": None},
        {"evidence": Evidence(0, 1, 1, True, "bad", {})},
        {"evidence": Evidence(float("inf"), 1, 1, 0, "bad", {})},
        {"evidence": Evidence(0, 1, 1, 0, "bad", {"level": -1})},
        {"evidence": Evidence(0, 1, 1, 0, "bad", {"level": float("nan")})},
        {"evidence": Evidence(0, 1, 1, 0, "bad", {"": 1})},
    ],
)
def test_invalid_base_output_is_visible_and_not_added_to_score_history(
    changes: dict[str, Any],
) -> None:
    calibration = quantile()
    model = CalibratedDetector(MalformedDetector(changes), calibration)
    with pytest.raises(ContractError):
        model.process(observation(0))
    assert calibration.threshold_state().history_size == 0
    with pytest.raises(ContractError, match="requires reset and replay"):
        model.process(observation(1))


def test_wrong_base_return_type_is_an_explicit_contract_error() -> None:
    class WrongDetector(ScriptedDetector):
        def process(self, current: Observation) -> Prediction:
            return cast(Prediction, None)

    model = CalibratedDetector(WrongDetector([1]), quantile())
    with pytest.raises(ContractError, match="return Prediction"):
        model.process(observation(0))


def test_component_evidence_is_copied_without_overwriting_base_reason() -> None:
    base = ScriptedDetector([1])
    result = CalibratedDetector(base, quantile()).process(observation(0))
    assert base.last_prediction is not None
    base.last_prediction.evidence.component_scores["combined"] = 999
    assert result.evidence.component_scores == {"combined": 1}
    assert result.evidence.reason.startswith("scripted_score; calibration=")
    assert base.last_prediction.evidence.reason == "scripted_score"


def test_output_and_base_inputs_normalize_direct_offset_timestamps_to_utc() -> None:
    base = ScriptedDetector([1])
    model = CalibratedDetector(base, quantile())
    offset = timezone(timedelta(hours=5, minutes=30))
    result = model.process(Observation("s", START.astimezone(offset), 1))
    assert result.timestamp.tzinfo == UTC
    assert base.calls[0].timestamp.tzinfo == UTC
    assert result.timestamp == START


def test_future_scores_do_not_rewrite_prefix_thresholds_or_evidence() -> None:
    scores = [float((i * 7) % 19) for i in range(40)] + [1e100]
    model = CalibratedDetector(ScriptedDetector(scores), quantile())
    prefix = [model.process(observation(i)) for i in range(20)]
    snapshot = json.dumps([prediction_record(p, 0) for p in prefix], allow_nan=False)
    for i in range(20, len(scores)):
        model.process(observation(i))
    fresh = CalibratedDetector(ScriptedDetector(scores), quantile())
    assert prefix == [fresh.process(observation(i)) for i in range(len(scores))][:20]
    assert snapshot == json.dumps([prediction_record(p, 0) for p in prefix], allow_nan=False)


def test_interleaved_series_keep_separate_calibration_buffers() -> None:
    config = DetectorConfig(window_size=4, min_history=2, scale_floor=0.5)
    left = [observation(i, v, "a") for i, v in enumerate([1, 1, 2, 10, 1, 2])]
    right = [observation(i, v, "b") for i, v in enumerate([100, 100, 100, 150, 100, 100])]
    mixed = [item for pair in zip(left, right, strict=True) for item in pair]
    factory = lambda: CalibratedDetector(RollingMADStarter(config), quantile())  # noqa: E731
    result = [p for p, _ in process_stream(mixed, factory)]
    for series, items in (("a", left), ("b", right)):
        expected = [p for p, _ in process_stream(items, factory)]
        assert [p for p in result if p.series_id == series] == expected


def test_mad_wrapper_preserves_raw_scores_and_serializes_with_provisional_evaluator() -> None:
    config = DetectorConfig()
    inputs = list(read_observations(FIXTURES / "synthetic_stream.csv"))
    raw_model = RollingMADStarter(config)
    raw = [raw_model.process(current) for current in inputs]
    results = list(
        process_stream(inputs, lambda: CalibratedDetector(RollingMADStarter(config), quantile()))
    )
    records = [prediction_record(p, elapsed) for p, elapsed in results]
    for (current, _), before in zip(results, raw, strict=True):
        assert current.score == before.score
        assert current.ready == before.ready
        assert current.evidence.baseline == before.evidence.baseline
        assert current.evidence.scale == before.evidence.scale
        assert current.evidence.residual == before.evidence.residual
        assert current.evidence.component_scores == before.evidence.component_scores
    assert results[10][0].label == "ANOMALOUS"
    # Once the spike expires from the three-score buffer, this later normal
    # point ties the historical maximum. Shared inclusive equality flags it.
    assert results[14][0].score == results[14][0].threshold
    assert results[14][0].label == "ANOMALOUS"
    json.dumps(records, allow_nan=False)
    metrics = event_metrics(records, read_windows(FIXTURES / "synthetic_windows.json"))
    assert not metrics["official_metric"]
    assert metrics["metric_id"] == "provisional_event_trigger_f1_v0"
    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (1, 1, 0)
