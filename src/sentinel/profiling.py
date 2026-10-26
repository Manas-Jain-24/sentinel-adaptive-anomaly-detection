"""Bounded-memory replay timing and workload accounting, independent of detector state."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sentinel.contracts import Prediction, timestamp_text


class TimingDistribution:
    """Integer histogram with <1/128 relative bin overestimate; exact below 256 ns."""

    def __init__(self) -> None:
        self._bins: dict[int, int] = {}
        self._count = self._total = 0
        self._minimum: int | None = None
        self._maximum: int | None = None

    def add(self, elapsed_ns: int) -> None:
        if type(elapsed_ns) is not int or elapsed_ns < 0:
            raise ValueError("elapsed_ns must be a nonnegative integer")
        shift = max(0, elapsed_ns.bit_length() - 8)
        upper = ((elapsed_ns >> shift) + 1) * (1 << shift) - 1
        self._bins[upper] = self._bins.get(upper, 0) + 1
        self._count += 1
        self._total += elapsed_ns
        self._minimum = elapsed_ns if self._minimum is None else min(self._minimum, elapsed_ns)
        self._maximum = elapsed_ns if self._maximum is None else max(self._maximum, elapsed_ns)

    def summary(self) -> dict[str, Any]:
        ordered = sorted(self._bins.items())

        def percentile(percent: int) -> int | None:
            rank = (self._count * percent + 99) // 100
            cumulative = 0
            for upper, count in ordered:
                cumulative += count
                if cumulative >= rank:
                    return upper
            return None

        return {
            "count": self._count,
            "total_ns": self._total,
            "min_ns": self._minimum,
            "max_ns": self._maximum,
            "p50_upper_bound_ns": percentile(50),
            "p95_upper_bound_ns": percentile(95),
            "histogram": [{"upper_bound_ns": upper, "count": count} for upper, count in ordered],
        }


@dataclass
class _SeriesWorkload:
    first: datetime
    last: datetime
    observations: int = 0
    ready: int = 0


class ReplayProfile:
    """Track populations separately: learning warmup differs from first-call cold time."""

    def __init__(self) -> None:
        self._series: dict[str, _SeriesWorkload] = {}
        self._timings = {
            name: TimingDistribution()
            for name in (
                "all_process",
                "ready_process",
                "warmup_process",
                "cold_process",
                "warm_process",
            )
        }

    def record(self, prediction: Prediction, elapsed_ns: int) -> None:
        cold = prediction.series_id not in self._series
        series = self._series.setdefault(
            prediction.series_id, _SeriesWorkload(prediction.timestamp, prediction.timestamp)
        )
        series.last = prediction.timestamp
        series.observations += 1
        series.ready += int(prediction.ready)
        self._timings["all_process"].add(elapsed_ns)
        self._timings["ready_process" if prediction.ready else "warmup_process"].add(elapsed_ns)
        self._timings["cold_process" if cold else "warm_process"].add(elapsed_ns)

    def timings(self) -> dict[str, Any]:
        return {
            "clock": "perf_counter_ns",
            "unit": "ns",
            "quantile_method": "nearest_rank_histogram_upper_bound",
            "quantile_relative_overestimate_limit": 1 / 128,
            "process_region": (
                "process() only; excludes factory, routing, parsing, writing, profiler"
            ),
            "cold_region": (
                "first process() per series; excludes construction and interpreter startup"
            ),
            "warm_region": "subsequent process() calls, including any remaining learning warmup",
            "distributions": {name: timing.summary() for name, timing in self._timings.items()},
        }

    def workload(self) -> dict[str, Any]:
        return {
            "series_count": len(self._series),
            "cadence_policy": "input timestamps as supplied; no resampling or replay sleeps",
            "series": {
                name: {
                    "observations": series.observations,
                    "ready_observations": series.ready,
                    "warmup_observations": series.observations - series.ready,
                    "first_timestamp": timestamp_text(series.first),
                    "last_timestamp": timestamp_text(series.last),
                }
                for name, series in sorted(self._series.items())
            },
        }
