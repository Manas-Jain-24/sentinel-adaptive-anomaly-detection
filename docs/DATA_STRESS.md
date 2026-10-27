# KS-06 synthetic data/feature stress report

Owner: Kaustubh. Scope: synthetic software robustness only. Test implementation:
`tests/data/test_stress.py`, consuming the real inventory, splits, extractor and existing pipeline.
No real EDA, official scorer, hidden labels, accuracy claim or runtime/memory benchmark is included.
The tests use deterministic values and hand-derived invariants, not simulated benchmark scores.

## Executed cases and observed behavior

| Scenario | Synthetic setup | Verified result / limitation |
|---|---|---|
| Flat/short/extreme finite | Values -1e308, 0, +1e308; lengths 1/3/4/64; W=4, min_history=4, floor=0.01 | History capped at 4; exactly max(0,N-4) ready frames. Warmup expectations/scale are null; ready level stays constant, delta/expected_delta=0, scale=0.01. Finite constant medians do not overflow. |
| Unit rescaling | Gains 2, 1000, -3 and offsets -17, 500, 7 on a varied trace, W=4/min=3 | Level/seasonal reference transform by gain and offset; deltas by gain; scale by absolute gain while the floor is inactive. Negative gain also passes. |
| Floor-dominated units | Prior [0,2] versus [0,0.002], W=2/min=2, fixed floor=0.01 | Original scale=1.4826, rescaled scale=0.01 instead of 0.0014826. Fixed floors have units and break small-unit scale invariance. Configure a justified floor on permitted training data. |
| Contaminated warmup | [100,100,100,10,10,10,10,10], W=4/min=4 | Ready reference levels [100,55,10,10]; first ready scale=0.01, next=66.717. Majority contamination can define the baseline while ready=true. No anomaly/drift guard is implied. |
| Missing span | Four points at minutes 0,1,2,100 with values 10,11,12,13; declared cadence=60s | Inventory reports 1 gap interval/97 missing steps. Extractor emits four frames, last level=11/delta=1. It neither imputes points nor turns delta into a per-minute rate. |
| Season after gap | Same missing-span trace with fixed observation lag=3 | Last reference=10 is 100 minutes old. Observation lag no longer represents a 3-minute physical season. Cadence validity is a caller responsibility; no hidden gap correction is applied. |
| Long bounded state | Paired 4096-point replays with different first 32 values, W=8/min=8/P=8 | History_size never exceeds 8. After the shared suffix fills the window, every frame is identical. Only current frames are retained by this stress test; no RSS/latency number is claimed. |
| Interleaved series | Two 50-point series with different levels/patterns | Separate extractor instances match independent replay; existing public pipeline predictions also match independent replays, omitting elapsed timing. No global normalization/state coupling. |
| Frozen boundaries / future edit | N=40/cuts=16,28/L=4 under both carry and reset; edit validation suffix | Earlier training target frames remain identical; frozen inventory and split validation both reject changed source bytes. Causality and immutable provenance are separate checks. |

There are 22 parameterized stress cases. Existing KS-02 tests separately cover invalid constructor
types, reversed/duplicate/fold instants, other-series errors, float/integer arithmetic overflow,
failed-update recovery and seasonal unavailability. KS-03 tests cover group isolation, wrong
indices, empty partitions, weakened purge/context metadata, and source-backed artifact validation.

The gap scenario's final delta is a raw difference across 98 minutes. The seasonal lag selects the
third preceding observed point, not an interpolated timestamp. These are documented behavior,
not evidence that the algorithm handles irregular cadence or missing periods well. Official Q09
must resolve input semantics before choosing a real gap/time-based policy.

## Reproduction and scope

Executed on Windows/Python 3.12.14 with existing pinned dev dependencies; no new dependencies.
From installed repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/data/test_stress.py --basetemp outputs/pytest-ks06-initial
```

Result: 22 passed, exit 0. Each assertion checks public behavior or a hand-derived numeric result.
Use a fresh basetemp directory. Full-suite/lint/type/CLI and independent review results are recorded
in the personal task file and task-specific handoff after the phase completes. This report adds
tests/documentation; it adds no experimental detector, official adapter, shared contract or harness.

Disjoint finite example supports do not establish independent IID samples or independence of
long-lived model/calibration state. Consumers must use adequate effective lookback and reviewed
state/reset policies, keep context out of metrics, and freeze valid split digests before tuning.
Provenance and group relationships remain explicit operator assertions, not inferred permission.

## Actual official-data blockers

The user confirmed the intended intake location as
`C:\Users\HP\Desktop\EngimaxIota hackathon\data\official\` once the pack arrives, and stated it
currently holds only README.md. They supplied no authorized download link and no organizer Q01/
Q09 answer. The PDF identifies a starter-pack NAB subset but does not supply those details.
The supplied HP-machine path is absent on this host (read-only Test-Path returned false).
The current checkout also has only its official-data README. These are external blockers:

- KS-04 needs the actual pack, authorized input/development-label access, prescribed partitions
  and confirmed timestamp/cadence/column/missing-value semantics. Preserve raw bytes and separate
  truth when adapting them; do not silently assume raw UTC or copy public NAB labels.
- KS-05 needs KS-04 plus approved development data/labels to perform real EDA and train-only
  periodicity analysis. No real EDA figure/event count or EXP-01 result has been fabricated.

When those inputs arrive, create a new owned task branch from reviewed code, inventory the actual
assets and record source/permissions/checksums. Complete organizer sample-mapping tests before
claiming KS-04 done, then carry out KS-05 on frozen permitted training prefixes. The independent
software phases can be reviewed/integrated while these external tasks remain BLOCKED.
