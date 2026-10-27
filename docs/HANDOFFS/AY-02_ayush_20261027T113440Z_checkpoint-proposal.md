# AY-02 checkpoint/resume contract proposal

- Executing scope: Ayush integration and Kaustubh data, explicitly assigned together by the user.
- Authored: 2026-10-27, Asia/Calcutta; filename timestamp is UTC.
- Status: IN_REVIEW proposal; checkpoint implementation BLOCKED on owner review/approval.
- Branch: `fix/kaustubh/KS-06-integration-review`, from main `8c1be6fdd167c741ad1de0123d48bda3effbab12`.
- Existing behavior: Detector v1 exposes only process/reset. Whole-file replay with new state
  is the supported recovery. There is no checkpoint file, state protocol or --resume option.
- Shared location: this proposal travels with the feature PR; see the final integration handoff
  and PR for the published commit. No approval or breaking ADR is claimed here.

## Decision and alternatives

Do not bolt serialization onto current private histories. PR #7 (`a52dd28`) composes independent
feature, residual and calibration state and already wires model identity/profiling. The main
branch still constructs MAD directly. A cursor plus a bounded value list cannot reproduce every
composed detector, and a resumed suffix alone is not a complete immutable run for the evaluator.

1. **Recommended now:** retain reset/full replay; publish this baseline-only proposal and the
   current-contract compatibility tests. It fits both main and PR #7 without changing contracts.
2. **After coordinated approval:** introduce an optional parallel StatefulDetector protocol and
   baseline-only checkpoint bundle. Profile parsing/state validation to establish useful savings.
3. Serializing arbitrary detector internals, pickle, or silently restarting calibration is rejected:
   none provides a reviewed portable state contract or guaranteed semantic continuation.

## Proposed optional interface (not implemented or approved)

Keep `Detector.process(Observation) -> Prediction` and `reset() -> None` unchanged. An optional
`StatefulDetector` would additionally expose `snapshot() -> JSON object` and
`restore(state: JSON object) -> None`. Manas owns baseline state production/restoration; Ayush
owns envelope/cursor/publication. Restore validates the entire state before mutation. Unsupported
models fail with full-replay guidance rather than pretend to resume. New schema/API, documentation,
tests and any required ADR must be reviewed together before implementation.

Old invocation remains the existing README command. Proposed opt-in invocation is
`sentinel run ... --resume CHECKPOINT_BUNDLE`; its exact flags and checkpoint scheduling remain
subject to Ayush's API review. Old runs need no migration. Removing the optional path restores
full replay without changing Prediction/Evidence, five-field DetectorConfig, or old artifacts.

Proposed `checkpoint.json` envelope example (illustrative, not a valid saved checkpoint):

```json
{
  "schema_version": "sentinel_checkpoint_v1",
  "algorithm": "rolling_mad_starter",
  "dataset_id": "synthetic-fixture-v1",
  "evaluation_scope": "synthetic_smoke",
  "input_sha256": "<actual complete immutable input digest>",
  "run_config_sha256": "<actual complete model/config identity>",
  "state_implementation_version": "<reviewed baseline state version>",
  "next_record_index": 2,
  "predictions_prefix_sha256": "<actual prefix file digest>",
  "series": {
    "s": {
      "observations_seen": 2,
      "last_timestamp": "2026-01-01T00:01:00Z",
      "history": [1.0, 3.0]
    }
  }
}
```

The bundle must contain both this envelope and the saved prediction prefix. It is a separate
recovery artifact; it is never published as a successful final run. `next_record_index` counts
parsed observations globally, not lines, byte offsets or per-series indices (CSV can interleave
and contain quoted newlines). Each series count sums to the cursor and last timestamp/history
matches its consumed subsequence. Histories are bounded by the configured W, counts/cardinality
by validated limits, numeric values finite, timestamps explicit UTC, and bools cannot be integers.
Full input/config/state-version/prefix identity must match before continuing. Source provenance
must record both execution revisions rather than label mixed revisions as one clean run.

Validation should stream the consumed CSV prefix to verify cursor, per-series counts/last times/
last-W values, and prediction-prefix alignment/checksum. This costs O(N) parsing and bounded
state, but avoids re-scoring that prefix. A checksum detects corruption, not author authenticity;
untrusted JSON still needs strict type/bounds/duplicate-key validation. No labels are restored.

Resume builds a new staged directory, copies the verified prefix, processes each remaining
observation exactly once, and publishes only a complete run. Output collisions preserve prior
bytes. A failed restore/replay leaves the checkpoint and prior runs intact. Prediction semantics
must match uninterrupted replay excluding elapsed timing; profiling must identify pre-checkpoint
and resumed populations/regions instead of fabricating one continuous wall-clock measurement.
Split context/reset/carry permission cannot be inferred from a checkpoint or opaque snapshot.

## Compatibility evidence and required future golden cases

`tests/pipeline/test_replay_contract.py` uses the real baseline through the existing Detector
protocol. Boundaries 1/8/12 cover warmup and saturated state: prefix + continued predictions equal
reset/full replay, with duplicate consumed timestamps rejected. Typed-double tests separately
check one factory per interleaved series, input order and no read-ahead after consumer termination.
These test the current fallback only; they do **not** validate checkpoint deserialization/resume.

Before implementing/approving resume, add real serializer/restore goldens for empty/warmup/full
history, interleaved series, offset-equivalent instants and chunk boundaries. Wrong version/model/
config/input/prefix/cursor, unknown/duplicate keys, bool counts, negative or oversized history,
NaN/Inf and duplicate/backwards times must fail without state mutation or published partial runs.
Corrupted-state/real-resume tests are **not run**, because no approved implementation exists.

## Owners, approval and exact next steps

1. Ayush reviews envelope, CLI compatibility, publication/profiling and rollback.
2. Manas reviews baseline state lifecycle/versioning; residual/calibration/forecast remain
   unsupported until each state producer and nested state version is reviewed explicitly.
3. Kaustubh reviews consumed-prefix order, cursor/input identity and feature-state implications;
   Mayank reviews complete artifact/evaluator compatibility, target masks and timing reporting.
4. Record actual approval references and any required ADR in DECISIONS before changing the shared
   contract. The user requested a proposal first and retained this approval gate.
5. Implement an approved baseline-only slice in the owning modules, run the goldens plus all
   README gates on its exact commit, and keep full replay as the explicit compatibility fallback.

Official update/chunk-context permission (Q04/Q08), input semantics (Q01/Q09), scorer/schema and
runtime rules remain unresolved. Synthetic persistence engineering would not establish official
permission or compliance. No organizer assets or public NAB data/labels were fetched.
