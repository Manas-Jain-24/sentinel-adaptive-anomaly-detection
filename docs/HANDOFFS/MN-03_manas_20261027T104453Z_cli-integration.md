# MN-03 CLI integration with AY-01 provenance/profiling

Developer executing: Manas. Original shared-file owner: Ayush.
Authored UTC: 2026-10-27T10:44:55.208204+00:00; client date 2026-10-27 Asia/Calcutta.
Status: IN_REVIEW, complete synthetic software increment; no main merge.
Branch: `feat/manas/MN-03-cli-integration`. Implementation: `beaa4182206275670c0cf02181847a07101fb4ee`.
Regression/docs commit: `3d22b4c9be996a1cdd87ab8e68fa2f7e8e54a7d0`. Final evidence/publication commits follow.

## Authorization / recovered state

The user said "do then" after the explicit recommendation to integrate published detector
components/CLI now while Mayank builds the harness in parallel. This is scoped human
permission for this feature-branch CLI/pipeline integration, not a permanent ownership
transfer, breaking-contract approval, fabricated Ayush review or main-merge permission.
[Proposal](MN-03_manas_20261027T103208Z_cli-integration-proposal.md) records old/new behavior,
impact/rollback and required reviews before implementation.

Reviewed main: `50f40009f4ddd757b5dfb7ac1c34e379d6801ac1`; clean local state preserved.
Published Manas PR #3/#4/#5 heads were inspected independently: no comments/reviews,
all reported CI successful; #3/#4 ready, #5 draft. Their histories were included unchanged.
Ayush branch at `a859457d1815824e84ac785a04cee3ce7d401222` was fetched, inspected and merged
into this feature branch with original authors/history preserved (merge `d422184`).
AY-01 handoff/task still says local-only; actual fetched remote proves publication.
No MY-02 branch/harness was visible. Central summaries still describe initialization;
Ayush must reconcile them after review/integration. No teammate active work was rewritten.

## Changes and files

- `detectors/selection.py`: separate strict frozen model config, real per-series factory,
  explicit algorithm ID and resolved feature/calibration/support metadata. Rejects ambiguous
  or unknown settings, duplicate keys, invalid/nonfinite calibration and seasonality.
- `cli.py`: --detector mad/zscore/residual OR --model-config; no silent override. No option
  still means MAD. `config.py`, legacy five-key JSON, Detector/Prediction/Evidence unchanged.
- `pipeline.py`: optional keyword-only model_config, actual factory/algorithm/model identity,
  model/combined hashes while base config hash retains its meaning. Preserves AY-01 source,
  environment, workload/timing, staged output and opaque split snapshot behavior.
- `configs/residual-quantile.model.json`, `residual-seasonal.model.json`: explicit examples,
  not tuned/final candidates. README and INTERFACES document options, limits and review state.
- Three owned test modules: selection, CLI composition/provenance, Windows publication errors.
  No foundation/pipeline/data/evaluation-owned tests changed. Personal task/handoff/evidence only;
  no central records, shared typed schema, new dependency, official adapter or harness added.
- Production guard prototypes remain disabled; forecast wrapper exists but unloaded models are
  not CLI selectors. No Chronos/TimesFM download/run, checkpoint or real-data fitting was added.

## Actual validation and findings

Using `.venv/Scripts/python.exe`:
- Before integration edits: `-m pytest -q --basetemp outputs/pytest-integration-baseline-001
  --tb=short`: 523 passed, one Windows symlink-privilege skip.
- Final: `-m pytest -q --basetemp outputs/pytest-cli-integration-final-001 --tb=short`:
  **582 passed, one Windows symlink-privilege skip**. Of these, 59 are new integration cases.
- `-m ruff check .`: passed. `-m ruff format --check --no-cache .`: 46 files formatted.
- `-m mypy`: 23 source files passed. `scripts/check_repository.py`: 32 mandatory docs,
  194 relative links, 24 task IDs/PDF hash passed before final evidence/docs.
- `git diff --check`: passed. Initial lint line lengths were formatted before final checks.
- Seven actual `python -m sentinel run` / `evaluate` subprocess smokes completed. Exact
  commands/results/full outputs at [evidence](../validation/MN-03_manas_20261027T104453Z_cli-integration/README.md).
  Default 16-point MAD equals Ayush baseline semantically; model/config hashes and source
  clean revision recorded. Long quantile smoke actually reaches nearest-rank after 40 rows.
- Measured diagnostic limitation: quantile ties start an episode at 40 before the synthetic
  event at 64, so provisional TP/FP/FN=0/1/1. Seasonal smoke has 1/1/0; fixed MAD/z/residual
  have 1/0/0 on this one artificial trace. No winning configuration or benchmark is claimed.
  Regression asserts observed miss; no metric/threshold/tuning changed to conceal it.

Two intermediate full suites failed at different Windows staged-directory renames with
WinError 5 (571 passes then 575 passes); three focused reruns between them passed. Root
cause of OS denial unknown. Added the minimal bounded publication retry for Windows
PermissionError 5/32 only: six attempts, 310 ms total backoff, recheck destination each
attempt. Five tests prove eventual success, persistent error propagation/cleanup, no
non-Windows retry and preservation of a collision appearing during backoff. Backoff is
outside existing measured profiling regions. Full suites after fix passed (581 then 582
when the tie regression was added). No failure is silently converted to successful output.

## Integration / review / continuation

1. Publish this branch and integration PR with this exact evidence. Existing module PRs
   remain open; no automatic merges/closures or branch deletion. Main unchanged. This PR
   combines their published commits plus AY-01 and the small wiring increment, so review
   dependencies before integration; avoid reimplementing/cherry-picking duplicate modules.
2. Ayush reviews CLI/pipeline/model hashes, additive INTERFACES proposal and minimal Windows
   publication fix. Kaustubh reviews feature settings/support; Mayank reviews artifacts and
   scientific/episode interpretation. All reviews are pending; no approval was invented.
3. Mayank can now build MY-02/MY-03 on real saved artifacts. --split-manifest still means
   checksum-only provenance: no source membership, filtering, target mask, fitting permission
   or lookback enforcement is certified. Apply KS-03 target/context policy in the harness,
   exclude context from metrics, and record exact complete run identity plus metric/data/code.
4. Request official pack/authorized labels/overlap permissions/splits and Q01/Q09 time/cadence,
   Q08 update/pretraining, official scorer/schema. Public NAB reference remains separate.
   MN-04 real guard promotion, MN-05 comparisons/freeze and MN-06 A/B gates remain blocked.
5. Ayush reconciles central summaries after authorized review/merge. No main merge here.

At authorship source is locally committed; this new branch is not yet pushed. Another
machine must wait for the final PR/publication record, then fetch that branch/head. Use
fresh output/basetemp directories; never overwrite existing runs. Final PR records actual
shared head/CI status. No new external message or extra GitHub review comment was sent.
