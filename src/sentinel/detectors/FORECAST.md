# Forecast interval detector: MN-05 software preparation

`ForecastIntervalDetector` accepts an injected `QuantileForecaster`; it does not load,
download, train, or benchmark Chronos or TimesFM. No provider adapter or optional model
dependency has been installed by this change. Real model comparisons remain blocked.
The prior EXP-12 plan is published on `feat/manas/MN-05-foundation-models` at
`6a957fb4186ca125a92122f302e8c93fccaa2182`; its shared-document proposals are not silently
treated as approved configuration or merged architecture.

## Arithmetic and causal order

1. Retain at most `context_window` preceding values for this series. During the first
   `min_history` observations emit the shared score-null, NORMAL, not-ready convention.
2. Before admitting the current value, call `forecast(tuple(past), horizon)` when a
   refresh is due. It returns exactly `horizon` `ForecastInterval(lower, median, upper)`
   objects for q10, q50, q90 in original units, ordered by future observation index.
3. Freeze the result. For the selected point, let width=q90-q10 and
   scale=max(width, scale_floor). Emit
   `max(0, q10-y, y-q90) / scale`. Equality with the fixed threshold flags an anomaly.
4. Only after building the prediction append the actual value and advance block age.

The score is an interval-exceedance magnitude, not a probability. Values inside either
endpoint score zero; a zero-width forecast uses the positive floor. Evidence uses the
existing baseline=q50, scale=effective interval width, residual=y-q50, and component
`interval_exceedance`. Reason text records all three quantiles, width, formula, origin
timestamp, age in points, horizon and stride. No shared schema fields were added.

Stride 1 refreshes the full horizon for every ready observation and uses its first
interval. Stride=horizon consumes a frozen block; observations during the block cannot
revise its remaining forecasts. Age counts observations, not elapsed time. Irregular
cadence is not converted to a regular grid. Any model requiring regular cadence needs
an explicitly approved adapter/intake policy. The current value is absent from the
model context for its own decision, including at the initial ready observation.

## Lifecycle and validation

One detector handles one ordered series. Context and blocks are private; model weights
may be shared only if the adapter is inference-only and keeps no mutable per-series
state. A model must not retain mutable contexts, fit on validation/test futures, or fetch
labels. The wrapper cannot inspect or undo adapter side effects or hidden fitting.

Reset clears context, sequence, forecasts and failure status. It does not reset/refit
the external model. Order/series errors reject before a call and preserve context.
Model errors, wrong output count/type and scoring overflow require reset plus full
replay; programming errors propagate. Intervals reject nonfinite/inverted quantiles
and overflowed width. All current shared Prediction/Detector contracts are preserved.

A frozen block also has a refresh phase. Restarting from a short context can shift
that phase even when the value history is sufficient. Generic W+C lookback is not a
continuation guarantee for block forecasts. Until a reviewed state/origin protocol
exists, replay from the original series start to reproduce block origins exactly;
do not claim partition parity merely from ready=true or enough feature context.

The wrapper stores O(context_window+horizon) values, excluding model memory. It calls
the model synchronously; time/memory and cold compilation/download costs are unmeasured.
`CalibratedDetector` can wrap this detector to calibrate combined interval scores from
their past. That optional composition is tested; it is not an approved model selection.

## Proposed use for owner review

```python
from sentinel.detectors.forecast import ForecastDetectorConfig, ForecastIntervalDetector

# adapter is an already-loaded inference-only implementation of QuantileForecaster.
detector = ForecastIntervalDetector(
    ForecastDetectorConfig(context_window=64, min_history=16, horizon=8, refresh_stride=8),
    adapter,
)
```

Ayush reviews CLI/factory/settings and exact algorithm metadata before persisting model
runs. Mayank's harness must compare identical approved partitions, warmup and metric.
Manas supplies reviewed provider adapters with pinned model/library revisions, model
terms, evidence, CPU/GPU/runtime checks, and real paired error examples. Model downloads,
provider API parity, performance and permission checks have **not** been performed here.
