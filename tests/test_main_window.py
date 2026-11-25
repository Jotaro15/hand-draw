import tkinter as tk

import numpy as np
import pytest

from handdraw.camera import CameraError
from handdraw.fingers import Finger
from handdraw.hand_overlay import HIGHLIGHT_COLOR, HIGHLIGHT_RADIUS
from handdraw.hand_tracker import LANDMARK_COUNT, Landmark
from handdraw.ui.main_window import (
    NO_CAMERA_TEXT,
    TRACKING_OFF_TEXT,
    TRACKING_ON_TEXT,
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


class FakeTracker:
    """Minimal stand-in for handdraw.hand_tracker.HandTracker."""

    def __init__(self, landmarks=None):
        self.landmarks = landmarks
        self.frames = []

    def detect(self, frame):
        self.frames.append(frame)
        return self.landmarks


def make_frame(width=VIDEO_WIDTH, height=VIDEO_HEIGHT):
    return np.zeros((height, width, 3), dtype=np.uint8)


@pytest.fixture
def make_window():
    windows = []

    def factory(camera=None, hand_tracker=None):
        try:
            window = MainWindow(camera, hand_tracker)
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


def test_tracking_status_is_off_without_a_tracker(make_window):
    assert make_window().tracking_status == TRACKING_OFF_TEXT


def test_tracking_status_is_on_with_a_tracker(make_window):
    assert make_window(hand_tracker=FakeTracker()).tracking_status == TRACKING_ON_TEXT


def test_update_frame_draws_the_detected_hand(make_window):
    frame = make_frame()
    tracker = FakeTracker(landmarks=[Landmark(0.5, 0.5)] * LANDMARK_COUNT)
    window = make_window(FakeCamera(frame=frame), tracker)

    window.update_frame()

    assert window.is_showing_frame
    assert tracker.frames == [frame]
    assert frame.any()  # something was drawn on the black frame


def test_update_frame_draws_nothing_when_no_hand_is_found(make_window):
    frame = make_frame()
    window = make_window(FakeCamera(frame=frame), FakeTracker(landmarks=None))

    window.update_frame()

    assert window.is_showing_frame
    assert not frame.any()


def test_update_frame_draws_nothing_without_a_tracker(make_window):
    frame = make_frame()
    window = make_window(FakeCamera(frame=frame))

    window.update_frame()

    assert window.is_showing_frame
    assert not frame.any()


def test_the_index_finger_is_selected_by_default(make_window):
    window = make_window()

    assert window.selected_finger is Finger.INDEX
    assert window.finger_selector.get() == "Index"


def test_finger_selector_lists_the_five_fingers(make_window):
    window = make_window()

    labels = list(window.finger_selector["values"])

    assert labels == ["Thumb", "Index", "Middle", "Ring", "Little"]


def test_select_finger_updates_the_selector(make_window):
    window = make_window()

    window.select_finger(Finger.THUMB)

    assert window.selected_finger is Finger.THUMB
    assert window.finger_selector.get() == "Thumb"


def test_choosing_a_finger_in_the_list_selects_it(make_window):
    window = make_window()

    window.finger_selector.current(4)
    window.finger_selector.event_generate("<<ComboboxSelected>>")
    window.root.update()

    assert window.selected_finger is Finger.LITTLE


def test_update_frame_circles_the_tip_of_the_selected_finger(make_window):
    frame = make_frame()
    landmarks = [Landmark(0.1, 0.1)] * LANDMARK_COUNT
    landmarks[4] = Landmark(0.25, 0.5)  # tip of the thumb
    landmarks[12] = Landmark(0.75, 0.5)  # tip of the middle finger
    window = make_window(FakeCamera(frame=frame), FakeTracker(landmarks))
    window.select_finger(Finger.MIDDLE)

    window.update_frame()

    middle_circle = frame[240, 480 + HIGHLIGHT_RADIUS]  # x = 0.75 * 640, y = 0.5 * 480
    thumb_circle = frame[240, 160 + HIGHLIGHT_RADIUS]  # x = 0.25 * 640, y = 0.5 * 480
    assert middle_circle.tolist() == list(HIGHLIGHT_COLOR)
    assert thumb_circle.tolist() == [0, 0, 0]
