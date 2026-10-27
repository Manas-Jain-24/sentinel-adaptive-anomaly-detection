# Sentinel Pulse

Causal, interpretable streaming anomaly detection for **Utkrishta 2026, Challenge 2: Sentinel**.
GitHub repository: [Manas-Jain-24/sentinel-adaptive-anomaly-detection](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection).
The foundation is published on `main`. The Python package and project name remain Sentinel Pulse.

**Status on this integration branch:** runnable MAD/z-score/residual detectors, optional
past-score quantile calibration, and reproducible profiled CLI replay, prepared for review.
Official dataset adaptation, official scoring/export and dashboard remain incomplete.
The organizer dataset, scoring code, submission schema, hardware limits, and deadline were not
provided. No official benchmark or hidden evaluation has been performed.

## Start here

- Humans and coding agents: [docs/START_HERE.md](docs/START_HERE.md).
- Agent rules: [AGENTS.md](AGENTS.md).
- Verified integrated state: [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md).
- Product: [PRD](docs/PRD.md); design: [architecture](docs/ARCHITECTURE.md).
- Shared types and formats: [interfaces](docs/INTERFACES.md).
- Work: [task board](tasks/TASK_BOARD.md); [developer prompts](tasks/AGENT_PROMPTS.md).
- Authoritative rules: [official PDF](<Utkrishta 2026 Participant Problem Statements.pdf>).

## Local setup

Python **3.11 or newer** and Git are required. Core processing uses the Python standard library;
development dependencies are pinned in `pyproject.toml`. No accounts, GPU, API key, database,
frontend, or network service is needed to execute the starter.

Windows PowerShell, from the repository root (activation is optional):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe scripts/check_repository.py
.\.venv\Scripts\python.exe -m sentinel run --input tests/fixtures/synthetic_stream.csv --config configs/starter.json --output-dir outputs/my-smoke-001 --dataset-id synthetic-fixture-v1 --scope synthetic_smoke
.\.venv\Scripts\python.exe -m sentinel evaluate --run-dir outputs/my-smoke-001 --windows tests/fixtures/synthetic_windows.json
```

On macOS/Linux, substitute `.venv/bin/python` for `.\.venv\Scripts\python.exe`.
Use a new output directory for every run; existing run artifacts are never overwritten.

This replays **16 synthetic points**, writes `predictions.jsonl` and `run.json`, then evaluates
the artificial event using **`provisional_event_trigger_f1_v0`**. A successful smoke result
proves software wiring only. It is neither the official metric implementation nor a NAB result.
Input timestamps must include an offset. Raw NAB CSV files need a documented adapter first.

## Select a detector

The original command/config still runs MAD. For another fixed-threshold detector, append
`--detector zscore` or `--detector residual` to `sentinel run`. Optional model settings use
a **separate** file; do not add model keys to `configs/starter.json`:

```powershell
.\.venv\Scripts\python.exe -m sentinel run --input tests/fixtures/synthetic_stream.csv --config configs/starter.json --model-config configs/residual-quantile.model.json --output-dir outputs/residual-quantile-001 --dataset-id synthetic-fixture-v1 --scope synthetic_smoke
.\.venv\Scripts\python.exe -m sentinel evaluate --run-dir outputs/residual-quantile-001 --windows tests/fixtures/synthetic_windows.json
```

`--detector` and `--model-config` are mutually exclusive. The supplied quantile example
requires 32 preceding **ready scores** before replacing its fallback threshold; the short
16-point fixture cannot fill that history. Longer synthetic tests exercise the empirical
path. Example settings prove software wiring and are not tuned competition parameters.
In a separate 96-point synthetic check, tied calibrated scores started an alert episode
before the spike; the provisional trigger metric counted TP/FP/FN=0/1/1. This is a known
configuration/metric interaction, not evidence for selecting quantiles over MAD.

`configs/residual-seasonal.model.json` demonstrates an explicit observation lag of four.
It is suitable only for a fixture with that declared lag, not inferred seasonality in real
data. Use only periods chosen from permitted past/training analysis. Missing cadence is
never imputed. Guards remain test-only, and unloaded Chronos/TimesFM models are not CLI choices.

Saved runs now identify the actual algorithm, resolved feature/calibration settings,
model hash and combined run-config hash alongside Ayush's provenance/profiling. The old
base-config hash keeps its original meaning. See [integration contract](docs/INTERFACES.md)
and the [integration proposal](docs/HANDOFFS/MN-03_manas_20261027T103208Z_cli-integration-proposal.md).
The optional split manifest remains an opaque checksum snapshot: it does not filter
partitions, validate membership/lookback, or exclude context from evaluation. Mayank's
harness must apply approved target/context policies before real split comparisons.

Run manifests also record Git revision/dirty state, resolved-config and environment hashes,
installed dependency versions, hardware, per-series workload, and timing populations. p50/p95
are bounded histogram upper estimates (less than 1/128 relative overestimate). Process timing
excludes construction and I/O; replay timing includes them. Cold timing means the first process
call per series, not interpreter startup. Final manifest write/publication is outside the recorded
prepublication duration. See [exact field and timing definitions](docs/INTERFACES.md).

Optionally append `--split-manifest path/to/manifest.json` to `sentinel run` to preserve and hash
an existing split file. The run stores its exact bytes in `split-manifest.snapshot`; this does
not validate split membership or pass split contents to the detector. Without the option, split
provenance is explicitly null. Dataset/scope remain operator assertions. Keep input files immutable
during replay; detected input changes fail without publishing artifacts.

## What exists

`src/sentinel/` contains typed contracts, strict canonical CSV ingestion, JSON config,
a causal rolling median/MAD starter, independent per-series state, CLI replay, numeric evidence,
checksummed run manifests, provenance/workload/timing distributions, and a provisional event
evaluator. Output publication
uses a temporary directory so input errors do not publish a partial run. Unit/integration tests,
synthetic fixtures, a repository checker, and a Windows/Linux CI definition are included.

Residual/seasonal scores and past-score quantiles are selectable on this branch. Promotion
to the competition candidate and any guarded adaptation require comparisons. See [delivery levels](docs/PRD.md) and
[experiment plan](docs/EXPERIMENT_PLAN.md). Warmup currently emits NORMAL with `ready=false`
and `score=null`; that is a documented internal convention awaiting organizer confirmation.

## Team

| Developer | Primary engineering ownership | Task file |
|---|---|---|
| Ayush | CLI, streaming orchestration, persistence, export, integration | [AYUSH](tasks/AYUSH.md) |
| Kaustubh | Dataset adaptation, causal features, split/provenance manifests | [KAUSTUBH](tasks/KAUSTUBH.md) |
| Manas | Detection baselines, residual scoring, thresholds, adaptation | [MANAS](tasks/MANAS.md) |
| Mayank | Event evaluation, experiment harness, result visualization/demo | [MAYANK](tasks/MAYANK.md) |

## Clone and collaborate

The foundation was pushed to the user-specified repository. Teammates can clone it:

```text
git clone https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection.git
cd sentinel-adaptive-anomaly-detection
```

Then follow local setup above and [START_HERE](docs/START_HERE.md). Use your own Git identity,
separate clone, and task branch such as `feat/manas/MN-01-zscore`; open PRs to `main`.
The repository owner still needs to arrange contributor permissions and desired branch protection;
invitations/protection have not been configured here. See [integration rules](tasks/INTEGRATION.md).
