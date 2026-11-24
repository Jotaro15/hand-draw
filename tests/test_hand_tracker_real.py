"""Optional test with the real MediaPipe model and a real photo.

It is skipped unless both of these exist:
- the model file, downloaded the first time the application runs;
- tests/data/hand.jpg, a photo of an open hand that you add yourself.
"""

from pathlib import Path

import cv2
import pytest

from handdraw.hand_tracker import LANDMARK_COUNT, MODEL_PATH, HandTracker

PHOTO_PATH = Path(__file__).parent / "data" / "hand.jpg"

pytestmark = pytest.mark.skipif(
    not (MODEL_PATH.exists() and PHOTO_PATH.exists()),
    reason="needs the downloaded model and tests/data/hand.jpg",
)


def test_detects_the_landmarks_of_a_real_hand():
    frame = cv2.imread(str(PHOTO_PATH))
    tracker = HandTracker()
    try:
        landmarks = tracker.detect(frame)
    finally:
        tracker.close()

    assert landmarks is not None
    assert len(landmarks) == LANDMARK_COUNT
