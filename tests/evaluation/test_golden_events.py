"""Comprehensive event golden tests for provisional event-trigger F1 v0.

Owned by Mayank (MY-01). Tests independently calculated TP/FP/FN counts, boundary
conditions, repeated episodes, warmup interactions, no-event series, gaps,
interleaving, micro vs macro aggregation, and strict contract error rejections.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from sentinel.contracts import AnomalyWindow, ContractError
from sentinel.evaluation.reference import event_metrics, format_evaluation_report


def iso_time(minute: int, second: int = 0, hour: int = 0) -> datetime:
    """Construct an explicit UTC datetime for deterministic test fixtures."""
    return datetime(2026, 1, 1, hour, minute, second, tzinfo=UTC)


def make_record(
    series_id: str,
    timestamp: datetime,
    score: float | None = 0.5,
    threshold: float = 3.0,
    ready: bool = True,
    label: str | None = None,
    schema_version: str = "1.0",
) -> dict[str, Any]:
    """Helper to construct valid or intentionally mutated prediction dictionaries."""
    if label is None:
        if not ready:
            label = "NORMAL"
        else:
            assert score is not None
            label = "ANOMALOUS" if score >= threshold else "NORMAL"
    return {
        "series_id": series_id,
        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "value": 10.0,
        "score": score,
        "threshold": threshold,
        "label": label,
        "ready": ready,
        "schema_version": schema_version,
    }


def make_window(series_id: str, start: datetime, end: datetime) -> AnomalyWindow:
    """Helper to construct an AnomalyWindow."""
    return AnomalyWindow(series_id=series_id, start=start, end=end)


# -----------------------------------------------------------------------------
# 1. Exact Window Boundary & Duration Tests
# -----------------------------------------------------------------------------


def test_trigger_at_exact_window_start() -> None:
    """Trigger occurs exactly on window.start: counted as TP with 0 delay."""
    t0 = iso_time(0)
    t1 = iso_time(1)
    t2 = iso_time(2)
    t3 = iso_time(3)
    records = [
        make_record("s", t0, score=0.1),
        make_record("s", t1, score=5.0),  # Exact match on window.start
        make_record("s", t2, score=5.0),
        make_record("s", t3, score=0.1),
    ]
    windows = [make_window("s", t1, t2)]
    metrics = event_metrics(records, windows)

    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (1, 0, 0)
    assert metrics["event_f1"] == 1.0
    assert metrics["delay_seconds"] == [0.0]
    assert metrics["mean_delay_seconds"] == 0.0


def test_trigger_at_exact_window_end() -> None:
    """Trigger occurs on the very last point of a closed window [start, end]."""
    t0 = iso_time(0)
    t1 = iso_time(1)
    t2 = iso_time(2)
    t3 = iso_time(3)
    records = [
        make_record("s", t0, score=0.1),
        make_record("s", t1, score=0.1),
        make_record("s", t2, score=5.0),  # Exact match on window.end
        make_record("s", t3, score=0.1),
    ]
    windows = [make_window("s", t1, t2)]
    metrics = event_metrics(records, windows)

    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (1, 0, 0)
    assert metrics["event_f1"] == 1.0
    assert metrics["delay_seconds"] == [60.0]
    assert metrics["mean_delay_seconds"] == 60.0


def test_point_duration_window() -> None:
    """Truth window where start == end (single-timestamp anomaly)."""
    t0 = iso_time(0)
    t1 = iso_time(1)
    t2 = iso_time(2)
    records = [
        make_record("s", t0, score=0.1),
        make_record("s", t1, score=5.0),  # Matches single-point window
        make_record("s", t2, score=0.1),
    ]
    windows = [make_window("s", t1, t1)]
    metrics = event_metrics(records, windows)

    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (1, 0, 0)
    assert metrics["event_f1"] == 1.0
    assert metrics["delay_seconds"] == [0.0]


# -----------------------------------------------------------------------------
# 2. Pre-Window and Post-Window Conservative Matching Policy
# -----------------------------------------------------------------------------


def test_pre_window_trigger_conservative_policy() -> None:
    """Episode starting before window and continuing inside is NOT credited as a hit.

    Explicit conservative trigger policy:
    - Episode began at t1 (before window [t2, t3]), causing a false positive.
    - Since the episode continues through t2 and t3 without a new trigger,
      window [t2, t3] is a miss (FN).
    """
    t0 = iso_time(0)
    t1 = iso_time(1)  # Episode starts here (outside window)
    t2 = iso_time(2)  # Window starts here
    t3 = iso_time(3)  # Window ends here
    t4 = iso_time(4)
    records = [
        make_record("s", t0, score=0.1),
        make_record("s", t1, score=5.0),
        make_record("s", t2, score=5.0),
        make_record("s", t3, score=5.0),
        make_record("s", t4, score=0.1),
    ]
    windows = [make_window("s", t2, t3)]
    metrics = event_metrics(records, windows)

    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (0, 1, 1)
    assert metrics["event_f1"] == 0.0
    assert metrics["delay_seconds"] == []
    assert metrics["mean_delay_seconds"] is None
    assert metrics["missed_events"] == 1


def test_post_window_trigger_is_miss_and_fp() -> None:
    """Alert triggers 1 second after window closes: window is missed (FN) and alert is FP."""
    t0 = iso_time(0)
    t1 = iso_time(1)  # Window starts
    t2 = iso_time(2)  # Window ends
    t3 = iso_time(3)  # Alert triggers late
    t4 = iso_time(4)
    records = [
        make_record("s", t0, score=0.1),
        make_record("s", t1, score=0.1),
        make_record("s", t2, score=0.1),
        make_record("s", t3, score=5.0),
        make_record("s", t4, score=0.1),
    ]
    windows = [make_window("s", t1, t2)]
    metrics = event_metrics(records, windows)

    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (0, 1, 1)
    assert metrics["event_f1"] == 0.0
    assert metrics["missed_events"] == 1


# -----------------------------------------------------------------------------
# 3. Repeated Episodes and Continuous Spans
# -----------------------------------------------------------------------------


def test_repeated_episodes_inside_single_window() -> None:
    """Three separate anomalous pulses inside a single truth window.

    First pulse matches window (TP=1).
    Second and third pulses inside the same window are penalized as false positives (FP=2).
    """
    t0 = iso_time(0)
    t1 = iso_time(1)  # Pulse 1: hit window
    t2 = iso_time(2)  # Normal
    t3 = iso_time(3)  # Pulse 2: repeat inside same window -> FP
    t4 = iso_time(4)  # Normal
    t5 = iso_time(5)  # Pulse 3: repeat inside same window -> FP
    t6 = iso_time(6)
    records = [
        make_record("s", t0, score=0.1),
        make_record("s", t1, score=5.0),
        make_record("s", t2, score=0.1),
        make_record("s", t3, score=5.0),
        make_record("s", t4, score=0.1),
        make_record("s", t5, score=5.0),
        make_record("s", t6, score=0.1),
    ]
    windows = [make_window("s", t1, t5)]
    metrics = event_metrics(records, windows)

    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (1, 2, 0)
    assert metrics["precision"] == pytest.approx(1 / 3)
    assert metrics["recall"] == 1.0
    assert metrics["event_f1"] == pytest.approx(0.5)
    assert metrics["delay_seconds"] == [0.0]


def test_continuous_episode_spanning_entire_window() -> None:
    """A continuous run of ANOMALOUS rows represents ONE episode with ONE trigger."""
    times = [iso_time(i) for i in range(10)]
    records = (
        [make_record("s", times[0], score=0.1), make_record("s", times[1], score=0.1)]
        + [make_record("s", times[i], score=5.0) for i in range(2, 7)]  # continuous episode
        + [make_record("s", times[7], score=0.1), make_record("s", times[8], score=0.1)]
    )
    windows = [make_window("s", times[2], times[6])]
    metrics = event_metrics(records, windows)

    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (1, 0, 0)
    assert metrics["event_f1"] == 1.0
    assert len(metrics["delay_seconds"]) == 1
    assert metrics["delay_seconds"][0] == 0.0


def test_multiple_disjoint_windows_partial_hits() -> None:
    """Three disjoint windows: 2 hits, 1 miss, plus 1 spurious alert outside windows."""
    # Window 1: [t1, t2] -> hit at t1 (delay=0)
    # Window 2: [t4, t6] -> hit at t5 (delay=60s)
    # Spurious: [t7] -> FP
    # Window 3: [t9, t10] -> missed (FN)
    times = [iso_time(i) for i in range(12)]
    records = [
        make_record("s", times[0], score=0.1),
        make_record("s", times[1], score=5.0),  # Hit window 1
        make_record("s", times[2], score=0.1),
        make_record("s", times[3], score=0.1),
        make_record("s", times[4], score=0.1),  # Window 2 starts
        make_record("s", times[5], score=5.0),  # Hit window 2 (delay 60s)
        make_record("s", times[6], score=0.1),
        make_record("s", times[7], score=5.0),  # Spurious alert -> FP
        make_record("s", times[8], score=0.1),
        make_record("s", times[9], score=0.1),  # Window 3 starts (missed)
        make_record("s", times[10], score=0.1),
        make_record("s", times[11], score=0.1),
    ]
    windows = [
        make_window("s", times[1], times[2]),
        make_window("s", times[4], times[6]),
        make_window("s", times[9], times[10]),
    ]
    metrics = event_metrics(records, windows)

    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (2, 1, 1)
    assert metrics["precision"] == pytest.approx(2 / 3)
    assert metrics["recall"] == pytest.approx(2 / 3)
    assert metrics["event_f1"] == pytest.approx(2 / 3)
    assert metrics["delay_seconds"] == [0.0, 60.0]
    assert metrics["mean_delay_seconds"] == pytest.approx(30.0)
    assert metrics["missed_events"] == 1


# -----------------------------------------------------------------------------
# 4. Warmup & Readiness Interactions
# -----------------------------------------------------------------------------


def test_window_during_warmup_is_missed() -> None:
    """Truth window occurs entirely during detector warmup (ready=False, score=None)."""
    times = [iso_time(i) for i in range(6)]
    records = [
        make_record("s", times[0], score=None, ready=False),
        make_record("s", times[1], score=None, ready=False),  # Window starts
        make_record("s", times[2], score=None, ready=False),  # Window ends
        make_record("s", times[3], score=0.1, ready=True),
        make_record("s", times[4], score=0.1, ready=True),
        make_record("s", times[5], score=0.1, ready=True),
    ]
    windows = [make_window("s", times[1], times[2])]
    metrics = event_metrics(records, windows)

    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (0, 0, 1)
    assert metrics["event_f1"] == 0.0
    assert metrics["warmup_points_included_in_coverage"] == 3
    assert metrics["missed_events"] == 1


def test_window_straddling_warmup_boundary() -> None:
    """Truth window begins during warmup but extends into ready phase, where it is triggered."""
    times = [iso_time(i) for i in range(6)]
    records = [
        make_record("s", times[0], score=None, ready=False),
        make_record("s", times[1], score=None, ready=False),  # Window starts in warmup
        make_record("s", times[2], score=5.0, ready=True),  # First ready point flags window!
        make_record("s", times[3], score=5.0, ready=True),
        make_record("s", times[4], score=0.1, ready=True),
        make_record("s", times[5], score=0.1, ready=True),
    ]
    windows = [make_window("s", times[1], times[3])]
    metrics = event_metrics(records, windows)

    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (1, 0, 0)
    assert metrics["event_f1"] == 1.0
    assert metrics["delay_seconds"] == [60.0]  # Measured from window.start (times[1])
    assert metrics["warmup_points_included_in_coverage"] == 2


# -----------------------------------------------------------------------------
# 5. Clean / No-Event Series & Zero-Denominator Policy
# -----------------------------------------------------------------------------


def test_clean_series_no_events_no_alerts() -> None:
    """Zero truth windows, zero alerts: precision, recall, and F1 are 0.0 by convention."""
    times = [iso_time(i) for i in range(4)]
    records = [make_record("s", t, score=0.1) for t in times]
    metrics = event_metrics(records, [])

    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (0, 0, 0)
    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["event_f1"] == 0.0
    assert metrics["mean_delay_seconds"] is None
    assert metrics["missed_events"] == 0


def test_clean_series_with_false_positives() -> None:
    """Zero truth windows, but model triggered 2 false alarms."""
    times = [iso_time(i) for i in range(4)]
    records = [
        make_record("s", times[0], score=0.1),
        make_record("s", times[1], score=5.0),  # FP 1
        make_record("s", times[2], score=0.1),
        make_record("s", times[3], score=5.0),  # FP 2
    ]
    metrics = event_metrics(records, [])

    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (0, 2, 0)
    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["event_f1"] == 0.0


# -----------------------------------------------------------------------------
# 6. Micro vs. Macro Multi-Series Divergence
# -----------------------------------------------------------------------------


def test_micro_vs_macro_aggregation() -> None:
    """Demonstrates that pooled Micro F1 and per-series Macro F1 can diverge significantly.

    Series 's1': 1 window, 1 hit -> F1 = 1.0
    Series 's2': 0 windows, 0 alerts -> F1 = 0.0 (by zero-denominator convention)

    Pooled Micro: 1 TP, 0 FP, 0 FN -> Micro F1 = 1.0
    Macro Avg: (1.0 + 0.0) / 2 = 0.5
    """
    times = [iso_time(i) for i in range(4)]
    records = [
        make_record("s1", times[0], score=0.1),
        make_record("s1", times[1], score=5.0),  # Hit
        make_record("s1", times[2], score=0.1),
        make_record("s1", times[3], score=0.1),
        make_record("s2", times[0], score=0.1),
        make_record("s2", times[1], score=0.1),
        make_record("s2", times[2], score=0.1),
        make_record("s2", times[3], score=0.1),
    ]
    windows = [make_window("s1", times[1], times[2])]
    metrics = event_metrics(records, windows)

    assert metrics["event_f1"] == 1.0  # Micro
    assert metrics["macro_event_f1"] == pytest.approx(0.5)  # Macro
    assert metrics["per_series"]["s1"]["event_f1"] == 1.0
    assert metrics["per_series"]["s2"]["event_f1"] == 0.0
    assert metrics["series_count"] == 2


# -----------------------------------------------------------------------------
# 7. Multi-Series Stream Interleaving & State Isolation
# -----------------------------------------------------------------------------


def test_multiseries_interleaving_state_isolation() -> None:
    """Chronologically interleaved points from multiple series do not pollute each other.

    Stream order:
      alpha@t0 (NORMAL)
      beta@t0 (NORMAL)
      alpha@t1 (ANOMALOUS -> matches alpha window)
      beta@t1 (ANOMALOUS -> matches beta window)
      alpha@t2 (ANOMALOUS -> continues alpha episode)
      beta@t2 (NORMAL -> ends beta episode)
      alpha@t3 (NORMAL -> ends alpha episode)
      beta@t3 (NORMAL)
    """
    t0, t1, t2, t3 = [iso_time(i) for i in range(4)]
    interleaved_stream = [
        make_record("alpha", t0, score=0.1),
        make_record("beta", t0, score=0.1),
        make_record("alpha", t1, score=5.0),
        make_record("beta", t1, score=5.0),
        make_record("alpha", t2, score=5.0),
        make_record("beta", t2, score=0.1),
        make_record("alpha", t3, score=0.1),
        make_record("beta", t3, score=0.1),
    ]
    windows = [
        make_window("alpha", t1, t2),
        make_window("beta", t1, t2),
    ]
    metrics = event_metrics(interleaved_stream, windows)

    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (2, 0, 0)
    assert metrics["event_f1"] == 1.0
    assert metrics["macro_event_f1"] == 1.0
    assert metrics["per_series"]["alpha"]["tp"] == 1
    assert metrics["per_series"]["beta"]["tp"] == 1
    assert metrics["per_series"]["alpha"]["fp"] == 0
    assert metrics["per_series"]["beta"]["fp"] == 0


# -----------------------------------------------------------------------------
# 8. Irregular Cadence and Temporal Gaps
# -----------------------------------------------------------------------------


def test_large_temporal_gaps_without_cadence_assumption() -> None:
    """Stream with large 2-hour jumps between observations; no cadence assumption breaks it."""
    t0 = iso_time(0, hour=0)
    t1 = iso_time(0, hour=2)  # 2h gap
    t2 = iso_time(0, hour=4)  # 2h gap
    t3 = iso_time(0, hour=6)
    records = [
        make_record("s", t0, score=0.1),
        make_record("s", t1, score=5.0),
        make_record("s", t2, score=5.0),
        make_record("s", t3, score=0.1),
    ]
    windows = [make_window("s", t1, t2)]
    metrics = event_metrics(records, windows)

    assert (metrics["tp"], metrics["fp"], metrics["fn"]) == (1, 0, 0)
    assert metrics["event_f1"] == 1.0
    assert metrics["delay_seconds"] == [0.0]


# -----------------------------------------------------------------------------
# 9. Latency Distributions (Mean, Median, p95, Min, Max)
# -----------------------------------------------------------------------------


def test_delay_percentile_calculations() -> None:
    """Verifies delay distribution calculations: mean, median, min, max, and p95."""
    # 5 windows with delays: 10s, 20s, 30s, 40s, 50s
    # p95 on [10, 20, 30, 40, 50]: index = 0.95 * 4 = 3.8 -> 40 + 0.8 * 10 = 48.0s
    records = []
    windows = []
    base_time = iso_time(0)
    for i, delay_sec in enumerate([10.0, 20.0, 30.0, 40.0, 50.0]):
        w_start = base_time + timedelta(minutes=i * 10)
        w_end = w_start + timedelta(minutes=5)
        trigger = w_start + timedelta(seconds=delay_sec)
        windows.append(make_window("s", w_start, w_end))
        records.extend(
            [
                make_record("s", w_start, score=0.1),
                make_record("s", trigger, score=5.0),
                make_record("s", w_end, score=0.1),
            ]
        )
    # Add a final bounding record so all windows are comfortably within coverage
    records.append(make_record("s", base_time + timedelta(hours=2), score=0.1))

    metrics = event_metrics(records, windows)
    assert metrics["tp"] == 5
    assert metrics["mean_delay_seconds"] == pytest.approx(30.0)
    assert metrics["median_delay_seconds"] == pytest.approx(30.0)
    assert metrics["min_delay_seconds"] == pytest.approx(10.0)
    assert metrics["max_delay_seconds"] == pytest.approx(50.0)
    assert metrics["p95_delay_seconds"] == pytest.approx(48.0)


# -----------------------------------------------------------------------------
# 10. Strict Contract Validation & Rejections
# -----------------------------------------------------------------------------


def test_reject_non_monotonic_timestamps() -> None:
    t0, t1 = iso_time(0), iso_time(1)
    with pytest.raises(ContractError, match="timestamps must increase"):
        event_metrics([make_record("s", t1), make_record("s", t0)], [])
    with pytest.raises(ContractError, match="timestamps must increase"):
        event_metrics([make_record("s", t1), make_record("s", t1)], [])


def test_reject_empty_series_id() -> None:
    t0 = iso_time(0)
    with pytest.raises(ContractError, match="Invalid series_id"):
        event_metrics([make_record("", t0)], [])
    with pytest.raises(ContractError, match="Invalid series_id"):
        event_metrics([make_record("   ", t0)], [])


def test_reject_unsupported_schema_version() -> None:
    t0 = iso_time(0)
    with pytest.raises(ContractError, match="Unsupported prediction schema"):
        event_metrics([make_record("s", t0, schema_version="2.0")], [])


def test_reject_invalid_ready_type() -> None:
    t0 = iso_time(0)
    rec = make_record("s", t0)
    rec["ready"] = "true"  # type: ignore
    with pytest.raises(ContractError, match="ready must be boolean"):
        event_metrics([rec], [])


def test_reject_negative_or_non_finite_ready_score() -> None:
    t0 = iso_time(0)
    with pytest.raises(ContractError, match="nonnegative"):
        event_metrics([make_record("s", t0, score=-1.0)], [])
    with pytest.raises(ContractError, match="nonnegative"):
        event_metrics([make_record("s", t0, score=float("inf"))], [])
    with pytest.raises(ContractError, match="nonnegative"):
        event_metrics([make_record("s", t0, score=float("nan"))], [])


def test_reject_invalid_threshold() -> None:
    t0 = iso_time(0)
    with pytest.raises(ContractError, match="Invalid threshold"):
        event_metrics([make_record("s", t0, threshold=0.0)], [])
    with pytest.raises(ContractError, match="Invalid threshold"):
        event_metrics([make_record("s", t0, threshold=-2.0)], [])
    with pytest.raises(ContractError, match="Invalid threshold"):
        event_metrics([make_record("s", t0, threshold=float("inf"))], [])


def test_reject_warmup_score_not_null() -> None:
    t0 = iso_time(0)
    with pytest.raises(ContractError, match="Warmup score must be null"):
        event_metrics([make_record("s", t0, score=2.0, ready=False)], [])


def test_reject_label_contradiction() -> None:
    t0 = iso_time(0)
    # Score >= threshold but labeled NORMAL
    with pytest.raises(ContractError, match="contradicts"):
        event_metrics([make_record("s", t0, score=5.0, threshold=3.0, label="NORMAL")], [])
    # Score < threshold but labeled ANOMALOUS
    with pytest.raises(ContractError, match="contradicts"):
        event_metrics([make_record("s", t0, score=1.0, threshold=3.0, label="ANOMALOUS")], [])
    # Warmup point labeled ANOMALOUS
    with pytest.raises(ContractError, match="contradicts"):
        event_metrics([make_record("s", t0, score=None, ready=False, label="ANOMALOUS")], [])


def test_reject_window_outside_coverage() -> None:
    t1, t2, t3 = iso_time(1), iso_time(2), iso_time(3)
    # Window starts before first observation
    with pytest.raises(ContractError, match="outside prediction coverage"):
        event_metrics([make_record("s", t2), make_record("s", t3)], [make_window("s", t1, t2)])
    # Window ends after last observation
    with pytest.raises(ContractError, match="outside prediction coverage"):
        event_metrics([make_record("s", t1), make_record("s", t2)], [make_window("s", t1, t3)])
    # Window for series not present in predictions
    with pytest.raises(ContractError, match="outside prediction coverage"):
        event_metrics([make_record("s1", t1), make_record("s1", t2)], [make_window("s2", t1, t2)])


def test_reject_overlapping_or_touching_windows() -> None:
    t1, t2, t3 = iso_time(1), iso_time(2), iso_time(3)
    # Touching windows: [t1, t2] and [t2, t3]
    with pytest.raises(ContractError, match="Overlapping/touching"):
        event_metrics(
            [make_record("s", t1), make_record("s", t3)],
            [make_window("s", t1, t2), make_window("s", t2, t3)],
        )


# -----------------------------------------------------------------------------
# 11. Report Formatting Function
# -----------------------------------------------------------------------------


def test_format_evaluation_report() -> None:
    """Verify that format_evaluation_report returns structured markdown."""
    t0, t1, t2 = iso_time(0), iso_time(1), iso_time(2)
    records = [
        make_record("s1", t0, score=0.1),
        make_record("s1", t1, score=5.0),
        make_record("s1", t2, score=0.1),
    ]
    windows = [make_window("s1", t1, t2)]
    metrics = event_metrics(records, windows)
    report_text = format_evaluation_report(metrics)

    assert "# Evaluation Report: provisional_event_trigger_f1_v0" in report_text
    assert "Overall Event Metrics" in report_text
    assert "| **Event F1** | **1.0000** |" in report_text
    assert "- **True Positives (TP)**: 1" in report_text
    assert "Per-Series Breakdown" in report_text
    assert "`s1`" in report_text
    assert "Policy & Semantics" in report_text
