import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from sentinel import provenance
from sentinel.provenance import canonical_sha256, environment_snapshot, source_state


def git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_source_revision_tracks_package_checkout_not_callers_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    source = package / "src" / "sentinel" / "module.py"
    source.parent.mkdir(parents=True)
    source.write_text("# synthetic package\n", encoding="utf-8")
    git(package, "init", "-q")
    git(package, "add", "src/sentinel/module.py")
    git(
        package,
        "-c",
        "user.name=Sentinel Test Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "-c",
        "core.hooksPath=unused-test-hooks",
        "commit",
        "-qm",
        "Synthetic source identity fixture",
    )
    revision = git(package, "rev-parse", "HEAD")
    unrelated = tmp_path / "caller"
    unrelated.mkdir()
    git(unrelated, "init", "-q")
    monkeypatch.chdir(unrelated)
    clean = source_state(source)
    assert clean["revision"] == revision
    assert clean["dirty"] is False
    assert clean["status"] == "git"
    source.write_text("# local edit\n", encoding="utf-8")
    assert source_state(source)["dirty"] is True
    source.write_text("# synthetic package\n", encoding="utf-8")
    (package / "new-untracked-file").write_text("local work", encoding="utf-8")
    untracked = source_state(source)
    assert untracked["revision"] == revision
    assert untracked["dirty"] is True
    # An untracked package inside a Git checkout must not borrow that repo's revision.
    assert source_state(package / "new-untracked-file")["revision"] is None


@pytest.mark.parametrize("failure", [FileNotFoundError("git"), subprocess.TimeoutExpired("git", 3)])
def test_git_unavailable_is_explicit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: Exception
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise failure

    monkeypatch.setattr(provenance.subprocess, "run", fail)
    state = source_state(tmp_path / "module.py")
    assert state["status"] == "unavailable"
    assert state["revision"] is state["dirty"] is None
    assert state["note"]


def test_untracked_source_without_git_does_not_invent_revision(tmp_path: Path) -> None:
    source = tmp_path / "installed-wheel.py"
    source.write_text("# installed without checkout\n", encoding="utf-8")
    assert source_state(source)["revision"] is None


def test_canonical_json_digest_and_dependency_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_bytes = b'{"a":1,"z":[true,null]}'
    assert (
        canonical_sha256({"z": [True, None], "a": 1}) == hashlib.sha256(expected_bytes).hexdigest()
    )
    assert canonical_sha256({"a": 1, "z": [True, None]}) == canonical_sha256(
        {"z": [True, None], "a": 1}
    )
    with pytest.raises(ValueError):
        canonical_sha256({"nonfinite": float("nan")})
    monkeypatch.setattr(
        provenance,
        "distributions",
        lambda: [
            SimpleNamespace(metadata={"Name": name}, version=version)
            for name, version in [("z", "2"), ("a", "1"), ("z", "2")]
        ],
    )
    monkeypatch.setenv("SENTINEL_TEST_PRIVATE", "must-not-appear")
    snapshot = environment_snapshot()
    assert snapshot["dependencies"] == [
        {"name": "a", "version": "1"},
        {"name": "z", "version": "2"},
    ]
    assert "must-not-appear" not in json.dumps(snapshot)
    assert snapshot["python"] and snapshot["machine"]
