# MN-03 prior-score calibration — Manas

- Task/developer/original owner: MN-03 / Manas / Manas.
- Authored: 2026-10-27 00:41:39 +05:30 (Asia/Kolkata); 2026-10-26 19:11:39 UTC.
- Status: IN_REVIEW. Local software acceptance and pinned composition tests pass; review/
  configuration adoption/main integration and real-data model selection remain pending.
- Branch: feat/manas/MN-03-prior-quantile, from reviewed main d7158d62eb8fa4e4c5d4907238d03c5989967083.
- Shared implementation commit: 6480a0e0824428c34795c8863223c0a8d6cc4694, exists and was pushed.
- Shared [task branch](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/tree/feat/manas/MN-03-prior-quantile).
- Draft review: [PR #4](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/4), targets main; no main merge or reviewer approval claimed.
- Reviewers: Ayush for config/factory/runtime; Mayank for calibration/evaluation/state support;
  Kaustubh for feature-context semantics. No teammate approval or main merge is claimed.

## Recovery and scope

Entry tree was clean on MN-02 at 2bdae80. Fetched origin; main still held d7158d6.
Read AGENTS, task/interfaces/architecture/experiment/decision/integration/handoff records and
actual shared types/config/code. MN-01/02 are separate published review branches (PR #1/#3);
MN-03 was the next unblocked TODO. Foundation tests passed before edits. Created a new branch
from reviewed main without copying unmerged prior work into tracked source.

Objective: a bounded empirical threshold based strictly on preceding scores, with a defined
minimum-history fallback, finite positive threshold, reset and causal/contamination tests.
The generic adapter was implemented using the existing Detector v1 boundary; no shared schema,
config JSON parser, CLI/pipeline, data/evaluator dependency or central integration record changed.

## Actual implementation and files

- [thresholds.py](../../src/sentinel/detectors/thresholds.py): local frozen QuantileThresholdConfig,
  immutable state/decision records and PriorScoreQuantile. Fixed fallback for fewer than M
  preceding valid scores; nearest-rank quantile thereafter with a positive floor. Decimal q
  is interpreted using Fraction(str(q)) so integral rank boundaries do not drift upward due
  to floating multiplication. Current score enters the bounded C-score history after its
  decision is built. Invalid direct scores reject without state mutation.
- [calibrated.py](../../src/sentinel/detectors/calibrated.py): per-series CalibratedDetector owns
  one base and calibrator; preserves score/readiness/arithmetic evidence, replaces threshold/
  label consistently, and appends calibration metadata to existing reason text. Feature warmup
  contributes no score; a valid short-calibration-history score uses fallback while staying
  ready. Order/identity checks precede base processing. A failure after the base call requires
  reset/replay because Detector v1 cannot roll back state.
- [94 unit/contract cases](../../tests/detectors/test_thresholds.py) and
  [wrapper tests](../../tests/detectors/test_calibrated.py): hand-derived ranks, q endpoints,
  exact decimal boundaries, ties, floors, short history, invalid data/settings, finite extremes,
  contamination/eviction, bounded long streams, pure queries/reset, prefix immutability,
  evidence/label compatibility, per-series isolation and shared synthetic reader/evaluator.
  The combined count of these two files is 94.
- [Four pinned composition cases](../../tests/detectors/test_calibrated_residual.py): actual
  published KS-02/MN-02 source verifies the combined score rather than separate branch
  calibration; W+C continuation matches; W-only context is a negative control.
- [Method notes](../../src/sentinel/detectors/CALIBRATION.md), package ownership description,
  personal MANAS record, and [verification/runtime evidence](../validation/MN-03_manas_20261026T190805Z_verification.json).
- This unique handoff is a later documentation commit; retrieve final branch HEAD as well.

## Actual commands and results

Windows 11/Python 3.13.5, installed pinned dev environment, repository root:
~~~powershell
.\.venv\Scripts\python.exe -m pytest tests/test_foundation.py -q
.\.venv\Scripts\python.exe -m pytest tests/detectors/test_thresholds.py tests/detectors/test_calibrated.py -q
.\.venv\Scripts\python.exe -m pytest tests/detectors -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m ruff format --check --no-cache .
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe scripts/check_repository.py
git diff --check
git diff --cached --check
~~~

- Before edits: foundation 24 passed.
- First owned run: 92 passed/1 failed, because a fixture assertion incorrectly expected zero
  false positives after a normal score tied its adaptive threshold. Inspected every fixture
  score/threshold/label, reproduced the inclusive tie, and corrected the reference assertion
  to its actual TP/FP/FN=1/1/0. The algorithm, config and shared >= rule were unchanged.
- Added one score-unit regression; final owned tests: 94 passed.
- Independent full suite: 118 passed, one optional composition-module skip (unmerged KS/MN
  modules). Pinned composition full suite below: 122 passed, no skips.
- Lint passed; format passed 19 files; strict mypy passed 14 source files.
- The concurrent format check emitted a cache-write access warning but exited 0 and reported
  formatted source. The subsequent no-cache format check completed cleanly.
- Repository check before handoff: 32 mandatory docs, 93 links, 24 task IDs and original PDF
  hash passed. Final documentation check also passed: 32 docs, 101 links, 24 task IDs and
  original PDF hash.
- No Linux/Python 3.11 or remote CI success is inferred from local checks.

Exact pinned composition command (uses only locally fetched source, no merge/install):
~~~powershell
@'
import hashlib
import importlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

modules = [
    ("954bd1bc38b866617de3a011b6b22d6921238601", "src/sentinel/data/features.py", "sentinel.data.features"),
    ("2bdae80560973dc72b489b906be34da0aa1c3dc2", "src/sentinel/detectors/residual.py", "sentinel.detectors.residual"),
]
directory = Path("outputs/MN-03-published-compat-001")
directory.mkdir(parents=True, exist_ok=False)
provenance = []
for commit, source_path, module_name in modules:
    source = subprocess.check_output(["git", "show", f"{commit}:{source_path}"])
    path = directory / Path(source_path).name
    path.write_bytes(source)
    parent_name, attribute = module_name.rsplit(".", 1)
    parent = importlib.import_module(parent_name)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    setattr(parent, attribute, module)
    provenance.append({"commit":commit, "path":source_path, "sha256":hashlib.sha256(source).hexdigest()})
result = int(pytest.main(["tests", "-q"]))
report = {"scope":"synthetic_published_detector_compatibility","official_benchmark":False,"sources":provenance,"exit_code":result}
(directory / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report))
raise SystemExit(result)
'@ | .\.venv\Scripts\python.exe -
~~~

Sources pinned: KS-02 features at 954bd1bc38b866617de3a011b6b22d6921238601 and MN-02 residual
at 2bdae80560973dc72b489b906be34da0aa1c3dc2. Their exact hashes are in the shared verification
artifact. The ignored snapshot/report is local; choose a new output directory to reproduce.

README CLI regression commands, both exited 0:
~~~powershell
.\.venv\Scripts\python.exe -m sentinel run --input tests/fixtures/synthetic_stream.csv --config configs/starter.json --output-dir outputs/manas-MN-03-smoke-001 --dataset-id synthetic-fixture-v1 --scope synthetic_smoke
.\.venv\Scripts\python.exe -m sentinel evaluate --run-dir outputs/manas-MN-03-smoke-001 --windows tests/fixtures/synthetic_windows.json
~~~

That CLI still runs/identifies MAD: 16 synthetic points, 8 ready, 1 alert, provisional TP/FP/
FN=1/0/0. The separate calibrated fixture regression with C=3/M=2/q=1/floor=0.01 yields 1/1/0
due to a later normal tie. Neither is official NAB/hidden-evaluation evidence, and no quality
promotion or nominal false-alarm guarantee is claimed.

## Runtime diagnostic and reproduction

One trial, 5,000 deterministic values/one series. Standalone threshold p95 was 3.5 us at
C=64 / 10.9 us at C=256; MAD+adapter p95 21.3 / 28.0 us; bare MAD p95 6.6 us. Each case
records its own discarded prefix and measured count. Standalone score and wrapper raw-value
streams differ explicitly. Construction/parsing/writing/cold start/memory are excluded.
The wrapper adds cost; these results do not establish a promotion gate or an official limit.

Exact executed diagnostic follows; its evidence path is exclusive, so use a new path to rerun:
~~~powershell
@'
import hashlib
import json
import platform
from datetime import UTC, datetime, timedelta
from math import ceil, sin
from pathlib import Path
from statistics import median
from time import perf_counter_ns

from sentinel.config import DetectorConfig
from sentinel.contracts import Observation
from sentinel.detectors.calibrated import CalibratedDetector
from sentinel.detectors.rolling import RollingMADStarter
from sentinel.detectors.thresholds import PriorScoreQuantile, QuantileThresholdConfig

values = [abs(sin(i / 9)) + 0.03 * (i % 7) + (4 if i % 499 == 0 else 0) for i in range(5000)]
start = datetime(2026, 1, 1, tzinfo=UTC)
points = [Observation("synthetic-profile", start + timedelta(seconds=i), 10 + v) for i, v in enumerate(values)]
base_config = DetectorConfig()
cases = [("mad_starter", RollingMADStarter(base_config), points, 32, None)]
for capacity in (64, 256):
    cfg = QuantileThresholdConfig(window_size=capacity)
    cases.append(("prior_score_quantile", PriorScoreQuantile(cfg), values, capacity, cfg.to_dict()))
    cases.append(("mad_prior_score_quantile", CalibratedDetector(RollingMADStarter(base_config), PriorScoreQuantile(cfg)), points, 32 + capacity, cfg.to_dict()))
timings = []
for name, model, stream, drop, cfg in cases:
    elapsed = []
    for value in stream:
        before = perf_counter_ns()
        model.process(value)
        elapsed.append(perf_counter_ns() - before)
    measured = sorted(elapsed[drop:])
    timings.append({
        "algorithm": name, "calibration_config": cfg, "discarded_prefix": drop,
        "measured_points": len(measured), "p50_us": median(measured) / 1000,
        "p95_us": measured[ceil(0.95 * len(measured)) - 1] / 1000,
    })
compat = json.loads(Path("outputs/MN-03-published-compat-001/report.json").read_text(encoding="utf-8"))
report = {
    "scope": "synthetic_calibration_software_verification", "official_benchmark": False,
    "authored_utc": datetime.now(UTC).isoformat(), "python": platform.python_version(),
    "platform": platform.platform(), "processor": platform.processor(),
    "implementation_state": "MN-03 working tree; actual implementation commit recorded in handoff",
    "source_sha256": {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in (
        "src/sentinel/detectors/thresholds.py", "src/sentinel/detectors/calibrated.py",
    )},
    "tests": {
        "foundation_before_changes": {"passed":24},
        "owned_unit_contract_cases": {"passed":94},
        "standalone_suite": {"passed":118,"skipped_modules":1,"reason":"KS-02/MN-02 are unmerged"},
        "published_composition_suite": {"passed":122,"skipped":0, **compat},
        "fixture_regression": {"scope":"synthetic_smoke","metric_id":"provisional_event_trigger_f1_v0","tp":1,"fp":1,"fn":0,
            "calibration_config":{"window_size":3,"min_history":2,"quantile":1,"fallback_threshold":4,"threshold_floor":0.01},
            "reason":"Later normal score ties empirical threshold; shared >= comparison flags it."},
        "initial_test_assumption": "One fixture assertion expected zero FP, failed, and was corrected after inspecting the actual score/threshold tie. Algorithm/comparison rule were unchanged.",
    },
    "runtime": {
        "input_count":5000, "active_series":1,"cadence_seconds":1,
        "score_formula":"abs(sin(i / 9)) + 0.03 * (i % 7) + (4 if i % 499 == 0 else 0)",
        "observation_value":"10 + generated_score", "base_config":base_config.to_dict(),
        "measurement":"One trial per case; perf_counter_ns around process(); discard stated prefix; nearest-rank p95. Standalone and wrapper inputs are explicitly different streams. Excludes parsing/writing/construction/cold-start/memory.",
        "results":timings,
    },
    "official_dataset":{"available_locally":False,"pdf_description":"NAB subset prepared in starter pack with hidden test windows","pdf_download_links":0,"official_directory_files":["README.md"],"user_reply":"Problem-statement description; no actual starter-pack link supplied."},
}
path = Path("docs/validation/MN-03_manas_20261026T190805Z_verification.json")
with path.open("x", encoding="utf-8", newline="\n") as stream:
    stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
print(json.dumps(report, indent=2, allow_nan=False))
'@ | .\.venv\Scripts\python.exe -
~~~

## Dataset clarification

The supplied official PDF page 2 names a NAB subset prepared in the starter pack with hidden
windows. It contains no embedded download link. data/official contains only README; the
repository has only the 16-point synthetic CSV; the supplied task attachment and matching
Downloads entries did not contain a starter pack. The user pasted the dataset-description
paragraph in response to a request for a portal/group link, without actual files or a URL.

Do not claim the organizers never distributed it elsewhere. A separate portal/group starter
pack may exist, but is not available in this session. KS-04/05 and real calibration/model
comparison still need the actual pack, authorized development labels/permissions/partitions,
Q01/Q09 semantics and official scorer/schema. No public NAB data or hidden labels were substituted.

## Integration obligations and exact next actions

1. Review the local calibration settings, nearest-rank/equality/floor policy, and adapter's
   failure/reset lifecycle. All accepted scores, including flagged scores, enter history.
   Ties/serial dependence/contamination invalidate a nominal alarm-rate claim.
2. Ayush owns eventual model/factory/config JSON and run-metadata adoption. Record base and
   calibration settings separately and use the correct calibrated algorithm identity; do not
   persist calibrated predictions under a plain MAD/residual manifest. CLI remains MAD today.
3. Mayank reviews train/calibration/target masks and effective support. For this tested
   full-buffer, always-ready-after-warmup finite model, W+C preceding raw points suffice;
   max(W,C) does not. Intermittent readiness or future fitted/guarded state needs its own
   policy and actual counts. Do not silently carry state across independent groups.
4. Resolve personal task/package-description overlaps with PR #1/#3 preserving every owned
   module and progress/handoff reference. Only an authorized integrator merges main and
   updates Ayush-owned central records after the combined checks.
5. Next work is integration plus permitted-data threshold/model ablations. MN-04 guards stay
   gated on sustained-fault/drift comparisons and data; no automatic rebaseline, quarantine
   or hidden-label tuning is justified by these unit tests.
6. Fresh agent: inspect actual Git/PR state, fetch referenced branches/commits if absent,
   reproduce the independent and pinned checks using fresh output paths, then continue the
   highest-priority unblocked owned work. Read current contracts before integration.

Draft PR #4 carries review information. Respect the user's preference against additional
GitHub review comments; no comment on another PR or main merge is part of this task.
