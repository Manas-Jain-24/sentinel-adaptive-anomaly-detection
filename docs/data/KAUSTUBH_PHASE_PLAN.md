# Kaustubh data workstream implementation plan

User authorization: continue phase by phase, review/fix each phase, complete assigned work.
This executes the existing architecture/task definitions; it does not redesign the system.

Goal: complete KS-02, KS-03 and KS-06 software deliverables, retaining KS-01 and truthful external
blockers for KS-04/05. Python >=3.11, stdlib only, existing FeatureExtractor/FeatureFrame unchanged.
Branch `feat/kaustubh/KS-01-02-03-06-data-workstream` retains the two existing KS-01 commits from
reviewed foundation main. INTEGRATION permits tightly coupled tasks on one branch when listed;
this branch explicitly contains KS-01, KS-02, KS-03 and KS-06, with separate phase commits.
Keep central summaries and other owners' code unchanged. Each software phase ends IN_REVIEW
pending the named human owners; agent reviews do not invent teammate approval or main merges.

## Phase 1: KS-02 causal features

Files: create src/sentinel/data/features.py, tests/data/test_features.py, docs/DATA_FEATURES.md;
update tasks/KAUSTUBH.md and create a unique KS-02 handoff.
Consumes Observation. Produces RollingFeatureExtractor.process(Observation) -> FeatureFrame,
reset() -> None, implementing the existing per-series protocol. Constructor-only implementation
settings: window_size=32, min_history=8, scale_floor=0.1, seasonal_period=None. No shared config
schema/CLI change; propose settings for Ayush/Manas review before adoption.

- [x] Write tests before implementation. Hand trace: prior [1,3] at current 9 gives level 2,
  expected_delta 2, current delta 6, scale 1.4826. Warmup expectations/scale are null. Use:
  `extractor = RollingFeatureExtractor(window_size=3, min_history=2, scale_floor=0.1)`.
- [x] Run `python -m pytest tests/data/test_features.py` and observe the absent-module failure.
- [x] Implement bounded prior-value median/MAD and median adjacent prior deltas. Compute the
  current delta from the last point; seasonal reference is value at lag P only when ready and
  P earlier points exist. P is explicit/train-selected and <= window_size; never estimate it from
  the full trace. Check finite outputs and chronology before changing state, normalize frame time
  to UTC, and reject a second series on the same instance. reset clears history/series identity.
- [x] Verify exact traces, floor, prefix invariance, changed-current expectations, reset, isolated
  instances, capped history, seasonal readiness/lag, malformed config and overflow recovery.
- [x] Run owned/full tests, Ruff lint/format, mypy, repository checker; request independent review,
  fix substantive findings and rerun affected checks. Record exact results and commit this phase.

## Phase 2: KS-03 frozen splits

Files: create src/sentinel/data/splits.py, tests/data/test_splits.py, docs/DATA_SPLITS.md and a
synthetic example; update personal tasks and create a unique KS-03 handoff. Consume KS-01's
InventoryManifest, not labels; new data-owned split format remains proposed for consumer review.
Produce build_group_split(inventory, assignments), build_chronological_split(inventory, cuts,
lookback, past_context), deterministic write/validate functions and split_digest.

- [x] Write hand-derived tests: group assignment must keep all related series in one partition;
  explicit complete group mapping is deterministic and requires train plus validation. No random
  split/seed is needed. Missing/extra groups, invalid partitions and overlapping examples fail.
- [x] For chronological splits use per-series exclusive cuts train_stop, calibration_stop. A
  target t uses support [t-lookback,t]. Reset policy keeps warmup inside each partition; carry
  policy explicitly reserves lookback previous points as context and purges preceding targets
  whose support could overlap the next partition's first example. With N=30, cuts 12/22, L=3,
  carry target ranges are [3,9), [12,19), [22,30); supports are disjoint between partitions.
- [x] Run failing tests, then implement strict cut/length/policy validation. Reject empty target
  ranges, noninteger/bool indices, incomplete series mappings, stale inventory linkage, unknown
  JSON fields/types, changed hashes/statistics or weakened purge/context metadata. Sort all
  mappings/ranges deterministically; encode source hashes and full inventory digest.
- [x] Test no shared feature-support observations across partition boundaries, group-held-out
  isolation, explicit context allowance, stable order/digest, no overwrite and source-backed
  validation. Keep source bytes read-only; no label-dependent boundaries or fitting.
- [x] Run checks and independent review; fix findings before documenting/committing this phase.

## Phase 3: KS-06 robustness and integration

Files: create tests/data/test_stress.py and docs/DATA_STRESS.md; create a unique KS-06 handoff
and update personal tasks. Add production fixes only for reproduced bugs in owned data modules.

- [x] Stress flat/short streams, missing spans, contaminated warmup, positive/negative rescaling,
  timestamp offsets, extreme finite values/overflow, long bounded streams, interleaved independent
  series and frozen split/feature context boundaries. Tests name observable failures, not mocks.
- [x] Establish expected invariants independently: positive affine transforms preserve median
  relationships when scale floor is inactive; contaminating future values cannot change prefix
  frames; missing spans are not imputed; lag is measured in observations, not wall-clock periods.
- [x] Record observed contamination/gap/scale-floor limits. Use synthetic robustness language;
  do not claim official F1, real-data generalization, or an invented speed/memory benchmark.
- [x] Run owned/full tests, lint/format/mypy/pip/repository checks and fresh CLI smoke. Request
  independent review, fix findings, record exact evidence and commit the phase and final handoff.

## External completion boundary

- [x] Recheck for actual official assets/permissions/Q01/Q09 answers. If absent, leave KS-04/05
  BLOCKED with precise required inputs, never substitute public NAB or synthetic EDA results.
- [x] Prepare final PR text with all phase commits, scope and review obligations. Leave publication
  local until authorized under ADR-09. Ayush reconciles central records after review/integration.
