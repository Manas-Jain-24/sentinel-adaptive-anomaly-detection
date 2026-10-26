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
| MN-02 | P0 / 3 | Implement residual detector with level/delta and optional seasonal components, fixed documented combination, direct component evidence | FeatureFrame contract; fake extractor now, KS-02 integration later | IN_REVIEW |
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

### Published MN-01 work, separate from this branch

MN-01 is implemented and locally verified on `feat/manas/MN-01-zscore`, published through
`8f6f6bf674cf0c8462da7fbecba9431bcb831a7b` in [draft PR #1](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/1).
It remains IN_REVIEW. Its implementation/tests/full progress record are on that branch; they
have not been merged into main or this independent MN-02 branch. Preserve both task records
when resolving the expected personal-file/package-description overlap during integration.

### MN-02 implementation and local verification — 2026-10-26 UTC

Branch: `feat/manas/MN-02-residual`, based on reviewed main `d7158d6`.
Status: **IN_REVIEW** — owned algorithm, synthetic acceptance and published-extractor
compatibility are verified; peer/integration review and merge remain pending.

- [ResidualDetector](../src/sentinel/detectors/residual.py) composes the unchanged FeatureExtractor
  contract: absolute level/current-delta/optional-seasonal residuals share an effective positive
  scale; a fixed maximum produces the score. It uses the existing threshold/floor and Prediction/
  Evidence fields. Seasonality defaults off and falls back to level/change when unavailable.
- [Method notes](../src/sentinel/detectors/RESIDUAL.md) explain units, readiness ownership,
  exact arithmetic evidence, per-series/reset lifecycle, error recovery and factory integration.
  Scores remain nonnegative magnitudes rather than probabilities. The maximum cannot veto
  a high level/change score simply because seasonality matches.
- FeatureExtractor.process may update internally before returning. Any feature/frame/scoring
  failure invalidates the wrapper until reset/replay; order/series checks happen before calling
  the extractor. No unreviewed rollback/checkpoint or structured Evidence fields were added.
- [69 deterministic-frame cases](../tests/detectors/test_residual.py) passed. The independent
  branch suite passed **93 tests, 1 skipped module** (KS-02 is unmerged). Loading Kaustubh's
  actual published feature module from commit `954bd1bc38b866617de3a011b6b22d6921238601`
  made all [13 compatibility cases](../tests/detectors/test_residual_features.py) execute:
  **106 tests passed, no skips**. Source SHA256 and exact scope are in the
  [verification artifact](../docs/validation/MN-02_manas_20261026T175539Z_verification.json).
  This is consumer compatibility testing, not approval or a merge of [PR #2](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/2).
- Actual configured checks passed: Ruff lint, Ruff format (**17 files**), strict mypy
  (**13 source files**). Foundation tests before changes: **24 passed**. Repository/whitespace
  checks and final sharing references are recorded in the task handoff after verification.
- README CLI replay/evaluation passed at local ignored `outputs/manas-MN-02-smoke-001`:
  MAD still ran 16 synthetic observations, 8 ready, 1 alert, provisional TP/FP/FN=1/0/0.
  A residual public-interface fixture test also passes; no official data/scoring claim is made.
- One synthetic 5,000-point, one-series runtime probe recorded p95 level/change=34.2 us and
  +seasonal=27.1 us at W=32, and 75.2/64.0 us at W=128. These one-trial measurements include
  the real extractor and have timing noise; they establish neither a seasonal speed benefit
  nor detection quality. No peak-memory, cold-start or official per-window benchmark ran.
- Remaining integration: Ayush owns model/config/factory selection and correct algorithm/run
  metadata. Keep the default MAD path accurately identified. Normal review must reconcile
  this task file with MN-01's longer record and the one-line package description. Central
  CURRENT_STATE/TASK_BOARD/INTEGRATION remain Ayush's responsibility after authorized integration.
- Next actionable task: **MN-03**, a bounded empirical threshold from preceding combined scores
  with explicit minimum-history fallback. Official model comparison remains blocked by assets.

Implementation commit: `8129bff278bd08853722bcb7dbab71293a769618`, pushed to
`origin/feat/manas/MN-02-residual`. The [MN-02 handoff](../docs/HANDOFFS/MN-02_manas_20261026T175901Z_residual-detector.md)
records the pinned real-extractor test command, diagnostic reproduction, integration limits
and exact continuation. Retrieve branch HEAD for the final documentation commit as well.
Draft review: [PR #3](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/3).

### PR #2 feature and consumer review (Manas scope)

Reviewed Kaustubh's published head `954bd1bc38b866617de3a011b6b22d6921238601` for causal
feature behavior and compatibility with MN-02. Inspected the diff, comments/reviews, CI and
data/method/handoff documents. Initial PR comments/reviews were empty; all four latest CI
matrix jobs passed for that exact head (Ubuntu/Windows, Python 3.11/3.13). The connected CI
tool was unavailable; authenticated GitHub REST supplied the actual check runs/annotations.
Maintenance annotations concern Actions runtime/image migration, owned by Ayush.

- Exact isolated PR snapshot: **191 passed, 1 Windows symlink-privilege skip**; Ruff lint,
  format (**21 files**), strict mypy (**15 source files**) and repository checks passed.
- Added **15** consumer cases in `tests/detectors/test_residual_partitions.py`: fresh reset/
  carry context reproduces target predictions; context stays outside metrics; insufficient
  declared lookback fails to reproduce full history even when ready=true; per-series indices
  work for interleaved CSVs; group state is separate; negative gain/floor changes, cadence
  gaps and real-extractor errors preserve the documented behavior.
- Added the manual dev utility `tests/detectors/check_published_data.py` to load all three
  exact data modules from a locally fetched commit and record source hashes/pytest results.
  The pinned combined consumer suite passed **121 tests, no skips**. The independent branch
  suite passed **93 tests, 2 optional-module skips**. Source lint/format (**19 files**) and
  configured strict mypy (**13 source files**) pass; runner+src type check passes **14 files**.
- An initial extra mypy invocation targeting only the runner could not resolve the editable
  package's type information; checking `src` and the runner together resolved it without
  modifying package/shared configuration. No production defect was reproduced or hidden.
- No blocking feature finding reproduced. This is an agent's scoped review for Manas, not
  a human approval, full split/config approval, or authorization to merge. Shared config,
  CLI/replay integration, fitting/state policy, target masks and exact metadata still need
  Ayush/Mayank review. KS-04/05 remain BLOCKED; official intake still contains only README.
- No Kaustubh-owned source/task file or Ayush-owned central record was edited. Review routing,
  evidence/handoff links and publication references are recorded after sharing below.
