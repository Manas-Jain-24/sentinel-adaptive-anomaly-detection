"""Manas's PR-2 consumer review: finite feature context and target-only metrics."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from sentinel.config import DetectorConfig
from sentinel.contracts import ContractError, Observation, Prediction, timestamp_text
from sentinel.data import features
from sentinel.data import inventory as inventory_api
from sentinel.data import splits as split_api
from sentinel.data.io import read_observations
from sentinel.detectors.residual import ResidualDetector
from sentinel.evaluation.reference import event_metrics
from sentinel.pipeline import prediction_record

START = datetime(2026, 1, 1, tzinfo=UTC)


def observations(series: str, count: int = 48) -> list[Observation]:
    return [
        Observation(series, START + timedelta(minutes=i), float((i * 7) % 19 + (i // 11) * 3))
        for i in range(count)
    ]


def detector(window: int = 4, floor: float = 0.5) -> ResidualDetector:
    return ResidualDetector(
        DetectorConfig(window_size=window, min_history=2, scale_floor=floor, threshold=6.3),
        features.RollingFeatureExtractor(
            window_size=window, min_history=2, scale_floor=floor, seasonal_period=3
        ),
        use_seasonal=True,
    )


def replay(items: list[Observation], *, window: int = 4, floor: float = 0.5) -> list[Prediction]:
    model = detector(window, floor)
    return [model.process(item) for item in items]


def write_source(root: Path, name: str, items: list[Observation], group: str) -> Any:
    path = root / name
    rows = ["series_id,timestamp,value"]
    rows += [f"{p.series_id},{timestamp_text(p.timestamp)},{p.value}" for p in items]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return inventory_api.SourceSpec(
        path=name,
        source="Deterministic hand-authored consumer-review trace",
        permission_basis="Synthetic software verification only",
        group_id=group,
        expected_cadence_seconds=60,
    )


@pytest.mark.parametrize("policy", ["carry", "reset"])
@pytest.mark.parametrize("lookback", [4, 6])
def test_fresh_partition_context_reproduces_full_stream_targets_and_excludes_context_from_metrics(
    tmp_path: Path, policy: str, lookback: int
) -> None:
    items = observations("s")
    source = write_source(tmp_path, "trace.csv", items, "synthetic-family")
    inventory = inventory_api.build_inventory(
        tmp_path, "synthetic-review", "synthetic_smoke", [source]
    )
    split = split_api.build_chronological_split(
        inventory,
        [split_api.ChronologicalCut("s", 16, 32)],
        lookback=lookback,
        past_context=policy,
    )
    reference = replay(items)
    supports: list[set[int]] = []
    for segment in split.ranges:
        context_and_targets = replay(items[segment.context_start : segment.target_stop])
        context_count = segment.target_start - segment.context_start
        targets = context_and_targets[context_count:]
        assert targets == reference[segment.target_start : segment.target_stop]
        assert all(p.ready for p in targets)
        assert len(targets) == segment.target_stop - segment.target_start
        records = [prediction_record(p, 0) for p in targets]
        metrics = event_metrics(records, [])
        assert metrics["observations"] == len(targets)
        assert metrics["warmup_points_included_in_coverage"] == 0
        support: set[int] = set()
        for index in range(segment.target_start, segment.target_stop):
            support.update(range(index - lookback, index + 1))
        supports.append(support)
    assert all(not left & right for i, left in enumerate(supports) for right in supports[i + 1 :])


@pytest.mark.parametrize("policy", ["carry", "reset"])
@pytest.mark.parametrize("declared", [1, 2])
def test_underdeclared_context_does_not_certify_a_history_consuming_detector(
    tmp_path: Path, policy: str, declared: int
) -> None:
    items = observations("s")
    source = write_source(tmp_path, "trace.csv", items, "synthetic-family")
    inventory = inventory_api.build_inventory(
        tmp_path, "synthetic-review", "synthetic_smoke", [source]
    )
    split = split_api.build_chronological_split(
        inventory, [split_api.ChronologicalCut("s", 16, 32)], lookback=declared, past_context=policy
    )
    validation = split.ranges[-1]
    replayed = replay(items[validation.context_start : validation.target_stop], window=8)
    first_target = replayed[validation.target_start - validation.context_start]
    # Even ready=true at L=2 does not prove that the W=8 reference was replayed.
    # The future harness must validate the model's actual effective support.
    assert first_target.ready == (declared >= 2)
    assert first_target.evidence.history_size == declared
    assert first_target != replay(items, window=8)[validation.target_start]


@pytest.mark.parametrize("policy", ["carry", "reset"])
def test_split_indices_apply_to_series_subsequences_of_an_interleaved_csv(
    tmp_path: Path, policy: str
) -> None:
    left, right = observations("a"), observations("b")
    right = [replace(p, value=100 + 2 * p.value) for p in right]
    mixed = [item for pair in zip(left, right, strict=True) for item in pair]
    source = write_source(tmp_path, "mixed.csv", mixed, "synthetic-family")
    inventory = inventory_api.build_inventory(
        tmp_path, "synthetic-review", "synthetic_smoke", [source]
    )
    split = split_api.build_chronological_split(
        inventory,
        [split_api.ChronologicalCut("a", 16, 32), split_api.ChronologicalCut("b", 16, 32)],
        lookback=4,
        past_context=policy,
    )
    canonical = list(read_observations(tmp_path / "mixed.csv"))
    for segment in split.ranges:
        series = [p for p in canonical if p.series_id == segment.series_id]
        replayed = replay(series[segment.context_start : segment.target_stop])
        targets = replayed[segment.target_start - segment.context_start :]
        assert targets == replay(series)[segment.target_start : segment.target_stop]
        assert all(p.series_id == segment.series_id for p in targets)


def test_group_holdout_context_keeps_each_group_and_detector_state_separate(tmp_path: Path) -> None:
    left, right = observations("a"), observations("b")
    right = [replace(p, value=p.value + 100) for p in right]
    sources = [
        write_source(tmp_path, "a.csv", left, "train-family"),
        write_source(tmp_path, "b.csv", right, "validation-family"),
    ]
    inventory = inventory_api.build_inventory(
        tmp_path, "synthetic-review", "synthetic_smoke", sources
    )
    split = split_api.build_group_split(
        inventory, {"train-family": "train", "validation-family": "validation"}, lookback=4
    )
    for segment in split.ranges:
        series = left if segment.series_id == "a" else right
        targets = replay(series)[segment.target_start : segment.target_stop]
        assert len(targets) == len(series) - 4
        assert all(p.ready and p.series_id == segment.series_id for p in targets)
        assert segment.context_start == 0
        assert segment.target_start == 4
    assert {s.group_id for s in split.ranges if s.partition == "train"}.isdisjoint(
        {s.group_id for s in split.ranges if s.partition == "validation"}
    )


@pytest.mark.parametrize("gain", [-3.0, -0.002])
def test_negative_unit_changes_with_scaled_floor_preserve_residual_decisions(gain: float) -> None:
    items = observations("s")
    expected = replay(items)
    actual = replay([replace(p, value=17 + gain * p.value) for p in items], floor=0.5 * abs(gain))
    for left, right in zip(expected, actual, strict=True):
        assert left.ready == right.ready
        assert left.label == right.label
        assert left.score == pytest.approx(right.score, abs=1e-8)
        assert left.evidence.component_scores == pytest.approx(
            right.evidence.component_scores, abs=1e-8
        )


def test_cadence_gap_preserves_observation_lag_and_raw_delta_semantics() -> None:
    values = [10, 11, 12, 13, 16]
    regular = [
        Observation("s", START + timedelta(minutes=i), value) for i, value in enumerate(values)
    ]
    gaps = [
        replace(p, timestamp=START + timedelta(minutes=i))
        for p, i in zip(regular, [0, 1, 2, 100, 101], strict=True)
    ]
    for expected, actual in zip(replay(regular), replay(gaps), strict=True):
        assert replace(actual, timestamp=expected.timestamp) == expected


def test_real_extractor_error_invalidates_wrapper_until_full_reset_replay() -> None:
    model = detector()
    first = Observation("s", START, -1e308)
    model.process(first)
    with pytest.raises(ContractError, match="overflow"):
        model.process(Observation("s", START + timedelta(minutes=1), 1e308))
    with pytest.raises(ContractError, match="requires reset and replay"):
        model.process(Observation("s", START + timedelta(minutes=1), -1e308))
    model.reset()
    points = [replace(first, timestamp=START + timedelta(minutes=i)) for i in range(4)]
    assert [model.process(p) for p in points] == replay(points)
