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
| MN-01 | P0 / 2 | Add causal rolling mean/z baseline as an independent comparator; verify MAD starter against hand-derived data; document score orientation/floors | Existing Detector and synthetic fixtures | IN_REVIEW |
| MN-02 | P0 / 3 | Implement residual detector with level/delta and optional seasonal components, fixed documented combination, direct component evidence | FeatureFrame contract; fake extractor now, KS-02 integration later | TODO |
| MN-03 | P0 / 2 | Implement bounded prior-score empirical quantile threshold with minimum-history fallback and causal calibration tests | Can start independent score-stream tests; integrate MN-02 later | TODO |
| MN-04 | P1 / 3 | Compare no guard/capped influence/finite quarantine and shadow drift; implement only validated update policy | MN-02/03, sustained-shift/fault tests, permitted data | TODO |
| MN-05 | P1 / 2 | Run component/calibration/guard ablations and optional IF comparator through Mayank harness; select/freeze candidate | MY-02, KS-04, official/local metric identity | BLOCKED |
| MN-06 | P2 / 1 initial spike | Prototype EVT tail calibration feasibility only after A/B gates; stop or separately estimate implementation | Level A valid, measured B; S1 gates | TODO |

**First three tasks:** MN-01, MN-02, MN-03. Start MN-01. MN-02 uses a deterministic
FeatureExtractor double to avoid waiting for KS-02. MN-03 accepts a prior score stream in tests;
the current score is compared before it enters calibration. Core+initial spike: 13 effort units.
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

### MN-01 implementation and local verification — 2026-10-26 UTC

Branch: `feat/manas/MN-01-zscore`, based on reviewed foundation `main` at `d7158d6`.
Status: **IN_REVIEW** — implementation and local acceptance checks complete; peer/integration
review and merge remain pending. Central integration summaries have not been changed.

- Added `RollingZScoreDetector` in `src/sentinel/detectors/zscore.py`, using preceding-window
  arithmetic mean and population standard deviation, a positive scale floor, absolute score,
  inclusive threshold, numerical evidence, bounded history, UTC output, and reset/error recovery.
- Added 48 owned cases in `tests/detectors/test_baselines.py`, including hand-derived odd/even/
  contaminated-history MAD references. The MAD algorithm and shared interfaces are unchanged.
- [Method notes](../src/sentinel/detectors/README.md) specify equations, score units, floors,
  readiness, update policy, limitations, and the existing programmatic factory integration.
- Actual commands with `.venv/Scripts/python.exe`: `-m pytest tests/test_foundation.py -q`
  before implementation: **24 passed**; `-m pytest tests/detectors -q`: **48 passed**;
  `-m pytest -q`: **72 passed**; `-m ruff check .`: passed; `-m ruff format --check .`:
  **16 files formatted**; `-m mypy`: **13 source files passed**; repository checker: passed.
  `git diff --check` passed. Exact commands and handoff reference follow in the task handoff.
- README CLI replay/evaluation passed at `outputs/manas-MN-01-smoke-001` (local, ignored).
  It still runs MAD: 16 synthetic points, one artificial event, provisional TP/FP/FN=1/0/0.
  A separate owned integration test proves z predictions work with the shared reader, replay,
  serializer, and provisional evaluator. Neither check is an official benchmark.
- [Synthetic runtime diagnostic](../docs/validation/MN-01_manas_20261026T161915Z_runtime.json):
  Python 3.13.5/Windows 11, one series/5,000 generated points, one trial, process-only timing
  after a full-window warmup. At W=32 z p95=90.6 microseconds versus MAD=12.0; at W=128 z
  p95=235.2 microseconds versus MAD=22.8. Standard-library stable statistics have higher
  overhead here; no speedup, memory bound measurement, or detection-quality improvement is claimed.
- Remaining integration: Ayush reviews optional CLI/config/factory selection and correct
  algorithm metadata before any persisted run is described as a z run. No shared schema or
  config extension was made. Ayush updates central records after integration; domain peers
  review score semantics. Official data/scorer are unnecessary for MN-01 software acceptance
  but still block genuine performance selection under MN-05.
- Next actionable task: **MN-02**, using a deterministic `FeatureExtractor` double until KS-02
  is available. MN-03 remains a separate causal prior-score calibration task.

Implementation commit: `5e28d5c4b9fd6b6f4517f1b18d97088cf7b47a49`, pushed to
`origin/feat/manas/MN-01-zscore`. See the [MN-01 handoff](../docs/HANDOFFS/MN-01_manas_20261026T162226Z_rolling-zscore.md)
for exact commands, runtime reproduction, sharing state, reviewer obligations, and continuation.
Draft review: [PR #1](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/1).


### Demo-readiness and presentation support — 2026-10-27

Status: **IN_REVIEW**. This is a user-requested cross-owner demo/presentation contribution; it does
not complete or change MN-05 and does not select a final detector. Original UI/presentation owner:
Mayank. Official-data work remains blocked until organizer assets and answers arrive.

- Rebuilt the bundled Mission Control run from `frontend/web/public/demo/stream.csv` using the
  checked-in CLI and starter config. The saved run and evaluation now agree on the 120-point input,
  predictions, and two synthetic event windows. All example data are explicitly synthetic smoke.
- Removed the unsupported planned/winner comparison rows; comparison state is empty until actual
  compatible run results are loaded. Overview values no longer fall back to invented F1, P95,
  throughput, or latency. The hero trace is drawn from saved detector predictions, not random flags.
- Predictions SHA verification now hashes original JSONL text instead of reserializing parsed
  numbers, which could change numeric formatting and produce a false mismatch.
- Added a reproducible synthetic-artifact refresh script and local UI instructions. Root README now
  links to the demo and deck. Created an editable 10-slide Challenge 2 deck with the supplied rubric,
  real demo evidence, and explicit official-data blockers. The pre-existing untracked draft deck was
  not modified or included.
- Verification: `scripts/build_demo_artifacts.py` completed; `.venv\Scripts\python.exe -m pytest -q`
  passed **266**, skipped **1** Windows symlink-privilege case; Vite production build completed with
  2,376 modules transformed. Ruff check and format passed for `src`, `tests`, and the demo builder;
  mypy passed for 16 source files; repository checker passed. Whole-repo Ruff also scans a separate,
  pre-existing untracked `scripts/generate_presentation.py` draft and fails on its unsupported claims
  and formatting; that file is not included in the PR. The finalizer validated 10 slides, one native
  table, package integrity, layout, fonts, and re-import. Browser access to the local UI was unavailable
  from the browser sandbox; do not describe that as a browser QA pass.
- Current main baseline is `4a46101`. Implementation commit: `a342650c1112a0e0eaf8694bb5609d2fd216ede5`.
  Pushed to `origin/codex/demo-readiness`; PR [#10](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/10)
  is open and not merged. See the uniquely named demo-readiness handoff for exact blockers and next steps.
