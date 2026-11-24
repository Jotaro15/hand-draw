"""Drawing of the hand skeleton on top of a camera frame."""

import cv2
import numpy as np

from handdraw.hand_tracker import Landmark

# Pairs of landmarks linked by a line, following the MediaPipe hand model.
HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),  # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),  # index finger
    (5, 9), (9, 10), (10, 11), (11, 12),  # middle finger
    (9, 13), (13, 14), (14, 15), (15, 16),  # ring finger
    (13, 17), (17, 18), (18, 19), (19, 20),  # little finger
    (0, 17),  # edge of the palm
)
LINE_COLOR = (0, 255, 0)  # green (BGR)
POINT_COLOR = (0, 0, 255)  # red (BGR)
LINE_THICKNESS = 2
POINT_RADIUS = 4


def draw_hand(frame: np.ndarray, landmarks: list[Landmark]) -> None:
    """Draw the landmarks and the lines between them on the frame (in place)."""
    height, width = frame.shape[:2]
    points = [(int(landmark.x * width), int(landmark.y * height)) for landmark in landmarks]
    for start, end in HAND_CONNECTIONS:
        cv2.line(frame, points[start], points[end], LINE_COLOR, LINE_THICKNESS)
    for point in points:
        cv2.circle(frame, point, POINT_RADIUS, POINT_COLOR, -1)
