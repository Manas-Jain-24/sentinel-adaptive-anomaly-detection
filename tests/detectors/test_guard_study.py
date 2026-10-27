"""Guard prototypes remain causal, reversible and outside production imports."""

from dataclasses import replace

import pytest
from guard_study import POLICIES, PolicyPrototype, StudyConfig, scenarios

from sentinel.config import DetectorConfig
from sentinel.contracts import ContractError
from sentinel.data.features import RollingFeatureExtractor
from sentinel.detectors.calibrated import CalibratedDetector
from sentinel.detectors.residual import ResidualDetector
from sentinel.detectors.thresholds import PriorScoreQuantile, QuantileThresholdConfig


@pytest.mark.parametrize("adaptive", [False, True])
def test_no_guard_is_the_real_residual_and_calibration_policy(adaptive: bool) -> None:
    cfg = StudyConfig()
    base = ResidualDetector(DetectorConfig(), RollingFeatureExtractor())
    calibrated = CalibratedDetector(
        base,
        PriorScoreQuantile(
            QuantileThresholdConfig(
                window_size=64, min_history=16, quantile=0.99, threshold_floor=4
            )
        ),
    )
    actual = calibrated if adaptive else base
    study = PolicyPrototype("none", adaptive=adaptive, config=cfg)
    for point in scenarios()[2].observations():
        left, right = study.process(point).prediction, actual.process(point)
        assert replace(right, evidence=left.evidence) == left
        assert left.evidence.component_scores == right.evidence.component_scores


@pytest.mark.parametrize("policy", POLICIES)
@pytest.mark.parametrize("adaptive", [False, True])
def test_future_and_reset_cannot_change_prefix(policy: str, adaptive: bool) -> None:
    model = PolicyPrototype(policy, adaptive=adaptive, config=StudyConfig())
    points = scenarios()[2].observations()
    first = [model.process(p) for p in points[:112]]
    [model.process(p) for p in points[112:]]
    model.reset()
    assert first == [model.process(p) for p in points[:112]]


def test_finite_quarantine_cannot_freeze_reference_forever() -> None:
    cfg = StudyConfig()
    model = PolicyPrototype("quarantine", adaptive=False, config=cfg)
    decisions = [model.process(p) for p in scenarios()[2].observations()]
    streak = 0
    for result in decisions:
        streak = streak + 1 if not result.admitted else 0
        assert streak <= cfg.max_quarantine
    assert any(d.action == "finite_release" for d in decisions)


def test_shadow_switch_is_after_alarm_and_cannot_distinguish_fault_from_benign_shift() -> None:
    outputs = []
    for case in scenarios()[2:4]:
        model = PolicyPrototype("shadow", adaptive=False, config=StudyConfig())
        results = [model.process(p) for p in case.observations()]
        changes = [i for i, d in enumerate(results) if d.action == "shadow_rebaseline"]
        assert changes
        for i in changes:
            assert results[i].prediction.label == "ANOMALOUS"
            assert (
                results[i + 1].prediction.evidence.baseline
                != results[i].prediction.evidence.baseline
            )
        outputs.append(
            [
                (d.prediction.score, d.prediction.threshold, d.prediction.label, d.action)
                for d in results
            ]
        )
    assert outputs[0] == outputs[1]


def test_disabling_guard_replays_exactly_the_no_guard_policy() -> None:
    points = scenarios()[2].observations()
    guarded = PolicyPrototype("shadow", adaptive=True, config=StudyConfig())
    baseline = PolicyPrototype("none", adaptive=True, config=StudyConfig())
    old = [guarded.process(p) for p in points]
    guarded.policy = "none"
    guarded.reset()  # Full replay is required; do not carry selectively admitted state.
    assert [guarded.process(p) for p in points] == [baseline.process(p) for p in points]
    assert any(d.action == "shadow_rebaseline" for d in old)


def test_wrong_order_or_series_reject_without_modifying_prototype_state() -> None:
    points = scenarios()[0].observations()
    model = PolicyPrototype("quarantine", adaptive=True, config=StudyConfig())
    first = model.process(points[0])
    for bad in (points[0], replace(points[1], series_id="other")):
        with pytest.raises(ContractError):
            model.process(bad)
    second = model.process(points[1])
    model.reset()
    assert [first, second] == [model.process(p) for p in points[:2]]
