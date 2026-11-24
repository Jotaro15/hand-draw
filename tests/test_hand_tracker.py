import zipfile
from types import SimpleNamespace

import numpy as np
import pytest

from handdraw import hand_tracker as tracker_module
from handdraw.hand_tracker import (
    LANDMARK_COUNT,
    HandTracker,
    HandTrackerError,
    Landmark,
    ensure_model,
)


class FakeLandmarker:
    """Minimal stand-in for the MediaPipe HandLandmarker."""

    def __init__(self, hands=()):
        self.hands = list(hands)
        self.calls = []
        self.closed = False

    def detect_for_video(self, image, timestamp_ms):
        self.calls.append((image, timestamp_ms))
        return SimpleNamespace(hand_landmarks=self.hands)

    def close(self):
        self.closed = True


def make_hand():
    """Return 21 fake MediaPipe points."""
    return [SimpleNamespace(x=i / 100, y=i / 50, z=0.0) for i in range(LANDMARK_COUNT)]


def make_frame():
    return np.zeros((4, 6, 3), dtype=np.uint8)


def make_zip_file(path):
    """Create a small zip archive, like the real .task model files."""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("hand_detector.tflite", b"data")
    return path


def use_fake_landmarker(monkeypatch, landmarker):
    """Make HandTracker use the given fake. Return the options it was created with."""
    created_with = []

    def fake_create_from_options(options):
        created_with.append(options)
        return landmarker

    monkeypatch.setattr(
        tracker_module.vision.HandLandmarker, "create_from_options", fake_create_from_options
    )
    return created_with


@pytest.fixture
def model_file(tmp_path):
    path = tmp_path / "hand_landmarker.task"
    path.write_bytes(b"fake model")
    return path


def test_tracker_loads_the_given_model(monkeypatch, model_file):
    created_with = use_fake_landmarker(monkeypatch, FakeLandmarker())

    HandTracker(model_file)

    assert created_with[0].base_options.model_asset_path == str(model_file)


def test_tracker_reports_a_model_that_cannot_be_loaded(monkeypatch, model_file):
    def broken_create_from_options(options):
        raise RuntimeError("Unable to open zip archive.")

    monkeypatch.setattr(
        tracker_module.vision.HandLandmarker, "create_from_options", broken_create_from_options
    )

    with pytest.raises(HandTrackerError) as error:
        HandTracker(model_file)

    assert str(model_file) in str(error.value)


def test_tracker_reports_a_corrupted_model_file(model_file):
    # No fake here: this checks what the real MediaPipe raises for a broken file.
    with pytest.raises(HandTrackerError):
        HandTracker(model_file)


def test_detect_returns_the_21_landmarks(monkeypatch, model_file):
    use_fake_landmarker(monkeypatch, FakeLandmarker(hands=[make_hand()]))
    tracker = HandTracker(model_file)

    landmarks = tracker.detect(make_frame())

    assert landmarks == [Landmark(i / 100, i / 50) for i in range(LANDMARK_COUNT)]


def test_detect_returns_none_when_there_is_no_hand(monkeypatch, model_file):
    use_fake_landmarker(monkeypatch, FakeLandmarker(hands=[]))
    tracker = HandTracker(model_file)

    assert tracker.detect(make_frame()) is None


def test_detect_gives_an_rgb_image_to_mediapipe(monkeypatch, model_file):
    landmarker = FakeLandmarker()
    use_fake_landmarker(monkeypatch, landmarker)
    tracker = HandTracker(model_file)
    frame = make_frame()
    frame[0, 0] = (10, 20, 30)  # blue, green, red

    tracker.detect(frame)

    image = landmarker.calls[0][0]
    assert image.numpy_view()[0, 0].tolist() == [30, 20, 10]


def test_detect_uses_increasing_timestamps(monkeypatch, model_file):
    landmarker = FakeLandmarker()
    use_fake_landmarker(monkeypatch, landmarker)
    tracker = HandTracker(model_file)

    for _ in range(3):
        tracker.detect(make_frame())

    timestamps = [timestamp for _, timestamp in landmarker.calls]
    assert timestamps == sorted(set(timestamps))  # sorted and without duplicates


def test_close_closes_the_landmarker(monkeypatch, model_file):
    landmarker = FakeLandmarker()
    use_fake_landmarker(monkeypatch, landmarker)
    tracker = HandTracker(model_file)

    tracker.close()

    assert landmarker.closed


def test_ensure_model_keeps_an_existing_model(model_file):
    assert ensure_model(model_file, url="file:///does/not/exist") == model_file


def test_ensure_model_downloads_the_model_the_first_time(tmp_path):
    source = make_zip_file(tmp_path / "source.task")
    target = tmp_path / "models" / "hand_landmarker.task"

    result = ensure_model(target, url=source.as_uri())

    assert result == target
    assert target.read_bytes() == source.read_bytes()
    assert list(target.parent.iterdir()) == [target]  # no leftover temporary file


def test_ensure_model_rejects_a_file_that_is_not_a_model(tmp_path):
    source = tmp_path / "error_page.html"
    source.write_text("<html>Not found</html>")
    target = tmp_path / "models" / "hand_landmarker.task"

    with pytest.raises(HandTrackerError):
        ensure_model(target, url=source.as_uri())

    assert list(target.parent.iterdir()) == []


def test_ensure_model_explains_how_to_install_it_by_hand(tmp_path):
    target = tmp_path / "models" / "hand_landmarker.task"

    with pytest.raises(HandTrackerError) as error:
        ensure_model(target, url=(tmp_path / "missing.task").as_uri())

    assert str(target) in str(error.value)
    assert "Download it from" in str(error.value)
