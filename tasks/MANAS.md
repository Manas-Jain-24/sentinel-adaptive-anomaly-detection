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
| MN-03 | P0 / 2 | Implement bounded prior-score empirical quantile threshold with minimum-history fallback and causal calibration tests | Can start independent score-stream tests; integrate MN-02 later | IN_REVIEW |
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

### Earlier published tasks

MN-01 remains IN_REVIEW in [PR #1](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/1),
published through `8f6f6bf`. MN-02 remains IN_REVIEW in
[PR #3](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/3), published
through `2bdae80`. Their source/tests/full task records remain on those independent branches.
This MN-03 branch starts from reviewed main `d7158d6`; no unmerged module was copied into it.
Preserve all personal progress records and detector modules when integrating these branches.

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
