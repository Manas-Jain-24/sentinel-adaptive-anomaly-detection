# Baseline detector methods (MN-01)

Both baselines implement the existing `Detector` v1.0 protocol. Each instance handles one
series, scores against its preceding observations, emits evidence, then appends the current
value. Histories contain at most `DetectorConfig.window_size` values. Labels never enter
inference. The following formulas describe software behavior, not detection-quality results.

| Detector | Pre-update baseline | Pre-update scale | Ready score / reason |
|---|---|---|---|
| `RollingMADStarter` in `rolling.py` | Median of preceding window | `max(1.4826 * median(abs(x - median)), scale_floor)` | `abs(value - median) / scale`; `rolling_mad_deviation` |
| `RollingZScoreDetector` in `zscore.py` | Arithmetic mean of preceding window | `max(sqrt(sum((x - mean)**2) / n), scale_floor)` | `abs(value - mean) / scale`; `rolling_z_deviation` |

The z comparator uses **population** standard deviation (`ddof=0`); its current observation
does not enter the mean or standard deviation until after the prediction. Standard-library
`statistics.mean` and `statistics.pstdev` avoid a naive sum/sum-of-squares overflow or
cancellation. Statistics are recomputed per point: O(W) time for z, O(W log W) for median/MAD,
and O(W) memory for either detector. These are algorithmic bounds, not runtime measurements.

`scale_floor` has the same units as the input value. It bounds the denominator for constant
or nearly constant histories. Both scores are finite nonnegative deviation magnitudes;
larger means more unusual. They are neither signed z values nor probabilities. The threshold
is in units of the selected detector's score; an identical numeric threshold does not imply
identical false-alarm behavior across the two methods.

Until there are `min_history` preceding values, the output is `ready=false`, `score=null`,
`label=NORMAL`, with reason `warmup`. A ready score equal to the configured threshold is
`ANOMALOUS`. Evidence includes the pre-update baseline, scale, signed residual, history size,
and the same score under `component_scores["level"]`. Timestamp/order/series errors reject
before updating. The z comparator also rejects nonfinite arithmetic without consuming the
observation; the caller must explicitly rescale an unrepresentable input stream.

All successful observations, including flagged values, enter history. Isolated spikes can
temporarily inflate the z scale. After a window of identical shifted values, either baseline
absorbs that shift and returns a zero score. This is an expected limitation pending MN-04
guard experiments, and is checked on synthetic traces without asserting sustained-fault recall.

## Programmatic integration

MN-01 adds a comparator through the existing factory boundary. Ayush owns CLI/config model
selection and run manifests: the current `sentinel run` and `run_file` still construct MAD
and write the MAD algorithm identity. Do not describe their artifacts as z-comparator runs.
The new comparator can already be passed to `process_stream`:

```python
from pathlib import Path

from sentinel.config import DetectorConfig
from sentinel.data.io import read_observations
from sentinel.detectors.zscore import RollingZScoreDetector
from sentinel.pipeline import process_stream

config = DetectorConfig(window_size=32, min_history=8, threshold=4, scale_floor=0.1)
for prediction, elapsed_ns in process_stream(
    read_observations(Path("tests/fixtures/synthetic_stream.csv")),
    lambda: RollingZScoreDetector(config),
    max_series=config.max_series,
):
    print(prediction, elapsed_ns)
```

Shared schemas, config fields, pipeline, and the MAD implementation are unchanged. The owned
tests check reference arithmetic, floors, threshold equality, warmup, eviction, causality,
immutable prefix evidence, reset/error recovery, isolated and sustained shifts, affine scale
behavior, per-series replay, extreme z arithmetic, and fixture serialization/evaluation.
The fixture evaluator is explicitly provisional; no official benchmark has run.
