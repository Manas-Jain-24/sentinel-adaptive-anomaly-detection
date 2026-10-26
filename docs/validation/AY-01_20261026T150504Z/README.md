# AY-01 verification evidence

Synthetic software validation on macOS arm64/Python 3.12.14, 2026-10-26 UTC.
This is not official benchmark, hidden evaluation, real-data validation or performance evidence.

- [checks.json](checks.json): actual commands, exit codes and outputs for 43 pytest cases,
  Ruff lint/format, strict mypy, repository checker, dependency check and CLI help.
- [run.json](run.json), [predictions.jsonl](predictions.jsonl),
  [metrics.json](metrics.json), [split snapshot](split-manifest.snapshot): actual CLI output for
  the 16-point fixture with an opaque synthetic split. Source revision is `d7158d6...` with
  dirty=true because these artifacts were collected before the AY-01 implementation commit.
  That revision identifies the committed base, not the uncommitted implementation.
- [baseline-predictions.jsonl](baseline-predictions.jsonl): pre-change foundation predictions.
  All 16 rows equal the new plain/split-run rows after excluding elapsed_ns. Timing and checksums
  containing elapsed_ns are intentionally nondeterministic. Provisional counts are TP=1, FP=FN=0.

Setup used the bundled Python 3.12.14 to create `.venv`, then installed exactly the existing
`.[dev]` requirements. Initial network-restricted installation/fetch failed; permitted network
retries succeeded. No dependency was added or changed. Baseline checks passed all 24 existing
tests, lint, formatting, strict typing, repository checks and pip check before implementation.
The initial new-test run passed 19 cases; Ruff found long lines, which were corrected/formatted
before the recorded full checks. The PDF was read with bundled pypdf without editing it.

Actual smoke commands (all exited 0, from repository root):

```text
.venv/bin/python -m sentinel run --input tests/fixtures/synthetic_stream.csv --config configs/starter.json --output-dir outputs/ay01-validation-20261026T145042Z/baseline --dataset-id synthetic-fixture-v1 --scope synthetic_smoke
.venv/bin/python -m sentinel evaluate --run-dir outputs/ay01-validation-20261026T145042Z/baseline --windows tests/fixtures/synthetic_windows.json
.venv/bin/python -m sentinel run --input tests/fixtures/synthetic_stream.csv --config configs/starter.json --output-dir outputs/ay01-validation-20261026T145042Z/replay --dataset-id synthetic-fixture-v1 --scope synthetic_smoke
.venv/bin/python -m sentinel evaluate --run-dir outputs/ay01-validation-20261026T145042Z/replay --windows tests/fixtures/synthetic_windows.json
.venv/bin/python -m sentinel run --input tests/fixtures/synthetic_stream.csv --config configs/starter.json --output-dir outputs/ay01-validation-20261026T145042Z/split-replay --dataset-id synthetic-fixture-v1 --scope synthetic_smoke --split-manifest outputs/ay01-validation-20261026T145042Z/split.json
.venv/bin/python -m sentinel evaluate --run-dir outputs/ay01-validation-20261026T145042Z/split-replay --windows tests/fixtures/synthetic_windows.json
```

The baseline was run before editing source. To reproduce the new run on another machine,
choose a fresh output directory and supply the preserved split-manifest.snapshot as the optional
split file. Old directories must not be reused. Run the README checks first. Installed environment
and hardware are recorded in run.json; timings here describe only this tiny fixture and must not
be promoted to a runtime benchmark. No Windows/Linux/CI execution is claimed for AY-01.
