# MN-02 handoff — Manas — 2026-10-26 17:59:01 UTC

- Task/developer/original owner: MN-02 / Manas / Manas.
- Status: IN_REVIEW. Local software acceptance and real published-extractor compatibility pass;
  normal peer/integration review and merge remain pending.
- Branch: feat/manas/MN-02-residual.
- Base main: d7158d62eb8fa4e4c5d4907238d03c5989967083.
- Implementation commit: 8129bff278bd08853722bcb7dbab71293a769618, committed and pushed.
- Shared location: [task branch](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/tree/feat/manas/MN-02-residual).
- Draft review: [PR #3](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/3), targets main; no merge or approval claimed.
- Objective: compose causal level/change/optional-seasonal residual scores using existing contracts.
- Reviewers: Ayush for factories/config/runtime, Kaustubh for feature semantics, Mayank for scoring.
  No teammate approval, main merge or central integration update is claimed.

## Recovery and ownership

Read AGENTS, task/state/contracts/architecture/integration/handoff records and actual code.
The tree was clean on MN-01's published branch at 8f6f6bf. Remote main still held the
foundation d7158d6; MN-01 remained in [draft PR #1](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/1).
MN-02 was the highest-priority unblocked TODO. Created an independent branch from main,
without incorporating unmerged MN-01 or Kaustubh source. Baseline tests passed before edits.

Kaustubh published [PR #2](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/2).
Read its actual FeatureExtractor implementation/method notes and publication handoff. Pinned
compatibility input: commit 954bd1bc38b866617de3a011b6b22d6921238601,
src/sentinel/data/features.py, SHA256
e8de0025fbed3bae54928da2a642e3304d667814bbaf8494818fb07a932f426b.
This source was loaded into a separate test process from an ignored snapshot, not copied into
tracked data-owned files or merged. Compatibility is verified; owner approval is not implied.

## Implemented files and behavior

- [ResidualDetector](../../src/sentinel/detectors/residual.py): one owned extractor per detector;
  constructor/reset clears both; one extractor call per valid observation; UTC/order/series
  checks; frame validation; shared positive scale; finite absolute level/change scores plus
  optional seasonal score; fixed maximum, inclusive threshold, immutable arithmetic evidence.
- [Method notes](../../src/sentinel/detectors/RESIDUAL.md): exact equations, settings/readiness
  ownership, score units, seasonal fallback, evidence representation and example factory.
- [Deterministic-frame tests](../../tests/detectors/test_residual.py): 69 cases covering reference
  arithmetic, each dominant branch, thresholds, floors, warmup, optional/missing seasonality,
  malformed frames, nonfinite/overflow errors, exactly-once processing, failure/reset lifecycle,
  sequence-error recovery, UTC folds, prefix immutability, interleaving and shared serialization.
- [Real extractor integration tests](../../tests/detectors/test_residual_features.py): 13 cases
  covering hand-derived feature/residual traces, missing synthetic peak, MAD level-score parity,
  prefix invariance, interleaved state, reset/replay, affine invariance and bounded constant traces.
- [Verification evidence](../validation/MN-02_manas_20261026T175539Z_verification.json): actual
  counts, pinned dependency/source hashes, residual source hash, platform and runtime observations.
- src/sentinel/detectors/__init__.py: general ownership description.
- [Personal task file](../../tasks/MANAS.md): MN-01 separate published review reference,
  MN-02 IN_REVIEW, actual tests/blockers and next task.
- This unique handoff is in a later documentation commit; retrieve final task-branch HEAD too.

Shared Detector/FeatureExtractor/FeatureFrame/Prediction/Evidence v1 types, DetectorConfig,
MAD source, pipeline/CLI, data modules, evaluator, dependencies and Ayush-owned central
documents were unchanged.

## Decisions and limits

Score = max of abs(value-expected_level)/scale, abs(delta-expected_delta)/scale and, when
enabled/available, abs(value-seasonal_expected)/scale. Effective scale is max(frame.scale,
config.scale_floor). The extractor controls readiness/history; detector config supplies fixed
threshold/floor. Constructor factories must align their feature settings explicitly.

Seasonality defaults off. A missing reference falls back to level/change without delaying
readiness. No period fitting or calibration is implemented. The maximum can add flags but
cannot cancel a large level/change score merely because seasonality matches. Shared value
units do not guarantee identical component distributions or a calibrated false-alarm rate.

Evidence's existing numeric baseline/scale/residual describe the level branch; component_scores
contain all included normalized magnitudes. Human-readable reason text includes each actual
arithmetic expression with its delta/seasonal inputs. No structured fields or new parsing
contract were added. A later structured reference/residual extension requires normal approval.

FeatureExtractor.process may update state before returning. Once that call begins, any feature,
frame-validation or scoring error invalidates the wrapper until reset and full prefix replay.
No prediction is emitted. There is no v1 rollback/checkpoint interface; retrying only a failed
point would risk inconsistent states. Order/series violations are caught before calling the
extractor and do not invalidate an otherwise healthy detector. Programming errors propagate.

The wrapper adds O(1) state and at most three residuals. KS-02 includes all accepted observations,
including anomalies, so persistent shifts can be absorbed. Guard-controlled updates under MN-04
may need a separately reviewed feature-update interface. Do not silently add guards here.

## Actual checks and results

Windows 11, Python 3.13.5, installed project virtual environment. All final checks below exited 0:

~~~powershell
.\.venv\Scripts\python.exe -m pytest tests/test_foundation.py -q
.\.venv\Scripts\python.exe -m pytest tests/detectors/test_residual.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe scripts/check_repository.py
git diff --check
git diff --cached --check
~~~

- Foundation before implementation: 24 passed.
- Deterministic-frame cases: 69 passed.
- Independent branch full suite: 93 passed, one skipped module because KS-02 is unmerged.
- Pinned KS-02 compatibility full suite below: 106 passed, no skips (all 13 real cases ran).
- Ruff lint passed; 17 Python files already formatted; strict mypy passed 13 source files.
- Repository checker after personal progress: 32 mandatory documents, 94 relative links,
  24 unique tasks and original PDF hash passed. Final documentation check also passed:
  32 mandatory documents, 101 relative links, 24 unique tasks and original PDF hash.
- Source/white-space checks passed. No remote CI or Linux/Python 3.11 result is claimed.
- MN-01's 48 separate-branch z tests are not present in this main-based task branch; its
  previously recorded results are not misrepresented as rerun here.

Exact CLI regression commands, both exited 0:
~~~powershell
.\.venv\Scripts\python.exe -m sentinel run --input tests/fixtures/synthetic_stream.csv --config configs/starter.json --output-dir outputs/manas-MN-02-smoke-001 --dataset-id synthetic-fixture-v1 --scope synthetic_smoke
.\.venv\Scripts\python.exe -m sentinel evaluate --run-dir outputs/manas-MN-02-smoke-001 --windows tests/fixtures/synthetic_windows.json
~~~

The CLI still correctly identifies rolling_mad_starter: 16 synthetic points, 8 ready, one
alert, provisional TP/FP/FN=1/0/0, artificial event F1=1, delay=0. Residual tests separately use
the public reader/replay/serializer/provisional evaluator. These are software wiring checks,
not organizer/NAB benchmarks. The smoke artifacts are local and ignored; rerun with fresh paths.

## Exact pinned compatibility reproduction

Fetch the published data branch first if the pinned commit is not locally available. This block
uses the exact source bytes, loads them only in that Python process, and runs this branch's suite.
The optional tests automatically execute normally once KS-02 is integrated into a checkout.

~~~powershell
@'
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import sentinel.data

commit = "954bd1bc38b866617de3a011b6b22d6921238601"
source_path = "src/sentinel/data/features.py"
source = subprocess.check_output(["git", "show", f"{commit}:{source_path}"])
snapshot = Path("outputs/MN-02-ks02-compat/features.py")
snapshot.parent.mkdir(parents=True, exist_ok=True)
if snapshot.exists() and snapshot.read_bytes() != source:
    raise SystemExit("Existing compatibility snapshot differs; use a new directory")
snapshot.write_bytes(source)
spec = importlib.util.spec_from_file_location("sentinel.data.features", snapshot)
if spec is None or spec.loader is None:
    raise SystemExit("Could not load pinned KS-02 snapshot")
module = importlib.util.module_from_spec(spec)
sys.modules["sentinel.data.features"] = module
spec.loader.exec_module(module)
sentinel.data.features = module
exit_code = int(pytest.main(["tests", "-q"]))
report = {
    "scope": "synthetic_published_extractor_compatibility",
    "official_benchmark": False,
    "published_commit": commit,
    "source_path": source_path,
    "source_sha256": hashlib.sha256(source).hexdigest(),
    "test_command": "pytest.main(['tests', '-q']) with pinned KS-02 module loaded only in this Python process",
    "exit_code": exit_code,
}
Path("outputs/MN-02-ks02-compat/report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report))
raise SystemExit(exit_code)
'@ | .\.venv\Scripts\python.exe -
~~~

The ignored snapshot/report are local. Their actual source hash and test result are also
preserved in the committed verification artifact. Do not count a normal skipped module as
proof the real extractor passed; reproduce the pinned process above.

## Runtime diagnostic

One trial per case, 5,000 generated points, one series, W=32/128, min_history=8, threshold=4,
floor=0.1, fixed synthetic lag=8. Discard first W calls, then median/nearest-rank p95 of
perf_counter_ns around process(). Construction, parsing, writing, cold start and memory excluded.

| W | Level/change p50/p95 us | Plus seasonal p50/p95 us |
|---|---|---|
| 32 | 19.3 / 34.2 | 20.7 / 27.1 |
| 128 | 46.0 / 75.2 | 47.5 / 64.0 |

The one-trial tails contain timing noise; no seasonal speed benefit or official limit compliance
is inferred. The committed artifact also records MAD and feature-only diagnostic timings.
These results establish no detection-quality improvement, F1 promotion, or peak-memory claim.

Exact executed diagnostic follows. It creates the committed evidence path exclusively;
choose a fresh output path to rerun and preserve the existing artifact:
~~~powershell
@'
import hashlib
import importlib.util
import json
import platform
import sys
from datetime import UTC, datetime, timedelta
from math import ceil, sin
from pathlib import Path
from statistics import median
from time import perf_counter_ns

from sentinel.config import DetectorConfig
from sentinel.contracts import Observation
from sentinel.detectors.residual import ResidualDetector
from sentinel.detectors.rolling import RollingMADStarter

compat = json.loads(Path("outputs/MN-02-ks02-compat/report.json").read_text(encoding="utf-8"))
snapshot = Path("outputs/MN-02-ks02-compat/features.py")
if hashlib.sha256(snapshot.read_bytes()).hexdigest() != compat["source_sha256"]:
    raise SystemExit("Pinned compatibility snapshot checksum mismatch")
spec = importlib.util.spec_from_file_location("sentinel.data.features", snapshot)
module = importlib.util.module_from_spec(spec)
sys.modules["sentinel.data.features"] = module
spec.loader.exec_module(module)
values = [10 + sin(i / 9) + 0.03 * (i % 7) + (4 if i % 499 == 0 else 0) for i in range(5000)]
start = datetime(2026, 1, 1, tzinfo=UTC)
observations = [Observation("synthetic-profile", start + timedelta(seconds=i), v) for i, v in enumerate(values)]
results = []
for window in (32, 128):
    config = DetectorConfig(window_size=window, min_history=8, threshold=4, scale_floor=0.1)
    def extractor():
        return module.RollingFeatureExtractor(window_size=window, min_history=8, scale_floor=0.1, seasonal_period=8)
    cases = (
        ("mad_starter", RollingMADStarter(config)),
        ("ks02_features_only", extractor()),
        ("residual_level_change", ResidualDetector(config, extractor())),
        ("residual_level_change_seasonal", ResidualDetector(config, extractor(), use_seasonal=True)),
    )
    for algorithm, model in cases:
        timings = []
        for current in observations:
            before = perf_counter_ns()
            model.process(current)
            timings.append(perf_counter_ns() - before)
        samples = sorted(timings[window:])
        results.append({
            "algorithm": algorithm, "window_size": window, "measured_points": len(samples),
            "p50_us": median(samples) / 1000,
            "p95_us": samples[ceil(0.95 * len(samples)) - 1] / 1000,
        })
report = {
    "scope": "synthetic_software_and_runtime_verification",
    "official_benchmark": False,
    "authored_utc": datetime.now(UTC).isoformat(),
    "python": platform.python_version(),
    "platform": platform.platform(),
    "processor": platform.processor(),
    "implementation_state": "MN-02 working tree; implementation commit recorded separately in handoff",
    "residual_source_sha256": hashlib.sha256(Path("src/sentinel/detectors/residual.py").read_bytes()).hexdigest(),
    "tests": {
        "foundation_before_changes": {"passed": 24},
        "deterministic_frame_cases": {"passed": 69},
        "standalone_full_suite": {"passed": 93, "skipped_modules": 1, "reason": "KS-02 module is unmerged"},
        "pinned_ks02_full_suite": {"passed": 106, "skipped": 0, **compat},
    },
    "runtime": {
        "observations": 5000, "active_series": 1, "cadence_seconds": 1,
        "value_formula": "10 + sin(i / 9) + 0.03 * (i % 7) + (4 if i % 499 == 0 else 0)",
        "config": {"min_history": 8, "threshold": 4, "scale_floor": 0.1, "seasonal_period": 8},
        "measurement": "One trial per case; perf_counter_ns around process(); discard first W; p95 nearest rank; feature-only result is FeatureFrame, others Prediction; excludes construction, parsing, writing, cold start and memory.",
        "results": results,
    },
}
path = Path("docs/validation/MN-02_manas_20261026T175539Z_verification.json")
with path.open("x", encoding="utf-8", newline="\n") as stream:
    stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
print(json.dumps(report, indent=2, allow_nan=False))
'@ | .\.venv\Scripts\python.exe -
~~~

## Remaining work and exact continuation

1. Review MN-02's implementation, evidence semantics and explicit reset/replay policy. Ayush
   owns any model/config/factory and algorithm-manifest adoption. Default CLI still runs MAD.
2. Resolve expected personal-task/package-description overlap with PR #1 by preserving both
   tasks' real implementation status, notes, references and owned modules. Do not replace one
   task record with the other branch's file. Merge only with authorization and normal review.
3. Integrate approved KS-02 via normal review; its existing protocol/constructor worked in
   the pinned compatibility check. Rerun the full suite after actual integration; the 13
   optional cases should run automatically rather than skip.
4. Ayush updates CURRENT_STATE/TASK_BOARD/INTEGRATION after authorized review/merge.
5. Next Manas task: MN-03, bounded empirical quantile threshold from strictly preceding combined
   scores with minimum-history fallback, boundary/tie/contamination/buffer/causality tests.
   Start a new coherent branch from reviewed main; do not silently redesign shared contracts.
6. Official assets/authorized labels/scorer/Q01/Q09 and schema remain unavailable. They still
   block actual dataset/model comparisons and official submission compliance. No substitution.

No known failing local test remains. Genuine data quality, threshold selection, periodic false
alerts, guarded adaptation, memory/cold-start profiling and final CLI/export/scorer integration
remain unverified or owned later work. This handoff records a complete software increment,
not the completed competition system.
