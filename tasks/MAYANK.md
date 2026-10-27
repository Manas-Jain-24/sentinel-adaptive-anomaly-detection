# Mayank - evaluation, experiment tooling, and evidence visualization

Role: evaluation/tooling engineer with substantial implementation ownership. Own
`src/sentinel/evaluation/`, `tests/evaluation/`, future `experiments/`, future `demo/`, and
their tests. Inputs: immutable prediction/run artifacts, permitted separate truth/split manifests;
outputs: validated metric reports, experiment comparisons, and artifact-based visualization.
Read [EVALUATION](../docs/EVALUATION.md), [DEMO_PLAN](../docs/DEMO_PLAN.md), and contracts.

Status vocabulary: TODO, IN_PROGRESS, BLOCKED, IN_REVIEW, DONE. One effort unit ~= a focused
half-day including verification; no experience level or hackathon deadline is assumed.

| ID | Priority / effort | Task and explicit deliverable | Dependencies | Status |
|---|---|---|---|---|
| MY-01 | P0 / 2 | Expand event golden tests: boundaries, repeated episodes, warmup, no-event series, gaps, interleaving, micro/macro; state policy in reports | Existing provisional evaluator and fixtures | DONE |
| MY-02 | P0 / 3 | Build config/split-driven experiment harness and immutable result index; compare baseline/candidates with reproducibility metadata and error slices | Current artifact schema; use real runner/test double now | TODO |
| MY-03 | P1 / 3 | Implement offline artifact viewer with trace/flags/score/threshold/evidence/provenance/runtime and graceful missing-data behavior | Saved starter run exists; no final model needed | DONE |
| MY-04 | P0 / 2 | Integrate actual organizer scorer, prove parity on golden examples, document event/warmup/aggregation semantics | Official scorer and Q02-Q05 answers | BLOCKED |
| MY-05 | P0 / 2 | Produce exact 10-slide deck and live/video evidence; trace all figures to runs, rehearse failure fallback | Real results and integrated core; team provides method/data content | TODO |
| MY-06 | P1 / 1 | Freeze final evaluation/error-analysis report with per-series counts, delays, uncertainty limits, and submission hashes | MY-02/04, KS-04, frozen model/export | BLOCKED |

**First three tasks:** MY-01, MY-02, MY-03. All start with existing saved-format contracts,
fixtures, and test doubles. MY-02 may run the current rolling starter instead of waiting for
MN-02. MY-03 is an actual visualization engineering task; presentation coordination is additional.
Total core effort: 13 units.

## Acceptance and test responsibilities

- MY-01: independently calculated TP/FP/FN and delay cases, no hindsight point adjustment,
  explicit zero-event policy and warmup coverage; reject malformed/coverage-incompatible artifacts.
- MY-02: reproducible result directories/index, failures logged without fake metrics, config/
  split/code/environment identity, paired candidate comparisons; never retune on untouched data.
- MY-03: every screen names dataset/scope/metric; clicking a flag shows actual evidence; missing
  labels show unlabeled state, not zero errors; core tests/CLI run without viewer dependencies.
- MY-04: official counts/metrics agree on supplied examples; keep provisional v0 under its old
  name; exact official semantics and scorer version documented, no guessed equivalence to NAB.
- MY-05: exactly 10 official slides, real or clearly synthetic examples, one false-positive/miss
  analysis, recorded runtime context, offline CLI/video fallback. No fabricated hidden results.
- MY-06: trace tables to shared commit/config/data/output hashes; report misses with hit delay;
  separate official, development, and synthetic findings; disclose sparse-event uncertainty.

Reviewers: Ayush for artifact/tool integration, Manas for score interpretation/ablation validity,
Kaustubh for split integrity. Do not change another developer's detector to make a report prettier.
Official evaluator changes and schema extensions follow coordinated contract review.

## Handoff and local progress

- **2026-10-26 (MY-01 DONE)**: Branch `feat/mayank/MY-01-event-cases`.
  - Implemented expanded evaluation metrics in `src/sentinel/evaluation/reference.py`:
    - Added delay distributions: `median_delay_seconds`, `p95_delay_seconds`, `min_delay_seconds`, `max_delay_seconds`.
    - Added `missed_events` count alongside delay reporting.
    - Added per-series metric tracking (`per_series` dictionary with series-level TP, FP, FN, precision, recall, F1, observations, warmup, and delays).
    - Added macro metrics: `macro_precision`, `macro_recall`, `macro_event_f1` averaged across all series present in predictions.
    - Added explicit `policy` metadata block stating the conservative matching rules, pre-window trigger policy, repeat trigger handling, zero-denominator convention, and warmup tracking.
    - Added `format_evaluation_report()` helper function producing clean, human-readable markdown summary reports.
  - Created comprehensive golden test suite in `tests/evaluation/test_golden_events.py` (27 golden test cases).
  - Verified 51/51 pytest tests pass and `python scripts/check_repository.py` passes.
  - Handoff file: [MY-01 handoff](../docs/HANDOFFS/MY-01_mayank_20261026T225700Z_event-golden-tests.md).

- **2026-10-27 (MY-03 DONE)**: Branch `feat/mayank/MY-01-event-cases`.
  - Built React 19 + Vite frontend in `frontend/web/` following "Regal Watchtower" design direction:
    - Midnight (#070B14) dark mode and Parchment (#F6F1E4) light mode with antique gold (#C9A24B) accent and muted crimson (#B3363E) exclusively for anomalies.
    - 3-layer parallax drifting constellation background canvas reacting to mouse and scroll at 60fps.
    - Animated ECG radar-sweep hero pulse line that flares crimson when anomalies are triggered.
    - Causal streaming chart with pre-update rolling median ± 4.0 MAD envelope, hatched warmup region, live heads-up display, and play/pause/step/scrubber/speed controls.
    - Slide-out numeric evidence drawer displaying baseline, scale, residual, threshold, latency, and plain-language reasoning.
    - Event evaluation dual-lane timeline strip aligning ground truth with triggers, and automated `provisional_event_trigger_f1_v0` metrics.
    - Level B experiment harness preview table and gate criteria.
    - Run manifest inspector with one-click cryptographic SHA-256 copying and toast alerts.
    - Team attribution cards with module ownership and Challenge 2 context.
    - Persistent scope badge (`synthetic_smoke`) and required honesty disclosure.
    - Zero backend dependencies; bundled synthetic run + client-side file picker/dropzone.
  - Verified clean production build with `npm run build` (0 errors).
