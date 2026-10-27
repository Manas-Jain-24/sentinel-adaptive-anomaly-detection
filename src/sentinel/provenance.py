"""Read-only source and environment evidence; no network or credential collection."""

import hashlib
import json
import os
import platform
import subprocess
from importlib.metadata import distributions
from pathlib import Path
from typing import Any


def canonical_sha256(value: object) -> str:
    """Hash sorted-key, compact, ASCII-escaped UTF-8 JSON (without a trailing newline)."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def source_state(source_file: Path) -> dict[str, Any]:
    """Identify the tracked package checkout, even when the caller runs elsewhere."""
    source_file = source_file.resolve()

    def git(*arguments: str) -> str:
        return subprocess.run(
            ["git", "-C", str(source_file.parent), *arguments],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        ).stdout.strip()

    try:
        root = Path(git("rev-parse", "--show-toplevel")).resolve()
        relative = source_file.relative_to(root)
        git("ls-files", "--error-unmatch", "--", f":(top,literal){relative.as_posix()}")
        revision = git("rev-parse", "--verify", "HEAD")
        dirty = bool(git("status", "--porcelain=v1", "--untracked-files=normal"))
    except (OSError, ValueError, subprocess.SubprocessError):
        return {
            "status": "unavailable",
            "revision": None,
            "dirty": None,
            "note": "Git unavailable, timed out, or package source is not in a tracked checkout",
        }
    return {
        "status": "git",
        "revision": revision,
        "dirty": dirty,
        "note": (
            "HEAD identifies committed base; dirty includes tracked and nonignored untracked files"
        ),
    }


def environment_snapshot() -> dict[str, Any]:
    """Record reproducibility facts without local paths, hostnames, or environment variables."""
    packages = sorted({(item.metadata["Name"], item.version) for item in distributions()})
    dependencies = [{"name": name, "version": version} for name, version in packages]
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or None,
        "logical_cpu_count": os.cpu_count(),
        "dependencies": dependencies,
    }
