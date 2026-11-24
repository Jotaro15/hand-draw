"""Application entry point."""

from handdraw.camera import DEFAULT_CAMERA_INDEX, Camera, CameraError, list_available_cameras
from handdraw.ui.main_window import MainWindow


def main() -> None:
    cameras = list_available_cameras()
    camera = Camera(cameras[0] if cameras else DEFAULT_CAMERA_INDEX)
    window = MainWindow(camera)
    window.set_available_cameras(cameras)
    try:
        camera.open()
    except CameraError as error:
        window.show_message(f"{error}\nPlug in a camera and restart the application.")
    try:
        window.run()
    finally:
        camera.release()
