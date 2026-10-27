import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from sentinel.contracts import ContractError
from sentinel.data import inventory


def source_spec(path: str = "trace.csv", **changes: Any) -> inventory.SourceSpec:
    fields = {
        "path": path,
        "source": "Hand-constructed synthetic data",
        "permission_basis": "Authored for software tests",
        "group_id": "synthetic-group",
    }
    fields.update(changes)
    return inventory.SourceSpec(**fields)


def write_trace(root: Path, rows: str, name: str = "trace.csv") -> Path:
    path = root / name
    path.write_text("series_id,timestamp,value\n" + rows, encoding="utf-8", newline="\n")
    return path


def saved_inventory(root: Path) -> Path:
    write_trace(root, "s,2026-01-01T00:00:00Z,1\ns,2026-01-01T00:01:00Z,2\n")
    manifest = inventory.build_inventory(
        root, "test-v1", "synthetic_smoke", [source_spec(expected_cadence_seconds=60)]
    )
    path = root / "inventory.json"
    inventory.write_inventory(manifest, path)
    return path


def test_hand_derived_inventory_preserves_per_series_cadence(tmp_path: Path) -> None:
    content = (
        b"series_id,timestamp,value\n"
        b"s,2026-01-01T01:00:00+01:00,-2\n"
        b"t,2026-01-01T00:00:00Z,100\n"
        b"s,2026-01-01T00:01:00Z,3\n"
        b"t,2026-01-01T00:01:00Z,101\n"
        b"s,2026-01-01T00:03:00Z,7\n"
        b"s,2026-01-01T00:06:00Z,4\n"
    )
    source = tmp_path / "trace.csv"
    source.write_bytes(content)
    spec = inventory.SourceSpec(
        path="trace.csv",
        source="Hand-constructed synthetic trace",
        permission_basis="Authored for synthetic software tests; no external data",
        group_id="synthetic-group",
        expected_cadence_seconds=60,
    )
    result = inventory.build_inventory(tmp_path, "test-v1", "synthetic_smoke", [spec])
    assert result.dataset_id == "test-v1"
    assert result.evaluation_scope == "synthetic_smoke"
    audited = result.sources[0]
    assert audited.sha256 == hashlib.sha256(content).hexdigest()
    assert audited.size_bytes == len(content)
    assert audited.observations == 6
    s, t = audited.series
    assert (s.series_id, s.length) == ("s", 4)
    assert (s.start, s.end) == ("2026-01-01T00:00:00Z", "2026-01-01T00:06:00Z")
    assert (s.value_min, s.value_max) == (-2, 7)
    assert (s.cadence_min_seconds, s.cadence_median_seconds, s.cadence_max_seconds) == (
        60,
        120,
        180,
    )
    assert (s.gap_intervals, s.missing_steps, s.off_grid_intervals) == (2, 3, 0)
    assert (t.series_id, t.length, t.gap_intervals) == ("t", 2, 0)
    assert t.cadence_median_seconds == pytest.approx(60)


def test_fixture_inventory_and_manifest_roundtrip(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    spec = source_spec("tests/fixtures/synthetic_stream.csv", expected_cadence_seconds=60)
    result = inventory.build_inventory(root, "synthetic-fixture-v1", "synthetic_smoke", [spec])
    path = tmp_path / "inventory.json"
    inventory.write_inventory(result, path)
    assert inventory.validate_inventory(path, root) == result
    assert b"\r" not in path.read_bytes()
    series = result.sources[0].series[0]
    assert (series.length, series.value_min, series.value_max) == (16, 9.9, 15)
    assert (series.gap_intervals, series.missing_steps, series.off_grid_intervals) == (0, 0, 0)


def test_committed_example_matches_actual_fixture() -> None:
    root = Path(__file__).resolve().parents[2]
    result = inventory.validate_inventory(root / "docs/data/synthetic-fixture-inventory.json", root)
    assert result.evaluation_scope == "synthetic_smoke"
    assert result.sources[0].observations == 16


@pytest.mark.parametrize("field", ["source", "permission_basis", "group_id"])
@pytest.mark.parametrize("value", ["", "   ", None, True])
def test_requires_explicit_provenance(field: str, value: Any) -> None:
    with pytest.raises(ContractError, match=field):
        source_spec(**{field: value})


@pytest.mark.parametrize(
    "cadence", [0, -1, float("nan"), float("inf"), True, "60", 0.0000001, 10**1000, 1e308]
)
def test_rejects_invalid_declared_cadence(cadence: Any) -> None:
    with pytest.raises(ContractError, match="cadence"):
        source_spec(expected_cadence_seconds=cadence)


@pytest.mark.parametrize("path", ["", "../trace.csv", "/trace.csv", "C:/trace.csv", "a\\b", "./a"])
def test_source_paths_are_portable_and_relative(path: str) -> None:
    with pytest.raises(ContractError, match="path"):
        source_spec(path)


def test_missing_source_is_visible(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        inventory.build_inventory(tmp_path, "test", "synthetic_smoke", [source_spec()])


def test_source_directory_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "trace.csv").mkdir()
    with pytest.raises(ContractError, match="not a file"):
        inventory.build_inventory(tmp_path, "test", "synthetic_smoke", [source_spec()])


def test_symlink_cannot_escape_declared_data_root(tmp_path: Path) -> None:
    outside = write_trace(tmp_path, "s,2026-01-01T00:00:00Z,1\n")
    root = tmp_path / "data"
    root.mkdir()
    try:
        (root / "trace.csv").symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"Creating symlinks unavailable on this host: {exc}")
    with pytest.raises(ContractError, match="escapes data root"):
        inventory.build_inventory(root, "test", "synthetic_smoke", [source_spec()])


@pytest.mark.parametrize("dataset_id", ["", "  ", None, True])
def test_dataset_identity_is_required(tmp_path: Path, dataset_id: Any) -> None:
    with pytest.raises(ContractError, match="dataset_id"):
        inventory.build_inventory(tmp_path, dataset_id, "synthetic_smoke", [source_spec()])


@pytest.mark.parametrize("scope", ["official_benchmark", "hidden_evaluation", "", None])
def test_unknown_or_official_scope_is_rejected(tmp_path: Path, scope: Any) -> None:
    with pytest.raises(ContractError, match="scope"):
        inventory.build_inventory(tmp_path, "test", scope, [source_spec()])


def test_empty_and_duplicate_sources_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ContractError, match="source"):
        inventory.build_inventory(tmp_path, "test", "synthetic_smoke", [])
    write_trace(tmp_path, "s,2026-01-01T00:00:00Z,1\n")
    with pytest.raises(ContractError, match="Duplicate source"):
        inventory.build_inventory(tmp_path, "test", "synthetic_smoke", [source_spec()] * 2)


@pytest.mark.parametrize("value", ["NaN", "inf", "-inf"])
def test_nonfinite_values_fail_with_row_context(tmp_path: Path, value: str) -> None:
    write_trace(tmp_path, f"s,2026-01-01T00:00:00Z,{value}\n")
    with pytest.raises(ContractError, match="trace.csv.*row 2.*finite"):
        inventory.build_inventory(tmp_path, "test", "synthetic_smoke", [source_spec()])


@pytest.mark.parametrize("second", ["2026-01-01T01:00:00+01:00", "2025-12-31T23:59:00Z"])
def test_duplicate_instants_and_backwards_time_are_rejected(tmp_path: Path, second: str) -> None:
    write_trace(tmp_path, f"s,2026-01-01T00:00:00Z,1\ns,{second},2\n")
    with pytest.raises(ContractError, match="trace.csv.*strictly increasing.*s"):
        inventory.build_inventory(tmp_path, "test", "synthetic_smoke", [source_spec()])


@pytest.mark.parametrize(
    "content",
    [
        "timestamp,value\n2026-01-01T00:00:00Z,1\n",
        "series_id,timestamp,value,label\ns,2026-01-01T00:00:00Z,1,NORMAL\n",
        "series_id,timestamp,value\n",
        "series_id,timestamp,value\ns,2026-01-01T00:00:00,1\n",
        "series_id,timestamp,value\ns,2026-01-01T00:00:00Z,1,extra\n",
    ],
)
def test_canonical_reader_errors_remain_visible(tmp_path: Path, content: str) -> None:
    (tmp_path / "trace.csv").write_text(content, encoding="utf-8")
    with pytest.raises(ContractError, match="trace.csv"):
        inventory.build_inventory(tmp_path, "test", "synthetic_smoke", [source_spec()])


def test_unknown_cadence_does_not_invent_gaps(tmp_path: Path) -> None:
    write_trace(tmp_path, "s,2026-01-01T00:00:00Z,1\ns,2026-01-01T00:05:00Z,2\n")
    result = inventory.build_inventory(tmp_path, "test", "development_validation", [source_spec()])
    s = result.sources[0].series[0]
    assert s.cadence_median_seconds == 300
    assert (s.gap_intervals, s.missing_steps, s.off_grid_intervals) == (None, None, None)


def test_off_grid_cadence_does_not_claim_exact_missing_samples(tmp_path: Path) -> None:
    write_trace(
        tmp_path,
        "s,2026-01-01T00:00:00Z,1\ns,2026-01-01T00:01:30Z,2\ns,2026-01-01T00:03:30Z,3\n",
    )
    result = inventory.build_inventory(
        tmp_path, "test", "synthetic_smoke", [source_spec(expected_cadence_seconds=60)]
    )
    s = result.sources[0].series[0]
    assert (s.gap_intervals, s.missing_steps, s.off_grid_intervals) == (2, None, 1)


def test_one_point_series_has_no_observed_cadence(tmp_path: Path) -> None:
    write_trace(tmp_path, "s,2026-01-01T00:00:00Z,1e308\n")
    result = inventory.build_inventory(
        tmp_path, "test", "synthetic_smoke", [source_spec(expected_cadence_seconds=60)]
    )
    s = result.sources[0].series[0]
    assert (s.cadence_min_seconds, s.cadence_median_seconds, s.cadence_max_seconds) == (
        None,
        None,
        None,
    )
    assert s.value_max == 1e308
    assert (s.gap_intervals, s.missing_steps, s.off_grid_intervals) == (0, 0, 0)


def test_microsecond_cadence_avoids_float_modulo_errors(tmp_path: Path) -> None:
    write_trace(
        tmp_path,
        "s,2026-01-01T00:00:00Z,1\n"
        "s,2026-01-01T00:00:00.000249Z,2\n"
        "s,2026-01-01T00:00:00.000747Z,3\n",
    )
    result = inventory.build_inventory(
        tmp_path, "test", "synthetic_smoke", [source_spec(expected_cadence_seconds=0.000249)]
    )
    s = result.sources[0].series[0]
    assert (s.gap_intervals, s.missing_steps, s.off_grid_intervals) == (1, 1, 0)


def test_source_modified_during_audit_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from collections.abc import Iterator

    from sentinel.contracts import Observation

    source = write_trace(tmp_path, "s,2026-01-01T00:00:00Z,1\n")
    reader = inventory.read_observations

    def changing_reader(path: Path) -> Iterator[Observation]:
        yield from reader(path)
        with source.open("a", encoding="utf-8") as stream:
            stream.write("s,2026-01-01T00:01:00Z,2\n")

    monkeypatch.setattr(inventory, "read_observations", changing_reader)
    with pytest.raises(ContractError, match="changed during inventory"):
        inventory.build_inventory(tmp_path, "test", "synthetic_smoke", [source_spec()])


def test_deterministic_order_and_no_overwrite(tmp_path: Path) -> None:
    write_trace(tmp_path, "z,2026-01-01T00:00:00Z,1\na,2026-01-01T00:00:00Z,2\n", "b.csv")
    write_trace(tmp_path, "s,2026-01-01T00:00:00Z,3\n", "a.csv")
    specs = [source_spec("b.csv"), source_spec("a.csv")]
    a = inventory.build_inventory(tmp_path, "test", "synthetic_smoke", specs)
    b = inventory.build_inventory(tmp_path, "test", "synthetic_smoke", specs[::-1])
    assert a == b
    assert [s.spec.path for s in a.sources] == ["a.csv", "b.csv"]
    assert [s.series_id for s in a.sources[1].series] == ["a", "z"]
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    inventory.write_inventory(a, first)
    inventory.write_inventory(b, second)
    before = first.read_bytes()
    assert before == second.read_bytes()
    with pytest.raises(FileExistsError):
        inventory.write_inventory(replace(a, dataset_id="different"), first)
    assert first.read_bytes() == before


def test_repeated_series_across_files_requires_explicit_shard_contract(tmp_path: Path) -> None:
    write_trace(tmp_path, "s,2026-01-01T00:00:00Z,1\n", "a.csv")
    write_trace(tmp_path, "s,2026-01-01T00:01:00Z,2\n", "b.csv")
    with pytest.raises(ContractError, match="series.*multiple sources"):
        inventory.build_inventory(
            tmp_path, "test", "synthetic_smoke", [source_spec("a.csv"), source_spec("b.csv")]
        )


@pytest.mark.parametrize("tamper", ["hash", "length", "boolean", "extra", "permission", "version"])
def test_validator_rejects_forged_or_incompatible_manifest(tmp_path: Path, tamper: str) -> None:
    path = saved_inventory(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    source = payload["sources"][0]
    if tamper == "hash":
        source["sha256"] = "0" * 64
    elif tamper == "length":
        source["series"][0]["length"] = 123
    elif tamper == "boolean":
        source["series"][0]["gap_intervals"] = False
    elif tamper == "extra":
        payload["unknown"] = "field"
    elif tamper == "permission":
        source["spec"]["permission_basis"] = ""
    else:
        payload["schema_version"] = "future"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ContractError):
        inventory.validate_inventory(path, tmp_path)


def test_validator_detects_source_changes_and_missing_file(tmp_path: Path) -> None:
    path = saved_inventory(tmp_path)
    source = tmp_path / "trace.csv"
    source.write_text(source.read_text().replace(",2", ",3"), encoding="utf-8")
    with pytest.raises(ContractError, match="match"):
        inventory.validate_inventory(path, tmp_path)
    source.unlink()
    with pytest.raises(FileNotFoundError):
        inventory.validate_inventory(path, tmp_path)


@pytest.mark.parametrize(
    "text",
    ["[]", "{}", "not JSON", '{"schema_version":NaN}', '{"x":1,"x":2}'],
)
def test_validator_rejects_invalid_json_and_duplicate_keys(tmp_path: Path, text: str) -> None:
    path = tmp_path / "inventory.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ContractError):
        inventory.validate_inventory(path, tmp_path)
