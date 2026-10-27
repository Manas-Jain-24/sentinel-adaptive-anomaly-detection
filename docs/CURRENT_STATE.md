# Current integrated state

Maintainer: Ayush. Repository audit: 2026-10-27 (Asia/Calcutta), authorized by the user's explicit
combined Ayush/Kaustubh scope. Verified integrated baseline: **origin/main 8c1be6fdd167c741ad1de0123d48bda3effbab12**.
This feature PR corrects stale summaries; pending PRs remain separate from main. No merge was
performed by this audit. Git/code/executed checks take precedence over historical planning prose.

## Actual implementation

- Python package/CLI, typed shared contracts including future FeatureFrame/FeatureExtractor.
- Strict canonical CSV and config loading, causal rolling median/MAD starter, bounded per-series state.
- Numerical evidence, new-directory JSONL/manifests/checksums, process timing, expected error handling.
- Provisional event-trigger F1 evaluator with explicit unofficial identity and separate truth.
- KS-01/02/03/06 inventory, causal features, frozen group/chronological split tooling and stress
  tests, merged through [PR #2](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/2)
  at `50f40009f4ddd757b5dfb7ac1c34e379d6801ac1`. Manas and Ayush APPROVED reviews are present;
  the prior COMMENTED agent review is distinct. No Mayank approval is claimed.
- MN-01 rolling z-score comparator/tests, merged through PR #1. Default CLI remains MAD;
  there is no model selector on main.
- MY-01 expanded provisional evaluator/golden cases and MY-03 frontend artifact viewer, merged
  through PR #6 (`b301c07`). Viewer build/browser QA was not rerun in this audit.
- Synthetic fixtures, foundation tests, lint/type/repository checks, Windows/Linux CI and
  requirements.txt with existing development pins. No new dependency was added by this audit.

## Planned, not implemented

Raw organizer adapter, real EDA, residual/quantile CLI integration, checkpoint/resume, MY-02
experiment harness, official scorer/exporter, candidate freeze, final PPT/video/submission and
teammate clean-clone reproduction. Inventory/features/splits and the viewer now exist; automatic
split-enforced CLI replay does not. No final competition milestone is certified.

## Verified checks and Git state

Exact main `8c1be6f`: **266 passed, 1 skipped** for unavailable Windows symlink privilege, also
reproduced from a Git archive. Ruff lint/format (25 files), strict mypy (16 source files), pip
check, repository checker (139 links/24 tasks/original PDF hash) and whitespace checks passed.
Archived-main README replay/evaluate: 16 synthetic points, provisional TP/FP/FN=1/0/0. Local
execution Windows/Python 3.12.14. Main's exact-head Actions run **40494596951** has four successful
Ubuntu/Windows Python 3.11/3.13 jobs, read from check-runs. Empty legacy statuses certify nothing.
All metric evidence is synthetic `provisional_event_trigger_f1_v0`, official_metric=false.

Origin remains [the shared repository](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection).
All branches were fetched; the old KS branch pull --ff-only was already current, and this new
task branch starts at fetched main. Initial tree clean; no stash/reset/force push/branch deletion.
Local main was not rewritten and no competition submission/release/protection change occurred.

## Pending review, not integrated

| PR | Fetched head | Actual state at recovery |
|---|---|---|
| #3 residual | `891a8539a4ad424e7a2673aca76a022345d52a05` | Open; four PR-matrix jobs passed; no reviews/comments |
| #4 prior quantile | `8907b47b6518b81b87aebe9c1b68389fbef6d76c` | Open; four PR-matrix jobs passed; no reviews/comments |
| #5 guard/forecast readiness | `9339ac2d84e62dd0762d58d2aaf585bf5455f79a` | Draft; four PR-matrix jobs passed; no reviews/comments |
| #7 CLI/profiling | `a52dd287e276bc9f4596394934999852d7bb3d55` | Open; eight push/PR check-runs passed; owner review pending |

PR #7 contains AY-01 `a859457`, published #3/#4/#5 history and model/CLI integration. Shared typed
contracts/base config/data code are unchanged. Its optional split snapshot is **checksum-only**,
not permission/source/lookback/target-mask validation. Exact head reproduced 609 passed / 1 skip;
Ruff/mypy/repository checks passed. Avoid duplicating its wiring/profiling/Windows retry work.

Follow-up implementation `05d2ee4ce733943baf46e36ee5bb40ef9aaa1594` hardens CSV parsing and adds
22 reader/replay/fallback cases. Pre-record candidate 288 passed / 1 skip. #7 archive plus only its
three source/test files 631 passed / 1 skip, full Python gates and default/short-quantile smoke parity.
This is a compatibility snapshot, not a merge. Checkpoint work is a
[proposal](HANDOFFS/AY-02_ayush_20261027T113440Z_checkpoint-proposal.md); no state API/--resume exists.
The [integration handoff](HANDOFFS/AY-03_ayush_20261027T113928Z_integration-review.md) records final
candidate commands/publication/reviews/next actions. Candidate changes remain subject to review.

## Known external blockers

Local data/official contains only README. Inspected remote main/open PRs, repository issues and
release assets supply no official pack, authorized download, or Q01/Q09 answer. No participant
portal access was supplied; absence from inspected evidence does not establish absence there.
KS-04/05 stay BLOCKED on organizer assets, authorized development labels/permissions, prescribed
partitions and timestamp/cadence/column/missingness semantics. Q04/Q08 context/update permission,
official scorer/goldens/schema and Q07/Q10 runtime/entrypoint/deadline also remain unresolved.
No guessed timezone/cadence, public NAB substitution, real EDA or official parity is claimed.

## First work

Review #7 and this follow-up with affected owners; approve/record shared-contract decisions
before AY-02 implementation; complete MY-02 under Mayank's ownership. Merge only with actual
authorization, rerun gates on the merged commit, then reconcile records. M4/G1 is incomplete
while the residual path/harness remain unintegrated; official G2 stays blocked. Use fixtures/doubles
for independent software work and preserve the [source hierarchy](START_HERE.md).
