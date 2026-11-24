"""Camera access built on top of OpenCV."""

import sys

import cv2
import numpy as np

DEFAULT_CAMERA_INDEX = 0
MAX_CAMERAS_TO_PROBE = 5
FRAME_WIDTH = 640
FRAME_HEIGHT = 480


class CameraError(Exception):
    """Raised when a camera cannot be opened or read."""


class Camera:
    """Thin wrapper around cv2.VideoCapture.

    Frames are mirrored by default: when you move your hand to the right,
    it moves to the right on the screen too, like in a mirror.
    """

    def __init__(self, index: int = DEFAULT_CAMERA_INDEX, mirror: bool = True) -> None:
        self.index = index
        self.mirror = mirror
        self._capture = None

    @property
    def is_open(self) -> bool:
        return self._capture is not None and self._capture.isOpened()

    def open(self) -> None:
        """Open the camera. Raise CameraError if it is not available."""
        if self.is_open:
            return
        self._capture = _open_capture(self.index)

    def switch(self, index: int) -> None:
        """Use another camera.

        If the new camera cannot be opened, CameraError is raised and the
        current camera is left untouched.
        """
        if index == self.index and self.is_open:
            return
        new_capture = _open_capture(index)
        self.release()
        self.index = index
        self._capture = new_capture

    def read(self) -> np.ndarray:
        """Return the next frame as a BGR image."""
        if not self.is_open:
            raise CameraError("The camera is not open.")
        success, frame = self._capture.read()
        if not success:
            raise CameraError(f"Cannot read from camera {self.index}.")
        if self.mirror:
            frame = cv2.flip(frame, 1)
        return frame

    def release(self) -> None:
        """Release the camera. It is safe to call this several times."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None


def list_available_cameras(max_cameras: int = MAX_CAMERAS_TO_PROBE) -> list[int]:
    """Return the indexes of the cameras that can be opened.

    OpenCV cannot list cameras with their names, so we simply try the first
    indexes (0, 1, 2...) and keep the ones that work. Call this before opening
    a camera: a camera that is already in use may not open a second time.
    """
    available = []
    for index in range(max_cameras):
        capture = cv2.VideoCapture(index, _get_backend())
        if capture.isOpened():
            available.append(index)
        capture.release()
    return available


def _open_capture(index: int) -> cv2.VideoCapture:
    """Open the camera with the given index. Raise CameraError if it is not available."""
    capture = cv2.VideoCapture(index, _get_backend())
    if not capture.isOpened():
        capture.release()
        raise CameraError(f"Cannot open camera {index}.")
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    return capture


def _get_backend() -> int:
    """Return the OpenCV backend to use (DirectShow starts faster on Windows)."""
    if sys.platform == "win32":
        return cv2.CAP_DSHOW
    return cv2.CAP_ANY
