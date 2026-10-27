import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from sentinel.contracts import ContractError
from sentinel.data.features import RollingFeatureExtractor
from sentinel.data.inventory import SourceSpec, build_inventory, write_inventory
from sentinel.data.io import read_observations
from sentinel.data.splits import (
    ChronologicalCut,
    build_chronological_split,
    build_group_split,
    split_digest,
    validate_split_manifest,
    write_split_manifest,
)


def fixture_inventory(root: Path) -> Any:
    specs = []
    # Two related series are interleaved in group g1, one independent series in g2.
    for name, series_ids, group in [("a", ["s", "t"], "g1"), ("b", ["u"], "g2")]:
        lines = ["series_id,timestamp,value"]
        for i in range(30):
            instant = (datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=i)).isoformat()
            lines.extend(f"{series},{instant},{i}" for series in series_ids)
        (root / f"{name}.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
        specs.append(
            SourceSpec(f"{name}.csv", "Hand-authored synthetic traces", "Software tests", group, 60)
        )
    return build_inventory(root, "split-fixture-v1", "synthetic_smoke", specs)


def cuts() -> list[ChronologicalCut]:
    return [ChronologicalCut(s, 12, 22) for s in ("s", "t", "u")]


def saved_split(root: Path) -> tuple[Path, Path]:
    inventory = fixture_inventory(root)
    inventory_path = root / "inventory.json"
    path = root / "split.json"
    write_inventory(inventory, inventory_path)
    split = build_chronological_split(inventory, cuts(), lookback=3, past_context="carry")
    write_split_manifest(split, path)
    return path, inventory_path


def test_group_holdout_keeps_related_series_together(tmp_path: Path) -> None:
    inventory = fixture_inventory(tmp_path)
    result = build_group_split(inventory, {"g1": "train", "g2": "validation"}, lookback=3)
    assert result.strategy == "group_holdout"
    assert result.dataset_id == "split-fixture-v1"
    assert result.evaluation_scope == "synthetic_smoke"
    assert [(r.series_id, r.group_id, r.partition) for r in result.ranges] == [
        ("s", "g1", "train"),
        ("t", "g1", "train"),
        ("u", "g2", "validation"),
    ]
    assert all(
        (r.context_start, r.target_start, r.target_stop) == (0, 3, 30) for r in result.ranges
    )
    assert {r.source_sha256 for r in result.ranges} == {s.sha256 for s in inventory.sources}


@pytest.mark.parametrize(
    "policy,expected",
    [
        ("carry", [(0, 3, 9), (9, 12, 19), (19, 22, 30)]),
        ("reset", [(0, 3, 12), (12, 15, 22), (22, 25, 30)]),
    ],
)
def test_chronological_boundaries_are_hand_derived_and_support_disjoint(
    tmp_path: Path, policy: Any, expected: list[tuple[int, int, int]]
) -> None:
    result = build_chronological_split(
        fixture_inventory(tmp_path), cuts(), lookback=3, past_context=policy
    )
    ranges = [r for r in result.ranges if r.series_id == "s"]
    assert [r.partition for r in ranges] == ["train", "calibration", "validation"]
    assert [(r.context_start, r.target_start, r.target_stop) for r in ranges] == expected
    assert [(r.partition_start, r.partition_stop) for r in ranges] == [(0, 12), (12, 22), (22, 30)]
    supports = [set(range(r.target_start - 3, r.target_stop)) for r in ranges]
    assert not supports[0] & supports[1]
    assert not supports[0] & supports[2]
    assert not supports[1] & supports[2]


def test_order_and_hash_are_stable_for_equivalent_declarations(tmp_path: Path) -> None:
    inventory = fixture_inventory(tmp_path)
    group_a = build_group_split(inventory, {"g1": "train", "g2": "validation"})
    group_b = build_group_split(inventory, {"g2": "validation", "g1": "train"})
    assert group_a == group_b
    chrono_a = build_chronological_split(inventory, cuts(), lookback=3, past_context="carry")
    chrono_b = build_chronological_split(inventory, cuts()[::-1], lookback=3, past_context="carry")
    assert chrono_a == chrono_b
    assert split_digest(chrono_a) == split_digest(chrono_b)
    assert len(split_digest(chrono_a)) == 64
    changed = build_chronological_split(inventory, cuts(), lookback=3, past_context="reset")
    assert split_digest(changed) != split_digest(chrono_a)


@pytest.mark.parametrize(
    "assignments",
    [
        {},
        {"g1": "train"},
        {"g1": "train", "g2": "validation", "extra": "test"},
        {"g1": "train", "g2": "train"},
        {"g1": "validation", "g2": "test"},
        {"g1": "train", "g2": "hidden"},
        {"g1": "train", "g2": True},
    ],
)
def test_incomplete_or_invalid_group_declarations_fail(tmp_path: Path, assignments: Any) -> None:
    with pytest.raises(ContractError):
        build_group_split(fixture_inventory(tmp_path), assignments)


@pytest.mark.parametrize("lookback", [-1, True, 2.5, "3", 30, 100])
def test_invalid_lookback_or_empty_target_range_is_rejected(tmp_path: Path, lookback: Any) -> None:
    inventory = fixture_inventory(tmp_path)
    with pytest.raises(ContractError):
        build_group_split(inventory, {"g1": "train", "g2": "validation"}, lookback=lookback)
    with pytest.raises(ContractError):
        build_chronological_split(inventory, cuts(), lookback=lookback, past_context="carry")


@pytest.mark.parametrize("policy", ["", "implicit", None, True])
def test_context_policy_must_be_explicit(tmp_path: Path, policy: Any) -> None:
    with pytest.raises(ContractError, match="past_context"):
        build_chronological_split(
            fixture_inventory(tmp_path), cuts(), lookback=3, past_context=policy
        )


@pytest.mark.parametrize("train,calibration", [(0, 22), (12, 12), (15, 12), (True, 22), (12, 22.0)])
def test_invalid_cuts_fail(train: Any, calibration: Any) -> None:
    with pytest.raises(ContractError):
        ChronologicalCut("s", train, calibration)


def test_cuts_must_cover_series_once_and_fit_source_lengths(tmp_path: Path) -> None:
    inventory = fixture_inventory(tmp_path)
    for declarations in [
        cuts()[:-1],
        cuts() + [cuts()[0]],
        cuts() + [ChronologicalCut("x", 12, 22)],
        [ChronologicalCut(s, 12, 30) for s in ("s", "t", "u")],
    ]:
        with pytest.raises(ContractError):
            build_chronological_split(inventory, declarations, lookback=3, past_context="carry")


def test_context_purge_can_make_small_segments_invalid(tmp_path: Path) -> None:
    inventory = fixture_inventory(tmp_path)
    # Training requires warmup L and a separate tail L reserved for the next context.
    with pytest.raises(ContractError, match="empty"):
        build_chronological_split(inventory, cuts(), lookback=6, past_context="carry")
    reset = build_chronological_split(inventory, cuts(), lookback=6, past_context="reset")
    assert all(r.target_stop > r.target_start for r in reset.ranges)


def test_manifest_roundtrip_does_not_overwrite(tmp_path: Path) -> None:
    path, inventory_path = saved_split(tmp_path)
    computed = validate_split_manifest(path, inventory_path, tmp_path)
    assert computed.lookback == 3
    assert computed.past_context == "carry"
    assert b"\r" not in path.read_bytes()
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        write_split_manifest(computed, path)
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "tamper", ["range", "source_hash", "inventory_hash", "context", "extra", "version", "bool"]
)
def test_manifest_rejects_stale_or_weakened_contracts(tmp_path: Path, tamper: str) -> None:
    path, inventory_path = saved_split(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if tamper == "range":
        payload["ranges"][0]["target_stop"] = 12  # Reintroduces cross-boundary overlap.
    elif tamper == "source_hash":
        payload["ranges"][0]["source_sha256"] = "0" * 64
    elif tamper == "inventory_hash":
        payload["inventory_sha256"] = "0" * 64
    elif tamper == "context":
        payload["ranges"][1]["context_start"] = 0
    elif tamper == "extra":
        payload["unknown"] = "field"
    elif tamper == "version":
        payload["schema_version"] = "future"
    else:
        payload["ranges"][0]["context_start"] = False
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ContractError):
        validate_split_manifest(path, inventory_path, tmp_path)


def test_group_manifest_is_revalidated_against_source_inventory(tmp_path: Path) -> None:
    inventory = fixture_inventory(tmp_path)
    inventory_path, split_path = tmp_path / "inventory.json", tmp_path / "split.json"
    write_inventory(inventory, inventory_path)
    split = build_group_split(inventory, {"g1": "train", "g2": "validation"})
    write_split_manifest(split, split_path)
    assert validate_split_manifest(split_path, inventory_path, tmp_path) == split
    source = tmp_path / "a.csv"
    source.write_text(source.read_text().replace(",29", ",30"), encoding="utf-8")
    with pytest.raises(ContractError):
        validate_split_manifest(split_path, inventory_path, tmp_path)


@pytest.mark.parametrize("text", ["[]", "{}", "bad JSON", '{"x":1,"x":2}', '{"x":NaN}'])
def test_invalid_split_json_is_rejected(tmp_path: Path, text: str) -> None:
    path, inventory_path = saved_split(tmp_path)
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ContractError):
        validate_split_manifest(path, inventory_path, tmp_path)


def test_inventory_version_is_not_silently_substituted(tmp_path: Path) -> None:
    inventory = replace(fixture_inventory(tmp_path), schema_version="future")
    with pytest.raises(ContractError):
        build_group_split(inventory, {"g1": "train", "g2": "validation"})


def test_bounded_feature_replay_uses_only_declared_context_and_targets(tmp_path: Path) -> None:
    inventory = fixture_inventory(tmp_path)
    split = build_chronological_split(inventory, cuts(), lookback=3, past_context="carry")
    trace = [p for p in read_observations(tmp_path / "a.csv") if p.series_id == "s"]
    full_extractor = RollingFeatureExtractor(window_size=3, min_history=2)
    full_frames = [full_extractor.process(p) for p in trace]
    for region in [r for r in split.ranges if r.series_id == "s"]:
        extractor = RollingFeatureExtractor(window_size=3, min_history=2)
        target_frames = []
        for index in range(region.context_start, region.target_stop):
            frame = extractor.process(trace[index])
            if index >= region.target_start:
                target_frames.append(frame)
                assert frame.ready
                assert frame.expected_level == index - 2
                assert frame.expected_delta == 1
        assert target_frames == full_frames[region.target_start : region.target_stop]


def test_committed_split_example_matches_fixture() -> None:
    root = Path(__file__).resolve().parents[2]
    split = validate_split_manifest(
        root / "docs/data/synthetic-fixture-split.json",
        root / "docs/data/synthetic-fixture-inventory.json",
        root,
    )
    assert [(r.target_start, r.target_stop) for r in split.ranges] == [(2, 4), (6, 9), (11, 16)]
