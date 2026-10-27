# Manas detector readiness: MN-04, MN-05 and MN-06 gate audit

Authored UTC: 2026-10-27T10:13:44.268265+00:00; client timezone Asia/Calcutta (2026-10-27).
Developer/original owner: Manas. Branch: `feat/manas/MN-04-05-detector-readiness`.
Implementation commit: `b88d38a77bd12bed704f7b68158985208406eae7` (local at authorship; publish branch/PR next).
Dependencies: MN-02 refreshed at `891a853`; MN-03 refreshed at `8907b47`.
Reviewed main: `50f40009f4ddd757b5dfb7ac1c34e379d6801ac1`.

## Status and scope

MN-01 DONE (merged PR #1). MN-02/03 IN_REVIEW (PR #3/#4) with direct required real
feature/partition/composition imports and current main history. MN-04 BLOCKED for
production-policy validation, with its synthetic comparison now implemented/verified.
MN-05 BLOCKED for real experiments/candidate freeze, with its causal forecast wrapper
implemented/verified. MN-06 BLOCKED by A/B gates; preliminary decision NO-GO, no EVT fit.
This is a tightly coupled readiness branch stacked on PR #4, not a new project.

Owned implementation: `src/sentinel/detectors/forecast.py`, FORECAST.md, READINESS.md;
`tests/detectors/guard_study.py`, test_guard_study.py, test_forecast.py;
personal tasks, this unique handoff and the linked validation artifact. No data-owned,
evaluation-owned, pipeline/CLI/config/contracts/CI or central record was changed.
Ayush's published AY-01 branch was inspected; no MY-02 branch/harness was visible.
No teammate work was taken over. Main was neither changed nor merged into by this work.

## Implementation / decisions

- Forecast interval scoring implements the previously proposed q10/q50/q90 exceedance
  formula with an injected inference-only model. Prior bounded contexts, exact horizons,
  frozen blocks/origins/age, numerical evidence, validation, UTC/order/series lifecycle,
  reset/failure recovery and optional empirical calibration preserve Detector v1.
  No actual Chronos/TimesFM adapter/library/weights/download/API parity or GPU run exists.
- 56 predeclared synthetic comparisons: seven scenarios x four policies x fixed/adaptive
  thresholds. Uses real residual/features and calibrator, labels only in the evaluator.
  Prototype reconstruction is intentionally slow; quarantine delta uses admitted history.
  Do not promote this test-only code or time it as the production core.
- Finite quarantine bounds consecutive exclusions and a disable/reset/replay regression
  reproduces no guard. Shadow changes state only after the alarm is emitted.
- Trade-off: on this synthetic sustained fault, fixed no guard flags 16/128 event points;
  finite quarantine flags 128/128, but benign-ramp alerts rise from 7 to 155. Both detect
  the event once under provisional matching, so event recall alone hides absorption.
  Adaptive thresholds and shadow also have mixed results; all exact counts are archived.
  Fault/benign-step observations are identical, illustrating the ambiguity of rebaseline.
  These are diagnostic points/episodes, not official recall/quality gains.
- Keep no guard in production. New forecast API is detector-local; shared CLI/model metadata
  adoption requires Ayush review. No shared contract schema/dependency change was made.
- Frozen forecast blocks have origin-phase state: sufficient W+C values alone does not
  prove partition parity. Full replay is required until reviewed persistence is available.
- Preliminary EVT NO-GO: A path not officially valid and B not measured. Synthetic final
  buffers' actual tail/tie counts are recorded; real tail sufficiency is unknown. No fit,
  library selection, build/license validation or completed post-gate spike is claimed.

## Actual verification

All Python commands use `.venv/Scripts/python.exe` from repository root.

- `-m pytest tests/detectors/test_forecast.py tests/detectors/test_guard_study.py -q
  --basetemp outputs/pytest-readiness-003 --tb=short`: 70 passed.
- `-m pytest -q --basetemp outputs/pytest-readiness-final-001 --tb=short`:
  504 passed, 1 Windows symlink-privilege skip. No optional integration-module skips.
- `-m ruff check .`: passed. `-m ruff format --check --no-cache .`: 37 files formatted.
- `-m mypy`: 20 source files passed. `scripts/check_repository.py`: passed before docs,
  32 docs / 171 links / 24 task IDs / official PDF hash. `git diff --check`: passed.
- `tests/detectors/guard_study.py --output-dir outputs/mn04-study-final-001`:
  56 comparisons completed on clean implementation `b88d38a77bd12bed704f7b68158985208406eae7`; all source hashes recorded.
- `-m sentinel run --input tests/fixtures/synthetic_stream.csv --config configs/starter.json
  --output-dir outputs/manas-readiness-smoke-001 --dataset-id synthetic-fixture-v1
  --scope synthetic_smoke`, then `-m sentinel evaluate --run-dir
  outputs/manas-readiness-smoke-001 --windows tests/fixtures/synthetic_windows.json`:
  16 points, unchanged MAD default, provisional TP/FP/FN=1/0/0.

Early lint runs caught long lines and a function-call default, corrected before final
checks. Initial focused software tests passed 60 cases; added endpoint, size, timezone,
fixed-baseline and block-phase cases increased this to 70. No test assertion or policy
parameter was changed to improve the observed comparison results. Earlier branch-refresh
Temp/encoding errors and their fixes are recorded in the MN-02/03 refresh handoffs.

Evidence: [portable summary](../validation/MN-04-05_manas_20261027T101343Z_synthetic-readiness.json). It includes complete configs,
synthetic fixtures, paired counts, flag indices, source hashes and semantic/action hashes.
The 10 MB full report is local/ignored; reproduce on another machine using the script and
compare canonical prediction/action hashes (wall time/environment fields may differ).
No official data benchmark, hidden evaluation, real model score or runtime is claimed.

## Integration and exact next actions

1. Push refreshed PR #3 and #4 and this branch; retain review order #3 -> #4 -> this PR.
   All PRs target main; later PR diffs shrink as dependencies merge. Do not automatically
   merge main, force-push, delete branches or post extra review comments.
2. Ayush reviews runtime/contracts/CLI adoption and reconciles stale central summaries;
   Kaustubh reviews feature interaction; Mayank reviews diagnostics, splits and selection.
   Passing checks are not fabricated peer approvals. No external messages are sent here.
3. Obtain official starter pack, authorized labels/permissions and overlap restrictions,
   prescribed partitions, Q01/Q09 time/cadence and Q08 update/pretraining permissions.
   Public NAB reference in ignored outputs remains separate and does not unblock these.
4. Use Mayank MY-02 harness to run EXP-01 and fixed/component/quantile/guard comparisons
   on approved partitions, recording actual error examples, delays/runtime and promotion gates.
   Coordinate an explicit feature/calibration update API before a production guard.
5. Implement/review real Chronos/TimesFM adapters and package/model terms/pins, measure CPU
   and permitted GPU workloads if available; use the tested forecast boundary. Freeze only
   after paired results. Optional IF comparison also requires dependency review.
6. Reopen MN-06 only after Level A/B gates; inspect actual tails, fit/build/license and
   fallback behavior. Disable/remove on insufficient evidence. No mandatory dependency now.

At authorship source is locally committed but not yet pushed; another machine cannot access
this new work until publication. Final PR body records the actual published branch/head/link.

Publication follow-up: refreshed PR #3/#4 branches and this branch were pushed. The
post-documentation repository checker found a task-file evidence link missing `docs/`;
the link was corrected in a follow-up commit and the checker rerun before final handoff.
Use the final PR head, not the first documentation commit, for clean-clone checks.

Published review: [draft PR #5](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/5).
The branch was shared through `eecdc915929e1b8fe211a761d558b06639742d69` before this
publication-only note. PR #3/#4 are now ready for review; exact refreshed heads
`891a8539a4ad424e7a2673aca76a022345d52a05` and
`8907b47b6518b81b87aebe9c1b68389fbef6d76c` have all reported CI jobs successful.
PR #5's final-head CI must be checked independently. Main remains `50f4000`.
