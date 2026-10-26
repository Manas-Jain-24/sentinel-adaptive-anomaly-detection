# Manas - causal anomaly detection and adaptation

Role: ML algorithm engineer. Own `src/sentinel/detectors/`, `tests/detectors/`, model configs
proposed through shared config review, and method/ablation notes. Inputs: Observation and
FeatureExtractor/FeatureFrame; output: Detector-compatible Prediction with arithmetic evidence.
Use [RESEARCH](../docs/RESEARCH.md), [INTERFACES](../docs/INTERFACES.md), and
[EXPERIMENT_PLAN](../docs/EXPERIMENT_PLAN.md). No experience level is assumed.

Status vocabulary: TODO, IN_PROGRESS, BLOCKED, IN_REVIEW, DONE. One effort unit ~= a focused
half-day including tests/review; real elapsed effort depends on findings.

| ID | Priority / effort | Task and explicit deliverable | Dependencies | Status |
|---|---|---|---|---|
| MN-01 | P0 / 2 | Add causal rolling mean/z baseline as an independent comparator; verify MAD starter against hand-derived data; document score orientation/floors | Existing Detector and synthetic fixtures | TODO |
| MN-02 | P0 / 3 | Implement residual detector with level/delta and optional seasonal components, fixed documented combination, direct component evidence | FeatureFrame contract; fake extractor now, KS-02 integration later | TODO |
| MN-03 | P0 / 2 | Implement bounded prior-score empirical quantile threshold with minimum-history fallback and causal calibration tests | Can start independent score-stream tests; integrate MN-02 later | TODO |
| MN-04 | P1 / 3 | Compare no guard/capped influence/finite quarantine and shadow drift; implement only validated update policy | MN-02/03, sustained-shift/fault tests, permitted data | TODO |
| MN-05 | P1 / 3 | Run component/calibration/guard ablations plus Chronos-2 and gated TimesFM-3 forecast-to-anomaly comparators through Mayank harness; select/freeze candidate | MY-02, KS-04, authorized labels/scorer; TimesFM license/runtime gate | BLOCKED |
| MN-06 | P2 / 1 initial spike | Prototype EVT tail calibration feasibility only after A/B gates; stop or separately estimate implementation | Level A valid, measured B; S1 gates | TODO |

**First three tasks:** MN-01, MN-02, MN-03. Start MN-01. MN-02 uses a deterministic
FeatureExtractor double to avoid waiting for KS-02. MN-03 accepts a prior score stream in tests;
the current score is compared before it enters calibration. Core+initial spike: 14 effort units.
MN-06's one unit is a feasibility decision, not the full three-unit stretch implementation.

## Algorithm and interface obligations

Preserve process/reset, per-series order, readiness, finite scores, and numerical evidence.
RollingMADStarter remains an unchanged runnable fallback unless a correctness fix is necessary.
New algorithm/config selection must be integrated with Ayush; do not repurpose starter threshold
as an empirical probability without changing the reviewed contract. No labels reach process().
Score components must be comparable and the **combined score** calibrated; maxing independent
scores does not preserve a nominal false-alarm rate. Seasonal predictions use an observed lag
and a training-prefix-selected period. No resetting based on ground truth or hindsight correction.
Do not label adaptation a root-cause explanation or claim theoretical novelty without evidence.

## Acceptance and test responsibilities

- MN-01: causal known-value z scores, degenerate variance floor, warmup/boundary/reset, prefix
  invariance, isolated and persistent shifts; all algorithm names/scores are unambiguous.
- MN-02: evidence reproduces level/change/seasonal scores; missing seasonal reference falls back
  safely; output remains deterministic and finite; fake/real extractor integration passes.
- MN-03: no use of current/future score in its threshold; quantile boundary/ties/short history,
  contamination and bounded buffer tests; empirically observed rate is not claimed as a guarantee.
- MN-04: sustained-fault recall and benign-drift alert storms compared; guard must not permanently
  freeze state; demonstrate rollback to no-guard policy if gains fail.
- MN-05: immutable configs/manifests, paired per-series results, false-positive/miss examples,
  runtime, no hidden labels/test tuning; compare against the simple baseline and promotion gates.
- MN-06: record tail sample sufficiency, fit/build/license issues and an explicit go/no-go; no
  mandatory dependency added for an inconclusive experiment.

Reviewers: Kaustubh for causal features, Mayank for scientific validity, Ayush for contracts/runtime.
Deliver tested detectors, config examples, method notes, and task-specific handoffs. Shared
interface changes follow proposal/approval; personal progress does not rewrite shared summaries.

## Handoff and local progress

No MN task is complete at initialization. The implemented MAD starter is not the final residual
ensemble, adaptive quantile system, or guarded drift policy. Record exact branch/commit, actual
tests, assumptions, failures/blockers, and next action in this file and a unique handoff.
Use [HANDOFF_PROTOCOL](../docs/HANDOFF_PROTOCOL.md); another machine cannot access local-only work.
