"""AY-03 replay lifecycle and AY-02 full-replay fallback using v1 public contracts."""

import logging
from collections.abc import Iterator
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sentinel import pipeline
from sentinel.cli import main
from sentinel.config import DetectorConfig
from sentinel.contracts import ContractError, Detector, Evidence, Observation, Prediction
from sentinel.data.io import read_observations
from sentinel.detectors.rolling import RollingMADStarter

FIXTURE = Path("tests/fixtures/synthetic_stream.csv")


def point(index: int, value: float, series: str = "a") -> Observation:
    return Observation(series, datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=index), value)


class PriorValueDetector:
    """A label-free Protocol double with a hand-checkable one-observation reference."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.previous: Observation | None = None

    def process(self, observation: Observation) -> Prediction:
        previous = self.previous
        if previous is not None:
            if (
                previous.series_id != observation.series_id
                or previous.timestamp >= observation.timestamp
            ):
                raise ContractError("Double requires one strictly ordered series")
        residual = None if previous is None else observation.value - previous.value
        score = None if residual is None else abs(residual)
        prediction = Prediction(
            observation.series_id,
            observation.timestamp,
            observation.value,
            score,
            2.0,
            "ANOMALOUS" if score is not None and score >= 2 else "NORMAL",
            previous is not None,
            Evidence(
                None if previous is None else previous.value,
                None if previous is None else 1.0,
                residual,
                int(previous is not None),
                "warmup" if previous is None else "prior_value_double",
                {} if score is None else {"level": score},
            ),
        )
        self.previous = observation
        return prediction


def test_protocol_double_routes_interleaved_series_in_input_order() -> None:
    left = [point(0, 1), point(1, 4), point(2, 5)]
    right = [point(0, 100, "b"), point(1, 100, "b"), point(2, 97, "b")]
    mixed = [left[0], right[0], right[1], left[1], left[2], right[2]]
    created: list[Detector] = []

    def factory() -> Detector:
        detector: Detector = PriorValueDetector()
        created.append(detector)
        return detector

    results = list(pipeline.process_stream(mixed, factory))
    predictions = [prediction for prediction, _ in results]
    assert [p.series_id for p in predictions] == ["a", "b", "b", "a", "a", "b"]
    assert [p.score for p in predictions] == [None, None, 0, 3, 1, 3]
    assert [p.label for p in predictions] == [
        "NORMAL",
        "NORMAL",
        "NORMAL",
        "ANOMALOUS",
        "NORMAL",
        "ANOMALOUS",
    ]
    assert len(created) == 2 and created[0] is not created[1]
    assert all(elapsed >= 0 for _, elapsed in results)
    for series, points in (("a", left), ("b", right)):
        isolated = [p for p, _ in pipeline.process_stream(points, PriorValueDetector)]
        assert [p for p in predictions if p.series_id == series] == isolated


def test_consumer_termination_does_not_read_or_process_the_next_point() -> None:
    consumed: list[int] = []

    def source() -> Iterator[Observation]:
        for index in range(3):
            consumed.append(index)
            yield point(index, float(index))

    observations = source()
    stream = pipeline.process_stream(observations, PriorValueDetector)
    assert next(stream)[0].value == 0
    stream.close()
    assert consumed == [0]
    # The caller owns the input iterator. Closing replay must not consume it.
    assert next(observations).value == 1
    observations.close()


def test_source_error_after_first_prediction_is_propagated_without_fake_output() -> None:
    def source() -> Iterator[Observation]:
        yield point(0, 1)
        raise ContractError("synthetic source failed at row 3")

    stream = pipeline.process_stream(source(), PriorValueDetector)
    assert next(stream)[0].value == 1
    with pytest.raises(ContractError, match="row 3"):
        next(stream)
    with pytest.raises(StopIteration):
        next(stream)


def test_cardinality_error_does_not_construct_an_unroutable_detector() -> None:
    created: list[Detector] = []

    def factory() -> Detector:
        detector: Detector = PriorValueDetector()
        created.append(detector)
        return detector

    stream = pipeline.process_stream([point(0, 1), point(0, 2, "b")], factory, max_series=1)
    assert next(stream)[0].series_id == "a"
    with pytest.raises(ContractError, match="Maximum active series"):
        next(stream)
    assert len(created) == 1


@pytest.mark.parametrize("failure", [KeyboardInterrupt, RuntimeError, OSError])
def test_interrupted_file_replay_removes_staging_and_preserves_other_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: type[BaseException]
) -> None:
    previous = tmp_path / "previous"
    previous.mkdir()
    sentinel = previous / "predictions.jsonl"
    sentinel.write_bytes(b"preserve existing run bytes\n")

    def interrupted(path: Path) -> Iterator[Observation]:
        with closing(read_observations(path)) as reader:
            yield next(reader)
        raise failure("synthetic interruption")

    monkeypatch.setattr(pipeline, "read_observations", interrupted)
    with pytest.raises(failure, match="synthetic interruption"):
        pipeline.run_file(FIXTURE, tmp_path / "run", DetectorConfig(), "synthetic_smoke", "fixture")
    assert not (tmp_path / "run").exists()
    assert not list(tmp_path.glob(".sentinel-*"))
    assert sentinel.read_bytes() == b"preserve existing run bytes\n"


def test_manifest_write_failure_cannot_publish_predictions_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = Path.write_text

    def write(path: Path, data: str, *args: object, **kwargs: object) -> int:
        if path.name == "run.json":
            raise OSError("synthetic manifest disk failure")
        return original(path, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", write)
    with pytest.raises(OSError, match="manifest disk"):
        pipeline.run_file(FIXTURE, tmp_path / "run", DetectorConfig(), "synthetic_smoke", "fixture")
    assert not (tmp_path / "run").exists()
    assert not list(tmp_path.glob(".sentinel-*"))


@pytest.mark.parametrize("directory", [False, True])
def test_collision_preserves_files_and_directories_before_reading_input(
    tmp_path: Path, directory: bool
) -> None:
    destination = tmp_path / "run"
    if directory:
        destination.mkdir()
    existing = destination / "keep" if directory else destination
    existing.write_bytes(b"existing bytes\n")
    with pytest.raises(ContractError, match="already exists"):
        pipeline.run_file(
            tmp_path / "missing-input.csv",
            destination,
            DetectorConfig(),
            "synthetic_smoke",
            "fixture",
        )
    assert existing.read_bytes() == b"existing bytes\n"
    assert not list(tmp_path.glob(".sentinel-*"))


def test_missing_input_is_an_actionable_cli_error_without_success_json(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "missing.csv"
    with caplog.at_level(logging.ERROR):
        result = main(
            [
                "run",
                "--input",
                str(source),
                "--config",
                "configs/starter.json",
                "--output-dir",
                str(tmp_path / "run"),
                "--dataset-id",
                "fixture",
                "--scope",
                "synthetic_smoke",
            ]
        )
    assert result == 2
    assert "missing.csv" in caplog.text
    assert capsys.readouterr().out == ""
    assert not (tmp_path / "run").exists()
    assert not list(tmp_path.glob(".sentinel-*"))


@pytest.mark.parametrize("boundary", [1, 8, 12])
def test_baseline_full_replay_fallback_matches_continuation_after_reset(boundary: int) -> None:
    points = list(read_observations(FIXTURE))
    config = DetectorConfig(window_size=4, min_history=2)
    detector: Detector = RollingMADStarter(config)
    prefix = [detector.process(p) for p in points[:boundary]]
    continued = [detector.process(p) for p in points[boundary:]]
    detector.reset()
    replayed = [detector.process(p) for p in points]
    assert replayed == prefix + continued
    assert len(replayed) == 16
    assert replayed[0].score is None and replayed[0].evidence.history_size == 0
    assert replayed[2].ready and replayed[2].evidence.history_size == 2
    # A consumed cursor must not be replayed into live state; v1 requires full reset/replay.
    with pytest.raises(ContractError, match="increasing"):
        detector.process(points[-1])
