"""Compose causal features into explicit level/change/optional-seasonal scores."""

from datetime import UTC, datetime
from math import isfinite

from sentinel.config import DetectorConfig
from sentinel.contracts import (
    ContractError,
    Evidence,
    FeatureExtractor,
    FeatureFrame,
    Observation,
    Prediction,
)


def _invalid_frame(message: str) -> ContractError:
    return ContractError(f"Invalid feature frame: {message}; reset and replay before continuing")


def _validate_frame(frame: FeatureFrame, observation: Observation) -> None:
    if not isinstance(frame, FeatureFrame):
        raise _invalid_frame("extractor must return FeatureFrame")
    if frame.series_id != observation.series_id:
        raise _invalid_frame("series_id does not match the observation")
    timestamp = frame.timestamp
    if (
        not isinstance(timestamp, datetime)
        or timestamp.tzinfo is None
        or timestamp.utcoffset() is None
        or timestamp.astimezone(UTC) != observation.timestamp
    ):
        raise _invalid_frame("timestamp does not match the observation instant")
    if type(frame.ready) is not bool:
        raise _invalid_frame("ready must be a boolean")
    if type(frame.history_size) is not int or frame.history_size < 0:
        raise _invalid_frame("history_size must be a nonnegative integer")
    for name in ("expected_level", "expected_delta", "scale", "delta", "seasonal_expected"):
        value = getattr(frame, name)
        if value is not None:
            if type(value) not in (int, float):
                raise _invalid_frame(f"{name} must be a finite number or null")
            try:
                finite = isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                raise _invalid_frame(f"{name} must be finite; rescale input explicitly")
    if frame.ready:
        if frame.history_size < 2:
            raise _invalid_frame("ready requires at least two preceding observations")
        if any(
            value is None
            for value in (frame.expected_level, frame.expected_delta, frame.scale, frame.delta)
        ):
            raise _invalid_frame("ready requires level, expected_delta, scale and current delta")
        assert frame.scale is not None
        if frame.scale <= 0:
            raise _invalid_frame("ready scale must be positive")


class ResidualDetector:
    """Max of comparable residual magnitudes; no score calibration or drift guard.

    The injected extractor owns readiness/windowing and must be exclusive to this
    detector. Constructor/reset clears it. DetectorConfig supplies the fixed
    threshold and scale floor; routing/window settings belong to their owners.
    Seasonal scoring is disabled unless explicitly enabled, with a level/change
    fallback when its reference is unavailable. All output uses shared v1 types.

    FeatureExtractor.process may update before returning. Any failure after that
    call begins therefore requires reset/replay; v1 has no rollback interface.
    """

    def __init__(
        self, config: DetectorConfig, extractor: FeatureExtractor, *, use_seasonal: bool = False
    ) -> None:
        if type(use_seasonal) is not bool:
            raise ContractError("use_seasonal must be a boolean")
        self.config = config
        self._extractor = extractor
        self._use_seasonal = use_seasonal
        self.reset()

    def reset(self) -> None:
        self._needs_reset = True
        self._extractor.reset()
        self._last: Observation | None = None
        self._needs_reset = False

    def process(self, observation: Observation) -> Prediction:
        if self._needs_reset:
            raise ContractError(
                "Residual detector requires reset and replay after feature/scoring failure"
            )
        observation = Observation(
            observation.series_id, observation.timestamp.astimezone(UTC), float(observation.value)
        )
        if self._last is not None:
            if observation.series_id != self._last.series_id:
                raise ContractError("A detector instance handles only one series")
            if observation.timestamp <= self._last.timestamp:
                raise ContractError("Timestamps must be strictly increasing within each series")

        # Leave this set on any extractor, frame-validation or scoring exception.
        self._needs_reset = True
        frame = self._extractor.process(observation)
        _validate_frame(frame, observation)
        baseline = float(frame.expected_level) if frame.expected_level is not None else None
        score = scale = residual = None
        components: dict[str, float] = {}
        reason = "warmup"
        if frame.ready:
            assert frame.expected_level is not None
            assert frame.expected_delta is not None
            assert frame.delta is not None
            assert frame.scale is not None
            assert baseline is not None
            scale = max(float(frame.scale), float(self.config.scale_floor))
            residual = observation.value - baseline
            references = [
                ("level", observation.value, baseline),
                ("change", float(frame.delta), float(frame.expected_delta)),
            ]
            if self._use_seasonal and frame.seasonal_expected is not None:
                references.append(("seasonal", observation.value, float(frame.seasonal_expected)))
            formulas = []
            for name, actual, expected in references:
                signed = actual - expected
                magnitude = abs(signed) / scale
                if not isfinite(signed) or not isfinite(magnitude):
                    raise ContractError(
                        f"Numerical overflow in {name} residual; rescale input and reset/replay"
                    )
                components[name] = magnitude
                formulas.append(f"{name}=abs({actual!r} - {expected!r}) / {scale!r}")
            score = max(components.values())
            reason = "residual_max: max(" + ", ".join(formulas) + ")"
            if self._use_seasonal and frame.seasonal_expected is None:
                reason += "; seasonal=unavailable"

        prediction = Prediction(
            series_id=observation.series_id,
            timestamp=observation.timestamp,
            value=observation.value,
            score=score,
            threshold=self.config.threshold,
            label="ANOMALOUS" if score is not None and score >= self.config.threshold else "NORMAL",
            ready=frame.ready,
            evidence=Evidence(
                baseline=baseline,
                scale=scale,
                residual=residual,
                history_size=frame.history_size,
                reason=reason,
                component_scores=components,
            ),
        )
        self._last = observation
        self._needs_reset = False
        return prediction
