from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sentinel.config import DetectorConfig
from sentinel.contracts import ContractError, FeatureFrame, Observation
from sentinel.data.features import RollingFeatureExtractor
from sentinel.data.inventory import SourceSpec, build_inventory, validate_inventory, write_inventory
from sentinel.data.io import read_observations
from sentinel.data.splits import (
    ChronologicalCut,
    PastContext,
    build_chronological_split,
    validate_split_manifest,
    write_split_manifest,
)
from sentinel.detectors.rolling import RollingMADStarter
from sentinel.pipeline import process_stream


def point(index: int, value: float, series: str = "s") -> Observation:
    return Observation(series, datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=index), value)


def frames(values: list[float], *, window: int = 4, minimum: int = 3) -> list[FeatureFrame]:
    extractor = RollingFeatureExtractor(
        window_size=window, min_history=minimum, scale_floor=0.01, seasonal_period=window
    )
    return [extractor.process(point(i, value)) for i, value in enumerate(values)]


@pytest.mark.parametrize("length", [1, 3, 4, 64])
@pytest.mark.parametrize("value", [-1e308, 0.0, 1e308])
def test_extreme_flat_and_short_streams_have_explicit_readiness(length: int, value: float) -> None:
    result = frames([value] * length, minimum=4)
    assert sum(frame.ready for frame in result) == max(0, length - 4)
    for index, frame in enumerate(result):
        assert frame.history_size == min(index, 4)
        assert frame.delta == (None if index == 0 else 0)
        if index < 4:
            assert frame.expected_level is frame.expected_delta is frame.scale is None
            assert frame.seasonal_expected is None
        else:
            assert frame.expected_level == value
            assert frame.expected_delta == 0
            assert frame.scale == 0.01
            assert frame.seasonal_expected == value


@pytest.mark.parametrize("gain,offset", [(2.0, -17.0), (1000.0, 500.0), (-3.0, 7.0)])
def test_affine_rescaling_preserves_features_when_floor_is_inactive(
    gain: float, offset: float
) -> None:
    values = [0.0, 2.0, 8.0, 4.0, 12.0, 6.0, 20.0, 14.0]
    original = frames(values)
    transformed = frames([gain * value + offset for value in values])
    for base, changed in zip(original, transformed, strict=True):
        if base.delta is not None:
            assert changed.delta == pytest.approx(gain * base.delta)
        if not base.ready:
            assert not changed.ready
            continue
        assert base.scale is not None and base.scale > 0.01
        assert base.expected_level is not None and base.expected_delta is not None
        assert changed.expected_level == pytest.approx(gain * base.expected_level + offset)
        assert changed.expected_delta == pytest.approx(gain * base.expected_delta)
        assert changed.scale == pytest.approx(abs(gain) * base.scale)
        if base.seasonal_expected is not None:
            assert changed.seasonal_expected == pytest.approx(
                gain * base.seasonal_expected + offset
            )


def test_fixed_scale_floor_breaks_small_unit_rescaling_invariance() -> None:
    original = frames([0, 2, 9], window=2, minimum=2)[-1]
    transformed = frames([0, 0.002, 0.009], window=2, minimum=2)[-1]
    assert original.expected_level == 1
    assert original.scale == pytest.approx(1.4826)
    assert transformed.expected_level == pytest.approx(0.001)
    assert transformed.scale == 0.01
    assert transformed.scale != pytest.approx(0.001 * original.scale)


def test_contaminated_warmup_changes_reference_until_prior_window_recovers() -> None:
    result = frames([100, 100, 100, 10, 10, 10, 10, 10], minimum=4)
    assert [frame.expected_level for frame in result[4:]] == [100, 55, 10, 10]
    assert result[4].scale == 0.01
    assert result[5].scale == pytest.approx(66.717)
    assert all(frame.ready for frame in result[4:])


def test_missing_span_is_audited_but_not_imputed_or_treated_as_time_rate(tmp_path: Path) -> None:
    source = tmp_path / "gap.csv"
    text = "series_id,timestamp,value\n" + "".join(
        f"s,{p.timestamp.isoformat()},{p.value}\n"
        for p in [point(0, 10), point(1, 11), point(2, 12), point(100, 13)]
    )
    source.write_text(text, encoding="utf-8", newline="\n")
    before = source.read_bytes()
    spec = SourceSpec("gap.csv", "Hand-authored missing-span fixture", "Software test", "gap", 60)
    audit = build_inventory(tmp_path, "gap-smoke-v1", "synthetic_smoke", [spec])
    s = audit.sources[0].series[0]
    assert (s.length, s.gap_intervals, s.missing_steps, s.off_grid_intervals) == (4, 1, 97, 0)
    extractor = RollingFeatureExtractor(window_size=3, min_history=2, seasonal_period=3)
    result = [extractor.process(p) for p in read_observations(source)]
    assert len(result) == 4
    assert result[-1].expected_level == 11
    assert result[-1].delta == 1  # A value difference across 98 minutes, not a per-minute rate.
    assert result[-1].seasonal_expected == 10  # Lag3 is 100 minutes old after the gap.
    assert source.read_bytes() == before


def test_long_bounded_stream_forgets_different_early_prefixes() -> None:
    a = RollingFeatureExtractor(window_size=8, min_history=8, seasonal_period=8)
    b = RollingFeatureExtractor(window_size=8, min_history=8, seasonal_period=8)
    for index in range(4096):
        suffix = float(index % 17 - 8)
        first = a.process(point(index, 1000 if index < 32 else suffix))
        second = b.process(point(index, -1000 if index < 32 else suffix))
        assert first.history_size <= 8
        assert second.history_size <= 8
        if index >= 40:
            assert first == second


def test_interleaved_features_and_existing_pipeline_keep_series_independent() -> None:
    a = [point(i, float(i % 7), "a") for i in range(50)]
    b = [point(i, float(100 + i % 11), "b") for i in range(50)]
    mixed = [p for pair in zip(a, b, strict=True) for p in pair]

    def feature_replay(points: list[Observation]) -> dict[str, list[FeatureFrame]]:
        extractors: dict[str, RollingFeatureExtractor] = {}
        output: dict[str, list[FeatureFrame]] = {}
        for p in points:
            if p.series_id not in extractors:
                extractors[p.series_id] = RollingFeatureExtractor(window_size=4, min_history=3)
            extractor = extractors[p.series_id]
            output.setdefault(p.series_id, []).append(extractor.process(p))
        return output

    assert feature_replay(mixed) == {**feature_replay(a), **feature_replay(b)}
    factory = lambda: RollingMADStarter(DetectorConfig(min_history=3))  # noqa: E731
    expected = [p for p, _ in process_stream(a, factory)] + [
        p for p, _ in process_stream(b, factory)
    ]
    actual = [p for p, _ in process_stream(mixed, factory)]
    assert sorted(actual, key=lambda p: (p.series_id, p.timestamp)) == expected


@pytest.mark.parametrize("policy", ["carry", "reset"])
def test_frozen_boundaries_prevent_future_suffix_affecting_earlier_targets(
    tmp_path: Path, policy: PastContext
) -> None:
    source = tmp_path / "trace.csv"

    def write_values(values: list[float]) -> None:
        source.write_text(
            "series_id,timestamp,value\n"
            + "".join(f"s,{point(i, v).timestamp.isoformat()},{v}\n" for i, v in enumerate(values)),
            encoding="utf-8",
            newline="\n",
        )

    values = [float(i % 9) for i in range(40)]
    write_values(values)
    spec = SourceSpec(
        "trace.csv", "Hand-authored split stress fixture", "Software test", "synthetic"
    )
    inventory = build_inventory(tmp_path, "boundary-smoke", "synthetic_smoke", [spec])
    inventory_path, split_path = tmp_path / "inventory.json", tmp_path / "split.json"
    write_inventory(inventory, inventory_path)
    split = build_chronological_split(
        inventory, [ChronologicalCut("s", 16, 28)], lookback=4, past_context=policy
    )
    write_split_manifest(split, split_path)
    assert validate_split_manifest(split_path, inventory_path, tmp_path) == split

    def train_frames() -> Iterator[FeatureFrame]:
        region = split.ranges[0]
        extractor = RollingFeatureExtractor(window_size=4, min_history=4)
        for index, p in enumerate(read_observations(source)):
            if region.context_start <= index < region.target_stop:
                frame = extractor.process(p)
                if index >= region.target_start:
                    yield frame

    original = list(train_frames())
    changed = values[:28] + [1000.0] * 12
    write_values(changed)
    assert list(train_frames()) == original
    # Frozen provenance detects the edit even though prior causal decisions are unchanged.
    with pytest.raises(ContractError):
        validate_inventory(inventory_path, tmp_path)
    with pytest.raises(ContractError):
        validate_split_manifest(split_path, inventory_path, tmp_path)
