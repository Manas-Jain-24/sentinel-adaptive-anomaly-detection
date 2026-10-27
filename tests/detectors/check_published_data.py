"""Reproduce consumer checks with exact Git data-module bytes, without a merge.

Manual dev utility, not part of inference or the experiment harness. Example:
python tests/detectors/check_published_data.py --ref <40-hex-commit> \
    --snapshot-dir outputs/consumer-review-001 -- tests -q
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import sentinel.data


class _Counts:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}

    def pytest_terminal_summary(self, terminalreporter: Any) -> None:
        self.values = {
            name: len(terminalreporter.stats.get(name, []))
            for name in ("passed", "failed", "skipped", "error", "xfailed", "xpassed")
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", required=True, help="Exact locally fetched 40-hex commit")
    parser.add_argument("--snapshot-dir", required=True, type=Path)
    options, arguments = parser.parse_known_args()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", options.ref):
        parser.error("--ref must be an exact 40-hex commit, not a moving branch")
    root = Path(__file__).resolve().parents[2]
    commit = options.ref.lower()
    subprocess.run(
        ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"],
        cwd=root,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    destination = (root / options.snapshot_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    report_path = destination / "report.json"
    if report_path.exists():
        parser.error("report.json exists; choose a fresh --snapshot-dir")
    hashes: dict[str, str] = {}
    for name in ("features", "inventory", "splits"):
        source_path = f"src/sentinel/data/{name}.py"
        source = subprocess.check_output(["git", "show", f"{commit}:{source_path}"], cwd=root)
        hashes[source_path] = hashlib.sha256(source).hexdigest()
        snapshot = destination / f"{name}.py"
        if snapshot.exists():
            if snapshot.read_bytes() != source:
                parser.error(f"{snapshot.name} differs; preserve it and use a fresh directory")
        else:
            with snapshot.open("xb") as stream:
                stream.write(source)
        module_name = f"sentinel.data.{name}"
        spec = importlib.util.spec_from_file_location(module_name, snapshot)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Cannot load {module_name}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        setattr(sentinel.data, name, module)
    if arguments[:1] == ["--"]:
        arguments = arguments[1:]
    counts = _Counts()
    os.chdir(root)
    exit_code = int(pytest.main(arguments or ["tests", "-q"], plugins=[counts]))
    report = {
        "scope": "synthetic_consumer_compatibility",
        "official_benchmark": False,
        "published_data_commit": commit,
        "source_sha256": hashes,
        "pytest_arguments": arguments or ["tests", "-q"],
        "pytest_counts": counts.values,
        "exit_code": exit_code,
    }
    with report_path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
