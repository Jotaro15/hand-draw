import cv2
import numpy as np
import pytest

from handdraw import camera as camera_module
from handdraw.camera import FRAME_HEIGHT, FRAME_WIDTH, Camera, CameraError


class FakeCapture:
    """Minimal stand-in for cv2.VideoCapture."""

    def __init__(self, opened=True, frame=None):
        self.opened = opened
        self.frame = frame
        self.released = False
        self.properties = {}

    def isOpened(self):
        return self.opened and not self.released

    def read(self):
        if self.frame is None:
            return False, None
        return True, self.frame.copy()

    def set(self, prop, value):
        self.properties[prop] = value
        return True

    def release(self):
        self.released = True


def make_frame():
    """Return a small frame: left half black, right half white."""
    frame = np.zeros((4, 6, 3), dtype=np.uint8)
    frame[:, 3:] = 255
    return frame


def use_fake_capture(monkeypatch, capture):
    """Make Camera use the given fake capture. Return the list of (index, backend) calls."""
    calls = []

    def fake_video_capture(index, backend):
        calls.append((index, backend))
        return capture

    monkeypatch.setattr(camera_module.cv2, "VideoCapture", fake_video_capture)
    return calls


def test_open_raises_when_the_camera_is_missing(monkeypatch):
    capture = FakeCapture(opened=False)
    use_fake_capture(monkeypatch, capture)
    camera = Camera()

    with pytest.raises(CameraError):
        camera.open()

    assert not camera.is_open
    assert capture.released


def test_open_uses_the_given_index(monkeypatch):
    calls = use_fake_capture(monkeypatch, FakeCapture())

    Camera(index=2).open()

    assert calls[0][0] == 2


def test_open_requests_the_expected_resolution(monkeypatch):
    capture = FakeCapture()
    use_fake_capture(monkeypatch, capture)

    Camera().open()

    assert capture.properties[cv2.CAP_PROP_FRAME_WIDTH] == FRAME_WIDTH
    assert capture.properties[cv2.CAP_PROP_FRAME_HEIGHT] == FRAME_HEIGHT


def test_open_uses_directshow_on_windows(monkeypatch):
    calls = use_fake_capture(monkeypatch, FakeCapture())
    monkeypatch.setattr(camera_module.sys, "platform", "win32")

    Camera().open()

    assert calls[0][1] == cv2.CAP_DSHOW


def test_open_twice_only_opens_one_capture(monkeypatch):
    calls = use_fake_capture(monkeypatch, FakeCapture())
    camera = Camera()

    camera.open()
    camera.open()

    assert len(calls) == 1


def test_read_returns_a_mirrored_frame(monkeypatch):
    use_fake_capture(monkeypatch, FakeCapture(frame=make_frame()))
    camera = Camera()
    camera.open()

    frame = camera.read()

    assert frame[0, 0, 0] == 255  # the white half is now on the left
    assert frame[0, 5, 0] == 0


def test_read_can_return_the_original_frame(monkeypatch):
    use_fake_capture(monkeypatch, FakeCapture(frame=make_frame()))
    camera = Camera(mirror=False)
    camera.open()

    frame = camera.read()

    assert np.array_equal(frame, make_frame())


def test_read_fails_when_the_camera_is_not_open():
    with pytest.raises(CameraError):
        Camera().read()


def test_read_fails_when_no_frame_is_available(monkeypatch):
    use_fake_capture(monkeypatch, FakeCapture(frame=None))
    camera = Camera()
    camera.open()

    with pytest.raises(CameraError):
        camera.read()


def test_release_closes_the_camera(monkeypatch):
    capture = FakeCapture()
    use_fake_capture(monkeypatch, capture)
    camera = Camera()
    camera.open()

    camera.release()
    camera.release()  # a second call must not fail

    assert capture.released
    assert not camera.is_open
