# AY-01 — run provenance and bounded profiling

- Developer/original owner: Ayush.
- Authored: 2026-10-26 15:45:12 UTC (21:15:12 Asia/Kolkata).
- Status: IN_REVIEW; implementation and local verification complete, peer review pending.
- Branch: `feat/ayush/AY-01-run-provenance-profiling`.
- Implementation commit: `07f17ed13787101f37422bf5260045d16002f2dd`.
- Base: inspected `origin/main` at `d7158d62eb8fa4e4c5d4907238d03c5989967083`.
- Sharing: **local-only commit**, not pushed. No PR, peer approval, CI success or main merge
  is claimed. Another machine cannot retrieve this implementation until the branch is shared.
- Objective: make replay artifacts identify actual source/config/environment/split and measured
  timing populations/workload while preserving existing numerical predictions and contracts.

## Implementation and decisions

- `src/sentinel/provenance.py`: canonical config/environment/dependency JSON hashes, installed
  distribution snapshot and hardware facts, tracked package source HEAD/dirty state independent
  of caller CWD. Unavailable Git/untracked installations report null revision/dirty and reason.
- `src/sentinel/profiling.py`: incremental timing histograms and per-series workload accounting.
  Exact counts/min/max/totals; nearest-rank p50/p95 upper bounds with relative overestimate
  <1/128, exact below 256 ns. Storage grows with series count and duration magnitude, not points.
- `src/sentinel/pipeline.py`: additive `provenance`, `profiling`, `workload` objects in v1 run.json;
  explicit process/ready/learning-warmup/first-call/subsequent-call timings and replay/prepublication
  wall regions. Optional split bytes are snapshotted and hashed, never parsed or fed to inference.
  Detected input-byte changes between pre/post hashes abort unpublished output.
- `src/sentinel/cli.py`: optional `--split-manifest PATH`, without changing existing commands.
- `tests/pipeline/`: 19 new cases for independent quantile bounds, bounded storage, provenance
  and unavailable Git, isolated nested checkout identity, config/environment hashes, split-byte
  preservation, timing populations, interleaved workloads, mutation cleanup and CLI errors.
- README and INTERFACES describe implemented fields/limits. `tasks/AYUSH.md` records actual work.
  [Proposal](AY-01_ayush_20261026T145042Z_manifest-proposal.md) records compatibility, affected
  owners and review plan. [Validation record](../validation/AY-01_20261026T150504Z/README.md)
  preserves commands, raw outputs, baseline/new predictions, manifest, split bytes and metrics.

No new dependencies, detector changes, evaluator changes, config changes, labels in inference,
official format assumptions or breaking interfaces. Other developers' modules/tasks are untouched.
The user identified as Ayush and requested implementation of his next assigned task. This is
implementation authorization, not fabricated affected-owner approval. Additive fields still need
review before integration. Shared integration summaries remain at the integrated foundation state.

## Actual verification

All commands below ran successfully using macOS arm64/Python 3.12.14 and the existing pinned dev
requirements. Baseline: 24 existing tests passed before editing. Final suite: **43 passed**
(24 existing + 19 new). See the validation record for command output and smoke commands.

```text
.venv/bin/python -m pytest tests/pipeline -q
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy
.venv/bin/python scripts/check_repository.py
.venv/bin/python -m pip check
.venv/bin/python -m sentinel run --help
git diff --check
git diff --cached --check
.venv/bin/python -m sentinel evaluate --run-dir docs/validation/AY-01_20261026T150504Z --windows tests/fixtures/synthetic_windows.json
```

Each command exited 0. Mypy checked 14 source files; Ruff formatting checked 19 Python files.
README synthetic replay/evaluation plus the optional split replay/evaluation exited 0. An actual
independent JSON comparison found all 16 prediction rows equal the pre-change baseline after
removing elapsed_ns for both paths. Provisional counts TP=1, FP=FN=0 (F1=1.0) show fixture wiring
only. No official benchmark, hidden evaluation, development-data experiment or performance claim.

The preserved sample records committed base `d7158d6...` plus dirty=true, collected before the
implementation commit. After commit, this additional CLI run exited 0:

```text
.venv/bin/python -m sentinel run --input tests/fixtures/synthetic_stream.csv --config configs/starter.json --output-dir outputs/ay01-validation-20261026T145042Z/committed-replay --dataset-id synthetic-fixture-v1 --scope synthetic_smoke
```

Its source state was asserted to be revision `07f17ed13787101f37422bf5260045d16002f2dd`, dirty=false.
That post-commit smoke output remains local/ignored under outputs. Subsequent handoff documentation
changes do not retroactively change its recorded source state. Raw preserved artifacts identify
their own execution state accurately. No clean-source or uncommitted-source substitution was made.

Initial restricted-network setup/fetch attempts failed, then permitted retries installed the
existing pins and fetched the newer documentation-only main. Initial Ruff long-line errors were
fixed before final verification. No outstanding local check failures. Windows/Linux/remote CI,
large-workload performance/peak-memory measurements and affected-owner review were not run.

## Remaining work, limitations and dependencies

- Mayank reviews artifact compatibility and measured regions; Kaustubh reviews split provenance.
  No checkpoint interface is introduced, so detector-owner coordination is unchanged for AY-02.
- Quantiles are documented upper estimates. Cold covers first process() per series, excluding
  construction/imports. Final run.json write/rename and CLI startup lie outside measured wall
  regions. Full process memory and benchmark scaling belong to AY-06.
- Split provenance is opaque/checksum-only; no frozen split membership/schema is certified.
  KS-03 integration should reuse its eventual reviewed schema rather than silently extending this.
- Input pre/post hashing detects ordinary mutation but provides no locking/snapshot isolation.
  Use immutable input assets. Whole-file replay remains the recovery fallback.
- Official dataset/scorer/submission schema, organizer matching/warmup/runtime rules remain
  unavailable. They block official evaluation/export, not AY-01 software verification.
- No implementation remains for AY-01 unless peer review requests changes. Mark DONE only after
  normal review/integration. Ayush updates central state/board/integration after authorized merge.

## Exact next actions

1. Review `git status`, the implementation commit, this handoff and the preserved evidence.
2. When sharing is authorized, push the local branch:
   `git push -u origin feat/ayush/AY-01-run-provenance-profiling`.
3. Open a PR to main using the summary below; request Mayank's artifact review and Kaustubh's
   split-provenance review. Attach the resulting PR to the Codex chat. No PR URL exists yet.
4. Resolve actual review feedback, run relevant tests plus all README gates and smoke on a new
   output directory, then merge only with authorization. Reconcile central summaries afterward.
5. Next engineering task: AY-02 state-contract proposal with affected-owner review before
   checkpoint implementation. AY-03 remains independently executable with the current Protocol.

## Prepared PR summary

**Title:** AY-01: record reproducible run provenance and bounded replay timing distributions

Run artifacts previously omitted source state, config/environment/split identity and timing
distributions. Add Git HEAD/dirty evidence, canonical hashes and an optional preserved split file,
plus bounded timing histograms, explicit cold/ready/warmup regions and workload details. Preserve
all existing prediction/evaluator semantics and reject detected input mutation before publication.

Validation: 43 tests passed; Ruff lint/format, strict mypy, repository/dependency checks, CLI help
and default/optional-split synthetic replay/evaluation passed. All 16 semantic predictions match
the pre-change baseline excluding elapsed_ns. Provisional synthetic counts only; no official score.

Contracts/review: additive v1 metadata and keyword-only optional split path. Mayank/Kaustubh review
required; approximate quantiles, measured-region exclusions and opaque split limitations are
documented. Link this handoff and the manifest proposal. No main merge or official-data claim.
