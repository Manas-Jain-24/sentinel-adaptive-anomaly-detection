from dataclasses import replace
from datetime import UTC, datetime, timedelta, tzinfo
from math import isfinite
from typing import Any

import pytest

from sentinel.contracts import ContractError, FeatureExtractor, Observation, parse_timestamp
from sentinel.data.features import RollingFeatureExtractor


def point(index: int, value: float, series: str = "s") -> Observation:
    return Observation(series, datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=index), value)


def test_known_level_delta_and_scale_use_only_prior_window() -> None:
    extractor: FeatureExtractor = RollingFeatureExtractor(window_size=3, min_history=2)
    first, second, third, fourth, fifth = [
        extractor.process(point(i, v)) for i, v in enumerate([1, 3, 9, 7, 8])
    ]
    assert not first.ready
    assert first.history_size == 0
    assert first.delta is None
    assert first.expected_level is first.expected_delta is first.scale is None
    assert not second.ready
    assert second.delta == 2
    assert second.expected_level is second.expected_delta is second.scale is None
    assert third.ready
    assert (third.history_size, third.expected_level, third.expected_delta, third.delta) == (
        2,
        2,
        2,
        6,
    )
    assert third.scale == pytest.approx(1.4826)
    assert (fourth.expected_level, fourth.expected_delta, fourth.delta) == (3, 4, -2)
    assert fourth.scale == pytest.approx(2.9652)
    assert (fifth.history_size, fifth.expected_level, fifth.expected_delta, fifth.delta) == (
        3,
        7,
        2,
        1,
    )
    assert fifth.scale == pytest.approx(2.9652)


def test_prefix_and_current_value_cannot_change_expected_statistics() -> None:
    points = [point(i, float((i * 7) % 19)) for i in range(40)]

    def frames(items: list[Observation]) -> list[Any]:
        extractor = RollingFeatureExtractor(window_size=8, min_history=3, seasonal_period=5)
        return [extractor.process(p) for p in items]

    short = frames(points[:17])
    assert short == frames(points)[:17]
    modified = points[:16] + [replace(points[16], value=9999)]
    changed = frames(modified)[-1]
    assert changed.delta != short[-1].delta
    assert replace(changed, delta=short[-1].delta) == short[-1]


def test_seasonal_lag_requires_past_context_and_readiness() -> None:
    extractor = RollingFeatureExtractor(window_size=4, min_history=2, seasonal_period=4)
    frames = [extractor.process(point(i, v)) for i, v in enumerate([10, 20, 30, 40, 100, 200])]
    assert all(frame.seasonal_expected is None for frame in frames[:4])
    assert frames[2].ready
    assert frames[4].seasonal_expected == 10
    assert frames[5].seasonal_expected == 20
    assert frames[5].history_size == 4


def test_no_seasonal_guess_and_constant_scale_floor() -> None:
    extractor = RollingFeatureExtractor(window_size=3, min_history=2, scale_floor=0.25)
    frames = [extractor.process(point(i, 5)) for i in range(20)]
    for frame in frames[2:]:
        assert frame.expected_level == 5
        assert frame.expected_delta == 0
        assert frame.delta == 0
        assert frame.scale == 0.25
        assert frame.seasonal_expected is None
        assert frame.history_size <= 3


def test_instances_isolate_interleaved_series_and_reset_identity() -> None:
    a = RollingFeatureExtractor(min_history=2)
    b = RollingFeatureExtractor(min_history=2)
    a.process(point(0, 1, "a"))
    b.process(point(0, 100, "b"))
    a.process(point(1, 3, "a"))
    b.process(point(1, 100, "b"))
    assert a.process(point(2, 8, "a")).expected_level == 2
    assert b.process(point(2, 100, "b")).expected_level == 100
    a.reset()
    frame = a.process(point(0, 7, "other"))
    assert frame.history_size == 0
    assert frame.delta is None


@pytest.mark.parametrize("bad_point", [point(0, 8), point(-1, 8), point(1, 8, "other")])
def test_rejected_point_does_not_mutate_state(bad_point: Observation) -> None:
    extractor = RollingFeatureExtractor(min_history=2)
    extractor.process(point(0, 1))
    with pytest.raises(ContractError):
        extractor.process(bad_point)
    accepted = extractor.process(point(1, 3))
    assert accepted.history_size == 1
    assert accepted.delta == 2


def test_offset_instants_normalize_to_utc_and_duplicates_are_rejected() -> None:
    extractor = RollingFeatureExtractor(min_history=2)
    first = Observation("s", parse_timestamp("2026-01-01T05:30:00+05:30"), 1)
    assert extractor.process(first).timestamp == datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ContractError, match="increasing"):
        extractor.process(point(0, 2))
    assert extractor.process(point(1, 3)).delta == 2


def test_fold_aware_timestamps_are_ordered_by_instant_not_wall_clock() -> None:
    class FoldOffset(tzinfo):
        def utcoffset(self, dt: datetime | None) -> timedelta:
            assert dt is not None
            return timedelta(hours=-5 if dt.fold else -4)

        def dst(self, dt: datetime | None) -> timedelta:
            return timedelta(0)

    zone = FoldOffset()
    early = Observation("s", datetime(2026, 11, 1, 1, 30, tzinfo=zone, fold=0), 1)
    late = Observation("s", datetime(2026, 11, 1, 1, 15, tzinfo=zone, fold=1), 2)
    extractor = RollingFeatureExtractor(min_history=2)
    extractor.process(early)
    result = extractor.process(late)
    assert result.timestamp == datetime(2026, 11, 1, 6, 15, tzinfo=UTC)
    assert result.delta == 1
    extractor.reset()
    extractor.process(late)
    with pytest.raises(ContractError, match="increasing"):
        extractor.process(early)


@pytest.mark.parametrize(
    "settings",
    [
        {"window_size": 1},
        {"window_size": True},
        {"window_size": 3.0},
        {"min_history": 1},
        {"min_history": 9, "window_size": 8},
        {"min_history": True},
        {"scale_floor": 0},
        {"scale_floor": -1},
        {"scale_floor": True},
        {"scale_floor": "0.1"},
        {"scale_floor": float("nan")},
        {"scale_floor": float("inf")},
        {"scale_floor": 10**1000},
        {"seasonal_period": 0},
        {"seasonal_period": True},
        {"seasonal_period": 2.0},
        {"seasonal_period": 33},
    ],
)
def test_invalid_constructor_settings_fail(settings: dict[str, Any]) -> None:
    with pytest.raises(ContractError):
        RollingFeatureExtractor(**settings)


def test_overflow_fails_before_updating_and_recovery_is_possible() -> None:
    extractor = RollingFeatureExtractor(min_history=2)
    extractor.process(point(0, 1e308))
    with pytest.raises(ContractError, match="overflow"):
        extractor.process(point(1, -1e308))
    assert extractor.process(point(1, 1e308)).history_size == 1
    frame = extractor.process(point(2, 1e308))
    assert frame.expected_level == 1e308
    assert frame.expected_delta == 0
    assert frame.scale == 0.1
    assert all(isfinite(v) for v in (frame.expected_level, frame.expected_delta, frame.scale))


def test_large_integer_inputs_report_unrepresentable_delta_as_contract_error() -> None:
    extractor = RollingFeatureExtractor(min_history=2)
    extractor.process(point(0, -(10**308)))
    with pytest.raises(ContractError, match="overflow"):
        extractor.process(point(1, 10**308))
    assert extractor.process(point(1, -(10**308))).delta == 0


def test_scale_overflow_is_not_emitted_or_silently_clamped() -> None:
    extractor = RollingFeatureExtractor(window_size=3, min_history=2)
    for i, value in enumerate([-1.7e308, 0, 1.7e308]):
        extractor.process(point(i, value))
    with pytest.raises(ContractError, match="overflow"):
        extractor.process(point(3, 1.7e308))
    extractor.reset()
    assert extractor.process(point(0, 0)).history_size == 0
