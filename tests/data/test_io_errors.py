"""Canonical CSV failures must reach inventory/replay as actionable contract errors."""

import csv
import logging
from pathlib import Path

import pytest

from sentinel.cli import main
from sentinel.contracts import ContractError
from sentinel.data.inventory import SourceSpec, build_inventory
from sentinel.data.io import read_observations

HEADER = "series_id,timestamp,value\n"
VALID = "s,2026-01-01T00:00:00Z,1\n"


@pytest.mark.parametrize(
    "bad_row",
    ['s,2026-01-01T00:01:00Z,"2\n', 's,2026-01-01T00:01:00Z,"2"trailing\n'],
)
def test_broken_csv_quoting_cannot_become_an_observation(tmp_path: Path, bad_row: str) -> None:
    source = tmp_path / "broken.csv"
    source.write_text(HEADER + VALID + bad_row, encoding="utf-8")
    observations = read_observations(source)
    assert next(observations).value == 1
    with pytest.raises(ContractError, match="CSV.*line.*broken.csv"):
        next(observations)


@pytest.mark.parametrize("in_header", [False, True])
def test_csv_field_limit_is_a_contract_error_in_header_or_body(
    tmp_path: Path, in_header: bool
) -> None:
    source = tmp_path / "oversized.csv"
    content = "s" * 129 + ",timestamp,value\n" if in_header else HEADER + "s" * 129 + VALID[1:]
    source.write_text(content, encoding="utf-8")
    previous = csv.field_size_limit(128)
    try:
        with pytest.raises(ContractError, match="CSV.*line.*oversized.csv.*field"):
            list(read_observations(source))
    finally:
        csv.field_size_limit(previous)


@pytest.mark.parametrize("kind", ["unterminated", "oversized"])
def test_cli_csv_parser_failure_does_not_publish_partial_run(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str], kind: str
) -> None:
    source, destination = tmp_path / "bad.csv", tmp_path / "run"
    bad = 's,2026-01-01T00:01:00Z,"2\n'
    if kind == "oversized":
        bad = "s" * 129 + ",2026-01-01T00:01:00Z,2\n"
    source.write_text(HEADER + VALID + bad, encoding="utf-8")
    previous = csv.field_size_limit(128)
    try:
        with caplog.at_level(logging.ERROR):
            result = main(
                [
                    "run",
                    "--input",
                    str(source),
                    "--config",
                    "configs/starter.json",
                    "--output-dir",
                    str(destination),
                    "--dataset-id",
                    "synthetic-csv-errors",
                    "--scope",
                    "synthetic_smoke",
                ]
            )
    finally:
        csv.field_size_limit(previous)
    assert result == 2
    assert "CSV" in caplog.text and "bad.csv" in caplog.text
    assert capsys.readouterr().out == ""
    assert not destination.exists()
    assert not list(tmp_path.glob(".sentinel-*"))
    assert source.read_text(encoding="utf-8") == HEADER + VALID + bad


def test_inventory_rejects_broken_csv_instead_of_certifying_its_checksum(tmp_path: Path) -> None:
    (tmp_path / "bad.csv").write_text(HEADER + 's,2026-01-01T00:00:00Z,"1\n', encoding="utf-8")
    spec = SourceSpec("bad.csv", "hand-authored test", "synthetic test fixture", "test")
    with pytest.raises(ContractError, match="bad.csv.*CSV"):
        build_inventory(tmp_path, "synthetic-csv-errors", "synthetic_smoke", [spec])


def test_valid_quoted_multiline_series_and_escaped_quote_still_parse(tmp_path: Path) -> None:
    source = tmp_path / "quoted.csv"
    source.write_text(
        HEADER + '"sensor,""A""\nroom",2026-01-01T05:30:00+05:30,"1.25"\n',
        encoding="utf-8",
        newline="\n",
    )
    observations = list(read_observations(source))
    assert len(observations) == 1
    assert observations[0].series_id == 'sensor,"A"\nroom'
    assert observations[0].value == 1.25
    assert observations[0].timestamp.isoformat() == "2026-01-01T00:00:00+00:00"
