"""Attach prior-score calibration without changing Detector or Prediction v1."""

from dataclasses import replace
from datetime import UTC, datetime

from sentinel.contracts import ContractError, Detector, Evidence, Observation, Prediction
from sentinel.detectors.thresholds import PriorScoreQuantile, _finite_number


def _validate_prediction(raw: Prediction, observation: Observation) -> float | None:
    if not isinstance(raw, Prediction):
        raise ContractError("Base detector must return Prediction")
    if (
        raw.series_id != observation.series_id
        or _finite_number(raw.value, "base value") != observation.value
    ):
        raise ContractError("Base prediction identity/value does not match observation")
    if (
        not isinstance(raw.timestamp, datetime)
        or raw.timestamp.tzinfo is None
        or raw.timestamp.utcoffset() is None
        or raw.timestamp.astimezone(UTC) != observation.timestamp
    ):
        raise ContractError("Base prediction timestamp does not match observation")
    if type(raw.ready) is not bool:
        raise ContractError("Base prediction ready must be a boolean")
    if _finite_number(raw.threshold, "base threshold") <= 0:
        raise ContractError("Base threshold must be positive")
    score = None
    if raw.ready:
        if raw.score is None:
            raise ContractError("Ready base prediction requires a score")
        score = _finite_number(raw.score, "base score")
        if score < 0:
            raise ContractError("Base score must be nonnegative")
    elif raw.score is not None:
        raise ContractError("Warmup base prediction requires a null score")
    expected = "ANOMALOUS" if score is not None and score >= raw.threshold else "NORMAL"
    if raw.label != expected:
        raise ContractError("Base prediction label contradicts its score/threshold")
    evidence = raw.evidence
    if not isinstance(evidence, Evidence):
        raise ContractError("Base prediction requires Evidence")
    if type(evidence.history_size) is not int or evidence.history_size < 0:
        raise ContractError("Base evidence history_size must be a nonnegative integer")
    if not isinstance(evidence.reason, str) or not isinstance(evidence.component_scores, dict):
        raise ContractError("Base evidence requires reason text and component scores")
    for name in ("baseline", "scale", "residual"):
        value = getattr(evidence, name)
        if value is not None:
            _finite_number(value, f"evidence {name}")
    for name, value in evidence.component_scores.items():
        if not isinstance(name, str) or not name:
            raise ContractError("Component names must be nonempty strings")
        if _finite_number(value, f"component {name}") < 0:
            raise ContractError("Component scores must be nonnegative")
    return score


class CalibratedDetector:
    """Re-label a base score using a threshold from strictly preceding scores.

    Each instance owns one base detector and calibrator; construction/reset clears
    both. Feature warmup is preserved and contributes no calibration sample.
    Calibration short history uses its configured fallback without hiding a valid
    base score. Errors after a base call require reset/replay, since Detector v1
    does not provide a rollback interface. No fitted state or labels are accepted.
    """

    def __init__(self, detector: Detector, calibrator: PriorScoreQuantile) -> None:
        self._base = detector
        self._calibrator = calibrator
        self.reset()

    def reset(self) -> None:
        self._needs_reset = True
        self._base.reset()
        self._calibrator.reset()
        self._last: Observation | None = None
        self._needs_reset = False

    def process(self, observation: Observation) -> Prediction:
        if self._needs_reset:
            raise ContractError(
                "Calibrated detector requires reset and replay after a base failure"
            )
        observation = Observation(
            observation.series_id, observation.timestamp.astimezone(UTC), float(observation.value)
        )
        if self._last is not None:
            if observation.series_id != self._last.series_id:
                raise ContractError("A detector instance handles only one series")
            if observation.timestamp <= self._last.timestamp:
                raise ContractError("Timestamps must be strictly increasing within each series")
        self._needs_reset = True
        raw = self._base.process(observation)
        score = _validate_prediction(raw, observation)
        state = (
            self._calibrator.threshold_state() if score is None else self._calibrator.process(score)
        )
        config = self._calibrator.config
        reason = (
            f"{raw.evidence.reason}; calibration={state.method}; "
            f"prior_scores={state.history_size}; quantile={config.quantile!r}; rank={state.rank}; "
            f"calibration_window={config.window_size}; min_scores={config.min_history}; "
            f"threshold_floor={config.threshold_floor!r}"
        )
        result = replace(
            raw,
            timestamp=observation.timestamp,
            score=score,
            threshold=state.threshold,
            label="ANOMALOUS" if score is not None and score >= state.threshold else "NORMAL",
            evidence=replace(
                raw.evidence,
                reason=reason,
                component_scores=dict(raw.evidence.component_scores),
            ),
        )
        self._last = observation
        self._needs_reset = False
        return result
