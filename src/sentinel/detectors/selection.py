"""Explicit, dependency-free model selection for the reviewed detector implementations."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from sentinel.config import DetectorConfig
from sentinel.contracts import ContractError, Detector
from sentinel.data.features import RollingFeatureExtractor
from sentinel.detectors.calibrated import CalibratedDetector
from sentinel.detectors.residual import ResidualDetector
from sentinel.detectors.rolling import RollingMADStarter
from sentinel.detectors.thresholds import PriorScoreQuantile, QuantileThresholdConfig
from sentinel.detectors.zscore import RollingZScoreDetector

DetectorName = Literal["mad", "zscore", "residual"]


@dataclass(frozen=True)
class ModelConfig:
    """Separate model selection; never overload the five-key legacy DetectorConfig."""

    detector: DetectorName = "mad"
    use_seasonal: bool = False
    seasonal_period: int | None = None
    calibration: QuantileThresholdConfig | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.detector, str) or self.detector not in ("mad", "zscore", "residual"):
            raise ContractError("detector must be mad, zscore or residual")
        if type(self.use_seasonal) is not bool:
            raise ContractError("use_seasonal must be a boolean")
        if self.seasonal_period is not None and (
            type(self.seasonal_period) is not int or self.seasonal_period < 1
        ):
            raise ContractError("seasonal_period must be a positive observation lag or null")
        if self.use_seasonal != (self.seasonal_period is not None):
            raise ContractError(
                "Seasonal scoring requires both use_seasonal=true and an explicit lag"
            )
        if self.use_seasonal and self.detector != "residual":
            raise ContractError("Seasonal scoring is supported only by the residual detector")
        if self.calibration is not None and not isinstance(
            self.calibration, QuantileThresholdConfig
        ):
            raise ContractError("calibration must be QuantileThresholdConfig or null")

    def validate_for(self, config: DetectorConfig) -> None:
        if self.seasonal_period is not None and self.seasonal_period > config.window_size:
            raise ContractError("seasonal_period must be <= the base window_size")

    def to_dict(self) -> dict[str, Any]:
        return {
            "detector": self.detector,
            "use_seasonal": self.use_seasonal,
            "seasonal_period": self.seasonal_period,
            "calibration": None if self.calibration is None else self.calibration.to_dict(),
        }

    @property
    def algorithm(self) -> str:
        base = {
            "mad": "rolling_mad_starter",
            "zscore": "rolling_zscore",
            "residual": "residual_max_seasonal" if self.use_seasonal else "residual_max",
        }[self.detector]
        return base if self.calibration is None else base + "_prior_quantile"

    def metadata(self, config: DetectorConfig) -> dict[str, Any]:
        self.validate_for(config)
        features = None
        if self.detector == "residual":
            features = {
                "implementation": "sentinel.data.features.RollingFeatureExtractor",
                "window_size": config.window_size,
                "min_history": config.min_history,
                "scale_floor": config.scale_floor,
                "seasonal_period": self.seasonal_period,
            }
        return {
            **self.to_dict(),
            "features": features,
            "reference_update_policy": "include_all_observations",
            "calibration_update_policy": (
                "include_all_ready_scores" if self.calibration is not None else "not_enabled"
            ),
            "replay_context": {
                "saturated_raw_lookback": config.window_size
                + (self.calibration.window_size if self.calibration is not None else 0),
                "note": "Bounded selected models only; not split validation or context permission",
            },
        }


def create_detector(config: DetectorConfig, model: ModelConfig) -> Detector:
    """Construct a new base/extractor/calibrator for exactly one series."""
    model.validate_for(config)
    detector: Detector
    if model.detector == "mad":
        detector = RollingMADStarter(config)
    elif model.detector == "zscore":
        detector = RollingZScoreDetector(config)
    else:
        detector = ResidualDetector(
            config,
            RollingFeatureExtractor(
                window_size=config.window_size,
                min_history=config.min_history,
                scale_floor=config.scale_floor,
                seasonal_period=model.seasonal_period,
            ),
            use_seasonal=model.use_seasonal,
        )
    if model.calibration is not None:
        return CalibratedDetector(detector, PriorScoreQuantile(model.calibration))
    return detector


def _unique_object(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise ContractError(f"Duplicate model config key: {key}")
        result[key] = value
    return result


def _nonfinite_constant(value: str) -> Any:
    raise ContractError(f"Nonfinite model config constant: {value}")


def load_model_config(path: Path) -> ModelConfig:
    """Strict settings only; labels, model code and unknown fields are rejected."""
    payload = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_nonfinite_constant,
    )
    if not isinstance(payload, dict):
        raise ContractError("Model config must be a JSON object")
    unknown = set(payload) - set(ModelConfig.__dataclass_fields__)
    if unknown:
        raise ContractError(f"Unknown model config keys: {sorted(unknown)}")
    calibration = payload.get("calibration")
    if calibration is not None:
        if not isinstance(calibration, dict):
            raise ContractError("Model calibration must be an object or null")
        unknown = set(calibration) - set(QuantileThresholdConfig.__dataclass_fields__)
        if unknown:
            raise ContractError(f"Unknown calibration config keys: {sorted(unknown)}")
        payload["calibration"] = QuantileThresholdConfig(**calibration)
    return ModelConfig(**payload)
