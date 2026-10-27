from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from sentinel.config import load_config
from sentinel.evaluation.reference import evaluate_run
from sentinel.pipeline import run_file


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild the bundled synthetic Mission Control run"
    )
    parser.add_argument("--output-dir", type=Path, default=Path("frontend/web/public/demo"))
    args = parser.parse_args()
    output = args.output_dir.resolve()
    stream = output / "stream.csv"
    windows = output / "windows.json"
    if not stream.is_file() or not windows.is_file():
        parser.error("output directory must contain stream.csv and windows.json")
    print("validating canonical input", flush=True)
    with tempfile.TemporaryDirectory(prefix="sentinel-demo-", dir=output) as temp_name:
        run_dir = Path(temp_name) / "run"
        print("running detector", flush=True)
        run_file(
            stream,
            run_dir,
            load_config(Path("configs/starter.json")),
            "synthetic_smoke",
            "synthetic-mission-control-v1",
        )
        print("evaluating saved output", flush=True)
        evaluation = evaluate_run(run_dir, windows)
        (run_dir / "evaluation.json").write_text(
            json.dumps(evaluation, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n"
        )
        print("publishing bundled artifacts", flush=True)
        for name in ("predictions.jsonl", "run.json", "evaluation.json"):
            shutil.copyfile(run_dir / name, output / name)
    print(f"Rebuilt synthetic demo artifacts in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
