import tkinter as tk

import numpy as np
import pytest

from handdraw.camera import CameraError
from handdraw.ui.main_window import (
    NO_CAMERA_TEXT,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
    WAITING_MESSAGE,
    WINDOW_TITLE,
    MainWindow,
)


class FakeCamera:
    """Minimal stand-in for handdraw.camera.Camera."""

    def __init__(self, frame=None, error=None, is_open=True, index=0, switch_error=None):
        self.frame = frame
        self.error = error
        self.is_open = is_open
        self.index = index
        self.switch_error = switch_error

    def read(self):
        if self.error is not None:
            raise self.error
        return self.frame

    def switch(self, index):
        if self.switch_error is not None:
            raise self.switch_error
        self.index = index


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


def test_selector_is_disabled_when_no_camera_is_found(make_window):
    window = make_window()

    window.set_available_cameras([])

    assert str(window.camera_selector["state"]) == "disabled"
    assert window.camera_selector.get() == NO_CAMERA_TEXT


def test_selector_lists_the_available_cameras(make_window):
    window = make_window(FakeCamera(index=2))

    window.set_available_cameras([0, 2])

    assert list(window.camera_selector["values"]) == ["Camera 0", "Camera 2"]
    assert str(window.camera_selector["state"]) == "readonly"
    assert window.camera_selector.get() == "Camera 2"


def test_select_camera_switches_the_camera(make_window):
    camera = FakeCamera(index=0)
    window = make_window(camera)
    window.set_available_cameras([0, 1])

    window.select_camera(1)

    assert camera.index == 1
    assert window.camera_selector.get() == "Camera 1"
    assert window.status == ""


def test_select_camera_reports_a_failure_and_keeps_the_current_camera(make_window):
    camera = FakeCamera(index=0, switch_error=CameraError("Cannot open camera 1."))
    window = make_window(camera)
    window.set_available_cameras([0, 1])

    window.select_camera(1)

    assert camera.index == 0
    assert window.camera_selector.get() == "Camera 0"
    assert window.status == "Cannot open camera 1. Still using camera 0."


def test_select_camera_failure_without_an_open_camera_only_shows_the_error(make_window):
    camera = FakeCamera(
        index=0, is_open=False, switch_error=CameraError("Cannot open camera 1.")
    )
    window = make_window(camera)
    window.set_available_cameras([0, 1])

    window.select_camera(1)

    assert window.status == "Cannot open camera 1."


def test_a_successful_switch_clears_the_previous_error(make_window):
    camera = FakeCamera(index=0, switch_error=CameraError("Cannot open camera 1."))
    window = make_window(camera)
    window.set_available_cameras([0, 1])
    window.select_camera(1)

    camera.switch_error = None
    window.select_camera(1)

    assert camera.index == 1
    assert window.status == ""


def test_select_camera_does_nothing_without_a_camera(make_window):
    window = make_window()

    window.select_camera(1)

    assert window.status == ""


def test_choosing_an_item_in_the_list_switches_the_camera(make_window):
    camera = FakeCamera(index=0)
    window = make_window(camera)
    window.set_available_cameras([0, 1])

    window.camera_selector.current(1)
    window.camera_selector.event_generate("<<ComboboxSelected>>")
    window.root.update()

    assert camera.index == 1
