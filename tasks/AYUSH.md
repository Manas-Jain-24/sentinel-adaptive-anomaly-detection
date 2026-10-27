# Ayush - streaming systems and final integration

Role: active systems engineer, technical coordinator, and final integration owner. No experience
level is assumed. Own `src/sentinel/pipeline.py`, `cli.py`, `config.py`, shared contracts,
`tests/pipeline/`, CI/build/setup, and shared integration summaries. Primary input is Observation
and Detector; output is deterministic predictions, reproducible manifests, and verified export.
Consult [INTERFACES](../docs/INTERFACES.md), [AGENTS](../AGENTS.md), and
[INTEGRATION](INTEGRATION.md). Existing foundation code is a starting point, not completion of
the task extensions below.

Status vocabulary: TODO, IN_PROGRESS, BLOCKED, IN_REVIEW, DONE. Statuses reflect verified work,
not intention. Effort: 1 unit ~= a focused half-day including tests/review; actual calendar unknown.

| ID | Priority / effort | Task and explicit deliverable | Dependencies | Status |
|---|---|---|---|---|
| AY-01 | P0 / 2 | Extend run manifests with revision/dirty state, environment/split/config hashes, and p50/p95/cold/end-to-end profiling; record workload | Published a859457, included in open #7; affected-owner review pending | IN_REVIEW |
| AY-02 | P1 / 3 | Propose reviewed state contract, implement versioned JSON checkpoints and compatible resume for baseline; full replay fallback | Proposal in this follow-up; implementation awaits recorded owner approval | BLOCKED |
| AY-03 | P0 / 2 | Add replay integration tests and clean error semantics for interleaving, early termination, atomic output, output collisions; integrate a test-double detector | Current Protocol; follow-up 05d2ee4 adds remaining cases without duplicating #7 | IN_REVIEW |
| AY-04 | P0 / 2 | Implement official prediction exporter/schema validator and execution adapter after Q06/Q10 | Organizer schema/runtime contract | BLOCKED |
| AY-05 | P0 / 2 | Review/merge authorized module PRs, run G1/G2 gates, reconcile summaries, clean-clone release reproduction | Audit/review in progress; main merge/release still requires authorization | IN_PROGRESS |
| AY-06 | P1 / 2 | Profile scaling/robustness and remove bottlenecks without changing semantics; export runtime report | AY-01; baseline/candidate integrated | TODO |

**First three tasks:** AY-01, AY-02, AY-03. Begin AY-01 now. AY-02 can start with a contract
proposal and corrupted-state golden tests; implementation waits for coordinated approval if the
shared schema changes. AY-03 is independently executable with the existing detector/test doubles.
Total planned core effort: 13 units, including integration obligations.

## Acceptance and test responsibilities

- AY-01: manifests identify actual source state and data/config; timing regions/units are explicit;
  prediction equality excludes runtime; no fictitious Git hash for dirty/uncommitted work.
- AY-02: uninterrupted and resumed results match numerically; wrong version/config/input cursor,
  nonfinite state, and duplicate timestamps reject safely. No unsafe pickle deserialization.
- AY-03: separate-stream vs interleaved outputs match; partial/error runs preserve prior files;
  nonzero CLI exit and actionable errors; no required evaluator/UI import in detector modules.
- AY-04: organizer-provided golden output roundtrips with exact ordering/dtypes/warmup semantics;
  internal JSONL must never be declared official merely because it serializes.
- AY-05: relevant suite and README smoke pass, official assets gaps stay explicit; team PRs include
  provenance and handoffs; summaries reflect merged code only.
- AY-06: hardware/window/cardinality/warmup and full timing distribution recorded; optimize only
  after profile evidence; unchanged numerical outputs and no suppressed errors.

Ayush reviews integration/system aspects of every module, with a second relevant owner reviewing
ML/data/evaluation semantics. Ayush-authored changes are reviewed by Kaustubh (data/state) or
Mayank (artifacts/evaluation); Manas reviews detector state semantics. Shared contracts/ADRs need
affected-owner coordination. Other developers report progress through their own files/handoffs.

## Handoff and local progress

No AY task is complete at initialization. INIT-01 supplies baseline orchestration but not AY-01's
full manifest/profile fields, AY-02 resume, or AY-04 exporter. Log actual task branch/commit,
tests/results, decisions/blockers, and next action below, then add a unique handoff using
[HANDOFF_PROTOCOL](../docs/HANDOFF_PROTOCOL.md). Only shared committed changes are portable.

Optional stretch: optimize state representation or add a schema-compatible batch reader only
after profiling shows benefit (within AY-06, no separate infrastructure project).

## Recovered integration continuation: 2026-10-27 (Asia/Calcutta)

User assigned Ayush integration plus Kaustubh data scope explicitly and confirmed both.
Branch `fix/kaustubh/KS-06-integration-review` starts at reviewed main `8c1be6f`.
Implementation **05d2ee4ce733943baf46e36ee5bb40ef9aaa1594**; final records/publication follow.
Earlier initialization/local-only statements are historical snapshots.

- Fetched every remote branch; existing KS branch pull --ff-only already up to date. Starting
  tree clean; no stash/reset/force push/branch deletion/main merge or other-owner implementation.
- All open PR heads/diffs/reviews/comments/CI inspected. #7 at `a52dd28` includes AY-01 `a859457`,
  residual/quantile/forecast history and shared CLI wiring. At recovery it had no owner reviews
  or approvals. Eight exact-head check-runs passed. Exact local suite **609 passed / 1 skip**;
  Ruff lint/format, mypy (23 source files), repository checker (199 links) passed. Not integrated.
- AY-03: `tests/pipeline/test_replay_contract.py` adds 14 cases: typed Protocol double and
  hand-derived interleaved scores/order, independent equivalence, no read-ahead on early close,
  source/cardinality errors, KeyboardInterrupt/RuntimeError/OSError after a partial replay,
  manifest-write failure, file/directory collisions, actionable missing-input CLI and real MAD
  full-replay fallback at warmup/saturated boundaries. No pipeline implementation was changed.
- Data-owned reader fix plus 8 regressions address inherited malformed-quote acceptance and
  escaping csv.Error. CLI exits 2 with path/approximate line and no staged/final partial output.
  Before fix seven cases failed and the valid quoting control passed; afterward all eight pass.
- AY-02: [proposal](../docs/HANDOFFS/AY-02_ayush_20261027T113440Z_checkpoint-proposal.md) evaluates
  optional parallel StatefulDetector and baseline-only state/cursor/prediction-prefix bundle.
  No new API/serialization/--resume implemented. Current reset/full-replay compatibility tested;
  corrupted-state/real-resume goldens not run because implementation awaits coordinated review.
- Pre-record candidate **288 passed / 1 skip**; owned data/pipeline **189 passed / 1 skip**; Ruff
  27 files, mypy 16 source files, pip/repository/whitespace checks and synthetic smoke passed.
  Independent agent review found no actionable defect and ran 22 focused tests plus 213 data/
  pipeline/foundation tests with 1 skip. Agent verification does not supply teammate approval.
- Disposable #7 archive plus only the three reader/test files: **631 passed / 1 skip**, Ruff
  50 files, mypy 23, repository 199 links, default/short-quantile smokes and semantic parity pass.
  This is a compatibility snapshot, not a merged commit. Quantile smoke is short/fallback only.
- Exact main audit **266 passed / 1 skip**, full Python gates/smoke; four exact-head CI jobs pass.
  Central records reflect only this verified main, with pending work clearly separated.

Required owners: Manas detector/state; Kaustubh input/features/cursor; Mayank masks/artifacts/
metric interpretation; Ayush shared APIs/publication. No approval invented. KS-04/05 and AY-04
remain BLOCKED on organizer assets/labels/permissions/partitions/time semantics/scorer/schema/
runtime answers. MY-02 remains Mayank's task. AY-06 follows measured workload evidence.
The [unique handoff](../docs/HANDOFFS/AY-03_ayush_20261027T113928Z_integration-review.md) records
commands/results, final publication/CI and exact continuation. Merge requires authorization.
