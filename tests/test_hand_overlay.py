import numpy as np

from handdraw.hand_overlay import HAND_CONNECTIONS, LINE_COLOR, POINT_COLOR, draw_hand
from handdraw.hand_tracker import LANDMARK_COUNT, Landmark


def make_landmarks(x=0.5, y=0.5):
    """Return 21 landmarks that are all at the same place."""
    return [Landmark(x, y) for _ in range(LANDMARK_COUNT)]


def test_connections_only_use_existing_landmarks():
    assert len(HAND_CONNECTIONS) == 21
    for start, end in HAND_CONNECTIONS:
        assert 0 <= start < LANDMARK_COUNT
        assert 0 <= end < LANDMARK_COUNT


def test_draw_hand_draws_the_landmark_points():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    landmarks = make_landmarks()
    landmarks[0] = Landmark(0.25, 0.75)

    draw_hand(frame, landmarks)

    assert frame[75, 25].tolist() == list(POINT_COLOR)


def test_draw_hand_draws_the_lines_between_landmarks():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    landmarks = make_landmarks(0.5, 0.95)
    landmarks[0] = Landmark(0.1, 0.5)  # wrist
    landmarks[1] = Landmark(0.9, 0.5)  # thumb base, linked to the wrist

    draw_hand(frame, landmarks)

    assert frame[50, 50].tolist() == list(LINE_COLOR)  # middle of the wrist-thumb line


def test_draw_hand_scales_the_points_to_the_frame_size():
    frame = np.zeros((50, 200, 3), dtype=np.uint8)  # 50 pixels high, 200 pixels wide

    draw_hand(frame, make_landmarks(0.5, 0.5))

    assert frame[25, 100].tolist() == list(POINT_COLOR)
