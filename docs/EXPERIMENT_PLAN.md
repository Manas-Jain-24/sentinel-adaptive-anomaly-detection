# Research and experiment plan

Owners: Mayank (harness/evaluation), Manas (models), Kaustubh (data/features), Ayush (runtime/artifacts).
No model comparison on official data has run. Starter fixture results are software validation only.
The 15-run cap belongs to Challenge 1, not this track; the budgets below are engineering choices.

## Dataset inspection and partitions

First inventory permitted files, source/checksum, series grouping, length, time range/cadence,
timezone, gaps/duplicates/NaNs, value scale, periodicity from past prefixes, and development event
counts. Record what labels are authorized. Confirm whether training/validation/test partitions are
provided. Use official partitions first. Keep raw assets read-only and outside committed source.

If no split is prescribed, freeze a documented group-held-out strategy using complete series
from related sources together. With enough groups, use three group folds for model selection
and reserve untouched groups for final reporting. Within a training group use chronological
train/calibration/validation segments; an initial 60/20/20 ratio is an ENGINEERING_ASSUMPTION,
subject to available history/events. Inspect event counts before freezing, not after chasing
scores. If groups/events are too scarce, use leave-one-group-out and report high uncertainty;
do not fabricate an independent test set. Purge training examples whose feature windows cross
the split boundary; permitted past context for inference must be recorded explicitly.

Prevent leakage: scalers and period estimates fit train prefixes only; calibration uses preceding
scores only; no shuffled overlapping windows; no labels in detector inputs; no future reconstruction
windows; no validation-driven rebaseline within a test trace. Track online state reset/carry policies.
Public NAB can be a separately labeled research dataset only with appropriate permission, never
a silent stand-in for the organizer-prepared subset or a way to recover hidden windows.

## Highest-value first technical experiment: EXP-01

On authorized labeled development data, compare **causal rolling MAD** against **a single causal
seasonal-naive residual detector**, with identical event semantics and a small training-selected
threshold grid. Stratify false alerts/missed events by periodic/nonperiodic traces. This tests
whether contextual seasonality is worth implementing before adding ensemble/guard complexity.
Record event F1/counts, precision/recall, onset delay, and p95 runtime. Use official scorer when
available; otherwise label the local provisional metric and rerun after official integration.
Do not claim the experiment ran until the missing data/scorer prerequisites are satisfied.

Before data arrives, MY-01 strengthens matching golden tests, KS-01/03 validates manifests/splits
on synthetic inputs, and MN-01 checks baseline causality. These are useful wiring work, not EXP-01.

## Prioritized backlog

| ID | Priority | Question / comparison | Dependencies | Owner | Expected artifact |
|---|---|---|---|---|---|
| EXP-00 | P0 | Are data, matching, splits, and score orientation correct? | KS-01, MY-01; official assets for parity | Kaustubh/Mayank | Audit, golden tests, frozen manifests |
| EXP-01 | P0 | Does causal seasonal context reduce errors? MAD vs seasonal residual | Permitted labeled data, KS-02, MN-01/02 | Manas/Mayank | Per-series paired result table |
| EXP-02 | P0 | Fixed standardized threshold vs past-score empirical quantile | MN-03, EXP-01 | Manas | Calibration/false-alert transfer report |
| EXP-03 | P1 | Level only vs level+delta vs +validated seasonal | MN-02/05, fixed evaluation | Manas | Component ablation and runtime |
| EXP-04 | P1 | No guard vs capped influence vs finite quarantine+shadow | MN-04, sustained-fault fixtures | Manas | Drift/fault trade-off report |
| EXP-05 | P1 | IF on causal features vs selected residual baseline | KS-02, optional dependency review | Manas/Kaustubh | Nonlinear comparator results |
| EXP-06 | P1 | Robustness to cadence gaps, scale, noise, contaminated warmup | KS-06, AY-06 | Kaustubh/Ayush | Stress report, no official-score claim |
| EXP-07 | P1 | Runtime and memory at growing history/series counts | AY-01/06 | Ayush | Hardware-tagged p50/p95/peak memory |
| EXP-08 | P2 | EVT calibration improves empirical threshold | Stretch S1 | Manas | Tail fit diagnostics and ablation |
| EXP-09 | P2 | Causal shape discord catches missed contextual events | Stretch S2 | Kaustubh/Manas | Past-only matching study |
| EXP-10 | P2 | Online expert selection improves transfer | Stretch S3 | All A/B gates passed | Manas/Mayank | Leakage-free selection study |
| EXP-11 | P0 | Frozen final model on untouched permitted split | Scorer/schema resolved, AY-05 | Mayank/Ayush | Final reproducible evaluation and export |
| [EXP-12](#exp-12-forecasting-foundation-models) | P1 | Do zero-shot foundation forecasts improve event detection enough to justify runtime? | Authorized labeled data, official scorer ideally, MN-05/MY-02/AY-06 | Manas lead; Mayank, Ayush, Kaustubh support | Paired event results, causal wrapper, license/runtime gate |

## EXP-12: Forecasting foundation models as anomaly candidates

**Question.** Do Amazon Chronos-2 and Google Research TimesFM-3 forecasts improve the event
F1/delay/recall/precision balance versus rolling MAD and the selected residual baseline, at an
acceptable per-window runtime and memory cost? Forecast accuracy alone is not the objective.

**Candidates.** First test `autogluon/chronos-2-small` (28M) as the practical CPU Chronos checkpoint;
test `amazon/chronos-2` (120M) only if latency/memory allow. Test TimesFM-3 (330M) only after a
runtime feasibility probe and explicit weight-license check. If the TimesFM-3 checkpoint cannot
be used or run in the permitted setup, test TimesFM-2.5 only after verifying its exact checkpoint
license and inference package. Original Chronos, fine-tuning, and additional TSFMs are out of the
first experiment. Keep optional libraries/models out of base install and Git; record exact model
ID, revision/hash, package versions, license URL/version, hardware, and download/cache source.

**Causal detector wrapper.** At prediction origin `t-1`, forecast the next `h` values from past
history only and obtain model quantiles `q10`, `q50`, and `q90`. When actual `y_t` arrives, emit
the frozen forecast error evidence and interval-exceedance score
`score_t = max(0, q10_t - y_t, y_t - q90_t) / max(q90_t - q10_t, scale_floor)`.
This is a nonnegative anomaly score, **not a probability**. Label using one threshold selected on
permitted train/development labels only. Alternatively calibrate a fixed score threshold on a
separate permitted calibration prefix, with the policy recorded before validation. Emit q50,
q10/q90, interval width, signed residual, score, threshold, origin timestamp, and forecast age as
interpretable evidence. Do not revise past scores after observations arrive.

**Freshness/latency variants.** Compare forecast stride 1 (refresh at every newly observed point)
with frozen block forecasts at horizon 8 (refresh only after the block). Both are causal: the
block policy never sees an actual observation early. Report event detection delay and score age
for each; do not present stale block forecasts as fully refreshed inference. Start after the same
warmup for every model. Batch series only as a secondary run, since batch startup/throughput may
not match per-window online latency. Separate model load and first-compile time from warmed per-
window inference, and also report end-to-end cold-start cost. First probe CPU use for both models;
on the current Windows host, TimesFM-3's upstream quickstart documents CUDA, while its repo also
describes an Apple Silicon MLX path. CPU availability is therefore unverified, not assumed. If a
permitted GPU is available, log its model/memory and compare the same workloads; GPU work is optional.

**Evaluation design.** Use identical authorized group/chronological splits, warmup, event matching,
and inputs for MAD, selected residual baseline, Chronos-2, and TimesFM-3. Fit no weights on hidden
or validation/test labels. Prefer the organizer's scorer. Until that arrives, report only the
named provisional metric, clearly scoped as development validation. Measure event F1, TP/FP/FN,
precision, recall, per-hit delay plus missed-event count, forecast coverage/interval width, cold
load, warmed p50/p95 per point, block latency, total replay time, peak RAM and accelerator memory.
Inspect spikes, seasonal peaks, regime shifts, flat/short streams, and persistent faults. For
stochastic/infrastructure-sensitive cases record repeat runs and versions. Perform no per-series
hidden-label tuning or post-hoc point adjustment.

**Acceptance / promotion.** First prove one-step/block origin timestamps and prefix invariance with
independent hand-built tests. Evaluate on approved labeled groups. Promote a TSFM into final B only
if it passes the existing frozen F1/recall/p95 gates in this plan, produces useful numerical
evidence, satisfies the actual runtime rules, and its model terms permit the contest use and chosen
sharing. Compare against both the rolling MAD fallback and the selected residual model; use paired
series/event results, not provider forecasting leaderboards. If inference fails, is slow, license
is unclear, or event gains do not pass gates, retain it as a measured comparator and submit the
simple detector. This candidate addition does not replace EXP-01 as the first value experiment;
run EXP-12 after the basic scorer/split/replay path is valid.

## Tuning, logging, and statistical caution

Begin with at most 12 config evaluations per family as an internal exploration budget; expand only
when learning justifies it. Example coarse candidates: histories 32/64/128, standardized thresholds
3/4/6; empirical quantiles 0.98/0.99/0.995 only with adequate past samples. Do not test the full
Cartesian product by default. Calibration history/floor/seasonal period are selected on training,
not the held-out trace's label-optimal threshold. Record every attempted config, including failures.

For stochastic comparators, use declared seeds 17, 29, 43 as a design convention; deterministic
statistics need no invented random seed. Cache input hashes, never cache leaked fitted state.
Track metric identity, code revision, resolved config, train/calibration/validation manifests,
environment, runtime and memory, error examples, and status. No experiment-tracking service is
necessary: one immutable directory plus a machine-readable index suffices (MY-02).

If enough independent series exist, bootstrap paired differences over series/groups and report
uncertainty; do not treat adjacent windows as independent samples. With very few events, publish
counts and per-series changes and describe uncertainty instead of overstating significance.

## Promotion criteria (internal design gates)

Freeze these before candidate results. Default B promotion requires pooled held-out event F1 at
least 0.02 above A, no recall drop over 0.03, and p95 detector time no more than 2x A on the same
hardware/workload; all correctness/export checks must pass. These are engineering thresholds,
not official rules or measured gains. Revisit only through a documented pre-evaluation decision.
If sample size is too small for a reliable conclusion, prefer simpler A unless consistent
per-series evidence and repeatability support B. Do not tune these gates to excuse a favored model.

Perform error review of isolated spikes, sustained faults, variance bursts, periodic peaks, flat
signals, short streams, missing spans, and contaminated warmup. A smaller aggregate gain that
destroys a critical failure category is a reason to withhold promotion. Latency metrics always
include misses/recall context. Hysteresis/cooldown are separate tunable components, disabled until
official event matching is known; they can merge distinct real events.

## Level C research stretch specifications

| Feature | Hypothesis / advantage | Approach / required experiment | Gate / effort | Failure modes and abandon conditions |
|---|---|---|---|---|
| S1 EVT threshold | Tail extrapolation reduces false alerts at similar recall | Compare empirical quantile to SPOT/DSPOT on causal combined residuals; inspect tail sample count/stability, stationary vs shifting slices | 3 effort units; beats empirical event F1 by >=0.01 without violating B runtime/recall gates | Sparse/dependent tails, unstable fit, contaminated calibration, build/license burden; abandon if gain absent or fit fails on any required series without a safe fallback |
| S2 Shape discord | Past-only nearest-normal window distance detects shape errors residuals miss | Bounded history, two training-selected motif lengths, left-only matches, freeze scores when emitted; compare level-only and augmented outputs | 4 units; >=0.02 held-out F1 gain with acceptable delay and <=2x selected B p95 | Level invariance, horizon cost, future-neighbor leakage, long-window onset delay; abandon for unstable gains or missed runtime budget |
| S3 Adaptive expert selection | Causal unsupervised predictor-loss selection transfers across regimes | Fixed small pool of level/seasonal predictors; weights updated only after observations, no event labels; compare to fixed weights across held-out groups | 4 units; consistent per-group improvement and no sustained-fault recall loss >0.03 | Forecasting loss may reward learning anomalies, added state, validation overfitting; abandon if advantage depends on per-series label tuning or hides faults |

One effort unit is approximately a focused half-day of engineering/review, not a calendar promise.
Stretch work begins only after the official-format A path and measured B are integrated. Disable
every stretch feature and verify A/B remain functional before final freeze.
