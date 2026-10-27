# KS-01/02/03/06 publication and receiving-agent handoff

- Developer/original owner: Kaustubh. Receiving friend/developer identity not supplied.
- Authored: 2026-10-26 22:07:53 +05:30 (Asia/Kolkata), 16:37:53 UTC.
- User authorization: explicitly push Kaustubh's work as a PR, state all remaining work and why,
  and prepare a prompt so a friend with a fresh agent can review/continue. No main merge authorized.
- Status: KS-01/02/03/06 IN_REVIEW; KS-04/05 BLOCKED; no ownership or shared-contract approvals invented.
- Shared branch: `feat/kaustubh/KS-01-02-03-06-data-workstream`, remote origin in the repository below.
- Shared [PR #2](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/2), open,
  targets main. Initial shared snapshot `955564571de61971ac270addf6cd560bc918c4da`.
- Base main at publication: `d7158d62eb8fa4e4c5d4907238d03c5989967083`.
- Implementation commits: KS-01 `9092d118201c62fec318a28afc9f9670a55745a8`;
  KS-02 `2b991a9b4b218ac74f447f0ff8b253d899cbef7a`;
  KS-03 `8047bc4bc7ff9c975c1901ad10af1cd26fe7e720`;
  KS-06 `04b91e86be5c5fca377c1f3049c96969c9b81318`.

This is the latest publication record; older handoffs' local-only statements describe historical
snapshots. The branch/implementation are now retrievable from GitHub. Ignored outputs/review logs,
virtual environments and any future restricted data are not published. No reset, force-push,
main merge, other-owner implementation or central integration-record edit was performed.

## Retrieval and required context

Repository: https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection

From a suitable clean checkout after inspecting status/remote (do not overwrite unrelated work):

```text
git fetch origin feat/kaustubh/KS-01-02-03-06-data-workstream
git switch --track origin/feat/kaustubh/KS-01-02-03-06-data-workstream
```

If the local branch already exists, inspect/reuse it safely instead of resetting it. A new clone
can use normal git clone and switch to this remote feature branch. Verify the PR's latest SHA
and actual working tree; later documentation commits record publication/PR references.

Read AGENTS, README, START_HERE, CURRENT_STATE, ARCHITECTURE, INTERFACES, personal tasks, INTEGRATION,
HANDOFF_PROTOCOL and this record. Then read the [previous full implementation handoff](KS-06_kaustubh_20261026T161521Z_final-workstream.md),
[inventory](../DATA_INVENTORY.md), [features](../DATA_FEATURES.md), [splits](../DATA_SPLITS.md),
[stress report](../DATA_STRESS.md) and [copyable agent prompt](../data/KAUSTUBH_AGENT_PROMPT.md).
CURRENT_STATE is Ayush's merged-main summary; use actual PR code/tests to establish unmerged state.

## Implemented and verified

Canonical source/permission inventory, SHA256/size and per-series cadence/gap statistics;
bounded causal FeatureExtractor with explicit warmup/seasonal unavailability and atomic errors;
deterministic group/chronological split manifests with source-backed validation and context/purge
bounds; synthetic stress/integration tests and examples. Actual source/tests are data-owned.
No shared Observation/FeatureFrame/config/run.json or default CLI/harness path was changed.

Every phase received independent agent review. KS-02 DST-fold ordering and integer-overflow
exception issues were reproduced, fixed and rechecked. No remaining agent-review findings.
The reviews are not teammate approvals. Existing data format/settings adoption needs normal review.

## Remaining work, owners and reasons

| Item | Responsible owner/reviewer | Why still pending / next action |
|---|---|---|
| Review KS-01/02/03/06 | Ayush: manifests/order/config; Manas: causal features; Mayank: splits/leakage/consumers | Tested components remain IN_REVIEW. Inspect actual diff and semantics, fix reproducible issues, record normal owner approval and required integration before DONE. |
| Adopt components in the intended pipeline/detector/harness | Existing Ayush/Manas/Mayank tasks, including AY-01/03, MN-02, MY-02 as applicable | Default CLI still runs MAD starter. Confirm current branches to avoid duplication, coordinate factories/config/artifact linkage and use declared context/target masks/effective lookback/state policy. New shared contracts require the normal approval process. |
| Latest CI matrix | Integration owner/reviewers | Local execution was Windows/Python 3.12. Check the latest PR-head Ubuntu/Windows Python 3.11/3.13 jobs and symlink case; do not infer success from configuration or an older head. |
| KS-04 official adapter | Kaustubh or explicit handoff recipient | BLOCKED: actual pack, authorized labels/permissions, prescribed partitions and Q01/Q09 semantics are missing. Preserve raw input; confirm timezone/cadence/columns/missingness and test actual sample mappings when supplied. |
| KS-05 real EDA / train-only periodicity | Kaustubh or explicit handoff recipient | BLOCKED: depends on KS-04 plus authorized development labels. Produce data/split-tagged EDA/figures for slides3/5 and EXP-01 only after those inputs exist. |
| Merge and reconcile central status | Ayush after authorized review | CURRENT_STATE/TASK_BOARD/INTEGRATION were intentionally not edited in parallel. Merge requires separate authorization/normal gates, then Ayush reruns checks and reconciles records. |

The user reported intended future official intake as
`C:\Users\HP\Desktop\EngimaxIota hackathon\data\official\`, currently only README, with no
authorized download or Q01/Q09 answer. That HP path is absent on this host; the current checkout's
data/official also contains only README. Do not use public NAB/hidden labels or assume raw UTC
to bypass these blockers. The original owner remains Kaustubh; identify the receiving developer
before modifying owned code and do not take over other developers' active work without authorization.

Known limits: fixed scale floors have units; contamination can define warmup reference; sample
lags are not time-based seasonality after gaps; disjoint finite feature supports do not certify
persistent model/calibration-state independence. All are documented rather than hidden by changes.

## Fresh publication verification and commands

Windows/Python 3.12.14, installed environment, repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest --basetemp outputs/pytest-pr-publication
.\.venv\Scripts\python.exe -m ruff check --no-cache .
.\.venv\Scripts\python.exe -m ruff format --check --no-cache .
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/check_repository.py
git diff --check origin/main...HEAD
git push -u origin feat/kaustubh/KS-01-02-03-06-data-workstream
gh pr create --repo Manas-Jain-24/sentinel-adaptive-anomaly-detection --base main --head feat/kaustubh/KS-01-02-03-06-data-workstream --title 'KS-01/02/03/06: data inventory, causal features and leakage-checked splits' --body-file outputs/kaustubh-pr-body.md
```

All final local checks, push and gh PR creation exited0. Pytest:191 passed/1 skipped (192 collected).
Ruff lint/format clean (21 files); strict mypy15 source files; pip no broken requirements;
repository docs/links/task IDs/PDF checksum and whitespace checks pass. The single local skip is
Windows symlink privilege. Use fresh basetemp and smoke-output paths when reproducing.

The GitHub connector could read but PR creation returned403 (integration permission); the
existing authenticated GitHub CLI successfully created PR #2. The PR was attached to this chat.
No credential/token was printed or placed in files/URLs. Remote CI is triggered; inspect its
latest actual result, not the local suite or any earlier PR head, before claiming matrix success.

Previous final CLI smoke in outputs/kaustubh-data-final-smoke-001 produced16 synthetic points,
8 ready/1 anomalous, provisional TP1/FP0/FN0. It was not rerun for these documentation-only
publication edits. Earlier handoff records exact commands and source hash/count parity. These
are synthetic wiring results only; no official score, real EDA or runtime benchmark was run.

## Immediate continuation

Start by reviewing this PR, reproducing checks, and inspecting current shared branches/handoffs.
Fix issues within authorized ownership, coordinate consumer adoption, and record changes/results
in personal tasks and a new unique handoff. Use the copyable prompt above. Only proceed to KS-04/05
when genuine authorized inputs/answers arrive; no unblocked data-module implementation was left
unfinished. Do not merge main or mark tasks DONE merely because this PR exists.
