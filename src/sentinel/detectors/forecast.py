"""Causal forecast-interval scoring with an injected, separately owned model.

No model library, network access, fitting or checkpoint is hidden in this module.
Chronos/TimesFM adapters can implement QuantileForecaster after their own review.
"""

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC
from math import isfinite
from sys import maxsize
from typing import Protocol

from sentinel.contracts import ContractError, Evidence, Observation, Prediction, timestamp_text
from sentinel.detectors.thresholds import _finite_number


@dataclass(frozen=True)
class ForecastInterval:
    """One future point's q10, q50 and q90 in original input units."""

    lower: float
    median: float
    upper: float

    def __post_init__(self) -> None:
        low = _finite_number(self.lower, "forecast lower")
        middle = _finite_number(self.median, "forecast median")
        high = _finite_number(self.upper, "forecast upper")
        if not low <= middle <= high:
            raise ContractError("Forecast requires lower <= median <= upper")
        if not isfinite(high - low):
            raise ContractError("Forecast interval width overflow; rescale explicitly")


class QuantileForecaster(Protocol):
    """An inference-only model returning the next horizon q10/q50/q90 points.

    Receives only preceding values in chronological order. Adapters must not fit
    on evaluation futures, normalize on an entire trace, fetch labels, or retain
    mutable per-series state. Model weights can be shared; contexts cannot.
    """

    def forecast(self, history: Sequence[float], horizon: int) -> Sequence[ForecastInterval]: ...


@dataclass(frozen=True)
class ForecastDetectorConfig:
    """Local proposed settings, independent of the unchanged shared CLI config."""

    context_window: int = 64
    min_history: int = 16
    horizon: int = 8
    refresh_stride: int = 1
    threshold: float = 4.0
    scale_floor: float = 0.1

    def __post_init__(self) -> None:
        for name in ("context_window", "min_history", "horizon", "refresh_stride"):
            if type(getattr(self, name)) is not int:
                raise ContractError(f"{name} must be an integer")
        if not 1 <= self.min_history <= self.context_window <= maxsize:
            raise ContractError("Require 1 <= min_history <= context_window <= sys.maxsize")
        if not 1 <= self.horizon <= maxsize or self.refresh_stride not in (1, self.horizon):
            raise ContractError("Require horizon >= 1 and refresh_stride either 1 or horizon")
        if _finite_number(self.threshold, "forecast threshold") <= 0:
            raise ContractError("forecast threshold must be positive")
        if _finite_number(self.scale_floor, "forecast scale_floor") <= 0:
            raise ContractError("forecast scale_floor must be positive")


class ForecastIntervalDetector:
    """Score the current value against a forecast made exclusively from its past.

    Stride 1 refreshes a complete horizon per scored observation and uses its first
    point. Stride horizon consumes a frozen block without seeing future actuals.
    Prediction evidence retains interval/origin/age, even after the next refresh.
    Any failure after a model call requires reset and full replay. Reset clears
    local contexts/blocks, but cannot undo model fitting or adapter side effects.
    """

    def __init__(self, config: ForecastDetectorConfig, forecaster: QuantileForecaster) -> None:
        self.config = config
        self._model = forecaster
        self.reset()

    def reset(self) -> None:
        self._history: deque[float] = deque(maxlen=self.config.context_window)
        self._last: Observation | None = None
        self._block: tuple[ForecastInterval, ...] = ()
        self._origin: Observation | None = None
        self._offset = 0
        self._needs_reset = False

    def process(self, observation: Observation) -> Prediction:
        if self._needs_reset:
            raise ContractError("Forecast detector requires reset and replay after model failure")
        observation = Observation(
            observation.series_id, observation.timestamp.astimezone(UTC), float(observation.value)
        )
        if self._last is not None:
            if observation.series_id != self._last.series_id:
                raise ContractError("A detector instance handles only one series")
            if observation.timestamp <= self._last.timestamp:
                raise ContractError("Timestamps must be strictly increasing within each series")
        size = len(self._history)
        score = baseline = scale = residual = None
        components: dict[str, float] = {}
        reason = "warmup"
        ready = size >= self.config.min_history
        if ready:
            self._needs_reset = True
            if self.config.refresh_stride == 1 or self._offset == len(self._block):
                raw = tuple(self._model.forecast(tuple(self._history), self.config.horizon))
                if len(raw) != self.config.horizon:
                    raise ContractError("Forecast must return exactly horizon intervals")
                if not all(isinstance(item, ForecastInterval) for item in raw):
                    raise ContractError("Forecast must return ForecastInterval values")
                self._block = raw
                self._origin = self._last
                self._offset = 0
            interval = self._block[self._offset]
            assert self._origin is not None
            low, baseline, high = map(float, (interval.lower, interval.median, interval.upper))
            width = high - low
            scale = max(width, float(self.config.scale_floor))
            residual = observation.value - baseline
            excess = max(0.0, low - observation.value, observation.value - high)
            score = excess / scale
            if not all(isfinite(value) for value in (residual, excess, score)):
                raise ContractError(
                    "Forecast scoring overflow; rescale explicitly and reset/replay"
                )
            components = {"interval_exceedance": score}
            reason = (
                f"forecast_interval: max(0, {low!r} - {observation.value!r}, "
                f"{observation.value!r} - {high!r}) / {scale!r}; "
                f"q10={low!r}; q50={baseline!r}; q90={high!r}; width={width!r}; "
                f"origin={timestamp_text(self._origin.timestamp)}; "
                f"age_points={self._offset + 1}; horizon={self.config.horizon}; "
                f"refresh_stride={self.config.refresh_stride}"
            )
        result = Prediction(
            series_id=observation.series_id,
            timestamp=observation.timestamp,
            value=observation.value,
            score=score,
            threshold=self.config.threshold,
            label="ANOMALOUS" if score is not None and score >= self.config.threshold else "NORMAL",
            ready=ready,
            evidence=Evidence(baseline, scale, residual, size, reason, components),
        )
        if ready:
            self._offset += 1
        self._history.append(observation.value)
        self._last = observation
        self._needs_reset = False
        return result
