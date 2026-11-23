"""Application entry point."""

from handdraw.camera import Camera, CameraError
from handdraw.ui.main_window import MainWindow


def main() -> None:
    camera = Camera()
    window = MainWindow(camera)
    try:
        camera.open()
    except CameraError as error:
        window.show_message(f"{error}\nPlug in a camera and restart the application.")
    try:
        window.run()
    finally:
        camera.release()
