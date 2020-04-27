"""UI component for time signatures."""
import music21
from PyQt5 import QtWidgets


class UITimeSignature(QtWidgets.QGraphicsItem):
    """Represents a time signature."""

    def __init__(self, num: int, den: int, *args, **kwargs):
        """Initialize the time signature."""
        super(UITimeSignature, self).__init__(*args, **kwargs)
        self.__num = num
        self.__den = den

    def __eq__(self, ts: music21.meter.TimeSignature) -> bool:
        """For comparing time signature equality."""
        return self.__num == ts.__num and self.__den == ts.__den

    def measureLength(self) -> float:
        """Return the length of a measure in quarter lengths."""
        return float(4 * (self.__num / self.__den))


def fromMusic21(ts: music21.meter.TimeSignature):
    """Given a Musci21 TimeSignature, return a corresponding UITimeSignature."""
    return UITimeSignature(ts.numerator, ts.denominator)
