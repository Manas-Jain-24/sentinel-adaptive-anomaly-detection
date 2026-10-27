"""Bounded causal features implementing the existing per-series FeatureExtractor."""

from collections import deque
from collections.abc import Sequence
from datetime import UTC
from math import isfinite

from sentinel.contracts import ContractError, FeatureFrame, Observation


def _median(values: Sequence[float]) -> float:
    """Avoid overflow of the sum of two finite middle values."""
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    low, high = ordered[middle - 1], ordered[middle]
    # Same-sign subtraction is bounded; opposite-sign addition cannot overflow.
    if (low >= 0) == (high >= 0):
        return low + (high - low) / 2
    return (low + high) / 2


class RollingFeatureExtractor:
    """One series, prior-window statistics, then exactly one state update.

    Constructor settings are local to this implementation, pending Ayush/Manas
    review for shared config integration. No automatic seasonal-period fitting.
    Period is an observation lag; irregular cadence is never silently imputed.
    Time O(W log W), memory O(W), with 2 <= min_history <= window_size.
    """

    def __init__(
        self,
        *,
        window_size: int = 32,
        min_history: int = 8,
        scale_floor: float = 0.1,
        seasonal_period: int | None = None,
    ) -> None:
        if type(window_size) is not int or type(min_history) is not int:
            raise ContractError("window_size and min_history must be integers")
        if not 2 <= min_history <= window_size:
            raise ContractError("Require 2 <= min_history <= window_size")
        if type(scale_floor) not in (int, float):
            raise ContractError("scale_floor must be finite and positive")
        try:
            floor = float(scale_floor)
        except OverflowError as exc:
            raise ContractError("scale_floor is too large") from exc
        if not isfinite(floor) or floor <= 0:
            raise ContractError("scale_floor must be finite and positive")
        if seasonal_period is not None and (
            type(seasonal_period) is not int or not 1 <= seasonal_period <= window_size
        ):
            raise ContractError("seasonal_period must be an integer in [1, window_size] or None")
        self._window_size = window_size
        self._min_history = min_history
        self._scale_floor = floor
        self._seasonal_period = seasonal_period
        self.reset()

    def reset(self) -> None:
        self._history: deque[float] = deque(maxlen=self._window_size)
        self._last: Observation | None = None

    def process(self, observation: Observation) -> FeatureFrame:
        """Emit finite pre-update features, or fail without changing state."""
        # Observation permits ints and any aware datetime. Normalize once so
        # arithmetic is float-bounded and fold-aware ordering compares instants.
        observation = Observation(
            observation.series_id, observation.timestamp.astimezone(UTC), float(observation.value)
        )
        previous = self._last
        if previous is not None:
            if observation.series_id != previous.series_id:
                raise ContractError("A feature extractor instance handles only one series")
            if observation.timestamp <= previous.timestamp:
                raise ContractError("Timestamps must be strictly increasing within each series")
        history = list(self._history)
        size = len(history)
        ready = size >= self._min_history
        delta = observation.value - previous.value if previous is not None else None
        level = expected_delta = scale = seasonal = None
        if ready:
            level = _median(history)
            deviations = [abs(value - level) for value in history]
            changes = [right - left for left, right in zip(history, history[1:], strict=False)]
            # Check before median/sorting so an overflow never enters order statistics.
            if not all(isfinite(value) for value in deviations + changes):
                raise ContractError(
                    "Numerical overflow in prior features; rescale input explicitly"
                )
            expected_delta = _median(changes)
            scale = max(1.4826 * _median(deviations), self._scale_floor)
            period = self._seasonal_period
            if period is not None and size >= period:
                seasonal = history[-period]
        values = (level, expected_delta, scale, delta, seasonal)
        if not all(value is None or isfinite(value) for value in values):
            raise ContractError("Numerical overflow in features; rescale input explicitly")
        frame = FeatureFrame(
            series_id=observation.series_id,
            timestamp=observation.timestamp.astimezone(UTC),
            expected_level=level,
            expected_delta=expected_delta,
            scale=scale,
            delta=delta,
            seasonal_expected=seasonal,
            history_size=size,
            ready=ready,
        )
        self._history.append(observation.value)
        self._last = observation
        return frame
