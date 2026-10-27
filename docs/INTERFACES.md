# Shared contracts v1.0

Custodian: Ayush. Typed definitions: `src/sentinel/contracts.py`. This document distinguishes
implemented formats from planned extensions; no external endpoint is part of the current design.

## Canonical input (implemented)

CSV header must be exactly `series_id,timestamp,value` in that order. `series_id` is a nonempty
string; `timestamp` is ISO 8601 with an explicit offset, normalized to UTC; `value` is finite float.
Offsets represent instants, not local clock order. Timestamps strictly increase **within each
series**, including interleaved input. Duplicate times/NaN/Inf/missing fields/extra label columns
are rejected. No implicit sorting, resampling, or imputation. Empty input is an error.

`Observation(series_id: str, timestamp: datetime, value: float)` has no label field. One observation
is currently one point-sized streaming window; future trailing windows end at the current timestamp.
Raw NAB `timestamp,value` input needs KS-04 to supply the series ID and approved timezone. Do not
rename/assume a raw timestamp convention silently. Series cardinality is bounded by max_series.

## Feature boundary (typed now; extractor not implemented)

`FeatureExtractor.process(Observation) -> FeatureFrame` and `reset() -> None` operate per series.
The frame fields are `series_id`, `timestamp`, `expected_level`, `expected_delta`, `scale`, `delta`,
`seasonal_expected`, `history_size`, `ready`. Expected values and scale use strictly earlier
observations; delta may use current value minus the preceding value. `scale` is positive when
ready; expected_level/expected_delta/scale may be null in warmup; seasonal_expected is null until
a validated period has sufficient past context. All present numerical values must be finite.
KS-02 implements this contract; MN-02 can use a deterministic fake FeatureExtractor meanwhile.
RollingMADStarter does not use FeatureFrame and remains runnable if feature development stalls.

## Detector boundary and lifecycle (implemented)

`Detector.process(Observation) -> Prediction` and `reset() -> None`. A detector instance handles
exactly one series, rejects non-increasing times, builds its decision from pre-update state, and
then updates. The owner of a wrapping detector calls its extractor once per point. Calling process
twice for the same timestamp is an error, not an idempotent retry. Reset clears all state. The
pipeline constructs one detector per series with a factory. No training labels or evaluation
objects may be passed to a detector.

`Prediction`: series_id, UTC timestamp, original value, score (float|null), threshold (positive
float), label (`NORMAL`|`ANOMALOUS`), ready (bool), evidence (Evidence). A ready score is finite,
nonnegative, and **not a probability**. Label is ANOMALOUS iff ready and score >= threshold.
Warmup uses score=null, ready=false, NORMAL; official acceptance of warmup mapping is unresolved.

`Evidence`: baseline/scale/residual (float|null), history_size (int), reason (algorithmic string),
component_scores (map of named finite nonnegative magnitudes). Starter reason is `warmup` or
`rolling_mad_deviation`, with component `level`. Evidence is captured before updating; residual
equals value-baseline when ready, scale=max(1.4826*MAD, scale_floor), score=abs(residual)/scale.
Future components `change` and `seasonal` require documented comparable normalization and
combined-score calibration. Evidence describes statistical deviation, not physical cause.

## Prediction serialization and run artifacts (implemented)

`predictions.jsonl`: one JSON object per input row, original order. Fields are Prediction fields
plus `schema_version="1.0"` and `elapsed_ns` (integer >=0). Evidence is a nested JSON object.
UTC timestamps end in Z. Artifact text uses LF newlines across platforms so shared checksums remain
stable under Git's newline policy. All JSON output disallows NaN/Inf. Unknown future fields may be ignored
by compatible readers; required fields/semantics cannot change without the protocol below.

`run.json` includes schema/package version, algorithm, evaluation_scope, dataset_id, input and
prediction SHA256, resolved configuration, Python/platform, point/readiness/anomalous counts,
detector total ns, runtime note, and `official_submission_ready=false`. Dataset ID/scope are
operator assertions, not automatic verification. Every run uses a new directory. Output files
are staged in a sibling temporary directory and published on success; this is single-process
publication, not a multiwriter transaction service.

AY-01 adds the following optional objects under schema 1.0; old runs without them remain valid.
The implementation is prepared for affected-owner review on the AY-01 branch; see the
[manifest proposal](HANDOFFS/AY-01_ayush_20261026T145042Z_manifest-proposal.md). Peer review and
integration are pending. No prediction/detector/config/evaluation semantics change.

`provenance` (version `1.0`):

- `source`: status (`git` or `unavailable`), full HEAD `revision` and boolean `dirty`, plus note.
  The tracked package checkout is used regardless of caller CWD. Dirty includes tracked edits
  and nonignored untracked files. HEAD identifies the committed base, never uncommitted code.
  Without tracked source/Git, revision and dirty are null with an explicit explanation.
- `config_sha256`: digest of resolved `config`. `environment` records Python version/implementation,
  OS/platform, architecture, processor (null if unknown), logical CPU count, and sorted unique
  installed distribution name/version pairs. `environment_sha256` hashes the full snapshot;
  `dependencies_sha256` hashes its dependency list. These three hashes use sorted-key, compact,
  ASCII-escaped UTF-8 JSON without a trailing newline and with NaN/Inf disallowed. They identify
  recorded metadata; they do not certify locked dependencies or reproduce uncommitted source.
- `split_manifest_sha256` and `split_manifest_artifact`: null unless an optional manifest is
  supplied. `--split-manifest PATH` copies bytes to `split-manifest.snapshot` in the run directory,
  then hashes that copy. `split_validation` is `checksum_only` or `not_supplied`. This preserves
  provenance without inventing KS-03 semantics or verifying split membership. Bytes are opaque
  and never passed to inference. Existing input/prediction hashes also hash exact file bytes.
- UTC `started_at_utc` and `prepared_at_utc`: entry to run_file and completion of metadata
  preparation, before the final manifest write/publication. No random seed is needed by the
  deterministic starter; no feature extractor or split schema version is invented.

`profiling` uses `perf_counter_ns`, nanoseconds, and explicit region descriptions:

- `distributions`: `all_process`, `ready_process`, `warmup_process`, `cold_process` (first process
  call per series) and `warm_process` (subsequent calls, including remaining learning warmup).
  Process time excludes detector construction, routing, parsing, serialization and profiler work.
  Cold does not measure interpreter startup, imports or constructor cost.
- Each population has exact `count`, `total_ns`, `min_ns`, `max_ns`, and a bounded integer
  `histogram` of `upper_bound_ns`/`count` pairs. `p50_upper_bound_ns`/`p95_upper_bound_ns` are
  nearest-rank quantile upper bounds, with relative overestimate <1/128; durations <256 ns are
  exact. Empty populations have zero count/total, null min/max/quantiles and empty histograms.
  The bound can exceed max_ns slightly. These are explicitly approximate quantiles, not exact
  observations. Storage depends on duration magnitude, not number of points.
- `end_to_end_replay_ns`: predictions file open through close, including CSV open/read, construction,
  routing, parsing, process, serialization, writing and profiling. `prepublication_elapsed_ns`: run_file
  entry through prepared metadata, also including input hashing, environment/Git collection,
  optional split snapshot, output setup and prediction hashing. Final run.json serialization/
  write/rename, CLI startup and evaluation are excluded to keep staged publication immutable.
  Wall time includes profiler overhead; no peak-memory or official-runtime measurement is implied.

`workload` records actual observation/readiness/warmup counts, series_count, configured window_size,
min_history/max_series, no-resampling cadence policy, and a per-series map of counts and UTC
first/last timestamps. Hardware is in provenance.environment. Profiling requires O(S + log T)
storage for S series and largest duration T, with a fixed number of histogram sub-buckets.

Input bytes are hashed before and after replay; a detected change aborts publication. This guard
does not lock the input file; use immutable input assets. Prediction equality excludes elapsed_ns;
run timestamps, runtime distributions, Git state and environment may also vary between runs.

## Config (implemented)

`configs/starter.json` uses DetectorConfig: window_size=32, min_history=8, threshold=4.0,
scale_floor=0.1, max_series=100. Require integer bounds 2<=min_history<=window_size, max_series>=1,
finite positive threshold/floor, and no unknown keys. These are starting values for wiring,
not tuned hyperparameters. Advanced model/period/quantile/guard settings must use a reviewed
separate config section or extension; do not overload threshold semantics silently.

### Detector selection (additive integration proposal)

The user authorized Manas to prepare CLI/pipeline integration across ownership boundaries;
Ayush and affected-owner review remains pending. See the
[scoped proposal](HANDOFFS/MN-03_manas_20261027T103208Z_cli-integration-proposal.md).
This implementation is on the integration feature branch, not a claim of main integration.
Detector/Prediction/Evidence and the legacy five-field DetectorConfig are unchanged.

`sentinel run` accepts optional `--detector mad|zscore|residual` (fixed threshold) OR
`--model-config PATH`, never both. Neither option means the same default MAD behavior.
`run_file` adds keyword-only `model_config: ModelConfig | None = None`; all existing
positional calls and `split_manifest_path` remain valid. Guards, model weight downloads,
fitting, label inputs and TSFM selectors are not introduced.

`detectors.selection.ModelConfig` is a separate frozen settings object. Its strict JSON
keys are `detector` (default mad), `use_seasonal` (default false), `seasonal_period`
(default null), and `calibration` (default null). Calibration is a JSON object containing
the validated QuantileThresholdConfig fields, with documented defaults in
[CALIBRATION](../src/sentinel/detectors/CALIBRATION.md). Empty calibration `{}` explicitly
enables its defaults; null disables it. Duplicate/unknown keys, bools masquerading as
numbers and nonfinite/invalid settings reject. Seasonal scoring requires residual,
use_seasonal=true and an explicit integer observation lag P in [1,W]. No fitting occurs.

The base config's W/min_history/scale_floor govern feature construction; its threshold
governs a fixed detector. When calibrated, the separate fallback/empirical threshold
replaces that fixed decision boundary, with all resolved calibration values recorded.
Each factory call creates fresh base, feature and calibration state for one series.

Algorithm IDs are `rolling_mad_starter`, `rolling_zscore`, `residual_max` and
`residual_max_seasonal`; enabled calibration appends `_prior_quantile`. Existing default
MAD predictions and algorithm ID are preserved. `run.json` adds `model`, containing the
resolved selector/seasonal/calibration values, actual feature implementation/settings (null
for direct baselines), inclusive raw reference/update policy and calibration sample policy.
`replay_context.saturated_raw_lookback` records W for fixed or W+C for these bounded
calibrated models; it certifies neither context permissions nor partition replay. It does
not apply to frozen forecast blocks, guarded/fitted models or intermittent readiness.

Provenance adds `model_config_sha256` (canonical hash of resolved `model`) and
`run_config_sha256` (canonical hash of `{"config": base_config, "model": resolved_model}`).
The existing config_sha256 still hashes only the unchanged base config. Consumers must
use the combined hash plus code/data/split/metric identity to compare complete runs.
Existing prediction schema, staging/error behavior and named provisional evaluator are
preserved. Split snapshots remain checksum-only; no implied fitting or target selection.

Integration verification reproduced intermittent Windows access-denied directory renames
on two different runs, after artifact handles were closed. Publication now retries only
PermissionError with Windows code 5/32, at most six attempts with 310 ms total backoff.
Destination existence is rechecked before each attempt. Persistent permission errors
and all other errors still fail and clean unpublished artifacts; existing outputs are
preserved. Backoff is outside the documented prepublication/profiling regions. This is
single-process publication, not an atomic multiwriter claim.

## Truth and evaluation (implemented, provisional)

Window JSON: `{"schema_version":"1.0","windows":[{"series_id":"s","start":"...Z","end":"...Z"}]}`.
Additional top-level provenance is allowed. Windows have explicit timezone, start<=end, closed
endpoints, no overlap/touch within a series, and must fit prediction timestamp coverage.
No label file is loaded during inference.

Evaluation result: metric_id=`provisional_event_trigger_f1_v0`, official_metric=false, tp/fp/fn,
precision/recall/event_f1, per-hit delay_seconds, mean_delay_seconds (null if no hits), observation
and warmup counts, and, through evaluate_run, scope, dataset ID, input/windows hashes.
[EVALUATION](EVALUATION.md) defines exact episode matching and edge cases. Unsupported metric or
scope must error. Official benchmark/hidden scopes are not supported by this starter evaluator.

## Errors, persistence, and future adapters

`ContractError(ValueError)` reports data/config/schema violations; CLI exits 2 for expected errors.
I/O/JSON errors also produce nonzero exit. Programming errors should remain visible for diagnosis.
Do not catch exceptions and produce a fake successful score. Failed replay removes its unpublished
temporary directory. A failed run never overwrites an existing destination.

Persistence is **planned**: AY-02 proposes schema/version/config hash/series states/cursor and
last times, validates JSON types/bounds, and proves resume equals uninterrupted replay. No
checkpoint methods exist in Detector v1 yet; adding a separate StatefulDetector Protocol requires
coordination. Avoid unsafe deserialization. Whole-file deterministic replay is the current fallback.

No trainer API exists because the starter is online statistics. A future fitted comparator must
record a train-prefix manifest, expose a fit factory separate from process(), and never fit on
validation futures. Official exporter and scorer signatures are deliberately deferred until actual
schema/scoring assets exist; adapter tests should first use organizer golden examples.

## Fixture and compatibility conventions

All wiring fixtures live in tests/fixtures with explicit synthetic provenance and deterministic
values. New test doubles implement typed Protocols; do not import another contributor's unfinished
private methods. Numerical comparisons use explicit tolerances and omit elapsed_ns. Prediction
history is immutable: no later-neighbor or label-based corrections to previous records.

## Contract-change protocol

1. File a uniquely named proposal under docs/HANDOFFS with task ID, old/new examples, motivation,
   affected producers/consumers, migration/versioning, and proposed golden tests.
2. Ayush approves shared-interface changes and affected owners review. Breaking changes require
   explicit approval recorded in DECISIONS before implementation. Additive fields also need review.
3. Change typed schemas, this document, config/examples, producer/consumer tests, and migration
   together on a coordinated branch. Never merge only half of a breaking change.
4. Run baseline/contract/integration checks. Ayush updates shared state after approved integration.

Emergency work follows the same breaking-change rule; use a scoped compatibility wrapper when
possible and document human-authorized exceptions. Neither urgency nor an agent's local success
permits silently changing shared semantics.
