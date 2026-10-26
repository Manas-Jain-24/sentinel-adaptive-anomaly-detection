# Residual detector composition (MN-02)

`residual.ResidualDetector` consumes the existing `FeatureExtractor` protocol and returns
the existing `Prediction`/`Evidence` types. No data implementation, shared type, config field,
CLI selector, mandatory dependency, adaptive threshold or drift guard is introduced here.

For a ready frame from observation t, use the positive denominator
`s = max(frame.scale, config.scale_floor)` and compute:

| Component | Magnitude |
|---|---|
| `level` | `abs(value - expected_level) / s` |
| `change` | `abs(delta - expected_delta) / s` |
| `seasonal`, only when enabled and available | `abs(value - seasonal_expected) / s` |

The combined score is the **maximum** of the available component magnitudes. It is a finite,
nonnegative deviation score; it is not a probability or a calibrated false-alarm rate. Label
ANOMALOUS when the score is greater than or equal to the fixed `config.threshold`. MN-03
will implement prior-score calibration separately, with the combined score as its input.

All denominators have input-value units. The current delta is a difference between adjacent
observed values, also in value units; it is not divided by elapsed time. Comparable units do
not imply identical distributions or the same false-alarm rate across components. Adding a
component can increase flags. A matching seasonal forecast cannot veto a high level/change
score in this fixed maximum. Do not claim this design reduces periodic false positives
without a separate permitted experiment.

## Readiness, settings and optional seasonality

The injected extractor owns windowing and readiness. A ready frame must contain at least two
preceding observations, finite expected level/delta, current delta, and a positive scale.
During warmup the detector emits NORMAL/ready=false/score=null, empty component scores, and
reason `warmup`. Optional finite expectations may be shown as a warmup baseline; no warmup
residual is scored. Warmup mapping to the official output schema remains unresolved.

The wrapper reads only `DetectorConfig.threshold` and `scale_floor`; configuration's window
and minimum-history settings belong to the extractor factory, and max_series to the router.
Construct matching feature settings explicitly. An extractor's higher scale floor cannot be
lowered by the detector's floor. Nothing updates thresholds or fits a seasonal period here.

Seasonality defaults to **disabled** (`use_seasonal=False`). When explicitly enabled but the
frame has no seasonal reference, continue scoring level/change at the same readiness and
append `seasonal=unavailable` to the reason. Include the seasonal branch as soon as the
extractor supplies a finite reference. Choose any period using permitted past/training data
and record it in the eventual reviewed run configuration. A sample lag after a cadence gap
does not automatically represent a physical season; there is no silent resampling.

## Evidence without a shared schema change

Evidence baseline/scale/residual contain expected level, effective scale, and signed level
residual. `component_scores` holds only the normalized nonnegative magnitudes named above.
The combined score can be reproduced as their maximum. The existing free-text `reason`
includes each actual arithmetic expression, retaining the delta expectation/current delta
and optional seasonal reference without adding unreviewed fields to Evidence.

For value 16, level expectation 10, current/expected delta 5/1 and scale 2:

```text
baseline=10, scale=2, residual=6
component_scores={level: 3, change: 2}, score=3
reason=residual_max: max(level=abs(16.0 - 10.0) / 2.0, change=abs(5.0 - 1.0) / 2.0)
```

The reason is display text rather than a new structured parsing contract. Consumers should
use the existing numeric fields for machine calculations. A future structured per-component
reference/residual extension needs normal Ayush/affected-owner approval. Evidence describes
the actual computation; it does not identify a physical root cause.

## Lifecycle and failure behavior

Each detector exclusively owns one extractor instance. Constructor/reset calls the extractor's
reset; do not share it between detectors or inject a populated instance expecting state to
survive construction. Each valid new observation calls process exactly once. The wrapper
normalizes UTC instants before order checks, including same-zone clock folds. Wrong series
and duplicate/backwards instants reject before calling the extractor and leave it usable.

The extractor must calculate expectations from strictly preceding values. It may update its
own state before returning the frame; the wrapper scores only that immutable past-based frame.
The wrapper checks identity/readiness/numeric consistency before emitting predictions.

If the extractor raises, returns an invalid frame, or the resulting residual/score overflows,
the wrapper **requires reset and replay** before processing further points. No prediction is
emitted. v1 has no extractor checkpoint/rollback method, so retrying only the failed point
could mix advanced and stale state. reset also clears the wrapper's series/time/failure state.
Unexpected programming exceptions remain visible. Rescale unrepresentable input explicitly;
never clip or replace invalid values with successful predictions.

The wrapper retains O(1) state and computes at most three residuals per point. Overall
history, adaptation policy and time complexity belong to the injected extractor. KS-02
uses bounded history and includes all accepted observations, including anomalies; sustained
faults can therefore change the baseline. Guarded update control under MN-04 may need a
separately reviewed feature-update interface; this wrapper does not silently add one.

## Programmatic factory after KS-02 is available

KS-02 is published in a separate unmerged PR. The following example requires its module to
be present in the same checkout; this task does not copy or merge that implementation:

```python
from sentinel.config import DetectorConfig
from sentinel.data.features import RollingFeatureExtractor
from sentinel.detectors.residual import ResidualDetector

config = DetectorConfig(window_size=32, min_history=8, threshold=4, scale_floor=0.1)

def factory() -> ResidualDetector:
    return ResidualDetector(
        config,
        RollingFeatureExtractor(
            window_size=config.window_size,
            min_history=config.min_history,
            scale_floor=config.scale_floor,
            seasonal_period=None,
        ),
        use_seasonal=False,
    )

# process_stream(observations, factory, max_series=config.max_series)
```

The current CLI/run_file still construct MAD and write its algorithm identity. Ayush owns any
model-selection and run-metadata extension; do not label their artifacts as residual runs.
Independent MN-01 z-score work remains in its own review branch. This branch starts from main.

## Verification scope

The 69 deterministic-frame tests cover known arithmetic, each winning component, missing
seasonality, scale floors, readiness, threshold equality, finite output, malformed frames,
exactly-once calls, failure/reset behavior, UTC folds, immutable prefixes and interleaving.
Another 13 compatibility tests cover the published real KS-02 extractor, including direct
MAD level-score parity and a missing synthetic peak. They run automatically once KS-02 is
importable and are explicitly skipped as a module in the independent branch otherwise.
All inputs are synthetic; no official detection-quality experiment or period fitting ran.
