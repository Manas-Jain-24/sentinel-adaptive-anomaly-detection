"""Deterministic, label-free split manifests linked to canonical inventories."""

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, cast

from sentinel.contracts import ContractError, EvaluationScope
from sentinel.data.inventory import (
    INVENTORY_VERSION,
    InventoryManifest,
    SeriesInventory,
    SourceInventory,
    validate_inventory,
)

SPLIT_VERSION = "sentinel_split_v1"
Partition = Literal["train", "calibration", "validation", "test"]
PastContext = Literal["reset", "carry"]
Strategy = Literal["group_holdout", "chronological"]
_PARTITIONS = ("train", "calibration", "validation", "test")


def _text(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name} must be a nonempty string")


def _lookback(value: int) -> None:
    if type(value) is not int or value < 0:
        raise ContractError("lookback must be a nonnegative integer")


def _partition(value: object) -> Partition:
    if not isinstance(value, str) or value not in _PARTITIONS:
        raise ContractError(f"Unsupported partition: {value!r}")
    return cast(Partition, value)


@dataclass(frozen=True)
class GroupAssignment:
    group_id: str
    partition: Partition


@dataclass(frozen=True)
class ChronologicalCut:
    series_id: str
    train_stop: int
    calibration_stop: int

    def __post_init__(self) -> None:
        _text(self.series_id, "series_id")
        if type(self.train_stop) is not int or type(self.calibration_stop) is not int:
            raise ContractError("Chronological cuts must be integer indices")
        if not 0 < self.train_stop < self.calibration_stop:
            raise ContractError("Require 0 < train_stop < calibration_stop")


@dataclass(frozen=True)
class SplitRange:
    series_id: str
    source_path: str
    source_sha256: str
    group_id: str
    partition: Partition
    partition_start: int
    partition_stop: int
    context_start: int
    target_start: int
    target_stop: int


@dataclass(frozen=True)
class SplitManifest:
    schema_version: str
    dataset_id: str
    evaluation_scope: EvaluationScope
    inventory_sha256: str
    strategy: Strategy
    lookback: int
    past_context: PastContext
    group_assignments: tuple[GroupAssignment, ...]
    cuts: tuple[ChronologicalCut, ...]
    ranges: tuple[SplitRange, ...]


def _canonical(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"


def _digest(payload: object) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _series_index(inventory: InventoryManifest) -> list[tuple[SourceInventory, SeriesInventory]]:
    """Builders consume an already audited inventory; loading verifies its sources."""
    if inventory.schema_version != INVENTORY_VERSION:
        raise ContractError("Unsupported inventory version")
    _text(inventory.dataset_id, "dataset_id")
    if inventory.evaluation_scope not in ("synthetic_smoke", "development_validation"):
        raise ContractError("Unsupported inventory scope")
    result = []
    seen_series: set[str] = set()
    seen_paths: set[str] = set()
    for source in sorted(inventory.sources, key=lambda item: item.spec.path):
        if source.spec.path in seen_paths:
            raise ContractError("Duplicate inventory source")
        seen_paths.add(source.spec.path)
        if not source.series:
            raise ContractError("Inventory source has no series")
        for series in sorted(source.series, key=lambda item: item.series_id):
            if series.series_id in seen_series:
                raise ContractError("Duplicate inventory series")
            if type(series.length) is not int or series.length < 1:
                raise ContractError("Inventory series length must be a positive integer")
            seen_series.add(series.series_id)
            result.append((source, series))
    if not result:
        raise ContractError("Inventory has no series")
    return sorted(result, key=lambda item: item[1].series_id)


def _range(
    source: SourceInventory,
    series: SeriesInventory,
    partition: Partition,
    partition_start: int,
    partition_stop: int,
    context_start: int,
    target_start: int,
    target_stop: int,
) -> SplitRange:
    if not 0 <= context_start <= target_start < target_stop <= partition_stop <= series.length:
        raise ContractError(f"Invalid or empty target range for {series.series_id}/{partition}")
    return SplitRange(
        series.series_id,
        source.spec.path,
        source.sha256,
        source.spec.group_id,
        partition,
        partition_start,
        partition_stop,
        context_start,
        target_start,
        target_stop,
    )


def build_group_split(
    inventory: InventoryManifest,
    assignments: Mapping[str, Partition],
    *,
    lookback: int = 0,
) -> SplitManifest:
    """Hold out complete explicit source groups; no random allocation or label use."""
    _lookback(lookback)
    index = _series_index(inventory)
    expected_groups = {source.spec.group_id for source, _ in index}
    if not isinstance(assignments, Mapping) or set(assignments) != expected_groups:
        raise ContractError("Group assignments must cover exactly the inventory groups")
    mapped = {group: _partition(value) for group, value in assignments.items()}
    if not {"train", "validation"} <= set(mapped.values()):
        raise ContractError("Group holdout requires nonempty train and validation partitions")
    ranges = tuple(
        _range(
            source,
            series,
            mapped[source.spec.group_id],
            0,
            series.length,
            0,
            lookback,
            series.length,
        )
        for source, series in index
    )
    return SplitManifest(
        SPLIT_VERSION,
        inventory.dataset_id,
        inventory.evaluation_scope,
        _digest(asdict(inventory)),
        "group_holdout",
        lookback,
        "reset",
        tuple(GroupAssignment(group, mapped[group]) for group in sorted(mapped)),
        (),
        ranges,
    )


def build_chronological_split(
    inventory: InventoryManifest,
    cuts: Sequence[ChronologicalCut],
    *,
    lookback: int,
    past_context: PastContext,
) -> SplitManifest:
    """Freeze train/calibration/validation ranges with disjoint example support.

    Each target t uses observations [t-lookback,t]. Reset warms inside each raw
    partition. Carry reserves prior context and purges the preceding partition's
    final lookback targets so those examples cannot overlap the next support.
    Indices are per-series zero-based, with exclusive stop, never CSV line numbers.
    """
    _lookback(lookback)
    if past_context not in ("reset", "carry"):
        raise ContractError("past_context must be explicitly reset or carry")
    index = _series_index(inventory)
    if any(not isinstance(cut, ChronologicalCut) for cut in cuts):
        raise ContractError("cuts must contain ChronologicalCut declarations")
    by_id = {cut.series_id: cut for cut in cuts}
    if len(by_id) != len(cuts) or set(by_id) != {series.series_id for _, series in index}:
        raise ContractError("Cuts must cover every inventory series exactly once")
    ranges = []
    for source, series in index:
        cut = by_id[series.series_id]
        if cut.calibration_stop >= series.length:
            raise ContractError("calibration_stop must leave validation observations")
        segments: tuple[tuple[Partition, int, int], ...] = (
            ("train", 0, cut.train_stop),
            ("calibration", cut.train_stop, cut.calibration_stop),
            ("validation", cut.calibration_stop, series.length),
        )
        for partition, start, stop in segments:
            target_start, target_stop, context_start = start + lookback, stop, start
            if past_context == "carry":
                target_start = lookback if start == 0 else start
                context_start = target_start - lookback
                if partition != "validation":
                    target_stop -= lookback
            ranges.append(
                _range(
                    source, series, partition, start, stop, context_start, target_start, target_stop
                )
            )
    return SplitManifest(
        SPLIT_VERSION,
        inventory.dataset_id,
        inventory.evaluation_scope,
        _digest(asdict(inventory)),
        "chronological",
        lookback,
        past_context,
        (),
        tuple(by_id[name] for name in sorted(by_id)),
        tuple(ranges),
    )


def split_digest(manifest: SplitManifest) -> str:
    """SHA256 of the complete deterministic logical manifest (no self-reference)."""
    return _digest(asdict(manifest))


def write_split_manifest(manifest: SplitManifest, path: Path) -> None:
    text = _canonical(asdict(manifest))
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"Duplicate split JSON key: {key}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ContractError(f"Nonfinite split JSON constant: {value}")


def _entries(payload: Any, fields: set[str]) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or any(
        not isinstance(entry, dict) or set(entry) != fields for entry in payload
    ):
        raise ContractError(f"Split declarations require exactly {sorted(fields)}")
    return cast(list[dict[str, Any]], payload)


def validate_split_manifest(path: Path, inventory_path: Path, data_root: Path) -> SplitManifest:
    """Verify source-backed inventory and regenerate every split range/metadata.

    Strict comparison checks types as well as values, including purge/context
    bounds. Never trust external serialized ranges as executable slice indices.
    """
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_object, parse_constant=_constant
        )
        if not isinstance(payload, dict) or set(payload) != set(SplitManifest.__dataclass_fields__):
            raise ContractError("Split manifest fields do not match schema")
        if payload["schema_version"] != SPLIT_VERSION:
            raise ContractError(f"Split requires schema_version {SPLIT_VERSION}")
        inventory = validate_inventory(inventory_path, data_root)
        if payload["strategy"] == "group_holdout":
            entries = _entries(payload["group_assignments"], {"group_id", "partition"})
            mapping = {}
            for entry in entries:
                _text(entry["group_id"], "group_id")
                if entry["group_id"] in mapping:
                    raise ContractError("Duplicate group assignment")
                mapping[entry["group_id"]] = _partition(entry["partition"])
            computed = build_group_split(inventory, mapping, lookback=payload["lookback"])
        elif payload["strategy"] == "chronological":
            entries = _entries(payload["cuts"], {"series_id", "train_stop", "calibration_stop"})
            computed = build_chronological_split(
                inventory,
                [ChronologicalCut(**entry) for entry in entries],
                lookback=payload["lookback"],
                past_context=payload["past_context"],
            )
        else:
            raise ContractError("Unsupported split strategy")
        if _canonical(payload) != _canonical(asdict(computed)):
            raise ContractError(
                "Split does not match inventory, declarations or boundary-purge rules"
            )
        return computed
    except (ValueError, TypeError) as exc:
        if isinstance(exc, ContractError):
            raise
        raise ContractError(f"Invalid split manifest: {exc}") from exc
