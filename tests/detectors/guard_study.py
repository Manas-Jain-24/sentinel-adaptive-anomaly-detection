"""MN-04 synthetic diagnostic only; never imported by production inference.

Run: python tests/detectors/guard_study.py --output-dir outputs/mn04-study-001
This deliberately slow reference prototype rebuilds the real residual extractor
from bounded admitted observations. It is not Mayank's experiment harness and
must not be used to report production runtime or official performance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from collections import deque
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import median
from typing import Literal

from sentinel.config import DetectorConfig
from sentinel.contracts import AnomalyWindow, ContractError, Observation, Prediction
from sentinel.data.features import RollingFeatureExtractor
from sentinel.detectors.residual import ResidualDetector
from sentinel.detectors.thresholds import PriorScoreQuantile, QuantileThresholdConfig
from sentinel.evaluation.reference import event_metrics
from sentinel.pipeline import prediction_record

Policy = Literal["none", "capped", "quarantine", "shadow"]
POLICIES: tuple[Policy, ...] = ("none", "capped", "quarantine", "shadow")
START = datetime(2026, 1, 1, tzinfo=UTC)


@dataclass(frozen=True)
class StudyConfig:
    window: int = 32
    min_history: int = 8
    threshold: float = 4.0
    scale_floor: float = 0.1
    calibration_window: int = 64
    calibration_min_history: int = 16
    quantile: float = 0.99
    cap_sigma: float = 3.0
    max_quarantine: int = 8
    shadow_window: int = 8


@dataclass(frozen=True)
class StudyDecision:
    prediction: Prediction
    action: str
    admitted: bool
    quarantine_streak: int
    rebaselines: int


class PolicyPrototype:
    """Study-only update policies; labels never enter process().

    none: admit raw value and raw score.
    capped: admit value clipped to baseline +/- 3 prior scales, score capped at 3.
    quarantine: withhold anomalous values/scores for at most Q consecutive points;
      admit the next raw value/score, reset streak, so no permanent exclusion.
    shadow: same finite quarantine, plus switch reference to the latest raw shadow
      once Q alarms agree on a shifted, low-spread level. Calibration resets only
      after emitting the current decision. This cannot identify fault vs benign drift.

    Delta uses the preceding *admitted* reference value. Quarantine gaps therefore
    change delta support; production use requires a reviewed explicit update API.
    """

    def __init__(self, policy: Policy, *, adaptive: bool, config: StudyConfig) -> None:
        if policy not in POLICIES:
            raise ValueError("Unknown study policy")
        self.policy, self.adaptive, self.config = policy, adaptive, config
        self.reset()

    def reset(self) -> None:
        cfg = self.config
        self._history: deque[Observation] = deque(maxlen=cfg.window)
        self._shadow: deque[Observation] = deque(maxlen=cfg.shadow_window)
        self._calibrator = PriorScoreQuantile(
            QuantileThresholdConfig(
                window_size=cfg.calibration_window,
                min_history=cfg.calibration_min_history,
                quantile=cfg.quantile,
                fallback_threshold=cfg.threshold,
                threshold_floor=cfg.threshold,
            )
        )
        self._last: Observation | None = None
        self._streak = self._rebaselines = 0

    def process(self, observation: Observation) -> StudyDecision:
        observation = replace(observation, timestamp=observation.timestamp.astimezone(UTC))
        if self._last is not None and (
            observation.series_id != self._last.series_id
            or observation.timestamp <= self._last.timestamp
        ):
            raise ContractError("Study requires one strictly ordered series")
        cfg = self.config
        base = ResidualDetector(
            DetectorConfig(
                window_size=cfg.window,
                min_history=cfg.min_history,
                threshold=cfg.threshold,
                scale_floor=cfg.scale_floor,
            ),
            RollingFeatureExtractor(
                window_size=cfg.window,
                min_history=cfg.min_history,
                scale_floor=cfg.scale_floor,
            ),
        )
        for prior in self._history:
            base.process(prior)
        raw = base.process(observation)
        threshold = self._calibrator.threshold_state().threshold if self.adaptive else cfg.threshold
        anomalous = raw.score is not None and raw.score >= threshold
        prediction = replace(raw, threshold=threshold, label="ANOMALOUS" if anomalous else "NORMAL")
        admitted, action, stored, learned_score = True, "raw", observation, raw.score
        if self.policy == "capped" and raw.ready:
            assert raw.evidence.baseline is not None and raw.evidence.scale is not None
            limit = cfg.cap_sigma * raw.evidence.scale
            center = raw.evidence.baseline
            stored = replace(observation, value=max(center - limit, min(center + limit, raw.value)))
            assert raw.score is not None
            learned_score = min(raw.score, cfg.cap_sigma)
            action = "capped" if stored.value != raw.value or learned_score != raw.score else "raw"
        if self.policy in ("quarantine", "shadow"):
            if anomalous and self._streak < cfg.max_quarantine:
                admitted, action = False, "withheld"
                self._streak += 1
            else:
                action = "finite_release" if anomalous else "raw"
                self._streak = 0
        self._shadow.append(observation)
        if admitted:
            self._history.append(stored)
            if learned_score is not None:
                self._calibrator.process(learned_score)
        if (
            self.policy == "shadow"
            and anomalous
            and self._streak >= cfg.max_quarantine
            and len(self._shadow) == cfg.shadow_window
        ):
            assert raw.evidence.baseline is not None and raw.evidence.scale is not None
            values = [p.value for p in self._shadow]
            level = median(values)
            spread = 1.4826 * median([abs(v - level) for v in values])
            if (
                spread <= raw.evidence.scale
                and abs(level - raw.evidence.baseline) >= threshold * raw.evidence.scale
            ):
                # Current prediction is already fixed. New state only affects t+1.
                self._history.clear()
                self._history.extend(self._shadow)
                self._calibrator.reset()
                self._streak = 0
                self._rebaselines += 1
                admitted, action = True, "shadow_rebaseline"
        self._last = observation
        return StudyDecision(prediction, action, admitted, self._streak, self._rebaselines)


@dataclass(frozen=True)
class Scenario:
    name: str
    values: tuple[float, ...]
    event_ranges: tuple[tuple[int, int], ...] = ()

    def observations(self) -> list[Observation]:
        return [
            Observation(self.name, START + timedelta(seconds=i), value)
            for i, value in enumerate(self.values)
        ]


def scenarios() -> tuple[Scenario, ...]:
    """Predeclared diagnostic construction; no data, label fitting or search."""
    stable = [(-0.2, 0.1, 0.0, 0.2, -0.1)[i % 5] for i in range(256)]
    step = [v + (12 if 96 <= i < 224 else 0) for i, v in enumerate(stable)]
    spike = [v + (12 if i == 96 else 0) for i, v in enumerate(stable)]
    ramp = [v + max(0, i - 96) * 0.1 for i, v in enumerate(stable)]
    variance = [v * (30 if 96 <= i < 160 else 1) for i, v in enumerate(stable)]
    contaminated = [v + (12 if i < 24 else 0) for i, v in enumerate(stable)]
    return (
        Scenario("stable", tuple(stable)),
        Scenario("isolated_spike", tuple(spike), ((96, 96),)),
        Scenario("sustained_fault", tuple(step), ((96, 223),)),
        # Identical observations with a different diagnostic interpretation. No
        # unsupervised update rule can know which interpretation is true.
        Scenario("benign_step", tuple(step)),
        Scenario("benign_ramp", tuple(ramp)),
        Scenario("variance_burst", tuple(variance), ((96, 159),)),
        Scenario("contaminated_warmup", tuple(contaminated), ((0, 23),)),
    )


def compare(config: StudyConfig | None = None) -> dict[str, object]:
    config = config or StudyConfig()
    cases = scenarios()
    rows: list[dict[str, object]] = []
    for scenario in cases:
        points = scenario.observations()
        windows = [
            AnomalyWindow(scenario.name, points[a].timestamp, points[b].timestamp)
            for a, b in scenario.event_ranges
        ]
        for adaptive in (False, True):
            for policy in POLICIES:
                model = PolicyPrototype(policy, adaptive=adaptive, config=config)
                decisions = [model.process(p) for p in points]
                records = [prediction_record(d.prediction, 0) for d in decisions]
                flags = [i for i, d in enumerate(decisions) if d.prediction.label == "ANOMALOUS"]
                rows.append(
                    {
                        "scenario": scenario.name,
                        "policy": policy,
                        "calibration": "prior_quantile" if adaptive else "fixed",
                        "metrics": event_metrics(records, windows),
                        "flagged_indices": flags,
                        "event_point_count": sum(b - a + 1 for a, b in scenario.event_ranges),
                        "flagged_event_points": sum(
                            any(a <= i <= b for a, b in scenario.event_ranges) for i in flags
                        ),
                        "withheld_points": sum(d.action == "withheld" for d in decisions),
                        "finite_releases": sum(d.action == "finite_release" for d in decisions),
                        "rebaselines": decisions[-1].rebaselines,
                        "predictions": records,
                        "actions": [d.action for d in decisions],
                    }
                )
    return {
        "scope": "synthetic_guard_diagnostic",
        "official_benchmark": False,
        "production_policy_promoted": False,
        "retained_production_policy": "no_guard",
        "decision": (
            "Withhold promotion: synthetic-only evidence; "
            "authorized paired data and MY-02 required."
        ),
        "runtime_measured": False,
        "runtime_note": (
            "Rebuild-based test prototype; elapsed_ns=0 is a serialization placeholder, "
            "not measured runtime."
        ),
        "configuration": asdict(config),
        "scenarios": [asdict(s) for s in cases],
        "results": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    options = parser.parse_args()
    # New directory only: retain each attempt and never overwrite measurements.
    options.output_dir.mkdir(parents=True, exist_ok=False)
    report = compare()
    root = Path(__file__).resolve().parents[2]
    sources = [Path(__file__).relative_to(root)] + sorted(
        p.relative_to(root) for p in (root / "src").rglob("*.py")
    )
    report["source_sha256"] = {
        p.as_posix(): hashlib.sha256((root / p).read_bytes()).hexdigest() for p in sources
    }
    report["git_revision"] = (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()
    )
    report["git_dirty"] = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root))
    report["authored_utc"] = datetime.now(UTC).isoformat()
    report["python"] = platform.python_version()
    report["platform"] = platform.platform()
    payload = json.dumps(report, indent=2, allow_nan=False) + "\n"
    with (options.output_dir / "report.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(payload)
    print(
        json.dumps(
            {
                "report": str(options.output_dir / "report.json"),
                "comparisons": len(report["results"]),
                "production_policy_promoted": False,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
