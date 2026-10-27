# KS-03 frozen group and chronological splits

Owner: Kaustubh. Implementation: `src/sentinel/data/splits.py`; tests: `tests/data/test_splits.py`.
The separate `sentinel_split_v1` format is proposed for Ayush/Mayank consumer review. Existing
Observation/FeatureFrame/config/run.json formats are unchanged. No labels or model fitting enter
this tooling. Always honor actual organizer-prescribed partitions before defining local cuts.

## Strategies and reproducibility

`build_group_split(inventory, assignments, *, lookback=0)` maps every inventory group explicitly
to train/calibration/validation/test, requiring at least one train and one validation group.
Each related-source group remains wholly in one partition. Every series has one full-source raw
partition; the first lookback observations are context and the remainder targets. Missing/extra
groups, invalid partitions and empty target ranges fail. No random assignment occurs, so a random
seed is neither required nor invented. The operator freezes the mapping before model selection.

`build_chronological_split(inventory, cuts, *, lookback, past_context)` requires exactly one
ChronologicalCut(series_id, train_stop, calibration_stop) per series. Cuts are zero-based
per-series indices with exclusive stop: train [0,a), calibration [a,b), validation [b,N).
They must satisfy 0<a<b<N; bools/floats/negative indices and empty resulting ranges fail.
Chronological splits intentionally reuse the same series/group over time; they do **not** claim
group-held-out generalization. Use complete held-out groups for that claim. No default 60/20/20
or automatic label-dependent boundary selection is implemented.

All source paths/hashes, dataset/scope, declared groups/cuts and context policy are frozen in the
manifest. Arrays are sorted deterministically by group or series, with train/calibration/validation
ordering within a chronological series. `inventory_sha256` hashes canonical logical JSON of the
full inventory; `split_digest(manifest)` hashes canonical JSON of the full split (no self-reference).
Changing source bytes, provenance, grouping, cuts, lookback or context policy changes linkage/hash.

## Feature supports, context, and purging

Declare lookback L to cover the complete history used by each feature example. Target t consumes
support [t-L,t], including the current observation. For RollingFeatureExtractor set L>=window_size
(its seasonal lag is already bounded by window_size). Zero is useful only for point-only examples;
it does not certify a history-consuming model. Scored targets and context observations are distinct.

| Policy | Context/target behavior |
|---|---|
| reset | Warm up on [partition_start,partition_start+L); score [partition_start+L,partition_stop) |
| carry | Train warms on [0,L). Later partitions may use [partition_start-L,partition_start) as preceding context. Purge the preceding partition's final L targets so example supports do not overlap across boundaries. |

For N=30, cuts 12/22, L=3:

| Policy / partition | Raw partition | Context | Scored targets |
|---|---|---|---|
| carry / train | [0,12) | [0,3) | [3,9) |
| carry / calibration | [12,22) | [9,12) | [12,19) |
| carry / validation | [22,30) | [19,22) | [22,30) |
| reset / train | [0,12) | [0,3) | [3,12) |
| reset / calibration | [12,22) | [12,15) | [15,22) |
| reset / validation | [22,30) | [22,25) | [25,30) |

Under carry, training example supports end at index 8, calibration starts at 9 and ends at 18,
and validation starts at 19. They share no observations across partitions. Purged tails remain
visible as partition_stop-target_stop; they are not training/scoring examples. Under reset,
each support remains entirely inside its raw partition. Small segments that cannot satisfy the
policy fail rather than silently reducing lookback or allowing overlap.

For bounded feature replay, use a fresh extractor with matching W, feed the context first without
including its frames in metrics, then feed each target exactly once. Carry names permission to
read preceding context, not an unvalidated checkpoint/state transfer. Long-lived detector weights,
threshold calibration buffers or longer composed feature horizons need their own reviewed state/
fit policy and sufficient effective support. Disjoint feature windows do not make serial samples
statistically independent. No such detector-state independence is claimed here.

## API, serialized schema and validation

SplitManifest fields: schema_version, dataset_id, evaluation_scope, inventory_sha256, strategy,
lookback, past_context, group_assignments, cuts, ranges. GroupAssignment contains group_id and
partition. ChronologicalCut contains series_id/train_stop/calibration_stop. The inactive declaration
array is empty. Each SplitRange contains series_id, source_path, source_sha256, group_id, partition,
partition_start/stop, context_start, target_start/stop. All stops are exclusive; indices refer to the
series subsequence even when multiple series interleave in the CSV.

Builders consume an audited InventoryManifest. Before trusting serialized/external artifacts call
`validate_split_manifest(path, inventory_path, data_root)`: it validates the inventory against the
actual source bytes and recomputes every range from declarations. Unknown fields/types/versions,
duplicate JSON keys/declarations, stale inventory/source hashes and altered purge/context bounds
fail. Booleans cannot replace integer indices. This verifies consistency, not organizer permission
or that a declared model uses the correct horizon. Keep the reviewed digest frozen externally to
detect an intentional change of otherwise valid declarations; validation does not authenticate authors.

`write_split_manifest(manifest, path)` writes new-file deterministic ASCII JSON with LF newlines;
existing files remain untouched. No raw inputs are changed and no label files are loaded.
Contract errors use ContractError, missing files remain FileNotFoundError, and I/O errors are visible.

## Reproducible synthetic example

The committed [example](data/synthetic-fixture-split.json) uses the existing 16-point synthetic
fixture inventory, cuts 6/11 and L=2 with carry. Target ranges are [2,4), [6,9), [11,16). It is a
small-window software example for W=2/min_history=2, **not** the W=32 CLI starter configuration,
an official split, or evidence of generalization. From the installed repository root:

```powershell
@'
from pathlib import Path
from sentinel.data.inventory import validate_inventory
from sentinel.data.splits import (
    ChronologicalCut, build_chronological_split, validate_split_manifest,
    write_split_manifest, split_digest,
)
root = Path.cwd()
inventory_path = Path("docs/data/synthetic-fixture-inventory.json")
inventory = validate_inventory(inventory_path, root)
manifest = build_chronological_split(
    inventory, [ChronologicalCut("synthetic-demo", 6, 11)],
    lookback=2, past_context="carry",
)
output = Path("outputs/split-001.json")
output.parent.mkdir(parents=True, exist_ok=True)
write_split_manifest(manifest, output)
assert validate_split_manifest(output, inventory_path, root) == manifest
print(split_digest(manifest))
'@ | .\.venv\Scripts\python.exe -
```

Official partitions/data permissions remain blocked by Q01/Q09 and KS-04. Group sources and
relatedness are explicit operator assertions; no public NAB data or hidden labels were fetched.
Ayush/Mayank must review this format and fitting/context rules before experiment-harness adoption.
