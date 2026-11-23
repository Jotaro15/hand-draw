import tkinter as tk

import numpy as np
import pytest

from handdraw.camera import CameraError
from handdraw.ui.main_window import (
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
    WAITING_MESSAGE,
    WINDOW_TITLE,
    MainWindow,
)


class FakeCamera:
    """Minimal stand-in for handdraw.camera.Camera."""

    def __init__(self, frame=None, error=None, is_open=True):
        self.frame = frame
        self.error = error
        self.is_open = is_open

    def read(self):
        if self.error is not None:
            raise self.error
        return self.frame


def make_frame(width=VIDEO_WIDTH, height=VIDEO_HEIGHT):
    return np.zeros((height, width, 3), dtype=np.uint8)


@pytest.fixture
def make_window():
    windows = []

    def factory(camera=None):
        try:
            window = MainWindow(camera)
        except tk.TclError:
            pytest.skip("no display available")
        windows.append(window)
        return window

    yield factory
    for window in windows:
        window.close()


def test_window_title(make_window):
    assert make_window().root.title() == WINDOW_TITLE


def test_video_canvas_size(make_window):
    window = make_window()
    assert int(window.video_canvas["width"]) == VIDEO_WIDTH
    assert int(window.video_canvas["height"]) == VIDEO_HEIGHT


def test_window_starts_with_a_waiting_message(make_window):
    window = make_window()
    assert window.message == WAITING_MESSAGE
    assert not window.is_showing_frame


def test_show_frame_replaces_the_message(make_window):
    window = make_window()

    window.show_frame(make_frame())

    assert window.is_showing_frame
    assert window.message == ""


def test_show_message_replaces_the_frame(make_window):
    window = make_window()
    window.show_frame(make_frame())

    window.show_message("Something happened")

    assert not window.is_showing_frame
    assert window.message == "Something happened"


def test_show_frame_accepts_a_frame_of_another_size(make_window):
    window = make_window()

    window.show_frame(make_frame(width=1280, height=720))

    assert window.is_showing_frame


def test_update_frame_displays_the_camera_image(make_window):
    window = make_window(FakeCamera(frame=make_frame()))

    window.update_frame()

    assert window.is_showing_frame


def test_update_frame_displays_camera_errors(make_window):
    window = make_window(FakeCamera(error=CameraError("Cannot read from camera 0.")))

    window.update_frame()

    assert not window.is_showing_frame
    assert window.message == "Cannot read from camera 0."


def test_update_frame_ignores_a_camera_that_is_not_open(make_window):
    window = make_window(FakeCamera(frame=make_frame(), is_open=False))

    window.update_frame()

    assert window.message == WAITING_MESSAGE


def test_update_frame_does_nothing_without_a_camera(make_window):
    window = make_window()

    window.update_frame()

    assert window.message == WAITING_MESSAGE
