"""Bounded empirical thresholds selected before the current score is stored."""

from collections import deque
from dataclasses import asdict, dataclass
from fractions import Fraction
from math import isfinite
from sys import maxsize
from typing import Any, Literal

from sentinel.contracts import ContractError

ThresholdMethod = Literal["fallback", "nearest_rank"]


def _finite_number(value: float, name: str) -> float:
    if type(value) not in (int, float):
        raise ContractError(f"{name} must be a finite real number")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ContractError(f"{name} must be finite") from exc
    if not isfinite(result):
        raise ContractError(f"{name} must be finite")
    return result


@dataclass(frozen=True)
class QuantileThresholdConfig:
    """Local detector settings; no extension of the shared CLI/config schema."""

    window_size: int = 256
    min_history: int = 32
    quantile: float = 0.99
    fallback_threshold: float = 4.0
    threshold_floor: float = 1e-6

    def __post_init__(self) -> None:
        if type(self.window_size) is not int or type(self.min_history) is not int:
            raise ContractError("Calibration window_size and min_history must be integers")
        if not 1 <= self.min_history <= self.window_size <= maxsize:
            raise ContractError("Require 1 <= min_history <= window_size <= sys.maxsize")
        quantile = _finite_number(self.quantile, "quantile")
        fallback = _finite_number(self.fallback_threshold, "fallback_threshold")
        floor = _finite_number(self.threshold_floor, "threshold_floor")
        if not 0 <= quantile <= 1:
            raise ContractError("quantile must be in [0, 1]")
        if not 0 < floor <= fallback:
            raise ContractError("Require 0 < threshold_floor <= fallback_threshold")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ThresholdState:
    threshold: float
    history_size: int
    method: ThresholdMethod
    rank: int | None


@dataclass(frozen=True)
class ThresholdDecision(ThresholdState):
    score: float
    anomalous: bool


class PriorScoreQuantile:
    """Use earlier valid scores, emit a decision, then append the current score.

    Empirical thresholds use nearest rank ceil(q*n), clamped to rank 1 at q=0.
    q is interpreted by its decimal string to avoid floating multiplication
    moving an integral rank up (for example q=0.07, n=100). No interpolation,
    label input, outlier exclusion or formal false-alarm guarantee is applied.
    O(C log C) query time and O(C) state for calibration capacity C.
    """

    def __init__(self, config: QuantileThresholdConfig) -> None:
        self.config = config
        self._quantile = Fraction(str(config.quantile))
        self.reset()

    def reset(self) -> None:
        self._history: deque[float] = deque(maxlen=self.config.window_size)

    def threshold_state(self) -> ThresholdState:
        size = len(self._history)
        if size < self.config.min_history:
            return ThresholdState(float(self.config.fallback_threshold), size, "fallback", None)
        numerator = self._quantile.numerator * size
        denominator = self._quantile.denominator
        rank = max(1, (numerator + denominator - 1) // denominator)
        ordered = sorted(self._history)
        threshold = max(ordered[rank - 1], float(self.config.threshold_floor))
        return ThresholdState(threshold, size, "nearest_rank", rank)

    def process(self, score: float) -> ThresholdDecision:
        score = _finite_number(score, "score")
        if score < 0:
            raise ContractError("score must be nonnegative")
        state = self.threshold_state()
        decision = ThresholdDecision(
            threshold=state.threshold,
            history_size=state.history_size,
            method=state.method,
            rank=state.rank,
            score=score,
            anomalous=score >= state.threshold,
        )
        self._history.append(score)
        return decision
