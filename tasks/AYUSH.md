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
| AY-01 | P0 / 2 | Extend run manifests with revision/dirty state, environment/split/config hashes, and p50/p95/cold/end-to-end profiling; record workload | Foundation contracts; works with synthetic replay | IN_REVIEW |
| AY-02 | P1 / 3 | Propose reviewed state contract, implement versioned JSON checkpoints and compatible resume for baseline; full replay fallback | Current Detector; coordinate extension before edits | TODO |
| AY-03 | P0 / 2 | Add replay integration tests and clean error semantics for interleaving, early termination, atomic output, output collisions; integrate a test-double detector | Current Protocol; no final model needed | TODO |
| AY-04 | P0 / 2 | Implement official prediction exporter/schema validator and execution adapter after Q06/Q10 | Organizer schema/runtime contract | BLOCKED |
| AY-05 | P0 / 2 | Review/merge authorized module PRs, run G1/G2 gates, reconcile summaries, clean-clone release reproduction | Module handoffs; human authorization for main merge | TODO |
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

No AY task was complete at initialization. INIT-01 supplies baseline orchestration but not AY-01's
full manifest/profile fields, AY-02 resume, or AY-04 exporter. Log actual task branch/commit,
tests/results, decisions/blockers, and next action below, then add a unique handoff using
[HANDOFF_PROTOCOL](../docs/HANDOFF_PROTOCOL.md). Only shared committed changes are portable.

Optional stretch: optimize state representation or add a schema-compatible batch reader only
after profiling shows benefit (within AY-06, no separate infrastructure project).

### AY-01 — implementation verified, awaiting peer review (2026-10-26)

- Branch: `feat/ayush/AY-01-run-provenance-profiling`, based on inspected shared `main`
  `d7158d62eb8fa4e4c5d4907238d03c5989967083`; local main was initially one documentation commit behind.
  The published remote exists; the newer publication record resolves the stale local notes.
- Implemented: additive provenance/profiling/workload metadata; actual Git HEAD/dirty or explicit
  unknown; canonical config/environment/dependency hashes with full environment snapshot;
  optional exact-byte split snapshot/checksum; per-series coverage/counts and hardware;
  bounded timing histograms with explicit p50/p95 upper bounds (<1/128 relative overestimate),
  learning-warmup/ready/cold/subsequent-call populations and defined replay/prepublication regions.
  Detected input mutation aborts publication. No detector/evaluator/config/prediction semantics changed.
- Files: `src/sentinel/pipeline.py`, `cli.py`, new `profiling.py`/`provenance.py`, three test modules
  under `tests/pipeline/`, README, INTERFACES, proposal and verification evidence.
- Verified: `.venv/bin/python -m pytest` **43 passed** (24 existing + 19 new); Ruff lint/format,
  strict mypy (14 source files), repository checker, pip check, CLI help all exited 0.
  README replay/evaluate commands and optional split CLI path exited 0. All 16 semantic prediction
  rows match the pre-change baseline after excluding elapsed_ns. Artificial-event counts TP=1,
  FP=FN=0 are provisional wiring evidence only; no official benchmark was evaluated.
  [Raw commands/results and artifacts](../docs/validation/AY-01_20261026T150504Z/README.md).
- Contract review: [additive proposal](../docs/HANDOFFS/AY-01_ayush_20261026T145042Z_manifest-proposal.md).
  Mayank reviews artifacts and timing semantics; Kaustubh reviews checksum-only split provenance.
  No peer approval/PR/CI execution or main integration is claimed. Shared summaries remain unchanged.
- Limitations: approximate quantiles are explicitly labeled; cold excludes construction/imports;
  final manifest write/rename is outside measured regions; split membership and peak memory are
  not validated/measured. Official assets/schema/scorer remain unavailable. AY-06 owns larger
  workload/robustness profiling; these tiny synthetic timings are not a performance benchmark.
- Remaining: share the task branch, obtain affected-owner review, rerun gates after any changes,
  then integrate only with authorization. Next engineering task is AY-02's state-contract proposal;
  checkpoint implementation requires coordination. AY-03 remains independently executable.
