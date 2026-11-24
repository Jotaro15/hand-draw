"""Application entry point."""

import sys

from handdraw.camera import DEFAULT_CAMERA_INDEX, Camera, CameraError, list_available_cameras
from handdraw.hand_tracker import HandTracker, HandTrackerError
from handdraw.ui.main_window import MainWindow


def main() -> None:
    cameras = list_available_cameras()
    camera = Camera(cameras[0] if cameras else DEFAULT_CAMERA_INDEX)
    hand_tracker = create_hand_tracker()
    window = MainWindow(camera, hand_tracker)
    window.set_available_cameras(cameras)
    try:
        camera.open()
    except CameraError as error:
        window.show_message(f"{error}\nPlug in a camera and restart the application.")
    try:
        window.run()
    finally:
        camera.release()
        if hand_tracker is not None:
            hand_tracker.close()


def create_hand_tracker() -> HandTracker | None:
    """Start hand tracking, or return None if it is not available.

    The application still shows the camera without hand tracking.
    """
    try:
        return HandTracker()
    except HandTrackerError as error:
        print(f"Hand tracking is disabled: {error}", file=sys.stderr)
        return None
