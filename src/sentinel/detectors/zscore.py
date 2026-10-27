"""Causal rolling mean/population-standard-deviation comparator for MN-01."""

from collections import deque
from datetime import UTC
from math import isfinite
from statistics import mean, pstdev

from sentinel.config import DetectorConfig
from sentinel.contracts import ContractError, Evidence, Observation, Prediction


class RollingZScoreDetector:
    """Score against the previous bounded window, then append the current value.

    The score is abs(value - mean) / max(population_stddev, scale_floor),
    a nonnegative deviation magnitude rather than a probability. All successful
    observations, including anomalies, enter history. No drift guard is applied.
    Statistics are recomputed in O(W) time with O(W) bounded state.
    """

    def __init__(self, config: DetectorConfig) -> None:
        self.config = config
        self.reset()

    def reset(self) -> None:
        self._history: deque[float] = deque(maxlen=self.config.window_size)
        self._last: Observation | None = None

    def process(self, observation: Observation) -> Prediction:
        if self._last is not None:
            if observation.series_id != self._last.series_id:
                raise ContractError("A detector instance handles only one series")
            if observation.timestamp <= self._last.timestamp:
                raise ContractError("Timestamps must be strictly increasing within each series")

        history_size = len(self._history)
        # statistics.mean avoids overflow in the sum of large finite inputs.
        baseline = mean(self._history) if self._history else None
        ready = history_size >= self.config.min_history
        score = scale = residual = None
        if ready:
            assert baseline is not None
            scale = max(pstdev(self._history), self.config.scale_floor)
            residual = observation.value - baseline
            score = abs(residual) / scale
            if not all(isfinite(value) for value in (baseline, scale, residual, score)):
                raise ContractError(
                    "Numerical overflow in z-score calculation; rescale input explicitly"
                )

        prediction = Prediction(
            series_id=observation.series_id,
            timestamp=observation.timestamp.astimezone(UTC),
            value=observation.value,
            score=score,
            threshold=self.config.threshold,
            label="ANOMALOUS" if score is not None and score >= self.config.threshold else "NORMAL",
            ready=ready,
            evidence=Evidence(
                baseline=baseline,
                scale=scale,
                residual=residual,
                history_size=history_size,
                reason="warmup" if not ready else "rolling_z_deviation",
                component_scores={} if score is None else {"level": score},
            ),
        )
        self._history.append(observation.value)
        self._last = observation
        return prediction
