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
| MN-01 | P0 / 2 | Add causal rolling mean/z baseline as an independent comparator; verify MAD starter against hand-derived data; document score orientation/floors | Existing Detector and synthetic fixtures | DONE |
| MN-02 | P0 / 3 | Implement residual detector with level/delta and optional seasonal components, fixed documented combination, direct component evidence | FeatureFrame contract; fake extractor now, KS-02 integration later | IN_REVIEW |
| MN-03 | P0 / 2 | Implement bounded prior-score empirical quantile threshold with minimum-history fallback and causal calibration tests | Can start independent score-stream tests; integrate MN-02 later | IN_REVIEW |
| MN-04 | P1 / 3 | Compare no guard/capped influence/finite quarantine and shadow drift; implement only validated update policy | MN-02/03, sustained-shift/fault tests, permitted data | BLOCKED |
| MN-05 | P1 / 2 | Run component/calibration/guard ablations plus Chronos/TimesFM and optional IF comparators through Mayank harness; select/freeze candidate | MY-02, KS-04, official/local metric identity | BLOCKED |
| MN-06 | P2 / 1 initial spike | Prototype EVT tail calibration feasibility only after A/B gates; stop or separately estimate implementation | Level A valid, measured B; S1 gates | BLOCKED |

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

### MN-01 implementation and local verification â€” 2026-10-26 UTC

Branch: `feat/manas/MN-01-zscore`, based on reviewed foundation `main` at `d7158d6`.
Status: **IN_REVIEW** â€” implementation and local acceptance checks complete; peer/integration
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


### MN-02 implementation and local verification â€” 2026-10-26 UTC

Branch: `feat/manas/MN-02-residual`, based on reviewed main `d7158d6`.
Status: **IN_REVIEW** â€” owned algorithm, synthetic acceptance and published-extractor
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

Shared review/consumer commit: `a9bab6e6d40d3a5f9f74a684838f73d4bcc3b19b`, pushed on the
MN-02 branch. Posted the [scoped PR #2 review](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/2#pullrequestreview-5657147497)
as COMMENTED at the reviewed SHA. Requested Ayush (`AJCoder01`) and Mayank
(`Kratos7heSpartanRage`) after verifying collaborator accounts/public profile names.
Their approvals and main integration remain pending. See the
[PR-2 review handoff](../docs/HANDOFFS/MN-02_manas_20261026T183629Z_pr2-feature-review.md)
for exact commands, source/CI evidence, ownership and next actions. PR #3's description now
reflects the full residual/context-consumer scope and current test counts.

### Integration refresh — 2026-10-27 (Asia/Calcutta)

MN-01 and Kaustubh KS-01/02/03/06 are now merged in remote main at
`50f40009f4ddd757b5dfb7ac1c34e379d6801ac1`. The MN-01 record above is historical;
its review/merge requirement has been satisfied. PR #3 now includes that main history
and all MN-01 and MN-02 task records. MN-03 remains published in PR #4.
Only owned task prose and the package description needed merge-conflict reconciliation.
Central summaries still describe initialization and require Ayush reconciliation.

Refresh verification: 336 passed, 1 Windows symlink skip; Ruff, format (28 files),
strict mypy (17 source files), repository and whitespace checks passed.
See [refresh handoff](../docs/HANDOFFS/MN-02_manas_20261027T100220Z_merged-feature-integration.md) for commands and
the initial sandbox Temp setup errors resolved by repository-local `--basetemp`.


### MN-03 implementation and local verification

Branch: `feat/manas/MN-03-prior-quantile`. Status: **IN_REVIEW** — software acceptance and
published-detector compatibility are locally verified; normal review/integration remains pending.

- [PriorScoreQuantile and local config](../src/sentinel/detectors/thresholds.py) provide a
  bounded ready-score buffer, fixed minimum-history fallback, nearest-rank quantile from
  preceding scores, positive threshold floor, pure state queries and reset. Exact decimal
  rank arithmetic prevents boundary errors such as ceil(0.07*100) selecting rank 8.
- [CalibratedDetector](../src/sentinel/detectors/calibrated.py) wraps the unchanged Detector
  protocol, preserves raw scores/readiness/arithmetic evidence, and consistently replaces
  threshold/label using prior combined scores. Feature warmup is excluded from calibration;
  failures after a base call require reset/replay. Wrong sequence/series rejects before it.
- [Method notes](../src/sentinel/detectors/CALIBRATION.md) document all defaults, units,
  nearest-rank boundaries, fallback versus feature warmup, inclusive ties, contamination,
  lifecycle, proposed factory use, accurate algorithm metadata and composed context support.
- Actual unit/contract checks: **94 passed**. Independent full suite: **118 passed, 1 optional
  integration-module skip**. Loading exact published KS-02 features at `954bd1b` and MN-02
  residual source at `2bdae80` executed all four composition cases: **122 passed, no skips**.
  These verify the combined score, component preservation and W+C continuation (W=4/C=3),
  including a negative control showing W-only context does not reproduce calibration state.
- Final Ruff lint passed; format check passed **19 files**; strict mypy passed **14 source
  files**. A concurrent local Ruff cache-write warning did not fail formatting; a subsequent
  `ruff format --check --no-cache .` completed cleanly. Baseline before edits: **24 passed**.
- The existing MAD CLI replay/evaluation passed on the 16-point fixture at ignored local
  `outputs/manas-MN-03-smoke-001`, provisional TP/FP/FN=1/0/0. A separate calibrated fixture
  test with C=3/M=2/q=1/floor=0.01 yields **1/1/0** because a later normal score equals its
  threshold. One initial zero-FP assertion failed; inspection confirmed the shared inclusive
  comparison, and the regression was corrected to assert actual behavior. No rule/config
  was changed to conceal the extra flag. Neither result is an official benchmark.
- [Verification/runtime evidence](../docs/validation/MN-03_manas_20261026T190805Z_verification.json)
  records source hashes, dependency commits, scope and workload. In one synthetic 5,000-point
  trial, standalone threshold p95 was 3.5 us at C=64 / 10.9 us at C=256; wrapped MAD p95 was
  21.3 / 28.0 us versus bare MAD 6.6 us. These diagnostic regions/prefixes are explicit;
  no speedup, quality promotion, peak-memory or official runtime claim is made.
- Dataset clarification: the official PDF references a starter-pack NAB subset with hidden
  windows but supplies no link. The repository/official intake, supplied task attachment and
  matching Downloads entries did not contain the pack. The user's reply pasted its PDF
  description, not a download link or data files. Separate portal/group distribution remains
  unverified; do not state that organizers never distributed it. Actual data-dependent work
  still requires the starter pack, authorized labels/permissions, splits and Q01/Q09 answers.
- Integration: Ayush reviews local settings/factory/run metadata adoption; Mayank reviews
  context/target/fitting policy and threshold experiments. No shared schema/config, pipeline,
  data-owned implementation or central record changed. Existing default CLI remains MAD.
  No additional GitHub review comments are requested by this task.
- Next work: review/integrate MN-01/02/03 with accurate metadata. MN-04 guards remain gated
  on measured sustained-fault/drift comparisons and permitted data; no automatic guard or
  rebaseline was added. Real model/threshold selection stays blocked on genuine assets.

Implementation commit: `6480a0e0824428c34795c8863223c0a8d6cc4694`, pushed to
`origin/feat/manas/MN-03-prior-quantile`. See the [MN-03 handoff](../docs/HANDOFFS/MN-03_manas_20261026T191139Z_prior-score-quantile.md)
for actual commands, pinned composition/runtime reproduction, dataset clarification,
sharing state and exact integration/continuation steps.
Draft review: [PR #4](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/4).

### MN-03 composition refresh — 2026-10-27 (Asia/Calcutta)

PR #4 now contains the refreshed PR #3 as a review dependency. Historical standalone
counts above describe their original commits. MN-01 and KS-01/02/03/06 are merged
in main; MN-02 and MN-03 remain IN_REVIEW. Required composition tests now import
real features and residual code directly rather than skipping absent dependencies.
Merge/review PR #3 before PR #4. No default CLI/config/contract changes.

Composition verification: 434 passed, 1 Windows symlink skip; Ruff lint/format
(33 files), strict mypy (19 files), repository and whitespace checks passed.
See [composition refresh](../docs/HANDOFFS/MN-03_manas_20261027T100338Z_composition-refresh.md).

### Remaining-work implementation — 2026-10-27 (Asia/Calcutta)

User authorized completing all Manas work. This does not override prerequisite/ownership
rules. Current branch `feat/manas/MN-04-05-detector-readiness`, implementation `b88d38a77bd12bed704f7b68158985208406eae7`.

- MN-01 **DONE**: PR #1 merged. MN-02/03 **IN_REVIEW**, refreshed against merged main,
  preserving histories and all personal records. PR #3 refresh `891a853` passed 336 tests;
  PR #4 refresh `8907b47` passed 434; each had one Windows symlink skip.
- MN-04 **BLOCKED for real-data promotion**, synthetic comparison implemented/verified:
  no guard/capped/finite quarantine/shadow x fixed/adaptive x seven scenarios, 56 paired
  diagnostic runs. Causal/prefix tests, bounded exclusion, after-decision rebaseline and
  disable/reset/raw-replay rollback pass. Synthetic results show fault/drift trade-offs;
  no production guard was enabled. Explicit update-boundary coordination is still needed.
- MN-05 **BLOCKED for experiments/freeze**, forecast software implemented/verified:
  [interval wrapper](../src/sentinel/detectors/forecast.py) with model injection, past-only
  contexts, fresh/frozen forecasts, origin/age arithmetic evidence and calibration support.
  [Method notes](../src/sentinel/detectors/FORECAST.md) explain lifecycle and block-phase
  partition limits. Tests use deterministic fakes; actual Chronos/TimesFM adapters,
  libraries, weights, performance, GPU and model terms have not been evaluated.
- MN-06 **BLOCKED by A/B gates**: preliminary NO-GO recorded; actual synthetic tail/tie
  counts archived but real tail sufficiency unknown. No EVT fit/dependency/build/license
  claim. Reassess only after the documented gate, rather than marking the spike DONE.
- Final software checks: **504 passed, 1 Windows symlink-privilege skip**; 70 new focused
  cases passed; Ruff lint/format (37 files), strict mypy (20 source files), repository and
  whitespace checks passed. MAD README smoke remained 16 points, provisional 1/0/0.
- [Readiness/gates](../src/sentinel/detectors/READINESS.md),
  [portable synthetic evidence](../validation/MN-04-05_manas_20261027T101343Z_synthetic-readiness.json) and
  [continuation handoff](../docs/HANDOFFS/MN-04_manas_20261027T101343Z_detector-readiness.md) record exact commands,
  clean implementation revision, comparisons, limitations and next actions.
- Data permissions/official pack, label/split/time semantics, model-use permissions and
  MY-02 harness still block genuine ablations/selection. Public NAB download is local,
  raw, reference-only. Default CLI remains MAD. No central or teammate-owned file changed.
- Publish these branches for review in order PR #3 -> #4 -> detector readiness. Ayush
  owns main integration and stale shared-summary reconciliation. No peer approvals or
  main merge are implied by this progress. See final PR body for publication state.
