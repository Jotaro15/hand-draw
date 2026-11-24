"""Hand detection built on top of MediaPipe."""

import time
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

LANDMARK_COUNT = 21
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_PATH = Path(__file__).resolve().parent / "models" / "hand_landmarker.task"


class HandTrackerError(Exception):
    """Raised when hand tracking cannot be started."""


@dataclass(frozen=True)
class Landmark:
    """One point of the hand. x and y go from 0.0 to 1.0 across the image."""

    x: float
    y: float


def ensure_model(model_path: Path = MODEL_PATH, url: str = MODEL_URL) -> Path:
    """Return the path of the model file, downloading it the first time."""
    if model_path.exists():
        return model_path

    print(f"Downloading the hand tracking model (first launch only) to {model_path} ...")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = model_path.with_name(model_path.name + ".part")
    try:
        urllib.request.urlretrieve(url, partial_path)
        if not zipfile.is_zipfile(partial_path):  # a .task file is a zip archive
            raise ValueError("the downloaded file is not a valid model")
        partial_path.replace(model_path)
    except (OSError, ValueError) as error:
        raise HandTrackerError(
            f"Cannot download the hand tracking model ({error}). "
            f"Download it from {url} and save it as {model_path}."
        ) from error
    finally:
        partial_path.unlink(missing_ok=True)
    return model_path


class HandTracker:
    """Find one hand in the camera frames and return its 21 landmarks."""

    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        model_path = ensure_model(model_path)
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
        )
        try:
            self._landmarker = vision.HandLandmarker.create_from_options(options)
        except (OSError, RuntimeError) as error:
            raise HandTrackerError(
                f"Cannot load the hand tracking model ({error}). "
                f"Delete {model_path} to download it again."
            ) from error
        self._start_time = time.monotonic()
        self._last_timestamp_ms = -1

    def detect(self, frame: np.ndarray) -> list[Landmark] | None:
        """Return the 21 landmarks of the hand found in a BGR frame, or None."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = self._landmarker.detect_for_video(image, self._next_timestamp_ms())
        if not result.hand_landmarks:
            return None
        return [Landmark(point.x, point.y) for point in result.hand_landmarks[0]]

    def close(self) -> None:
        """Free the resources used by MediaPipe."""
        self._landmarker.close()

    def _next_timestamp_ms(self) -> int:
        """Return the time of the current frame. MediaPipe needs increasing timestamps."""
        timestamp = int((time.monotonic() - self._start_time) * 1000)
        timestamp = max(timestamp, self._last_timestamp_ms + 1)
        self._last_timestamp_ms = timestamp
        return timestamp
