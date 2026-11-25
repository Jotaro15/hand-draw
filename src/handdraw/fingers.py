"""The five fingers and where their tips are in the MediaPipe hand model."""

from enum import Enum

from handdraw.hand_tracker import Landmark


class Finger(Enum):
    """A finger of the hand, with the index of its tip among the 21 landmarks."""

    THUMB = ("Thumb", 4)
    INDEX = ("Index", 8)
    MIDDLE = ("Middle", 12)
    RING = ("Ring", 16)
    LITTLE = ("Little", 20)

    def __init__(self, label: str, tip_index: int) -> None:
        self.label = label
        self.tip_index = tip_index

    def tip(self, landmarks: list[Landmark]) -> Landmark:
        """Return the landmark at the tip of this finger."""
        return landmarks[self.tip_index]


DEFAULT_FINGER = Finger.INDEX
