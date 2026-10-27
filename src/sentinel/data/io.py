import csv
import json
from collections.abc import Iterator
from pathlib import Path

from sentinel.contracts import AnomalyWindow, ContractError, Observation, parse_timestamp


def read_observations(path: Path) -> Iterator[Observation]:
    """Read canonical CSV only. Raw NAB adaptation is a future explicit step."""
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        try:
            if reader.fieldnames != ["series_id", "timestamp", "value"]:
                raise ContractError("CSV header must be exactly series_id,timestamp,value")
            count = 0
            for line, row in enumerate(reader, start=2):
                try:
                    if None in row or any(value is None for value in row.values()):
                        raise ContractError("Wrong number of CSV columns")
                    observation = Observation(
                        row["series_id"], parse_timestamp(row["timestamp"]), float(row["value"])
                    )
                except (ValueError, TypeError) as exc:
                    raise ContractError(f"{path}: CSV row {line}: {exc}") from exc
                count += 1
                yield observation
            if count == 0:
                raise ContractError("Input CSV contains no observations")
        except csv.Error as exc:
            # DictReader advances line_num only after a successfully parsed record.
            # A malformed multiline field may span later lines, so report its start
            # approximately rather than claim an exact physical error location.
            raise ContractError(f"CSV near line {reader.line_num + 1} in {path}: {exc}") from exc


def read_windows(path: Path) -> list[AnomalyWindow]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
        raise ContractError("Window file requires schema_version 1.0")
    raw_windows = payload.get("windows")
    if not isinstance(raw_windows, list):
        raise ContractError("windows must be a list")
    windows = []
    for item in raw_windows:
        if not isinstance(item, dict) or set(item) != {"series_id", "start", "end"}:
            raise ContractError("Window requires series_id,start,end")
        windows.append(
            AnomalyWindow(
                item["series_id"], parse_timestamp(item["start"]), parse_timestamp(item["end"])
            )
        )
    return windows
