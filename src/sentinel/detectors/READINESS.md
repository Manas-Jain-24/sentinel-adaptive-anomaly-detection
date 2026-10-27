# Remaining Manas work and promotion gates

This note describes detector-owned preparation. It does not supersede Ayush's central
records or authorize changing the shared CLI/contracts or official-data intake.

## MN-04: synthetic policy diagnostic

Run from the repository root, choosing a fresh output directory:

```powershell
.venv/Scripts/python.exe tests/detectors/guard_study.py --output-dir outputs/mn04-study-001
```

The test-only reference prototype compares none/capped influence/finite quarantine/
shadow rebaseline with both fixed and prior-score quantile thresholds. There are seven
predeclared 256-point scenarios: stable, isolated spike, sustained fault, benign step,
benign ramp, variance burst and contaminated warmup. Configurations are fixed in
`StudyConfig`; there is no search or label-driven online decision. Raw synthetic values,
event ranges, every prediction and action, source hashes, revision/dirty status, metric
identity and environment are recorded in a new report. No public NAB data/labels are read.

The baseline is the actual residual implementation and calibration logic. For this
diagnostic W=32, min_history=8, scale floor=.1, fixed/fallback threshold=4, C=64,
minimum score history=16, q=.99, and quantile floor=4. This larger floor is a fixed study
choice, not the general calibrator default or a tuned final parameter.

- **None:** admit each raw value and score after the decision.
- **Capped:** clip each ready value into prior baseline +/- 3 prior scales and cap its
  calibration contribution at 3. Prediction still uses the original current value/score.
- **Finite quarantine:** exclude flagged values/scores for at most eight successive
  observations; admit the ninth and reset the streak. Normal observations admit/reset.
- **Shadow:** finite quarantine plus an eight-observation raw shadow. After eight
  consecutive withheld flags, adopt its median-shifted, low-MAD reference if its spread
  is at most the current reference scale and separation is at least threshold*scale.
  The current decision stays unchanged; clear calibration for subsequent observations.

To avoid modifying Kaustubh's process-and-update feature API, the prototype reconstructs
the extractor from its bounded admitted history per point. Delta is between admitted
observations, including across quarantine gaps. This is deliberately a **test prototype**,
not a production guard, runtime benchmark or alternative experiment harness. Production
adoption needs a reviewed explicit update boundary covering both feature and calibration
state, not a monkeypatch of teammate private fields.

The study uses the existing `provisional_event_trigger_f1_v0`, never the official metric.
Report event counts/delay with flagged event-point counts and alert lengths: event recall
alone can credit a fault that is detected once and then absorbed. A benign step and the
sustained fault have identical values but different synthetic interpretations, illustrating
why an unsupervised shift signal cannot establish whether a change is safe to learn.

Finite-release tests bound consecutive exclusion; prefix/reset checks enforce causal
decisions. A rollback test disables the prototype policy, clears selective state and
replays the raw stream, reproducing no-guard predictions exactly. Production keeps the
existing no-guard path. No policy is promoted without authorized paired data and gates.

## MN-05: prepared software, blocked experiments

The interval wrapper in `forecast.py` provides causal score arithmetic, frozen one-step/
block contexts and existing-schema evidence. Deterministic fake models test the boundary;
they are not Chronos/TimesFM performance results. Provider adapters and actual model runs
must identify model/library revisions and terms, workload/hardware, cold/warm cost, and
the forecast origin/age. Optional dependencies remain outside the base installation.

Required next inputs: MY-02 shared experiment harness; official starter adapter (KS-04);
authorized labels, overlap permissions, prescribed partitions and timestamp/cadence
semantics; named local/official metric; online-update and pretraining permissions.
Then run EXP-01, component/calibration/guard ablations and the separately proposed
Chronos/TimesFM comparisons with frozen configs and paired series results. Do not fit
on hidden windows or treat the downloaded public NAB reference as the organizer pack.
No candidate can be frozen on the current software-only checks.

## MN-06: preliminary gate decision is NO-GO

Level A official adapter/scorer/export/warmup mapping is incomplete and measured Level B
comparisons do not exist. The documented S1 gate therefore prevents EVT fitting now.
Synthetic tail counts can expose degeneracy but cannot establish real tail sufficiency,
stationarity, independent samples or a quality gain. At C=256 and q=.99 the nominal
upper one-percent mass is only 2.56 observations before ties/dependence; this is not a
tail-fit sample-size guarantee. Actual permitted series/tail counts remain unknown.

No EVT library was selected, installed or license/build tested; these checks are not
passed. No fit, SPOT/DSPOT result, performance number or completed feasibility spike is
claimed. Keep MN-06 BLOCKED until A/B gates pass. Reassess tail support and fit stability
then, using the existing >=.01 improvement and B recall/runtime gates; stop on sparse or
unstable tails or unmet build/terms constraints. No mandatory dependency is justified now.
