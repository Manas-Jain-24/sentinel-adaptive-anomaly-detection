# KS-01 canonical-data inventory

Owner: Kaustubh. Status: proposed inventory format for review by Ayush and Mayank.
Implementation: `src/sentinel/data/inventory.py`; tests: `tests/data/test_inventory.py`.
This offline audit is separate from the shared Observation/FeatureFrame, config, and run.json
contracts. No existing producer or consumer has been migrated. Review the format before wiring
it into AY-01/MY-02/KS-03; incompatible future formats need a new inventory version.

## Scope and source declarations

Only the existing canonical CSV format is supported: `series_id,timestamp,value`, explicit UTC
offsets, finite values, nonempty series IDs, and strictly increasing timestamps per series.
Interleaving is allowed. The original file and row order are unchanged. Missing files, wrong
headers/column counts, empty inputs, duplicate instants (including different offsets for the same
instant), backwards timestamps, and NaN/Inf produce visible errors. There is no raw NAB adapter,
label loading, imputation, resampling, permission inference, or automatic source substitution.

Every SourceSpec requires:

| Field | Meaning |
|---|---|
| path | Normalized relative POSIX path, resolved under an explicit data root; escaping symlinks, absolute paths, backslashes and parent traversal are rejected |
| source | Nonempty source description/reference supplied by the operator |
| permission_basis | Nonempty access/use authorization reference supplied by the operator |
| group_id | Explicit related-source group for later split review; never inferred from a filename |
| expected_cadence_seconds | Positive finite cadence at whole-microsecond resolution, or null if unknown |

Dataset identity and evaluation scope are explicit. Supported scopes are `synthetic_smoke` and
`development_validation`; official/hidden scopes are unavailable. A declaration is an operator
assertion, not automatic proof that data is authorized or synthetic. Use the correct scope and
permission basis. A CSV may contain multiple series, all in the declared source group. Reusing a
file or a series ID across files fails; sharded series need a reviewed explicit aggregation policy.

## Manifest schema: sentinel_inventory_v1

The frozen InventoryManifest dataclass serializes as a JSON object with exactly:

| Field | Value |
|---|---|
| schema_version | `sentinel_inventory_v1` |
| dataset_id | Nonempty operator-assigned dataset/version ID |
| evaluation_scope | One supported scope above |
| sources | Nonempty array sorted by source path |

Each source has exactly `spec` (all SourceSpec fields), `sha256` (raw-byte SHA256), `size_bytes`,
`observations` (all rows), and `series` (sorted by series_id). Every series has exactly:

| Field | Meaning |
|---|---|
| series_id, length | Original series identifier and accepted finite-observation count |
| start, end | First/last instant normalized to UTC text ending in Z |
| value_min, value_max | Descriptive range of accepted finite values |
| cadence_min_seconds, cadence_median_seconds, cadence_max_seconds | Descriptive positive interarrival statistics; all null for a one-point series |
| gap_intervals | Count of intervals longer than declared cadence; null when cadence is unknown |
| off_grid_intervals | Count of intervals not an integer multiple of declared cadence; null when unknown |
| missing_steps | Sum of interval/cadence minus one when every interval is aligned; null if cadence is unknown or any interval is off grid |

For a one-point series with declared cadence, gap/off-grid/missing counts are zero. An interval
shorter than cadence is off grid. Off-grid intervals are reported without guessing an exact
missing-sample count. Exact interval arithmetic uses integer microseconds. Cadence may be declared
per file; heterogeneous-cadence series should be supplied as separate canonical files.

For example, four observations at 0, 1, 3, and 6 minutes give min/median/max interarrivals of
60/120/180 seconds. With declared cadence 60 seconds there are two gap intervals, three missing
steps, and zero off-grid intervals. Without declared cadence all three gap-related counts are null.

These whole-file statistics are descriptive inventory only. Never feed them into causal feature
scaling, seasonal period selection, detector calibration, or test-time fitting. Those operations
must use approved training prefixes/past observations under the existing architecture.

## API and reproducible fixture audit

`build_inventory(data_root, dataset_id, evaluation_scope, sources)` returns an immutable manifest.
`write_inventory(manifest, path)` writes deterministic sorted-key ASCII JSON with LF newlines to
a new file; an existing file is preserved. `validate_inventory(path, data_root)` reloads the JSON,
checks the schema, and re-audits every source to compare all bytes/counts/statistics. Duplicate JSON
keys, unknown fields, stale hashes/statistics, wrong JSON types, and unsupported versions fail.
Paths resolve under data_root, independently of the manifest file's location. Missing files raise
FileNotFoundError; invalid contracts raise ContractError; other I/O errors stay visible.

Run from the installed repository in PowerShell, choosing a fresh output path:

```powershell
@'
from pathlib import Path
from sentinel.data.inventory import SourceSpec, build_inventory, write_inventory, validate_inventory

root = Path.cwd()
manifest = build_inventory(
    root, "synthetic-fixture-v1", "synthetic_smoke",
    [SourceSpec(
        path="tests/fixtures/synthetic_stream.csv",
        source="Repository hand-authored fixture; tests/fixtures/README.md",
        permission_basis="Repository fixture supplied for synthetic software verification",
        group_id="synthetic-fixture",
        expected_cadence_seconds=60.0,
    )],
)
output = Path("outputs/inventory-001.json")
output.parent.mkdir(parents=True, exist_ok=True)
write_inventory(manifest, output)
assert validate_inventory(output, root) == manifest
print(output)
'@ | .\.venv\Scripts\python.exe -
```

The committed [fixture audit](data/synthetic-fixture-inventory.json) records 16 points of
`synthetic-demo`, UTC range 00:00 through 00:15 on 2026-01-01, 60-second cadence, values 9.9 to 15,
and zero declared-cadence gaps. This is synthetic software evidence, not an official NAB inventory
or anomaly-detection benchmark. Validate this example from the repository root using:

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; from sentinel.data.inventory import validate_inventory; print(validate_inventory(Path('docs/data/synthetic-fixture-inventory.json'), Path.cwd()))"
```

## Limits and integration

Audits read source bytes for a checksum before and after parsing, rejecting ordinary mid-audit
changes. Inputs must remain stable during the audit; this is not a filesystem snapshot or a
multiwriter protocol. Exact interval medians retain O(N) intervals for N observations; inference
does not import or execute this audit. No new dependency is required.

Official assets, their timestamp mapping, and actual access permissions remain unavailable.
KS-04 owns raw adaptation; real inventory follows only after those assets/answers arrive. No
shared contract approval, pipeline integration, split tooling, or official evaluation is claimed
by this change. Ayush should reconcile central progress records only after reviewing/merging it.
