"""Regressions for Windows publication failures observed during integration."""

from pathlib import Path

import pytest

from sentinel import pipeline
from sentinel.config import DetectorConfig
from sentinel.contracts import ContractError
from sentinel.detectors.selection import ModelConfig


@pytest.mark.parametrize("winerror", [5, 32])
def test_transient_windows_publication_failure_retries_closed_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    winerror: int,
) -> None:
    original = Path.rename
    attempts = []
    waits = []

    def rename(source: Path, target: Path) -> Path:
        attempts.append(target)
        # Both files are already readable/closed when publication begins.
        assert (source / "run.json").read_text(encoding="utf-8")
        assert (source / "predictions.jsonl").read_text(encoding="utf-8")
        if len(attempts) <= 2:
            error = PermissionError("simulated transient Windows denial")
            error.winerror = winerror
            raise error
        return original(source, target)

    monkeypatch.setattr(Path, "rename", rename)
    monkeypatch.setattr(pipeline, "sleep", waits.append)
    destination = tmp_path / "run"
    manifest = pipeline.run_file(
        Path("tests/fixtures/synthetic_stream.csv"),
        destination,
        DetectorConfig(),
        "synthetic_smoke",
        "fixture",
        model_config=ModelConfig(detector="residual"),
    )
    assert manifest["algorithm"] == "residual_max"
    assert len(attempts) == 3
    assert waits == [0.01, 0.02]
    assert destination.exists()
    assert not list(tmp_path.glob(".sentinel-*"))


def test_persistent_windows_denial_is_bounded_and_removes_unpublished_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts, waits = [], []

    def denied(source: Path, target: Path) -> Path:
        attempts.append(target)
        error = PermissionError("persistent Windows denial")
        error.winerror = 5
        raise error

    monkeypatch.setattr(Path, "rename", denied)
    monkeypatch.setattr(pipeline, "sleep", waits.append)
    with pytest.raises(PermissionError, match="persistent"):
        pipeline.run_file(
            Path("tests/fixtures/synthetic_stream.csv"),
            tmp_path / "run",
            DetectorConfig(),
            "synthetic_smoke",
            "fixture",
        )
    assert len(attempts) == 6
    assert sum(waits) == pytest.approx(0.31)
    assert not (tmp_path / "run").exists()
    assert not list(tmp_path.glob(".sentinel-*"))


def test_non_windows_permission_error_does_not_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "stage"
    source.mkdir()
    attempts, waits = [], []

    def denied(source: Path, target: Path) -> Path:
        attempts.append(target)
        raise PermissionError("non-Windows denial")

    monkeypatch.setattr(Path, "rename", denied)
    monkeypatch.setattr(pipeline, "sleep", waits.append)
    with pytest.raises(PermissionError, match="non-Windows"):
        pipeline._publish_run(source, tmp_path / "run")
    assert len(attempts) == 1
    assert not waits


def test_destination_appearing_during_retry_is_preserved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, destination = tmp_path / "stage", tmp_path / "run"
    source.mkdir()

    def denied(stage: Path, target: Path) -> Path:
        error = PermissionError("simulated Windows denial")
        error.winerror = 32
        raise error

    def create_collision(delay: float) -> None:
        destination.mkdir()
        (destination / "keep").write_text("preserve")

    monkeypatch.setattr(Path, "rename", denied)
    monkeypatch.setattr(pipeline, "sleep", create_collision)
    with pytest.raises(ContractError, match="already exists"):
        pipeline._publish_run(source, destination)
    assert (destination / "keep").read_text() == "preserve"
    assert source.exists()
