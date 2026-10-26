# Technology choices

| Choice | Reason | Current state / boundary |
|---|---|---|
| Python >=3.11 | Familiar ML ecosystem, typing, portable CPU execution | Standard-library core; locally validated Python version recorded in VALIDATION |
| Dataclasses and Protocols | Explicit shared types without schema-framework dependency | contracts.py is the typed source of truth for Python interfaces |
| CSV input; JSONL output; JSON config/manifest | Streamable, inspectable, easy adapter boundary | Internal schemas only; official format unknown |
| argparse and logging | Small CLI with actionable errors; no backend needed | Implemented run/evaluate, nonzero exit on failure |
| Median/MAD starter | Robust, simple, direct numerical evidence | Fixed-threshold foundation; not the final adaptive algorithm |
| setuptools 80.9.0 | Conventional editable build | Build pin; dependencies are installed in local .venv |
| pytest 8.3.5 | Hand-derived correctness, integration, leakage regression tests | Pinned development dependency |
| Ruff 0.11.13 | Fast lint and uniform formatting | Pinned; required checks |
| mypy 1.15.0 | Validate module signatures and typed boundaries | Strict for src/; tests are runtime-checked by pytest |
| Git and GitHub PRs | Durable context and independent contributor branches | Foundation pushed to user-specified GitHub repository; PR permissions/protection remain owner setup |
| GitHub Actions | Reproduce checks on Windows/Linux, Python 3.11/3.13 | Workflow configured; no remote run is implied |
| Optional scikit-learn | IF/LOF/OCSVM comparisons if experiments justify them | Not installed as project dependencies |
| Optional River / STUMPY / libspot | Drift / shape / EVT research candidates | Not adopted; version/platform/license review first |
| Optional Chronos-2 / TimesFM | Zero-shot forecast comparators for EXP-12 | Not installed; separate optional environment and model terms/runtime gate required |
| Optional static HTML/SVG viewer | Inspect genuine artifacts offline | Mayank task; no runtime dependency of core |

No LLM calls in scoring/evidence: arithmetic evidence is faster, reproducible, and tied to actual
decisions. No PyTorch/GPU unless a comparator earns its cost. No web framework, database, Docker,
or deployment platform in the initial foundation. This keeps the baseline independently runnable.

Exact top-level dev/build versions are pinned in pyproject.toml. Transitive versions are recorded
in `docs/validation/environment-freeze.txt` for this initialization environment; that snapshot is
evidence, not a portable install lock. AY-01 will establish platform-aware experiment locks and
code-revision capture. Avoid adding optional research libraries to every contributor's environment.
There are no required environment variables or secrets, so no empty environment template is needed.
