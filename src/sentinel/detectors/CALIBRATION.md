# Prior-score empirical threshold (MN-03)

`thresholds.PriorScoreQuantile` chooses a threshold from the preceding valid scores, creates
the current decision, then stores the current score in a bounded buffer. It accepts only finite,
nonnegative magnitudes. No labels, future scores, probability conversion or outlier exclusion
enter this component. It can be used independently before a specific detector is selected.

## Exact threshold rule

For n preceding scores, calibration capacity C, minimum score count M and quantile q:

1. If n<M, use the configured fixed fallback.
2. Otherwise sort the preceding scores and select one-based rank `max(1, ceil(q*n))`.
3. Apply `max(selected_score, threshold_floor)` to keep the threshold strictly positive.
4. Flag the current score when `score >= threshold`, then append it, evicting the oldest
   stored score when the C-score buffer is full.

Nearest rank uses q's decimal string with exact rational rank arithmetic. Thus q=0.07/n=100
selects rank 7, even though direct float multiplication can produce 7.000000000000001.
q=0 selects the minimum and q=1 the maximum. No interpolation or sum of large score values
is required. Threshold queries are read-only; reset clears the buffer.

For preceding scores [1,2,3], q=0.5 selects threshold 2. A current score of 100 is compared
with 2; it can affect the next threshold only after that decision has been constructed.

## Local configuration

`QuantileThresholdConfig` is a frozen Manas-owned settings object, not an extension of the
shared CLI JSON parser. All fields can be recorded with to_dict() for later reviewed manifests.

| Field | Default | Semantics |
|---|---|---|
| window_size | 256 | Calibration score capacity C, not the feature window |
| min_history | 32 | Minimum preceding valid scores M; require 1<=M<=C<=sys.maxsize |
| quantile | 0.99 | q in [0,1], interpreted via its decimal string |
| fallback_threshold | 4.0 | Used only while n<M; it is not a lower bound on empirical thresholds |
| threshold_floor | 1e-6 | Positive minimum in score units; require floor<=fallback |

The threshold floor has score units. DetectorConfig.scale_floor has input-value units; the
two settings are distinct. Bool/string/nonfinite/invalid settings and scores fail explicitly.
An invalid standalone score leaves the calibrator unchanged and can be retried.

At q=0.99 and n=32, nearest rank selects the sample maximum. Limited history, serial dependence,
contamination and ties prevent a nominal 1% false-alarm guarantee. All positive constant scores
can flag under the shared inclusive equality rule. Zero-score constant history remains NORMAL
because its empirical threshold is floored above zero. Flagged scores enter the buffer too;
high contamination can raise future thresholds until it expires. Guard policy remains MN-04.

## Detector adapter and evidence

`calibrated.CalibratedDetector` wraps any v1 Detector. It preserves the raw score, readiness and
numerical evidence, replaces threshold/label consistently, copies component evidence, and adds
calibration method/prior count/q/rank/window/minimum/floor to the existing reason text.
Evidence.history_size remains the base feature-history count, not calibration history.

Base feature warmup remains score=null/NORMAL/ready=false and contributes no calibration
sample. A valid base score is ready even before M preceding scores exist; the fallback is
used for that period. Intermittent warmup does not erase earlier scores or enter the buffer.
Each series must have its own base detector and calibrator; constructor/reset clears both.

The wrapper rejects invalid base predictions instead of hiding their contract violations.
After a base call starts, any base/validation/scoring failure requires reset and full replay:
the shared Detector protocol provides no rollback. Wrong-series/duplicate/backwards instants
are caught before calling the base and preserve an otherwise healthy wrapper. UTC comparison
and output normalization occur at the wrapper boundary. Programming exceptions stay visible.

The existing reader/replay/serializer/provisional evaluator accept the resulting Prediction
without a shared schema change. CLI/run_file still run and identify the original MAD starter.
Ayush owns any model-selection/config/run-metadata adoption; a calibrated run needs both base
and calibration settings plus the correct algorithm identity, rather than a MAD-only manifest.

```python
from sentinel.config import DetectorConfig
from sentinel.detectors.calibrated import CalibratedDetector
from sentinel.detectors.rolling import RollingMADStarter
from sentinel.detectors.thresholds import PriorScoreQuantile, QuantileThresholdConfig

base_config = DetectorConfig()
calibration_config = QuantileThresholdConfig()

def factory() -> CalibratedDetector:
    return CalibratedDetector(
        RollingMADStarter(base_config),
        PriorScoreQuantile(calibration_config),
    )

# process_stream(observations, factory, max_series=base_config.max_series)
```

MN-02's residual detector can occupy the same base slot once its branch is reviewed/integrated.
The adapter calibrates its combined maximum score; it does not independently calibrate branches
and assume their maximum retains an alarm rate. The pinned compatibility tests exercise the real
published MN-02 residual and KS-02 features without copying those implementations into this branch.

## Effective support and verification limits

Calibration retains O(C) scores and sorts at query time in O(C log C). The wrapper adds base
processing, finite-field checks, evidence copying and metadata formatting. A bounded W-point
feature model plus C preceding scores may require W+C preceding raw observations to reproduce
full state after both buffers saturate. The combined model needs this composed support, not
max(W,C). Tests demonstrate W=4/C=3 continuation with seven points and a mismatch with four.
Intermittent readiness or fitted/guarded state can require a different reviewed context policy.

The synthetic 16-point fixture with test settings C=3/M=2/q=1/floor=0.01 produces provisional
TP/FP/FN=1/1/0: the original spike flags, and a later normal score equals its learned threshold
and flags too. An initial test incorrectly expected zero false positives; inspection reproduced
the tie and the regression now asserts the actual behavior. No operator or comparison rule was
changed to hide that result. This is software evidence, not an official F1 or promotion result.

No organizer dataset, authorized development labels, prescribed partitions, timestamp/cadence
answers or official scorer were supplied here. The problem PDF references a starter-pack NAB
subset but has no download link. Real threshold selection and detection-quality comparison remain
blocked until those inputs arrive. No public NAB data or hidden labels were substituted.
