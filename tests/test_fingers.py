from handdraw.fingers import DEFAULT_FINGER, Finger
from handdraw.hand_tracker import LANDMARK_COUNT, Landmark


def test_fingers_go_from_the_thumb_to_the_little_finger():
    labels = [finger.label for finger in Finger]

    assert labels == ["Thumb", "Index", "Middle", "Ring", "Little"]


def test_tip_indexes_follow_the_mediapipe_hand_model():
    tip_indexes = [finger.tip_index for finger in Finger]

    assert tip_indexes == [4, 8, 12, 16, 20]


def test_tip_returns_the_landmark_at_the_end_of_the_finger():
    landmarks = [Landmark(i / 100, i / 50) for i in range(LANDMARK_COUNT)]

    assert Finger.INDEX.tip(landmarks) == landmarks[8]
    assert Finger.LITTLE.tip(landmarks) == landmarks[20]


def test_the_index_finger_is_the_default_finger():
    assert DEFAULT_FINGER is Finger.INDEX
