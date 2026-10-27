"""Offline canonical-data audit; never used to fit inference-time statistics.

The inventory format is local to KS-01 pending consumer review. It does not extend
Observation, FeatureFrame, detector config, or run.json shared contracts.
"""

import hashlib
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime
from math import isfinite
from pathlib import Path, PurePosixPath
from statistics import median
from typing import Any, cast

from sentinel.contracts import ContractError, EvaluationScope, Observation, timestamp_text
from sentinel.data.io import read_observations

INVENTORY_VERSION = "sentinel_inventory_v1"


def _required_text(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name} must be a nonempty string")


def _cadence_microseconds(value: float | None) -> int | None:
    if value is None:
        return None
    if type(value) not in (int, float):
        raise ContractError("expected_cadence_seconds must be finite and positive")
    try:
        seconds = float(value)
    except OverflowError as exc:
        raise ContractError("expected_cadence_seconds is too large") from exc
    microseconds = seconds * 1_000_000
    if not isfinite(microseconds) or seconds <= 0:
        raise ContractError("expected_cadence_seconds must be finite and positive")
    rounded = round(microseconds)
    if seconds != rounded / 1_000_000:
        raise ContractError("expected_cadence_seconds must resolve to whole microseconds")
    return rounded


@dataclass(frozen=True)
class SourceSpec:
    """Operator assertions, not automatic proof of access or organizer permission.

    group_id declares a related-source group for later split review. A single
    series cannot span multiple files in this initial canonical-only format.
    """

    path: str
    source: str
    permission_basis: str
    group_id: str
    expected_cadence_seconds: float | None = None

    def __post_init__(self) -> None:
        for name in ("path", "source", "permission_basis", "group_id"):
            _required_text(getattr(self, name), name)
        path = PurePosixPath(self.path)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "\\" in self.path
            or ":" in self.path
            or str(path) != self.path
            or self.path == "."
        ):
            raise ContractError("Source path must be a normalized relative POSIX file path")
        _cadence_microseconds(self.expected_cadence_seconds)


@dataclass(frozen=True)
class SeriesInventory:
    series_id: str
    length: int
    start: str
    end: str
    value_min: float
    value_max: float
    cadence_min_seconds: float | None
    cadence_median_seconds: float | None
    cadence_max_seconds: float | None
    gap_intervals: int | None
    missing_steps: int | None
    off_grid_intervals: int | None


@dataclass(frozen=True)
class SourceInventory:
    spec: SourceSpec
    sha256: str
    size_bytes: int
    observations: int
    series: tuple[SeriesInventory, ...]


@dataclass(frozen=True)
class InventoryManifest:
    schema_version: str
    dataset_id: str
    evaluation_scope: EvaluationScope
    sources: tuple[SourceInventory, ...]


@dataclass
class _SeriesAudit:
    start: datetime
    last: datetime
    value_min: float
    value_max: float
    length: int = 1
    intervals_us: list[int] = field(default_factory=list)

    def append(self, observation: Observation) -> None:
        if observation.timestamp <= self.last:
            raise ContractError(
                f"Timestamps must be strictly increasing for series {observation.series_id!r}; "
                "duplicate or backwards instant"
            )
        interval = observation.timestamp - self.last
        self.intervals_us.append(
            (interval.days * 86400 + interval.seconds) * 1_000_000 + interval.microseconds
        )
        self.last = observation.timestamp
        self.length += 1
        self.value_min = min(self.value_min, observation.value)
        self.value_max = max(self.value_max, observation.value)

    def finish(self, series_id: str, cadence_us: int | None) -> SeriesInventory:
        intervals = self.intervals_us
        gaps = missing = off_grid = None
        if cadence_us is not None:
            gaps = sum(interval > cadence_us for interval in intervals)
            off_grid = sum(interval % cadence_us != 0 for interval in intervals)
            if off_grid == 0:
                missing = sum(interval // cadence_us - 1 for interval in intervals)
        return SeriesInventory(
            series_id=series_id,
            length=self.length,
            start=timestamp_text(self.start),
            end=timestamp_text(self.last),
            value_min=self.value_min,
            value_max=self.value_max,
            cadence_min_seconds=min(intervals) / 1_000_000 if intervals else None,
            cadence_median_seconds=median(intervals) / 1_000_000 if intervals else None,
            cadence_max_seconds=max(intervals) / 1_000_000 if intervals else None,
            gap_intervals=gaps,
            missing_steps=missing,
            off_grid_intervals=off_grid,
        )


def _file_fingerprint(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _source_path(data_root: Path, spec: SourceSpec) -> Path:
    resolved = (data_root / spec.path).resolve(strict=True)
    if not resolved.is_relative_to(data_root):
        raise ContractError(f"Source path escapes data root: {spec.path}")
    if not resolved.is_file():
        raise ContractError(f"Source path is not a file: {spec.path}")
    return resolved


def _audit_source(path: Path, spec: SourceSpec) -> SourceInventory:
    before = _file_fingerprint(path)
    series: dict[str, _SeriesAudit] = {}
    count = 0
    try:
        for observation in read_observations(path):
            if observation.series_id in series:
                series[observation.series_id].append(observation)
            else:
                series[observation.series_id] = _SeriesAudit(
                    observation.timestamp,
                    observation.timestamp,
                    observation.value,
                    observation.value,
                )
            count += 1
    except (ValueError, UnicodeError) as exc:
        raise ContractError(f"{spec.path}: {exc}") from exc
    if before != _file_fingerprint(path):
        raise ContractError(f"Source changed during inventory: {spec.path}")
    cadence_us = _cadence_microseconds(spec.expected_cadence_seconds)
    return SourceInventory(
        spec=spec,
        sha256=before[0],
        size_bytes=before[1],
        observations=count,
        series=tuple(series[name].finish(name, cadence_us) for name in sorted(series)),
    )


def build_inventory(
    data_root: Path,
    dataset_id: str,
    evaluation_scope: EvaluationScope,
    sources: Sequence[SourceSpec],
) -> InventoryManifest:
    """Audit explicitly permitted canonical files without sorting or changing rows.

    Uses the existing reader and enforces per-series chronology. Descriptive
    cadence is computed offline; missing-step counts require a declared cadence.
    Memory is O(number of observations) for exact median timestamp intervals.
    No timestamps, wall-clock times, or machine paths are added to provenance.
    """
    _required_text(dataset_id, "dataset_id")
    if evaluation_scope not in ("synthetic_smoke", "development_validation"):
        raise ContractError("Unsupported inventory evaluation_scope")
    if not sources:
        raise ContractError("Inventory requires at least one source")
    root = data_root.resolve(strict=True)
    paths: set[Path] = set()
    series_ids: set[str] = set()
    audited = []
    for spec in sorted(sources, key=lambda item: item.path):
        path = _source_path(root, spec)
        if path in paths:
            raise ContractError(f"Duplicate source path: {spec.path}")
        paths.add(path)
        source = _audit_source(path, spec)
        ids = {series.series_id for series in source.series}
        overlap = ids & series_ids
        if overlap:
            raise ContractError(f"A series occurs in multiple sources: {sorted(overlap)}")
        series_ids.update(ids)
        audited.append(source)
    return InventoryManifest(INVENTORY_VERSION, dataset_id, evaluation_scope, tuple(audited))


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"


def write_inventory(manifest: InventoryManifest, path: Path) -> None:
    """Write deterministic LF JSON to a new file; preserve an existing manifest."""
    text = _canonical_json(asdict(manifest))
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"Duplicate inventory JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ContractError(f"Nonfinite inventory JSON constant: {value}")


def validate_inventory(path: Path, data_root: Path) -> InventoryManifest:
    """Verify schema, source bytes, and every statistic by re-auditing the files.

    Provenance is a required operator declaration, not verified legal permission.
    Unknown fields, duplicate JSON keys, unsupported scopes, and stale or forged
    statistics fail closed. Sources are resolved relative to data_root, never to
    the manifest location or an embedded absolute path.
    """
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
        if not isinstance(payload, dict) or set(payload) != {
            "schema_version",
            "dataset_id",
            "evaluation_scope",
            "sources",
        }:
            raise ContractError(
                "Inventory requires exactly schema/version, identity, scope, sources"
            )
        if payload["schema_version"] != INVENTORY_VERSION:
            raise ContractError(f"Inventory requires schema_version {INVENTORY_VERSION}")
        raw_sources = payload["sources"]
        if not isinstance(raw_sources, list):
            raise ContractError("Inventory sources must be a list")
        specs = []
        for source in raw_sources:
            if not isinstance(source, dict) or not isinstance(source.get("spec"), dict):
                raise ContractError("Inventory source requires a spec object")
            if set(source["spec"]) != {
                "path",
                "source",
                "permission_basis",
                "group_id",
                "expected_cadence_seconds",
            }:
                raise ContractError("Inventory source spec fields do not match schema")
            specs.append(SourceSpec(**source["spec"]))
        computed = build_inventory(
            data_root,
            payload["dataset_id"],
            cast(EvaluationScope, payload["evaluation_scope"]),
            specs,
        )
        # Compare strict JSON types too: False must not stand in for an integer 0.
        if _canonical_json(payload) != _canonical_json(asdict(computed)):
            raise ContractError("Inventory does not match source checksums, schema, or statistics")
        return computed
    except (ValueError, TypeError, UnicodeError) as exc:
        if isinstance(exc, ContractError):
            raise
        raise ContractError(f"Invalid inventory manifest: {exc}") from exc
