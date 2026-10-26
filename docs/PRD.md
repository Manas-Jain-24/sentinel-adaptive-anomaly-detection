# Sentinel Pulse product requirements

## Executive summary and vision

Sentinel Pulse detects abnormal observations in a stream, shows the numerical reason for a flag,
and produces reproducible artifacts that can be evaluated independently of a UI. We target
Utkrishta Challenge 2 with an efficient causal residual detector, a simple fallback, and disciplined
event evaluation. Winning is an aspiration; no benchmark result or competitive rank is promised.

The product makes an alert inspectable: what arrived, what the detector expected using only past
data, how large the deviation was, what threshold applied, and how much time inference took.
This directly supports official scores, evidence, runtime, and presentation requirements.

## Problem, objective, and users

The official objective is baseline learning from streaming time series and identifying deviating
observations/windows with score, NORMAL/ANOMALOUS label, and evidence (PDF p2). The competition
objective is strong organizer-held event F1 with defensible precision/recall/delay and runtime.
Judging weights and complete requirement IDs are in [traceability](REQUIREMENTS_TRACEABILITY.md).

Primary users are the team running controlled experiments and judges inspecting outputs.
An illustrative operations analyst can inspect a suspicious server/sensor trace; this is a use
case, not a claim of production readiness, diagnosis, or multivariate root-cause discovery.

## Official requirements and constraints

OFF-01 through OFF-24 are authoritative. Use the organizer NAB subset, emit scores/labels/evidence,
evaluate event F1/precision/recall/delay/runtime, deliver runnable code plus README, official-format
predictions, a 10-slide PPT, and a live/video demo. Scoring implementation/output schema are missing.
Challenge 1's 15-run limit does not apply. No deadline, numeric performance target, or hardware
ceiling is specified. [Organizers' questions](QUESTIONS_FOR_ORGANIZERS.md) remain unresolved.

## Functional requirements and acceptance

| ID | Behavior / reason | Acceptance / owner |
|---|---|---|
| FR-01 | Validate and normalize permitted input; prevent silent bad data | Exact canonical columns, finite values, explicit timezone, per-series order errors; KS-01/04 |
| FR-02 | Replay sequentially with isolated state; represent real streaming constraints | Prefix decisions unchanged by appended future data; interleaved streams equal independent replays; AY-03 |
| FR-03 | Learn baseline and score causally; avoid temporal leakage | Pre-update statistics and tests for early spikes/constant signals; MN-01/02 |
| FR-04 | Label each observation and expose readiness; avoid fabricated warmup confidence | Score-null warmup in internal format, threshold equality documented; MN-03 / official mapping AY-04 |
| FR-05 | Emit direct evidence for every flag; satisfy interpretability | Baseline/scale/residual/branch score reproduces score, no unsupported cause attribution; MN-02 |
| FR-06 | Adapt threshold to past context; transfer across scales/regimes | Causal calibration ablation and held-out results; MN-03/04 |
| FR-07 | Evaluate events separately from inference; isolate labels | Event matching golden tests and official scorer parity; MY-01/04 |
| FR-08 | Export reproducible results; make claims auditable | Checksums, config, metric/version, split, code revision, scope, dependency snapshot; AY-01/MY-02 |
| FR-09 | Write organizer-format predictions; secure a valid submission | Roundtrip against actual organizer schema, exact row order/columns; AY-04, blocked |
| FR-10 | Visualize genuine outputs; support inspection/Q&A | Trace, flags, threshold, evidence, timing, provenance; MY-03 |
| FR-11 | Recover state or reproduce by replay; avoid corrupted resumes | Versioned JSON checkpoint equality or a documented full-replay fallback; AY-02 |

## Input, output, and ML requirements

Internal input is `series_id,timestamp,value` CSV, timezone-aware ISO times, strictly increasing
within each series. Labels live in a separate window file available only to evaluation. Raw NAB
timestamps require an explicitly approved timezone convention, not an implicit UTC guess.
Exact typed schemas are in [INTERFACES](INTERFACES.md). The initial univariate contract is an
ENGINEERING_ASSUMPTION pending actual asset inspection.

Internal output is one JSONL record per input point plus `run.json`. A score is a nonnegative
deviation magnitude, not a calibrated probability. Warmup uses null score and NORMAL/ready=false.
The official schema adapter must resolve whether this is allowed or needs a finite warmup value.
Every anomaly has numerical evidence and an algorithmic reason. Missingness and root causes
must not be inferred without supporting data.

Only past features, scalers, predictions, residuals, and scores may affect a decision. Development
labels may select configurations on approved training/validation partitions; labels never enter
`Detector.process`. Final configuration is frozen before untouched evaluation. No future-aware
decomposition or hindsight revisions of emitted predictions are permitted by our design.

## Non-functional, performance, and reliability requirements

- Core must run locally on CPU without UI, API keys, or external services. Bounded histories and
  max-series guard prevent unbounded state. Explicit limits are engineering defaults, not rules.
- Measure warm and cold starts, p50/p95 process time, end-to-end replay time, peak memory, series
  counts, and hardware. Starter timing is per point, not official per-window profiling.
- Internal engineering investigation budget: seek p95 below 10 ms/point and core peak memory
  below 256 MiB on a recorded team laptop for a declared workload. These are **unverified goals**,
  not hard acceptance rules or promised performance. Replace with organizer limits when known.
- Deterministic predictions for identical data/config/code; elapsed time is excluded from equality.
- Malformed inputs must fail with actionable errors and no published partial run. Existing run
  directories are preserved. Checkpoints use validated JSON, never arbitrary object execution.
- Development checks: relevant pytest, Ruff lint/format, mypy, repository consistency checker.
  CI matrix is configured but remote success cannot be asserted before execution.

## Three delivery levels

**Level A - reliable competition baseline:** canonical adapter, rolling z/MAD baseline, causal
windowing, evidence, approved warmup mapping, official exporter/scorer, reproducible CLI,
meaningful correctness tests, README, real-data results, required deck/demo. Initialization only
implements the internal portion. A valid competition fallback is **not yet complete** without
official assets, schema, and scorer. UI and advanced models are optional.

**Level B - competitive final system:** calibrated combination of level/change residuals with
seasonal expectation when supported by the past, guarded updates/shadow drift only if validated,
runtime profiling, experiment tracking, error analysis, robust export, and artifact-based viewer.
Chronos-2 and TimesFM-3 are forecasting-model comparators in EXP-12, not default runtime
dependencies or an assumed detector replacement. Each added component has a measured promotion
gate. A simpler model may be selected for final submission if it performs better or the advanced
system is unreliable.

**Level C - research stretch:** see [EXPERIMENT_PLAN](EXPERIMENT_PLAN.md) for hypotheses, effort,
failure and abandonment gates for EVT calibration, shape discord augmentation, and adaptive
expert selection. All are optional, disabled by default, and removable without breaking A/B.

## Journeys and demo

An experimenter inspects assets -> freezes splits -> runs a baseline -> compares one change ->
inspects false positives/misses/delay -> chooses a configuration -> exports predictions. Each run
produces enough provenance for another machine to reproduce the result. A judge opens a saved
run -> sees data/scope/metric -> selects an event -> inspects actual residual/threshold evidence ->
compares a baseline and a failure example. The CLI remains the demo fallback.

Viewer screens and exact presentation are in [DEMO_PLAN](DEMO_PLAN.md) and
[PRESENTATION_PLAN](PRESENTATION_PLAN.md). Real dev outputs and synthetic examples have distinct
visible provenance. No chart may show an invented hidden score.

## Success metrics and selection criteria

Primary success is official event F1 when the official scorer is available. Report event precision,
recall, onset delay distribution (and misses), per-series counts, runtime distribution, and memory.
Use both official aggregation and diagnostic macro/micro views clearly named. No arbitrary
numeric F1 target is promised. Promote B only after predefined held-out improvement criteria,
robustness checks, and code/runtime gates; see [EVALUATION](EVALUATION.md).

## Scope exclusions, assumptions, and risks

No production monitoring service, multi-tenant backend, database, cloud deployment, LLM-generated
explanations, multivariate root-cause engine, or guaranteed distribution-free alarm rate is in
scope. The team's experience and hackathon schedule are unknown; estimates use relative effort.
Data/scorer/schema are unavailable. Scarce events, contaminated warmup, regime changes, event
semantics, output mismatch, and collaboration conflicts are tracked in [RISK_REGISTER](RISK_REGISTER.md).

## Definition of Done

Initialization is done when mandatory docs/contracts/task ownership exist, setup installs, imports
and tests/checks run with recorded outcomes, synthetic replay/evaluation succeeds, Git state is
truthfully recorded, and a fresh agent can identify its next task. This does not mean Level A
or the hackathon submission is done.

The final competition project is done only when official requirements and schema are verified,
the final artifact is reproduced from a shared commit and frozen manifests, hidden claims are
limited to organizer results, exactly 10 slides and demo are ready, all required checks pass,
and every P0 submission item is satisfied or explicitly resolved with the organizers.
