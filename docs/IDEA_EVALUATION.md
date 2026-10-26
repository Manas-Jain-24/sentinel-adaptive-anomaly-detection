# Competing concepts and selection

All ratings are **design estimates**, not measured F1, latency, memory, or competition outcomes.
Suitability is conditional on the unseen organizer subset. The research rationale is in
[RESEARCH](RESEARCH.md); official rubric is in [PROBLEM_ANALYSIS](PROBLEM_ANALYSIS.md).

## Six distinct concepts

| Concept | Core/adaptation | Strength and innovation | Suitability / explanation | Runtime and memory estimate | Complexity / research risk / generalization | Demo and four-person feasibility |
|---|---|---|---|---|---|---|
| C1 Robust statistics | Rolling median/MAD; local window follows baseline | Strong simple fallback; limited differentiation | Spikes/level deviations; direct baseline/scale evidence; weak periodic context | Starter O(W log W) per point, O(SW) state | Low effort/risk; drifts contaminate window; scale-sensitive floor | Very clear demo, easy parallel plumbing/eval work |
| C2 Feature isolation forest | Fit IF on causal lag/change/window features, periodically refit on permitted past data | Nonlinear feature interactions | May capture variance/context anomalies; feature deviation explanations are approximate | Fit roughly O(Trees*n*log n); per point O(Trees*depth + features); bounded training reservoir required | Medium effort; refit contamination and transfer risk | Good score/feature view; four people feasible with adapter/tests |
| C3 Causal shape discord | Past-only matrix profile or bounded nearest-subsequence distances | Shape departures, nearest-normal examples | Motif-rich series; absolute-level information can disappear under normalization | Reference horizon H drives cost; naive O(Hm) per update, O(H) state; optimized library must be profiled | Medium/high effort; motif length and history selection fragile | Compelling matched-shape demo; feasible as comparator, risky default |
| C4 Small temporal autoencoder | Train causal trailing-window reconstruction model; recalibrate residuals | Flexible nonlinear reconstruction | Sufficient clean development data needed; residual evidence less direct | Train/forward depend on window/channels; model plus O(W) buffer; CPU cost unmeasured | High effort/risk; contamination, few events, reconstruction shortcuts | Attractive visualization; four-person integration possible but research cost high |
| C5 Forecast plus EVT | Causal seasonal/robust prediction, SPOT/DSPOT tail calibration | Tail-based alarm thresholds, natural residual explanations | Residual tails need enough observations and fit stability | Bounded residual buffer plus tail fit; refit cost variable | Medium/high risk on short/dependent/shifted series | Good residual/tail story; feasible after empirical baseline |
| C6 Guarded residual ensemble | Level/change/optional seasonal residuals; calibrate combined score on prior data; shadow adaptation | Coherent differentiation in contamination control and causal evidence | Covers multiple anomaly types; every branch numerically explainable | Target bounded O(S(W+H)); exact window statistics O(W log W); no GPU | Medium effort/risk; selection bias, overadaptation, ensemble false positives require ablation | Strong honest demo and clean parallel module boundaries |

## Rubric-weighted comparison

Scores 1-5 (higher better) express anticipated fit to judging criteria, not empirical outcomes.
Raw = 0.40*technical + 0.20*innovation + 0.15*efficiency + 0.15*presentation + 0.10*code/demo.
Risk is a separate explicit deduction: 0.10, 0.25, or 0.45 points for low, medium, or high
implementation/research risk. The deduction is an internal planning convention, not official scoring.

| Concept | Technical 40% | Innovation 20% | Efficiency 15% | Presentation 15% | Code/demo 10% | Raw /5 | Risk deduction | Adjusted /5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C1 | 3 | 2 | 5 | 4 | 5 | 3.45 | 0.10 | 3.35 |
| C2 | 3 | 3 | 4 | 4 | 4 | 3.40 | 0.25 | 3.15 |
| C3 | 4 | 4 | 2 | 4 | 3 | 3.60 | 0.45 | 3.15 |
| C4 | 3 | 4 | 2 | 4 | 3 | 3.20 | 0.45 | 2.75 |
| C5 | 4 | 4 | 4 | 4 | 3 | 3.90 | 0.45 | 3.45 |
| C6 | 4 | 4 | 4 | 5 | 4 | 4.15 | 0.25 | 3.90 |

## Additional pretrained forecast candidates (not detector replacements)

Chronos-2 and TimesFM-3 are forecasters, not methods scored by this project. Their outputs could
support a causal anomaly wrapper, so assess them as C7/C8 only through EXP-12. The same
40/20/15/15/10 rubric and planning risk deduction are shown below; scores remain subjective
estimates, not benchmark results.

| Comparator | Technical 40% | Innovation 20% | Efficiency 15% | Presentation 15% | Code/demo 10% | Raw /5 | Risk deduction | Adjusted /5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C7 Chronos-2 forecast residual | 4 | 4 | 3 | 4 | 3 | 3.75 | 0.45 | 3.30 |
| C8 TimesFM-3 forecast residual | 4 | 4 | 2 | 4 | 3 | 3.60 | 0.45 | 3.15 |

C7/C8 carry added adoption risk: forecasting-to-alert calibration is unproven on the competition
metric, refreshing each point can cost time, checkpoints add dependencies, and TimesFM-3 weights
have restrictive upstream terms. Chronos-2 is the first practical probe; TimesFM-3 remains gated.
TimesFM-2.5 is a separate fallback only if its checkpoint and terms are verified. Exact evidence
and gates are in EXP-12.

## Selection: Sentinel Pulse (C6)

C6 offers explicit evidence, bounded sequential execution, and separable workstreams. C1 is
retained as the always-runnable fallback. Seasonal residuals from C5 are coherent only when a
past prefix supports them; EVT is a stretch, not mandatory. C2/C3 remain independent comparators.
Do not add every model to the final ensemble: each branch must improve held-out event F1,
error balance, or robustness with an acceptable runtime cost under the promotion gates.

The subjective ranking can change once data/scorer arrive. If equal technical weights for C1/C6
prove more realistic, the engineering justification weakens; prefer the simpler baseline when
measured gains are absent. If motif anomalies dominate, promote C3 only after causal evaluation.
No paper establishes that C6 wins on the organizer subset. The final selection is provisional
architecture with a measured fallback, not a claim of scientific novelty or a new theorem.

## Adversarial design reviews and changes

**ML research reviewer:** The proposed ensemble is not novel merely because it combines familiar
scores. Event F1 is underspecified and threshold selection can overfit very few events. Gating
outliers biases calibration and can erase persistent faults. Changes: require separate component
ablations, untouched validation series, explicit calibration variants, and no adaptation promotion
without sustained-fault tests. Retain the raw baseline and freeze a final untouched evaluation.

**Principal engineer:** Four modules could independently invent windowing and output semantics.
State persistence and a UI can delay the baseline. Changes: canonical shared types and schemas,
one detector lifecycle, one run manifest, separate ownership, finite state limits, explicit errors,
and no database/API/frontend in the core. Checkpointing is a later task with replay-parity tests.

**Hackathon judge:** A polished synthetic demo might be mistaken for real detection performance.
An intricate architecture without a valid prediction file could lose reliability points. Changes:
show data provenance and metric identity on every result, put the official exporter/scorer on P0,
use the exact 10-slide structure, and rehearse an offline CLI fallback. Display a real false positive
and missed event, rather than presenting only attractive examples.

Unresolved trade-offs: sustained shifts versus benign drift, threshold sensitivity versus delay,
calibration history versus memory, per-series tuning versus transfer, event deduplication semantics,
and available labels. These require experiments and organizer clarification, not rhetorical certainty.
