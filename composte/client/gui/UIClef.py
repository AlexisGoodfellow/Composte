import music21
from PyQt5 import QtWidgets


class UIClef(QtWidgets.QGraphicsItem):
    def __init__(self, baseline: music21.pitch.Pitch, *args, **kwargs):
        """
        :param baseline: The pitch corresponding to the bottom line of the staff
            for the clef, as a music21 Pitch.
        """
        super(UIClef, self).__init__(*args, **kwargs)
        self.__baseline = baseline

    def __eq__(self, clef):
        return self.__baseline == clef.__baseline

    def position(self, pitch: music21.pitch.Pitch):
        """
        Return the line index of the given pitch relative to the lowest staff
        line in this clef.

        :param pitch: Pitch whose position is being checked

        :return: An integer, the number of lines above or below the lowest staff
                 line of this clef
        """
        return pitch.diatonicNoteNum - self.__baseline.diatonicNoteNum


# END class UIClef


def treble():
    return UIClef(music21.pitch.Pitch("E4"))


def fromMusic21(cl: music21.clef.Clef):
    """
    Given a Music21 clef, return the corresponding graphics clef.  If it is an
    unsupported clef, raise a RuntimeError.
    """
    if isinstance(cl, music21.clef.TrebleClef):
        return treble()
    else:
        raise RuntimeError("Unsupported clef " + cl)
