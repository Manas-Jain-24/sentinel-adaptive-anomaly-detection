# Kaustubh - data integrity and causal time-series features

Role: data/feature engineer. Own `src/sentinel/data/`, `tests/data/`, permitted data adapters,
inventory/split manifests, and data-specific documentation. Inputs: authorized raw assets or
explicit synthetic fixtures. Outputs: validated Observation streams, FeatureFrame, provenance,
and frozen splits. Never commit restricted data or silently infer timezone/label permissions.
Read [INTERFACES](../docs/INTERFACES.md) and [EXPERIMENT_PLAN](../docs/EXPERIMENT_PLAN.md).

Status vocabulary: TODO, IN_PROGRESS, BLOCKED, IN_REVIEW, DONE. One effort unit ~= a focused
half-day including verification; no calendar deadline or skill level is assumed.

| ID | Priority / effort | Task and explicit deliverable | Dependencies | Status |
|---|---|---|---|---|
| KS-01 | P0 / 2 | Build inventory/provenance manifest schema and validator; lengths/cadence/gaps/duplicates/finite values; audit fixtures now and real assets when received | Approved/merged #2 at 50f4000; consumer adoption continues in #7/MY-02 | DONE |
| KS-02 | P0 / 3 | Implement bounded causal FeatureExtractor: prior median/scale, expected delta, observed delta, optional past-only seasonal reference with explicit unavailable state | Existing FeatureFrame; approved/merged #2; shared config adoption in open #7 | DONE |
| KS-03 | P0 / 2 | Implement deterministic group/chronological split manifest tooling and boundary-purge validation; hashes and group constraints | Approved/merged #2; MY-02 target/context adoption pending | DONE |
| KS-04 | P0 / 2 | Adapt organizer starter files/labels to canonical input, with documented timezone/gap/column mapping and access provenance | Official assets and Q01/Q09 answers | BLOCKED |
| KS-05 | P1 / 2 | Real dataset EDA and train-only periodicity/cadence analysis; provide figures/notes for slides 3/5 and EXP-01 | KS-04, permitted development labels | BLOCKED |
| KS-06 | P1 / 2 | Stress feature/data behavior on missing spans, rescaling, contaminated warmup, flat/short series; report limitations | Original tests approved/merged #2; reader/replay follow-up in review | DONE |

**First three tasks:** KS-01, KS-02, KS-03. KS-01 starts on synthetic inputs with explicit labels
and cannot claim a real NAB inventory. KS-02/03 can be developed with fixed mock manifests;
do not wait for official assets to implement validation and leakage tests. Core effort: 13 units.

## Ownership and shared interfaces

Use typed Observation/FeatureFrame and explicit UTC normalization. The extractor constructs
expected statistics from earlier observations, computes current delta from the previous point,
then updates once. No centered rolling windows, global normalization, future interpolation,
whole-series period estimates, or label features. Warmup and unavailable seasonality are explicit
nulls/readiness, not invented zeros. Expose bounded history configuration through a reviewed
contract extension; coordinate shared config/type changes with Ayush and Manas.

Manas owns detection/calibration; do not tune hidden labels or independently redefine the
Prediction schema. Mayank consumes frozen split/label manifests; detector inputs exclude labels.
Manas can use fake feature frames before KS-02 is ready. AY-03 consumes the canonical stream.

## Acceptance and test responsibilities

- KS-01: correct source/checksum/time/cadence counts on a hand-derived example; missing permission,
  schema mismatch, duplicates, nonfinite values, and missing files are visible errors.
- KS-02: prefix invariance; exact known level/delta traces; scale floor; one-point/constant/short
  streams; periodic lag absent until enough past context; independent per-series state.
- KS-03: stable hashes/order; group isolation; no overlapping feature windows across training
  boundaries; reproducible split seed if needed; explicit past-context allowance at validation.
- KS-04: real sample mapping matches organizer semantics; official truth stays separate; raw
  source is unchanged; timezone assumption confirmed or explicitly unresolved rather than guessed.
- KS-05: each EDA claim identifies data/split; no test-fitted seasonality; provide actual figures
  and event counts only after authorized data is available.
- KS-06: stress results distinguish synthetic robustness from development performance; surface
  where gap handling/scale invariance fail and include integration regression tests.

Reviewer: Ayush for manifest/order/contracts and Manas for feature causality/semantics. Mayank
reviews split leakage and evaluation compatibility. Deliver tested code, example manifests,
data notes, and a unique task handoff; update only this personal task file and owned docs.

## Handoff and local progress

Initialization supplied only the strict internal reader `data/io.py`. The progress below records
subsequent owned work; shared CURRENT_STATE/TASK_BOARD/INTEGRATION remain Ayush's responsibility.

### KS-01: inventory/provenance validation, 2026-10-26 (Asia/Kolkata)

- Status: IN_REVIEW. Synthetic acceptance cases are implemented and verified; Ayush/Mayank review
  and integration remain pending. No official asset inventory or peer approval is claimed.
- Branch: `feat/kaustubh/KS-01-inventory`, from main `d7158d62eb8fa4e4c5d4907238d03c5989967083`.
- Implementation commit: `9092d118201c62fec318a28afc9f9670a55745a8` (local only, not pushed).
  Another machine cannot retrieve this work until an authorized push/shared archive exists.
- Code: `src/sentinel/data/inventory.py` adds typed source/inventory dataclasses, required source
  and permission declarations, portable contained paths, exact file hashes/sizes, per-series
  lengths/UTC ranges/value ranges/cadence/gap statistics, deterministic new-file JSON, and full
  schema/checksum/statistic revalidation. It reuses the canonical reader and rejects duplicates,
  backwards instants, nonfinite/malformed inputs, repeated source/series IDs, and stale manifests.
- Tests: `tests/data/test_inventory.py`. Documentation/example:
  [data inventory](../docs/DATA_INVENTORY.md) and
  [synthetic audit](../docs/data/synthetic-fixture-inventory.json).
- Actual final checks on Windows/Python 3.12.14: owned tests **70 passed, 1 skipped**; full suite
  **94 passed, 1 skipped** (95 collected). Windows lacks symlink-creation privilege; the escaping
  symlink test is skipped and must run on a capable CI/reviewer host. Ruff lint/format, strict
  mypy (13 source files), pip dependency check, repository checker, and Git whitespace checks pass.
- Existing CLI replay/evaluation passed on 16 synthetic fixture points. Audit source SHA256 and
  observation count match the CLI manifest. The provisional artificial-event result was TP=1,
  FP=0, FN=0; this is wiring evidence only. No official benchmark or performance measurement ran.
- Contracts: shared Observation/FeatureFrame/config/run.json are unchanged. The separate versioned
  inventory format is proposed for consumer review before AY-01/MY-02/KS-03 adoption. Declared
  provenance is an operator assertion; unknown cadence does not imply zero missing samples.
- Independent agent review reproduced the checks and reported no findings. This does not supply
  Ayush/Mayank approval; required owner review remains pending.
- Limits/dependencies: offline exact cadence medians retain O(N) intervals; inputs must remain
  stable during audit. Official data/permissions/timezone mapping remain missing (KS-04 blocker).
  No raw adapter, labels, features, splits, or detector fitting are added by this task.
- Exact commands, results, review/publication obligations and continuation steps are in the
  [KS-01 handoff](../docs/HANDOFFS/KS-01_kaustubh_20261026T152032Z_inventory.md).
- Next: obtain Ayush's manifest/order review and Mayank's consumer review, publish/open the
  prepared PR when authorized, then start **KS-02** on its own feature branch. Coordinate bounded
  feature configuration with Ayush/Manas before changing shared contracts. KS-03 remains TODO.

Optional stretch: contribute past-only reference-window tooling for EXP-09/S2 after P0 tasks;
coordinate with Manas and document horizon/memory effects before adoption.

### Phased continuation: KS-02, 2026-10-26 (Asia/Kolkata)

- User authorized completing assigned work phase by phase with review/fixes after each phase.
  Active aggregate branch: `feat/kaustubh/KS-01-02-03-06-data-workstream`. It retains KS-01's
  original commits; INTEGRATION permits this explicitly listed tightly coupled task set.
- KS-02 is implemented and verified, status IN_REVIEW pending Ayush/Manas consumer review.
  Implementation commit `2b991a9b4b218ac74f447f0ff8b253d899cbef7a` is local, not published.
- Added `src/sentinel/data/features.py`, `tests/data/test_features.py`, and
  [feature semantics](../docs/DATA_FEATURES.md). Existing FeatureFrame/protocol/config remain intact.
  Constructor parameters are proposed implementation settings; shared config integration still
  requires Ayush/Manas review. No label input, period estimation, interpolation or detector changes.
- Independent review found UTC-fold ordering and integer-overflow exception issues. Both were
  reproduced with failing tests, fixed by normalizing instants/values before processing, and
  rechecked by the reviewer: no remaining findings. Agent review is not teammate approval.
- Actual final commands: feature suite 30 passed; full pytest 124 passed / 1 skipped; Ruff check
  and format check pass (18 files), strict mypy passes (14 source files), repository checker and
  whitespace check pass. The existing symlink test skips for Windows privilege; only Python 3.12
  Windows executed. Exact commands/limitations are in the
  [KS-02 handoff](../docs/HANDOFFS/KS-02_kaustubh_20261026T155217Z_features.md).
- Next software phase: KS-03 frozen splits; then KS-06 stress/integration. KS-04/05 remain blocked
  by actual organizer assets and permissions. No official performance result has been produced.

### Phased continuation: KS-03, 2026-10-26 (Asia/Kolkata)

- Status IN_REVIEW; software phase complete, Ayush/Mayank approval pending. Implementation commit
  `8047bc4bc7ff9c975c1901ad10af1cd26fe7e720` on the aggregate branch, local only/not pushed.
- Added `src/sentinel/data/splits.py`, `tests/data/test_splits.py`,
  [split semantics/API](../docs/DATA_SPLITS.md) and
  [synthetic example](../docs/data/synthetic-fixture-split.json). Explicit full-group assignment or
  per-series chronological cuts; deterministic inventory/split hashes, strict source-backed
  validation, explicit context/targets and conservative boundary purging. No random split/seed,
  label loading, model fitting, shared contract or other-owner edits.
- Final focused split tests: 45 passed; full suite: 169 passed / 1 skipped (170 collected). Ruff
  lint/format pass (20 files), mypy passes (15 source files), repository/whitespace checks pass.
  Actual feature replay on declared context matches uninterrupted causal replay. Only Windows/
  Python 3.12 executed; the previous symlink privilege skip remains.
- Independent review found no Critical/Important/Minor issues and verified source/schema tamper
  rejection and cross-partition support isolation. This does not imply human approval.
- Context carry permits preceding observations, not implicit detector checkpoint/state reuse.
  The consumer must declare enough effective history; bounds do not prove statistical independence.
- Exact evidence, schema obligations and continuation are in the
  [KS-03 handoff](../docs/HANDOFFS/KS-03_kaustubh_20261026T160340Z_splits.md).
- Next phase: KS-06 stress/integration and limitations report. KS-04/05 remain externally blocked.

### Current continuation status: all unblocked software phases reviewed

Date: 2026-10-26 (Asia/Kolkata). Earlier phase entries above are historical snapshots; this is
the latest continuation state. Active branch: `feat/kaustubh/KS-01-02-03-06-data-workstream`.

- KS-01/02/03/06 are implemented and verified, IN_REVIEW pending the named owners' review and
  integration. No peer approval, main merge, official benchmark or official-data audit is claimed.
- KS-06 implementation commit: `04b91e86be5c5fca377c1f3049c96969c9b81318`. Added
  `tests/data/test_stress.py` (22 cases) and [actual stress report](../docs/DATA_STRESS.md).
  No further production fix was necessary in this phase.
- Independent review after each phase completed. KS-02's two findings were fixed/rechecked;
  KS-03 and KS-06 have no findings. Final reviewer independently checked 167 passing owned data
  tests/1 skipped and a separate 112-target median/MAD oracle across both context policies.
  Agent review is not Ayush/Manas/Mayank approval.
- Final full pytest: **191 passed, 1 skipped** (192 collected; includes 24 foundation tests).
  Ruff lint/format pass (21 files), strict mypy passes (15 source files), pip check passes,
  repository checker and Git whitespace checks pass. Windows/Python 3.12.14 executed; the single
  symlink test requires unavailable Windows privilege. Linux/Python 3.11/3.13 remain unexecuted.
- Fresh CLI replay/evaluate passed in `outputs/kaustubh-data-final-smoke-001`: 16 synthetic points,
  8 ready/1 anomalous, provisional TP=1/FP=0/FN=0. Committed inventory/split source validation and
  CLI hash/count parity pass. These prove wiring only; no official score/runtime result exists.
- Known limits: fixed floors have units; contaminated warmup can define the reference; sample
  lag is not time-based seasonality after gaps; disjoint feature supports do not validate persistent
  detector state. All are documented and tested. Existing shared contracts and other-owner paths
  remain untouched; feature settings/new data schemas require normal consumer review.
- KS-04/05 remain BLOCKED. User confirmed intake path
  `C:\Users\HP\Desktop\EngimaxIota hackathon\data\official\` currently contains only README;
  no authorized download/Q01/Q09 answer exists. This path is absent on this host; local official/
  also contains only README. Need actual pack, permissions, prescribed splits and raw timestamp/
  cadence/missingness mapping; then KS-04 sample parity and KS-05 train-only EDA can proceed.
- All commits are **local only**, not pushed. Another machine cannot retrieve this work yet.
  [Final handoff](../docs/HANDOFFS/KS-06_kaustubh_20261026T161521Z_final-workstream.md) records
  exact commands/commits/restart steps; [prepared PR](../docs/data/KAUSTUBH_PR_SUMMARY.md) is ready
  for publication when authorized under ADR-09. Ayush updates central integration records after
  human review/merge. Next engineering task is KS-04 when its external inputs actually arrive.

### Latest publication status: shared PR and receiving-agent instructions

2026-10-26 (Asia/Kolkata). This supersedes all historical local-only publication statements above.
The user explicitly requested pushing the branch as a PR and documenting remaining work so a
friend with a fresh coding agent can continue. They also requested a copyable agent prompt.

- Published branch: `origin/feat/kaustubh/KS-01-02-03-06-data-workstream`.
- Open [PR #2](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/2) targets
  main. No merge or force push occurred. Shared initial snapshot:
  `955564571de61971ac270addf6cd560bc918c4da`; later documentation commits record publication.
- Fresh pre-publication checks: pytest 191 passed / 1 skipped; Ruff lint/format, strict mypy
  (15 source files), pip check, repository/PDF/link and Git whitespace checks pass. Check the PR's
  latest CI head for actual Ubuntu/Windows Python 3.11/3.13 results; local tests remain Python 3.12.
- KS-01/02/03/06 remain IN_REVIEW: publish/review does not imply owner approval or integration.
  Review the new manifests and feature settings, then coordinate wiring with existing Ayush,
  Manas and Mayank tasks/branches. Ayush alone updates central records after authorized merge.
- KS-04/05 remain BLOCKED for the confirmed missing official pack/permissions/Q01/Q09 answers;
  no synthetic/public dataset substitution or assumed raw timestamp convention is authorized.
- Original owner remains Kaustubh. Receiving developer identity is unspecified; confirm it before
  editing owned modules. User authorized sharing/continuation, not taking over active work of
  other named developers or bypassing shared-contract review/main-merge authorization.
- Start with the [publication handoff](../docs/HANDOFFS/KS-06_kaustubh_20261026T163753Z_publication.md)
  and [agent prompt](../docs/data/KAUSTUBH_AGENT_PROMPT.md), which contain exact retrieval/check
  commands, remaining tasks, owners, reasons, context policies, limits and next actions.

### Latest recovery and owned follow-up: 2026-10-27 (Asia/Calcutta)

This entry supersedes historical open/local-only statements above. User assigned both Kaustubh
and Ayush scopes and confirmed both, preserving other owners' boundaries. Active branch:
`fix/kaustubh/KS-06-integration-review`, from main `8c1be6f`. Implementation:
**05d2ee4ce733943baf46e36ee5bb40ef9aaa1594**; final records/PR carry publication.

- GitHub #2 is **merged** at `50f40009f4ddd757b5dfb7ac1c34e379d6801ac1`. Manas APPROVED on
  2026-10-26T18:45:23Z; Ayush/AJCoder01 APPROVED on 2026-10-27T08:40:00Z. Earlier COMMENTED agent
  review is distinct. No Mayank approval found/claimed. Actual main code/tests establish KS-01/
  02/03/06 implementation. DONE covers these original synthetic deliverables; new follow-up stays
  IN_REVIEW, and official data/later harness/config adoption are not included in completion.
- Inspected inventory/features/splits/stress implementation and #7 factory/config/support.
  #7 keeps data/typed contracts/base config unchanged and records W+C saturated calibrated
  lookback. Seasonal lag counts observations. Its split snapshot applies no target mask or
  permission validation; Mayank's MY-02 must enforce reviewed context/target/effective support.
- Fixed `src/sentinel/data/io.py`: strict quoting, csv.Error to contextual ContractError, valid
  quoted multiline fields preserved. Eight `tests/data/test_io_errors.py` cases cover reader,
  inventory and real CLI publication. Seven failed/one control passed before fix; all eight
  pass afterward. No dependency or shared schema change.
- Owned data/pipeline **189 passed / 1 skip**, full candidate **288 passed / 1 skip**; Ruff/mypy/pip/
  repository/whitespace checks and synthetic smoke passed. Exact main **266 passed / 1 skip**;
  exact #7 **609 passed / 1 skip**; archived #7 plus owned patch **631 passed / 1 skip** with full
  Python gates and default/short-quantile semantic parity. Skip is Windows symlink privilege.
  Independent agent review found no actionable defect; peer reviews remain required.
- Local data/official contains only README. Remote main/open PRs/issues/release assets supplied
  no pack or Q01/Q09 answers. No authorized download/participant-portal access was provided.
  KS-04/05 remain BLOCKED on actual organizer assets, development labels/access/permission,
  prescribed splits and timestamp/cadence/columns/missingness. No public NAB substitution,
  guessed timezone/cadence, real EDA, official parity or hidden evaluation is claimed.
- Explicit Ayush authorization covers central records and 14 pipeline/fallback cases. Detector/
  evaluator/frontend/other personal tasks remain untouched. AY-02 remains a proposal only.

Reviewers/next: Ayush manifest/order/CLI/envelope; Manas causal features/calibration/state; Mayank
split/leakage/target masks and complete artifacts. Retrieve the published PR head, rerun fresh
gates, review #7 without duplicating it, and merge only with authorization. Start KS-04 only after
missing inputs arrive; KS-05 follows authorized frozen training data. Exact commands/files,
blockers and restart instructions are in the
[new data handoff](../docs/HANDOFFS/KS-06_kaustubh_20261027T113928Z_data-integration-review.md).


### Concurrent-main preservation before publication

Main advanced to `3d18760e709c9ef4fe897d90d7dd0888c10bd046` with Mayank's separate demo/web
addition. Verified no Python/config/test/CI diff from the original audited main. Feature-only
merge `137cad38a6cb4a82971549649683a220f195abdc` preserves the upstream files unchanged;
no merge into main or other-owner edit. Refreshed exact-main archive: 266 passed / 1 Windows
symlink skip, Ruff 25 files, mypy 16, repository 139 links and README smoke TP/FP/FN=1/0/0.
Four exact-head CI jobs succeeded in run 40498576245. Initial archive pytest had 178 passed /
89 setup errors because the local harness omitted its outputs parent; created the parent and
reran successfully with fresh basetemp. Failed command is retained in compatibility evidence.
No viewer build/browser QA or comparison-result validity is claimed. Final feature candidate
is checked after this preservation/record update; PR identifies exact head and actual CI.


### Verified publication and coordination

Published [PR #8](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/8)
from `fix/kaustubh/KS-06-integration-review` to main. Initial published candidate
`22e86ab2b843bc50175ed48b74afa6e2fef8366d` passed all README gates on the exact committed tree:
288 passed / 1 Windows privilege skip, Ruff 27 files, strict mypy 16 files, pip/repository/
whitespace checks, synthetic 16-point replay/evaluate TP/FP/FN=1/0/0. Raw commands/results are
in `docs/validation/AY-03_20261027T113928Z/candidate-22e86ab-checks.json` (repository-relative).
All eight exact-head CI jobs succeeded: push run 40499158468 and PR run 40499214180.
This final publication record follows that candidate; final PR body identifies the later checked
head and actual latest CI instead of attributing earlier checks to a new commit.

[Scoped #7 review](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/7#pullrequestreview-5666596852)
was actually posted by kaustubh-dot at a52dd28, state COMMENTED, 2026-10-27T11:51:52Z.
It reports the inherited parser failures/fix and bounded feature/context compatibility; it is
not an APPROVE or Ayush/human approval. PR #8 actually requests AJCoder01 (Ayush), Manas-Jain-24
(Manas) and Kratos7heSpartanRage (Mayank); no submitted reviews were present at publication.
GitHub connector writes returned 403 Resource not accessible by integration; authenticated CLI
successfully performed the authorized PR/review/reviewer actions. No credential was exposed.

Exact sharing commands: `git push -u origin fix/kaustubh/KS-06-integration-review`,
`gh pr create --repo Manas-Jain-24/sentinel-adaptive-anomaly-detection --base main --head fix/kaustubh/KS-06-integration-review --title 'KS-06 / AY-03: harden CSV replay and reconcile verified integration' --body-file outputs/integration-review-pr-body.md`,
`gh api repos/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pulls/7/reviews --method POST --input outputs/pr7-review-payload.json`,
and `gh pr edit 8 --repo Manas-Jain-24/sentinel-adaptive-anomaly-detection --add-reviewer 'AJCoder01,Manas-Jain-24,Kratos7heSpartanRage'`.
All CLI publication actions exited 0. Body/payload files are local/ignored; actual content is
shared on GitHub. The branch/handoffs are portable after the final non-force push.

Next actions remain named-owner reviews, authorized integration, AY-02 proposal approval before
state API work, Mayank's MY-02 target-mask/harness implementation, and organizer asset/permission/
label/split/Q01/Q09/scorer/schema/runtime answers. KS-04/05 remain BLOCKED. No merge into main,
release, official parity, real EDA, benchmark/candidate promotion or submission was performed.
