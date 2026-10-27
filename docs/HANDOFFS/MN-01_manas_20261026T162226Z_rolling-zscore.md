# MN-01 handoff — Manas — 2026-10-26 16:22:26 UTC

- Task ID / developer / original owner: MN-01 / Manas / Manas.
- Status: IN_REVIEW. Algorithm and local software acceptance checks are complete; review/merge pending.
- Branch: feat/manas/MN-01-zscore.
- Base: reviewed main d7158d62eb8fa4e4c5d4907238d03c5989967083.
- Implementation commit: 5e28d5c4b9fd6b6f4517f1b18d97088cf7b47a49 (exists and was pushed).
- Shared location: [GitHub task branch](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/tree/feat/manas/MN-01-zscore).
- Draft PR: [MN-01 #1](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/1), opened against main; no merge or reviewer approval claimed.
- Objective: implement the independent causal rolling mean/z comparator and verify the existing MAD baseline against hand-derived references.
- Shared interfaces: Detector, Observation, Prediction, Evidence v1.0 and existing DetectorConfig, unchanged.
- Reviewers: Ayush for integration/runtime; Kaustubh for causality or Mayank for score/evaluation semantics. No review approval is claimed.

## Repository recovery and selected task

At recovery the working tree was clean on feat/manas/MN-05-foundation-models at 6a957fb.
Remote main matched local main d7158d6. Read AGENTS, README, START_HERE, CURRENT_STATE, PRD,
ARCHITECTURE, INTERFACES, IMPLEMENTATION_PLAN, TASK_BOARD, MANAS, INTEGRATION and
HANDOFF_PROTOCOL; inspected implementation/tests and extracted official PDF page 2.
No MN task was implemented beyond the MAD foundation; no IN_PROGRESS task existed.
MN-01 was the first unblocked P0 TODO. The baseline suite ran successfully before modification.

This task branch was created from main. The earlier Chronos/TimesFM research plan remains
on the separate feat/manas/MN-05-foundation-models branch; it has not been merged into main
or this branch, and no forecasting library/model was installed or evaluated here.

## Actual implementation and owned files

- [Z comparator](../../src/sentinel/detectors/zscore.py): RollingZScoreDetector implements the
  existing per-series process/reset protocol, bounded preceding-value history, arithmetic mean,
  population standard deviation (ddof=0), scale floor, absolute score, inclusive threshold,
  numerical evidence, UTC output, and explicit arithmetic-overflow errors before state mutation.
- [Owned tests](../../tests/detectors/test_baselines.py): 48 cases, with independent arithmetic
  references for z and odd/even/contaminated MAD histories. Also covers warmup, floor activation,
  equality/sign, eviction, ordering/series errors and recovery, reset, prefix invariance,
  immutable evidence, isolated spikes, absorption of sustained shifts, affine transformations,
  interleaved replay parity, extreme z arithmetic, and reader/replay/JSON/provisional-evaluator
  integration on the synthetic fixture.
- [Method notes](../../src/sentinel/detectors/README.md): formulas, units, update policy, runtime
  complexity, limitations and a runnable example using the public process_stream factory.
- src/sentinel/detectors/__init__.py: corrected package description.
- [Personal task record](../../tasks/MANAS.md): MN-01 IN_REVIEW and actual implementation/results.
- [Synthetic runtime evidence](../validation/MN-01_manas_20261026T161915Z_runtime.json):
  recorded workload, configuration, processor/platform/Python and one-trial p50/p95 timings.
- This uniquely named handoff was authored after the implementation commit. Retrieve branch
  HEAD for the final documentation commit as well; it cannot refer to its own commit hash.

No dependency, shared config/schema, pipeline/CLI, data module, evaluator, other developer's
implementation, or Ayush-owned central integration record was changed. The MAD algorithm
remains the same file content as on main.

## Actual verification

All commands below ran from the repository root on Windows 11/Python 3.13.5.
The executable prefix is .\.venv\Scripts\python.exe.

| Command / check | Actual result |
|---|---|
| -m pytest tests/test_foundation.py -q (before changes) | exit 0; 24 passed |
| -m ruff format src/sentinel/detectors/zscore.py tests/detectors/test_baselines.py | exit 0; 2 files already formatted |
| -m pytest tests/detectors -q | exit 0; 48 passed |
| -m pytest -q | exit 0; 72 passed |
| -m ruff check . | exit 0; all checks passed |
| -m ruff format --check . | exit 0; 16 files already formatted |
| -m mypy | exit 0; no issues in 13 source files |
| scripts/check_repository.py | exit 0; 32 mandatory docs, 89 relative links, 24 unique tasks, original PDF hash |
| git diff --check and git diff --cached --check before implementation commit | exit 0 |

The repository checker also passed after the final handoff links were added: 32 mandatory
documents, 97 relative links, 24 task IDs and the official PDF hash. These documentation edits
do not change Python code.

These exact smoke commands both exited 0:
~~~powershell
.\.venv\Scripts\python.exe -m sentinel run --input tests/fixtures/synthetic_stream.csv --config configs/starter.json --output-dir outputs/manas-MN-01-smoke-001 --dataset-id synthetic-fixture-v1 --scope synthetic_smoke
.\.venv\Scripts\python.exe -m sentinel evaluate --run-dir outputs/manas-MN-01-smoke-001 --windows tests/fixtures/synthetic_windows.json
~~~

That CLI still runs rolling_mad_starter: 16 observations, 8 ready, one artificial alert;
provisional TP/FP/FN=1/0/0, event F1=1 and delay=0 seconds. The z public-interface test
separately produced the same artificial event counts through process_stream/serializer and
the provisional evaluator. These establish wiring only. No NAB/official performance claim.

The smoke output directory is local and ignored by Git. Another machine should rerun the
commands using a fresh output directory. Runtime JSON is committed/shared.

## Runtime observation and exact reproduction command

One synthetic 5,000-point series, W=32 and W=128, min_history=8, threshold=4, floor=0.1.
Each pair uses identical preconstructed observations. Timings are the existing process_stream
measurements around process(); drop the first W points, then report median and nearest-rank
p95. One trial, no concurrent verification workload; parsing/writing/observation construction
and peak process memory are excluded.

| W | MAD p50 / p95, microseconds | Z p50 / p95, microseconds |
|---|---|---|
| 32 | 6.6 / 12.0 | 66.7 / 90.6 |
| 128 | 18.4 / 22.8 | 145.9 / 235.2 |

Stable standard-library mean/pstdev carry higher overhead in this probe despite linear window
complexity. No speedup is claimed. Timings are not official per-window measurements or
statistical evidence about detection quality; broad profiling remains AY-06.

The following PowerShell block ran successfully. It creates its artifact exclusively, so choose
a new output path before rerunning; preserve the recorded result:
~~~powershell
@'
import json
import platform
from datetime import UTC, datetime, timedelta
from math import ceil, sin
from pathlib import Path
from statistics import median

from sentinel.config import DetectorConfig
from sentinel.contracts import Observation
from sentinel.detectors.rolling import RollingMADStarter
from sentinel.detectors.zscore import RollingZScoreDetector
from sentinel.pipeline import process_stream

values = [10 + sin(i / 9) + 0.03 * (i % 7) + (4 if i % 499 == 0 else 0) for i in range(5000)]
start = datetime(2026, 1, 1, tzinfo=UTC)
observations = [Observation("synthetic-profile", start + timedelta(seconds=i), v) for i, v in enumerate(values)]
results = []
for window in (32, 128):
    config = DetectorConfig(window_size=window, min_history=8, threshold=4, scale_floor=0.1)
    for detector_class in (RollingMADStarter, RollingZScoreDetector):
        timings = [elapsed for _, elapsed in process_stream(observations, lambda: detector_class(config))]
        measured = sorted(timings[window:])
        results.append({
            "algorithm": detector_class.__name__,
            "config": config.to_dict(),
            "measured_points": len(measured),
            "p50_us": median(measured) / 1000,
            "p95_us": measured[ceil(0.95 * len(measured)) - 1] / 1000,
        })
report = {
    "scope": "synthetic_runtime_diagnostic",
    "official_benchmark": False,
    "authored_utc": datetime.now(UTC).isoformat(),
    "python": platform.python_version(),
    "platform": platform.platform(),
    "processor": platform.processor(),
    "observations": len(observations),
    "active_series": 1,
    "cadence_seconds": 1,
    "value_formula": "10 + sin(i / 9) + 0.03 * (i % 7) + (4 if i % 499 == 0 else 0)",
    "measurement": "One trial; process_stream process() time only; discard first window_size calls; p95 nearest rank; excludes parsing, writing and observation construction; no memory measurement.",
    "results": results,
}
path = Path("docs/validation/MN-01_manas_20261026T161915Z_runtime.json")
with path.open("x", encoding="utf-8", newline="\n") as stream:
    stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
print(json.dumps(report, indent=2, allow_nan=False))
'@ | .\.venv\Scripts\python.exe -
~~~

## Decisions, limitations and remaining integration

Population standard deviation is explicit; no new config field or algorithm selector was
introduced. Both scores are magnitudes, never probabilities. Threshold equality flags.
Flagged values still enter history; both baselines eventually absorb persistent identical shifts.
The tests document that limitation rather than silently adding MN-04 guards.

The comparator is usable through the existing process_stream factory. CLI/run_file still
construct MAD and write its algorithm identity. Ayush must coordinate any optional model
selection/config/manifest extension, with accurate algorithm metadata and integration tests.
Do not persist z predictions under a MAD run manifest.

No known new comparator correctness issue remains from local checks. Official assets,
authorized labels, timestamp/cadence semantics, scorer and submission schema remain unavailable.
No official-data comparison, hidden evaluation, actual peak memory profile, Linux/Python 3.11
execution, or remote CI result is claimed. No shared contract approval was needed because
the current contracts and config fields were preserved.

## Exact next actions

1. Fetch the shared branch and inspect its HEAD and this handoff; run required checks in your
   installed environment. For a new local branch:
   ~~~text
   git fetch origin
   git switch --track origin/feat/manas/MN-01-zscore
   ~~~
   If the local branch already exists, switch to its name and compare remote changes safely.
2. Ayush and a domain peer review MN-01. Only an authorized integrator merges into main and
   then synchronizes CURRENT_STATE/TASK_BOARD/INTEGRATION with actual evidence.
3. If integration needs a CLI selector, implement that in Ayush's workstream with accurate
   algorithm metadata; the programmatic comparator is already available.
4. Manas's next unblocked task is MN-02: inspect FeatureFrame/FeatureExtractor and implement
   the residual detector using a deterministic fake until KS-02 can be integrated. Use a
   new task branch from reviewed main; do not silently incorporate unpublished teammate code.
5. Keep MN-05 official model comparison blocked until permitted data/harness/labels/scorer
   and model-specific runtime/license gates are available. No public NAB substitution.

## Pull request summary

Adds a causal rolling mean/population-z comparator with bounded state and direct arithmetic
evidence through the existing Detector factory contract. Adds 48 owned tests that also verify
the MAD fallback, method documentation, synthetic runtime evidence and personal progress.
All 72 local tests and configured checks pass. No shared interface or mandatory dependency
changes; official performance selection and optional CLI model selection remain pending.
