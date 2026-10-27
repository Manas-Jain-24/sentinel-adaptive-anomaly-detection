import argparse
import json
import logging
from pathlib import Path
from typing import cast

from sentinel.config import load_config
from sentinel.contracts import ContractError, EvaluationScope
from sentinel.detectors.selection import ModelConfig, load_model_config
from sentinel.evaluation.reference import evaluate_run
from sentinel.pipeline import run_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sentinel Pulse starter (unofficial schemas)")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Sequential replay through a selected causal detector")
    run.add_argument("--input", type=Path, required=True)
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--dataset-id", required=True)
    model = run.add_mutually_exclusive_group()
    model.add_argument(
        "--detector",
        choices=["mad", "zscore", "residual"],
        help="Fixed-threshold model; default mad",
    )
    model.add_argument(
        "--model-config", type=Path, help="Separate model/seasonal/quantile settings JSON"
    )
    run.add_argument(
        "--split-manifest",
        type=Path,
        help=(
            "Snapshot/hash an optional split manifest; "
            "does not validate membership or feed inference"
        ),
    )
    run.add_argument(
        "--scope", choices=["synthetic_smoke", "development_validation"], required=True
    )
    evaluate = commands.add_parser(
        "evaluate", help="Provisional local event F1, not official scoring"
    )
    evaluate.add_argument("--run-dir", type=Path, required=True)
    evaluate.add_argument("--windows", type=Path, required=True)
    arguments = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        if arguments.command == "run":
            selection = (
                load_model_config(arguments.model_config)
                if arguments.model_config is not None
                else ModelConfig(detector=arguments.detector or "mad")
            )
            result = run_file(
                arguments.input,
                arguments.output_dir,
                load_config(arguments.config),
                cast(EvaluationScope, arguments.scope),
                arguments.dataset_id,
                split_manifest_path=arguments.split_manifest,
                model_config=selection,
            )
        else:
            result = evaluate_run(arguments.run_dir, arguments.windows)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (ContractError, OSError, ValueError) as exc:
        logging.error("%s", exc)
        return 2
