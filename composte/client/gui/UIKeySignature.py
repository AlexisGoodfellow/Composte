"""UI component for key signatures."""
from typing import List

import music21
from PyQt5 import QtWidgets


class UIKeySignature(QtWidgets.QGraphicsItem):
    """Defines a key signature."""

    def __init__(
        self, name: str, sharps: List[str] = [], flats: List[str] = [], *args, **kwargs
    ):
        """Initialize the key signature."""
        super(UIKeySignature, self).__init__(*args, **kwargs)
        self.__name = name
        self.__sharps = sharps
        self.__flats = flats

    def accidentalMarkOf(self, pitch: music21.pitch.Pitch):
        """Given a pitch, return what accidental mark should be displayed for it."""
        sharps = self.__sharps
        flats = self.__flats
        if pitch.accidental is None and pitch.step in sharps or pitch.step in flats:
            return music21.pitch.Accidental("natural")
        elif pitch.accidental is None:
            return None

        elif pitch.accidental.name == "sharp" and pitch.step in sharps:
            return None
        elif pitch.accidental.name == "sharp":
            return music21.pitch.Accidental("sharp")

        elif pitch.accidental.name == "flat" and pitch.step in flats:
            return None
        elif pitch.accidental.name == "flat":
            return music21.pitch.Accidental("flat")

        else:
            raise RuntimeError("Unsupported accidental '" + pitch.accidental.name + "'")

    def __str__(self):
        """Define key signature string representation."""
        return "UIKeySignature<" + self.__name + ">"


def C():
    """Create key signature in C."""
    return UIKeySignature("C", sharps=[])


def G():
    """Create key signature in G."""
    return UIKeySignature("G", sharps=["F"])


def D():
    """Create key signature in D."""
    return UIKeySignature("D", sharps=["F", "C"])


def A():
    """Create key signature in A."""
    return UIKeySignature("A", sharps=["F", "C", "G"])


def E():
    """Create key signature in E."""
    return UIKeySignature("E", sharps=["F", "C", "G", "D"])


def B():
    """Create key signature in B."""
    return UIKeySignature("B", sharps=["F", "C", "G", "D", "A"])


def F():
    """Create key signature in F."""
    return UIKeySignature("F", flats=["B"])


def Bb():
    """Create key signature in Bb."""
    return UIKeySignature("Bb", flats=["B", "E"])


def Eb():
    """Create key signature in Eb."""
    return UIKeySignature("Eb", flats=["B", "E", "A"])


def Ab():
    """Create key signature in Ab."""
    return UIKeySignature("Ab", flats=["B", "E", "A", "D"])


def Db():
    """Create key signature in Db."""
    return UIKeySignature("Db", flats=["B", "E", "A", "D", "G"])


def Fs():
    """Create key signature in F#."""
    return UIKeySignature("B", sharps=["F", "C", "G", "D", "A", "E"])


def fromMusic21(ks: music21.key.KeySignature):
    """
    Given a music21 KeySignature, return a corresponding UIKeySignature.

    Raise a RuntimeError if there is no corresponding supported UIKeySignature.
    """
    # TODO: Support more key signatures.
    if ks.sharps == 0:
        return C()
    elif ks.sharps == 1:
        return G()
    else:
        raise RuntimeError("Unsupported key signature " + ks)
