import music21

from PyQt5 import QtWidgets


class UITimeSignature(QtWidgets.QGraphicsItem):
    def __init__(self, num, den, *args, **kwargs):
        """
        :param num: Numerator of the time signature.
        :param den: Denominator of the time signature.
        """
        super(UITimeSignature, self).__init__(*args, **kwargs)
        self.__num = num
        self.__den = den

    def __eq__(self, ts):
        return self.__num == ts.__num and self.__den == ts.__den

    def measureLength(self):
        return 4 * self.__num / self.__den


# END class UITimeSignature


def fromMusic21(ts: music21.meter.TimeSignature):
    """
    Given a Musci21 TimeSignature, return a corresponding UITimeSignature.
    """
    return UITimeSignature(ts.numerator, ts.denominator)
