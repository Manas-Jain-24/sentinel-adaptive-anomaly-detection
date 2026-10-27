"""Hand-derived quantiles and state invariants; synthetic software verification."""

import json
from dataclasses import asdict
from itertools import permutations
from math import isfinite
from sys import maxsize
from typing import Any

import pytest

from sentinel.contracts import ContractError
from sentinel.detectors.thresholds import PriorScoreQuantile, QuantileThresholdConfig


def calibrator(**changes: Any) -> PriorScoreQuantile:
    settings = {"window_size": 4, "min_history": 3, "quantile": 0.5, "fallback_threshold": 9}
    return PriorScoreQuantile(QuantileThresholdConfig(**(settings | changes)))


def test_short_history_uses_fallback_then_prior_only_reference_quantile() -> None:
    model = calibrator()
    decisions = [model.process(v) for v in [4, 1, 3, 100, 2]]
    assert [d.threshold for d in decisions] == [9, 9, 9, 3, 3]
    assert [d.history_size for d in decisions] == [0, 1, 2, 3, 4]
    assert [d.method for d in decisions] == ["fallback"] * 3 + ["nearest_rank"] * 2
    assert [d.rank for d in decisions] == [None, None, None, 2, 2]
    assert [d.anomalous for d in decisions] == [False, False, False, True, False]
    assert model.threshold_state().threshold == 2


@pytest.mark.parametrize(
    ("quantile", "rank", "threshold"),
    [(0, 1, 1), (0.25, 1, 1), (0.26, 2, 3), (0.5, 2, 3), (0.75, 3, 7), (1, 4, 9)],
)
def test_nearest_rank_endpoints_and_boundaries(
    quantile: float, rank: int, threshold: float
) -> None:
    model = calibrator(min_history=4, quantile=quantile)
    for value in [9, 1, 7, 3]:
        model.process(value)
    result = model.process(5)
    assert result.rank == rank
    assert result.threshold == threshold
    assert result.anomalous == (5 >= threshold)


@pytest.mark.parametrize(("quantile", "rank"), [(0.07, 7), (0.28, 28), (0.99, 99), (1, 100)])
def test_decimal_integral_rank_is_not_rounded_up_by_float_multiplication(
    quantile: float, rank: int
) -> None:
    model = calibrator(window_size=100, min_history=100, quantile=quantile)
    for score in range(1, 101):
        model.process(score)
    state = model.threshold_state()
    assert state.rank == rank
    assert state.threshold == rank


@pytest.mark.parametrize("history", list(permutations([1, 2, 9])))
def test_empirical_quantile_depends_on_values_not_prior_order(history: tuple[int, ...]) -> None:
    model = calibrator(window_size=3)
    for score in history:
        model.process(score)
    assert model.threshold_state().threshold == 2


def test_current_score_cannot_raise_its_own_threshold() -> None:
    low, high = calibrator(quantile=1), calibrator(quantile=1)
    for score in [1, 2, 3]:
        low.process(score)
        high.process(score)
    first, second = low.process(0), high.process(1e308)
    assert first.threshold == second.threshold == 3
    assert first.history_size == second.history_size == 3
    assert first.rank == second.rank == 3
    assert not first.anomalous
    assert second.anomalous
    assert low.threshold_state().threshold == 3
    assert high.threshold_state().threshold == 1e308


def test_inclusive_ties_do_not_imply_a_nominal_false_alarm_rate() -> None:
    model = calibrator(quantile=0.99)
    for _ in range(3):
        model.process(2)
    decisions = [model.process(2) for _ in range(20)]
    assert all(d.threshold == 2 and d.anomalous for d in decisions)


def test_positive_floor_prevents_zero_score_ties_from_flagging_flat_history() -> None:
    model = calibrator(threshold_floor=0.01)
    decisions = [model.process(0) for _ in range(20)]
    assert all(not d.anomalous for d in decisions)
    assert all(d.threshold == 0.01 for d in decisions[3:])


def test_floor_applies_to_nonzero_empirical_threshold_and_equality_flags() -> None:
    model = calibrator(threshold_floor=0.5)
    for value in [1e-8, 2e-8, 3e-8]:
        model.process(value)
    decision = model.process(0.5)
    assert decision.threshold == 0.5
    assert decision.anomalous


def test_flagged_scores_enter_history_and_contamination_expires_at_capacity() -> None:
    model = calibrator(window_size=3, min_history=2, quantile=1)
    model.process(1)
    model.process(1)
    assert model.process(100).anomalous
    assert model.threshold_state().threshold == 100
    for _ in range(3):
        model.process(1)
    assert model.threshold_state().threshold == 1
    assert model.process(2).anomalous


def test_single_score_window_is_causal_and_bounded() -> None:
    model = calibrator(window_size=1, min_history=1, quantile=1, fallback_threshold=4)
    decisions = [model.process(v) for v in [2, 3, 0]]
    assert [d.threshold for d in decisions] == [4, 2, 3]
    assert [d.history_size for d in decisions] == [0, 1, 1]
    assert [d.anomalous for d in decisions] == [False, True, False]
    assert model.threshold_state().history_size == 1


def test_history_remains_bounded_on_a_long_score_stream() -> None:
    model = calibrator(window_size=16, min_history=4)
    for index in range(4096):
        decision = model.process(float((index * 7) % 37))
        assert decision.history_size == min(index, 16)
        assert model.threshold_state().history_size == min(index + 1, 16)


def test_queries_do_not_advance_state_and_reset_restores_fallback() -> None:
    model = calibrator()
    empty = model.threshold_state()
    assert model.threshold_state() == empty
    for score in [1, 2, 3]:
        model.process(score)
    current = model.threshold_state()
    assert model.threshold_state() == current
    model.reset()
    assert model.threshold_state() == empty
    assert model.process(4) == calibrator().process(4)
    json.dumps(model.config.to_dict(), allow_nan=False)


@pytest.mark.parametrize(
    "value", [None, True, "1", -1, float("nan"), float("inf"), -float("inf"), 10**400]
)
def test_invalid_score_rejects_without_mutating_history(value: Any) -> None:
    model, control = calibrator(), calibrator()
    for score in [1, 2, 3]:
        model.process(score)
        control.process(score)
    before = model.threshold_state()
    with pytest.raises(ContractError):
        model.process(value)
    assert model.threshold_state() == before
    assert model.process(4) == control.process(4)


@pytest.mark.parametrize(
    "changes",
    [
        {"window_size": 0},
        {"window_size": True},
        {"window_size": 3.0},
        {"window_size": maxsize + 1},
        {"min_history": 0},
        {"min_history": True},
        {"min_history": 257},
        {"quantile": -0.01},
        {"quantile": 1.01},
        {"quantile": True},
        {"quantile": "0.99"},
        {"quantile": float("nan")},
        {"quantile": float("inf")},
        {"fallback_threshold": 0},
        {"fallback_threshold": -1},
        {"fallback_threshold": True},
        {"fallback_threshold": float("inf")},
        {"threshold_floor": 0},
        {"threshold_floor": float("nan")},
        {"threshold_floor": 5},
        {"threshold_floor": 10**400},
    ],
)
def test_invalid_local_configuration_is_an_explicit_contract_error(changes: dict[str, Any]) -> None:
    with pytest.raises(ContractError):
        QuantileThresholdConfig(**changes)


def test_extreme_finite_scores_do_not_require_interpolation_or_overflowing_sums() -> None:
    model = calibrator(window_size=2, min_history=2)
    model.process(1e308)
    model.process(1.6e308)
    result = model.process(1.7e308)
    assert result.threshold == 1e308
    assert isfinite(result.threshold)
    assert result.anomalous


def test_future_suffix_preserves_earlier_decisions_and_thresholds() -> None:
    values = [float((i * 7) % 19) for i in range(40)] + [1e100, 0, 1e90]
    short_model, full_model = calibrator(), calibrator()
    prefix = [short_model.process(v) for v in values[:20]]
    snapshot = json.dumps([asdict(x) for x in prefix], allow_nan=False)
    for score in values[20:]:
        short_model.process(score)
    assert prefix == [full_model.process(v) for v in values][:20]
    assert snapshot == json.dumps([asdict(x) for x in prefix], allow_nan=False)


def test_score_unit_change_requires_matching_fallback_and_floor() -> None:
    values = [0, 0, 1, 2, 3, 100, 1, 0, 2, 1]
    original = calibrator(fallback_threshold=4, threshold_floor=0.125)
    scaled = calibrator(fallback_threshold=32, threshold_floor=1)
    for value in values:
        left, right = original.process(value), scaled.process(8 * value)
        assert right.threshold == 8 * left.threshold
        assert right.anomalous == left.anomalous
