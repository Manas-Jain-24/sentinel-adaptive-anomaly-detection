import math

import pytest

from sentinel.profiling import TimingDistribution


@pytest.mark.parametrize(
    "values",
    [
        [0],
        [1, 2],
        list(range(256)),
        list(range(5000, 0, -3)),
        [2**power + delta for power in range(8, 63) for delta in (-1, 0, 1)],
    ],
)
def test_quantile_bounds_against_independent_exact_ranks(values: list[int]) -> None:
    distribution = TimingDistribution()
    for value in values:
        distribution.add(value)
    summary = distribution.summary()
    assert summary["count"] == len(values)
    assert summary["total_ns"] == sum(values)
    assert summary["min_ns"] == min(values)
    assert summary["max_ns"] == max(values)
    assert sum(bucket["count"] for bucket in summary["histogram"]) == len(values)
    for percent in (50, 95):
        exact = sorted(values)[math.ceil(len(values) * percent / 100) - 1]
        bound = summary[f"p{percent}_upper_bound_ns"]
        assert exact <= bound
        if exact < 256:
            assert bound == exact
        else:
            assert (bound - exact) / exact < 1 / 128


def test_empty_population_and_bounded_histogram_storage() -> None:
    distribution = TimingDistribution()
    empty = distribution.summary()
    assert empty["count"] == empty["total_ns"] == 0
    assert empty["p50_upper_bound_ns"] is None
    assert empty["p95_upper_bound_ns"] is None
    assert empty["min_ns"] is empty["max_ns"] is None
    assert empty["histogram"] == []
    # Many distinct durations must not create one retained sample/bin per observation.
    for elapsed in range(100_000):
        distribution.add(elapsed)
    summary = distribution.summary()
    assert summary["count"] == 100_000
    assert len(summary["histogram"]) < 1600


@pytest.mark.parametrize("value", [-1, True, 1.2])
def test_invalid_duration_rejected(value: int) -> None:
    with pytest.raises(ValueError, match="nonnegative integer"):
        TimingDistribution().add(value)
