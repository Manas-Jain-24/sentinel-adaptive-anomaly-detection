# KS-02 - reviewed causal features

- Developer/original owner: Kaustubh; no transfer.
- Authored: 2026-10-26 21:22:17 +05:30, Asia/Kolkata (15:52:17 UTC).
- Status: IN_REVIEW; software phase complete, Ayush/Manas owner review pending.
- Branch: `feat/kaustubh/KS-01-02-03-06-data-workstream`, retained KS-01 commits from main.
- Implementation commit: `2b991a9b4b218ac74f447f0ff8b253d899cbef7a`.
- Sharing: local only, not pushed; another machine cannot retrieve these changes yet.
- Objective: implement existing FeatureExtractor/FeatureFrame without modifying shared interfaces.

## Implementation and decisions

`src/sentinel/data/features.py` provides RollingFeatureExtractor with process/reset. Bounded prior
values produce median level, median adjacent prior delta, MAD scale with positive floor, and an
optional fixed observation-lag reference. Current delta uses the previous accepted observation.
Warmup expectations/scale and unavailable seasonality are null. One instance owns one series;
reset clears identity/history. All outputs are finite and errors leave state unchanged.

Typed constructor parameters window_size/min_history/scale_floor/seasonal_period are local
implementation settings. The existing shared DetectorConfig, FeatureFrame, Protocol and CLI remain
unchanged. Ayush/Manas must review these controls before config/factory integration; no approval
or shared configuration extension is claimed. See [exact semantics](../DATA_FEATURES.md).
Any future shared config addition should use a separate feature section, include these bounds,
record lookback in run/split metadata, and follow INTERFACES approval/migration rules. A compatible
consumer today can construct a local factory returning the existing FeatureExtractor protocol.

Numerical midpoint calculation avoids finite constant-signal overflow. Inputs normalize to UTC
and float before arithmetic. Genuine overflow fails with ContractError/rescaling guidance rather
than clipping. Seasonality counts samples; gaps are not filled or converted into a time rate.
All accepted values update history, including contamination; adaptation remains Manas's scope.
Time O(W log W), memory O(W). No speed or real-data performance benchmark ran.

## Tests and independent review

`tests/data/test_features.py` covers hand-derived traces, null warmup, prefix invariance,
current-value independence of expectations, scale floor, capped history, season lag readiness,
isolated instances/reset, ordering/UTC, bad constructor types/bounds and numeric overflow recovery.

Observed missing-module failure before implementation. Phase review found two Important issues:
same-tz DST-fold wall-time ordering, and large integer deltas leaking OverflowError. Added two
regression tests, observed both failures, normalized UTC/float at the boundary, then reran tests.
Reviewer independently checked both fixes and 30 passing feature cases, reporting no remaining
Critical/Important/Minor findings. This is agent review, not Ayush/Manas approval.

Actual commands (repo root, Windows/Python 3.12.14), all final exit codes 0:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/data/test_features.py --basetemp outputs/pytest-ks02-review-fixed
.\.venv\Scripts\python.exe -m pytest --basetemp outputs/pytest-ks02-reviewed
.\.venv\Scripts\python.exe -m ruff check --no-cache .
.\.venv\Scripts\python.exe -m ruff format --check --no-cache .
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe scripts/check_repository.py
git diff --cached --check
```

Feature tests: 30 passed. Full suite: 124 passed/1 skipped (125 collected). Ruff: lint clean,
18 formatted files. Mypy: 14 source files clean. Repository documents/links/task IDs/PDF checksum
pass; checker is rerun after phase records. Skip remains Windows symlink creation privilege.
Python 3.11/3.13 and Linux not executed. No official assets/evaluation/benchmark are claimed.

## Remaining work and continuation

No known phase implementation bug remains on this environment. Human approval and shared config
integration are pending; KS-04/05 external blockers persist. Central status files remain Ayush's.

1. Continue KS-03 according to [phase plan](../data/KAUSTUBH_PHASE_PLAN.md), using explicit group
   assignments/chronological cuts and separate context versus scored targets. Then review/fix it.
2. Complete KS-06 synthetic stress/integration, report gap/contamination/scale-floor limitations,
   and preserve all exact results in the personal task file and a unique handoff.
3. When publication is authorized under ADR-09, push this task-set branch and open a PR to main,
   requesting Ayush/Manas feature review and Mayank manifest/split review. No automatic main merge.
4. Another machine must retrieve the actual published branch/commit; until then it cannot access
   the local implementation or ignored output directories.

Prepared PR addition: implement bounded strictly causal feature frames with explicit warmup and
seasonal unavailability, atomic error handling and hand-derived/leakage regression coverage.
Shared types and existing starter path remain compatible. Link this handoff and implementation.
