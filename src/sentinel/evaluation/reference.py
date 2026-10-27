"""Provisional event-trigger F1 v0. See docs/EVALUATION.md before interpreting."""

import json
import statistics
from collections import defaultdict
from collections.abc import Iterable
from math import isfinite
from pathlib import Path
from typing import Any

from sentinel.contracts import AnomalyWindow, ContractError, parse_timestamp
from sentinel.data.io import read_windows
from sentinel.pipeline import sha256_file


def _calculate_quantile(data: list[float], q: float) -> float:
    """Compute empirical quantile using linear interpolation on sorted observations."""
    if not data:
        raise ValueError("Cannot calculate quantile of empty data")
    if len(data) == 1:
        return data[0]
    sorted_data = sorted(data)
    pos = q * (len(sorted_data) - 1)
    base = int(pos)
    rest = pos - base
    if base + 1 < len(sorted_data):
        return sorted_data[base] + rest * (sorted_data[base + 1] - sorted_data[base])
    return sorted_data[base]


def event_metrics(
    records: Iterable[dict[str, Any]], windows: list[AnomalyWindow]
) -> dict[str, Any]:
    grouped: dict[str, list[AnomalyWindow]] = defaultdict(list)
    for window in windows:
        grouped[window.series_id].append(window)
    for items in grouped.values():
        items.sort(key=lambda item: item.start)
        for previous, current in zip(items, items[1:], strict=False):
            if current.start <= previous.end:
                raise ContractError("Overlapping/touching closed truth windows are ambiguous")

    matched: set[tuple[str, int]] = set()
    active: dict[str, bool] = {}
    last_time: dict[str, Any] = {}
    first_time: dict[str, Any] = {}
    delays: list[float] = []

    series_tp: dict[str, int] = defaultdict(int)
    series_fp: dict[str, int] = defaultdict(int)
    series_delays: dict[str, list[float]] = defaultdict(list)
    series_warmup: dict[str, int] = defaultdict(int)
    series_counts: dict[str, int] = defaultdict(int)

    tp = fp = warmup_count = count = 0
    for record in records:
        try:
            series = record["series_id"]
            if not isinstance(series, str) or not series.strip():
                raise ContractError("Invalid series_id")
            timestamp = parse_timestamp(record["timestamp"])
            if series in last_time and timestamp <= last_time[series]:
                raise ContractError("Prediction timestamps must increase within each series")
            first_time.setdefault(series, timestamp)
            last_time[series] = timestamp
            if record["schema_version"] != "1.0":
                raise ContractError("Unsupported prediction schema")
            ready = record["ready"]
            if type(ready) is not bool:
                raise ContractError("ready must be boolean")
            score, threshold = record["score"], record["threshold"]
            if type(threshold) not in (int, float) or not isfinite(threshold) or threshold <= 0:
                raise ContractError("Invalid threshold")
            if ready:
                if type(score) not in (int, float) or not isfinite(score) or score < 0:
                    raise ContractError("Ready score must be finite and nonnegative")
                expected = "ANOMALOUS" if score >= threshold else "NORMAL"
            else:
                if score is not None:
                    raise ContractError("Warmup score must be null")
                expected = "NORMAL"
                warmup_count += 1
                series_warmup[series] += 1
            if record["label"] != expected:
                raise ContractError("Label contradicts score/threshold/readiness")
            flagged = record["label"] == "ANOMALOUS"
        except (KeyError, TypeError) as exc:
            raise ContractError(f"Malformed prediction record: {exc}") from exc
        count += 1
        series_counts[series] += 1
        if flagged and not active.get(series, False):
            found = next(
                (
                    index
                    for index, window in enumerate(grouped.get(series, []))
                    if window.start <= timestamp <= window.end and (series, index) not in matched
                ),
                None,
            )
            if found is None:
                fp += 1
                series_fp[series] += 1
            else:
                matched.add((series, found))
                tp += 1
                series_tp[series] += 1
                delay_val = (timestamp - grouped[series][found].start).total_seconds()
                delays.append(delay_val)
                series_delays[series].append(delay_val)
        active[series] = flagged

    if not count:
        raise ContractError("Predictions are empty")
    for window in windows:
        if (
            window.series_id not in last_time
            or window.start < first_time[window.series_id]
            or window.end > last_time[window.series_id]
        ):
            raise ContractError("Truth window lies outside prediction coverage")

    all_series = sorted(last_time.keys())
    per_series: dict[str, dict[str, Any]] = {}
    for s in all_series:
        s_windows = grouped.get(s, [])
        s_tp = series_tp[s]
        s_fp = series_fp[s]
        s_fn = len(s_windows) - s_tp
        s_prec = s_tp / (s_tp + s_fp) if (s_tp + s_fp) else 0.0
        s_rec = s_tp / (s_tp + s_fn) if (s_tp + s_fn) else 0.0
        s_f1 = 2 * s_tp / (2 * s_tp + s_fp + s_fn) if (2 * s_tp + s_fp + s_fn) else 0.0
        s_d = series_delays[s]
        per_series[s] = {
            "tp": s_tp,
            "fp": s_fp,
            "fn": s_fn,
            "precision": s_prec,
            "recall": s_rec,
            "event_f1": s_f1,
            "windows_count": len(s_windows),
            "observations": series_counts[s],
            "warmup_points": series_warmup[s],
            "delay_seconds": s_d,
            "mean_delay_seconds": sum(s_d) / len(s_d) if s_d else None,
            "median_delay_seconds": statistics.median(s_d) if s_d else None,
        }

    fn = len(windows) - tp
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0

    num_series = len(all_series)
    macro_precision = (
        sum(item["precision"] for item in per_series.values()) / num_series if num_series else 0.0
    )
    macro_recall = (
        sum(item["recall"] for item in per_series.values()) / num_series if num_series else 0.0
    )
    macro_event_f1 = (
        sum(item["event_f1"] for item in per_series.values()) / num_series if num_series else 0.0
    )

    mean_delay = sum(delays) / len(delays) if delays else None
    median_delay = statistics.median(delays) if delays else None
    min_delay = min(delays) if delays else None
    max_delay = max(delays) if delays else None
    p95_delay = _calculate_quantile(delays, 0.95) if delays else None

    return {
        "metric_id": "provisional_event_trigger_f1_v0",
        "official_metric": False,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "event_f1": f1,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_event_f1": macro_event_f1,
        "delay_seconds": delays,
        "mean_delay_seconds": mean_delay,
        "median_delay_seconds": median_delay,
        "min_delay_seconds": min_delay,
        "max_delay_seconds": max_delay,
        "p95_delay_seconds": p95_delay,
        "missed_events": fn,
        "warmup_points_included_in_coverage": warmup_count,
        "observations": count,
        "series_count": num_series,
        "per_series": per_series,
        "policy": {
            "matching": "first_trigger_in_closed_window",
            "pre_window_trigger": "false_positive_window_unmatched",
            "repeat_trigger_in_window": "false_positive",
            "zero_denominator_convention": 0.0,
            "warmup_policy": "included_in_coverage_unflagged",
        },
    }


def format_evaluation_report(metrics: dict[str, Any]) -> str:
    """Format evaluation metrics as an informative, markdown-formatted report."""
    f1 = metrics.get("event_f1", 0.0)
    prec = metrics.get("precision", 0.0)
    rec = metrics.get("recall", 0.0)
    macro_f1 = metrics.get("macro_event_f1", 0.0)
    macro_prec = metrics.get("macro_precision", 0.0)
    macro_rec = metrics.get("macro_recall", 0.0)
    tp, fp, fn = metrics.get("tp", 0), metrics.get("fp", 0), metrics.get("fn", 0)
    mean_d = metrics.get("mean_delay_seconds")
    median_d = metrics.get("median_delay_seconds")
    p95_d = metrics.get("p95_delay_seconds")
    min_d = metrics.get("min_delay_seconds")
    max_d = metrics.get("max_delay_seconds")

    mean_d_str = f"{mean_d:.2f}s" if mean_d is not None else "N/A"
    median_d_str = f"{median_d:.2f}s" if median_d is not None else "N/A"
    p95_d_str = f"{p95_d:.2f}s" if p95_d is not None else "N/A"
    min_d_str = f"{min_d:.2f}s" if min_d is not None else "N/A"
    max_d_str = f"{max_d:.2f}s" if max_d is not None else "N/A"

    lines = [
        f"# Evaluation Report: {metrics.get('metric_id', 'provisional_event_trigger_f1_v0')}",
        "",
        "## Overall Event Metrics",
        "",
        "| Metric | Micro (Pooled) | Macro (Per-Series Avg) |",
        "|---|---|---|",
        f"| **Event F1** | **{f1:.4f}** | **{macro_f1:.4f}** |",
        f"| **Precision** | {prec:.4f} | {macro_prec:.4f} |",
        f"| **Recall** | {rec:.4f} | {macro_rec:.4f} |",
        "",
        "## Event Counts & Coverage",
        "",
        f"- **True Positives (TP)**: {tp}",
        f"- **False Positives (FP)**: {fp}",
        f"- **False Negatives (FN / Misses)**: {fn}",
        f"- **Total Observations**: {metrics.get('observations', 0)}",
        f"- **Warmup Points in Coverage**: {metrics.get('warmup_points_included_in_coverage', 0)}",
        f"- **Distinct Series**: {metrics.get('series_count', 0)}",
        "",
        "## Detection Latency",
        "",
        "| Statistic | Value |",
        "|---|---|",
        f"| Mean Delay | {mean_d_str} |",
        f"| Median Delay | {median_d_str} |",
        f"| p95 Delay | {p95_d_str} |",
        f"| Min Delay | {min_d_str} |",
        f"| Max Delay | {max_d_str} |",
        "",
    ]

    per_series = metrics.get("per_series", {})
    if per_series:
        lines.extend(
            [
                "## Per-Series Breakdown",
                "",
                "| Series | Windows | TP | FP | FN | Precision | Recall | Event F1 | Delay | Obs |",
                "|---|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for s_id, s_stats in per_series.items():
            s_mean_d = s_stats.get("mean_delay_seconds")
            s_mean_str = f"{s_mean_d:.2f}s" if s_mean_d is not None else "N/A"
            lines.append(
                f"| `{s_id}` | {s_stats['windows_count']} | {s_stats['tp']} | {s_stats['fp']} | "
                f"{s_stats['fn']} | {s_stats['precision']:.3f} | {s_stats['recall']:.3f} | "
                f"{s_stats['event_f1']:.3f} | {s_mean_str} | {s_stats['observations']} |"
            )
        lines.append("")

    policy = metrics.get("policy", {})
    if policy:
        lines.extend(
            [
                "## Policy & Semantics",
                "",
                f"- **Matching Rule**: {policy.get('matching')}",
                f"- **Pre-Window Trigger Policy**: {policy.get('pre_window_trigger')}",
                f"- **Repeat Trigger in Window**: {policy.get('repeat_trigger_in_window')}",
                f"- **Zero Denominator Convention**: {policy.get('zero_denominator_convention')}",
                f"- **Warmup Policy**: {policy.get('warmup_policy')}",
                "",
            ]
        )

    return "\n".join(lines)


def evaluate_run(run_dir: Path, windows_path: Path) -> dict[str, Any]:
    metadata = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    if metadata.get("evaluation_scope") not in ("synthetic_smoke", "development_validation"):
        raise ContractError("Unsupported scope; official scoring adapter is not implemented")
    predictions_path = run_dir / "predictions.jsonl"
    if metadata.get("predictions_sha256") != sha256_file(predictions_path):
        raise ContractError("Predictions checksum differs from run manifest")
    with predictions_path.open(encoding="utf-8") as stream:
        result = event_metrics((json.loads(line) for line in stream), read_windows(windows_path))
    return {
        **result,
        "evaluation_scope": metadata["evaluation_scope"],
        "dataset_id": metadata["dataset_id"],
        "input_sha256": metadata["input_sha256"],
        "windows_sha256": sha256_file(windows_path),
    }
