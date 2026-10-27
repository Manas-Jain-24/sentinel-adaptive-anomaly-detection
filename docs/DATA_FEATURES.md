# KS-02 causal rolling features

Owner: Kaustubh. Implementation: `src/sentinel/data/features.py`; tests:
`tests/data/test_features.py`. Status: data-owned implementation proposed for Ayush/Manas review.
It implements the existing FeatureExtractor protocol and emits the unchanged FeatureFrame.
No shared config schema, CLI factory, detector, or run manifest is modified.

```python
from sentinel.contracts import FeatureExtractor
from sentinel.data.features import RollingFeatureExtractor

extractor: FeatureExtractor = RollingFeatureExtractor(
    window_size=32, min_history=8, scale_floor=0.1, seasonal_period=None
)
# Call once per new Observation; construct a separate instance for every series.
# frame = extractor.process(observation)
extractor.reset()
```

## Exact semantics

For observation t, history is the last at most W accepted values strictly before t. Ready means
at least min_history earlier values exist (2 <= min_history <= W). During warmup expected_level,
expected_delta and scale are null. Current delta is available after the first observation,
independently of readiness. Emission occurs before appending the current value.

| Frame field | Definition |
|---|---|
| series_id, timestamp | Original series ID and current instant normalized to UTC |
| history_size | Pre-update accepted history length, capped at W |
| expected_level | Median of prior history when ready |
| expected_delta | Median of adjacent differences within prior history (W-1 differences at capacity) when ready |
| scale | max(1.4826 * median absolute deviation around expected_level, scale_floor) when ready |
| delta | Current value minus immediately previous accepted value, or null on the first observation |
| seasonal_expected | Prior value at lag P when ready and at least P earlier observations exist; null when disabled/unavailable |
| ready | History length >= min_history; seasonal unavailability does not suppress readiness |

Hand trace with W=3 and min_history=2: at current 9 following [1,3], expected level=2, expected
delta=2, current delta=6, scale=1.4826. At current 7 following [1,3,9], expected level=3, expected
delta=4, current delta=-2, scale=2.9652. Only earlier observations affect the expectations.

Settings are validated constructor parameters owned by this implementation. Seasonal period is
an explicit integer from 1 through W, supplied from approved past/training analysis; no automatic
whole-trace period selection exists. min_history/window_size reject bools/nonintegers; scale_floor
must be finite and positive. There is no new shared config object. Before CLI/config adoption,
Ayush/Manas must review these settings and choose their shared configuration representation.

## Lifecycle, numerical behavior and limits

One instance rejects a different series and duplicate/backwards instants. Input timestamps are
normalized to UTC before comparison, including fold-aware clock changes. Accepted integer values
are normalized to floats before arithmetic. reset clears history, timestamp and series identity.
Every present feature is finite. Unsupported numerical magnitude
raises ContractError with a rescaling message before mutation, allowing retry at the same instant
with valid input. Median midpoint calculation avoids overflowing a finite constant baseline;
unrepresentable differences/MAD scales still fail visibly. No silent clipping is introduced.

History uses O(W) memory; recomputed medians cost O(W log W) per point. There is no global state,
label input, centered window, imputation, normalization fitted on futures, or hindsight revision.
Unsupervised updates include all accepted observations, including anomalies; contaminated warmup
or sustained faults can change the reference. Guard/adaptation policy remains Manas's work.

P counts **observations**, not elapsed time. After a missing span, the last observed value still
defines delta; it is not a rate per second. An observation lag can stop representing a physical
season after a gap. Inventory reports gaps separately; the extractor neither fills them nor
pretends seasonal cadence is valid. Disable period/use an explicitly reviewed gap policy when
time-based seasonality is required. These are engineering conventions awaiting official Q09.

KS-03's lookback must cover max(W,P) for ready feature examples (P is already <= W here).
Callers may replay explicitly permitted context before target observations; only target outputs
may enter partition metrics. Do not use the offline inventory's full-series statistics for fitting.
No official-data performance, detector integration approval, or benchmark is claimed by these tests.
