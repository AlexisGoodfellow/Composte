import music21
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsLineItem

from client.gui import UISettings
from client.gui.UINote import UINote


class UIMeasure(QtWidgets.QGraphicsItemGroup):

    __stafflineWidth = 1
    __barlineWidth = 2
    __stafflinePen = QtGui.QPen(
        QtGui.QBrush(Qt.black), __stafflineWidth, Qt.SolidLine, Qt.FlatCap
    )
    __barlinePen = QtGui.QPen(
        QtGui.QBrush(Qt.black), __barlineWidth, Qt.SolidLine, Qt.FlatCap
    )

    def __init__(
        self,
        scene,
        width,
        clef,
        keysig,
        timesig,
        newClef=False,
        newKeysig=False,
        newTimesig=False,
        forceDrawClef=False,
        *args,
        **kwargs,
    ):
        """
        :note: Most of the features related to drawing clef/keysig/timesig don't
        work correctly yet.

        :param canvas: QGraphicsScene being used to manage the score view.
        :param width: Visual width of the measure.
        :param clef: UIClef for the measure.
        :param keysig: UIKeySignature for the measure.
        :param timesig: UITimeSignature for the measure.
        :param newClef: If set, clef has changed since previous measure, so draw
            clef mark.
        :param newKeysig: If set, key signature has changed since previous
            measure, so draw it.
        :param newTimesig: If set, time signature has changed since previous
            measure, so draw it.
        :param forceDrawClef: Force clef, key signature, time signature to be
            drawn.  For use at the beginning of staff lines, and for debugging.
        """
        super(UIMeasure, self).__init__(*args, **kwargs)
        self.__scene = scene
        self.__width = width

        self.__clef = clef
        self.__newClef = newClef
        self.__keysig = keysig
        self.__newKeysig = newKeysig
        self.__timesig = timesig
        self.__newTimesig = newTimesig

        self.__baseObjs = []
        self.__noteObjs = {}

        self.__initGraphics()

    def __initGraphics(self):
        """
        Draw in staff and bar lines.
        """
        for i in range(0, 5):
            line = QGraphicsLineItem(
                0,
                2 * i * UISettings.PITCH_LINE_SEP,
                self.__width,
                2 * i * UISettings.PITCH_LINE_SEP,
                self,
            )
            line.setPen(self.__stafflinePen)
            self.__baseObjs.append(line)

        barline_y1 = -self.__stafflineWidth / 2
        barline_y2 = 4 * 2 * UISettings.PITCH_LINE_SEP + self.__stafflineWidth / 2

        barline = QGraphicsLineItem(0, barline_y1, 0, barline_y2, parent=self)
        barline.setPen(self.__barlinePen)
        self.__baseObjs.append(barline)
        barline = QGraphicsLineItem(
            self.__width, barline_y1, self.__width, barline_y2, parent=self
        )
        barline.setPen(self.__barlinePen)
        self.__baseObjs.append(barline)

    def clear(self):
        """
        Clear all graphics objects, except for the staff and bar lines.
        """
        for item in self.__noteObjs.values():
            self.__scene.removeItem(item)
        self.__noteObjs.clear()
        for item in self.__baseObjs:
            self.__scene.removeItem(item)
        self.__baseObjs.clear()
        self.__initGraphics()

    def __redraw(self):
        """
        Redraw all graphics objects, moving them to update as necessary, e.g.
        after a resize.

        :note: This does *not* update the existing notes from the underlying
        Music21 representation.
        """
        ## TODO: This is a terrible way of doing this, we could reuse the old
        ##   objects rather than destroying them and creating new ones.
        notes = list(self.__noteObjs.keys())
        self.clear()

        self.__initGraphics()
        for note in notes:
            self.addNote(*note)

    def insertNote(self, pitch: music21.pitch.Pitch, ntype, offset: float):
        """
        Insert a note into this measure.  Raises ValueError if the note extends
        past the end of the measure.

        :param pitch: The pitch of the note to be inserted, as a music21 Pitch.
        :param ntype: The type of note to be inserted; this should be a subclass
            of UINote.UINote.
        :param offset: Quarter-note offset of the start of the note, from the
            beginning of this measure.
        """
        note = ntype(pitch, self.__clef, self.__keysig)
        if offset + note.length() > self.length():
            raise ValueError("Note extends past end of measure")
        note.setParentItem(self)
        self.__noteObjs[(pitch, ntype, offset)] = note

        notesWidth = (
            self.__width - UISettings.BARLINE_FRONT_PAD - UISettings.BARLINE_REAR_PAD
        )
        note_x = UISettings.BARLINE_FRONT_PAD + notesWidth * (
            offset / (self.length() - 1)
        )
        note_y = 0
        note.setPos(note_x, note_y)

    def deleteNote(self, pitch: music21.pitch.Pitch, offset: float):
        """
        Remove a note from this measure.  Return whether the note was
        successfully removed.

        :param pitch: The pitch of the note to be removed, as a music21 Pitch.
        :param offset: Quarter-note offset of the start of the note to be
            removed, from the beginning of this measure

        :returns: True when a note is successfully removed; False if the note to
                  be removed does not exist.
        """
        for note in self.__noteObjs.keys():
            if note[0] == pitch and note[2] == offset:
                self.__scene.removeItem(self.__noteObjs[note])
                del self.__noteObjs[note]
                return True
        return False

    # Getters
    def clef(self):
        return self.__clef

    def keysig(self):
        return self.__keysig

    def timesig(self):
        return self.__timesig

    def width(self):
        return self.__width

    # Setters
    def setClef(self, clef, newClef=True):
        self.__clef = clef
        self.__newClef = newClef

    def setKeysig(self, keysig, newKeysig=True):
        self.__keysig = keysig
        self.__newKeysig = newKeysig

    def setTimesig(self, timesig, newTimesig=True):
        self.__timesig = timesig
        self.__newTimesig = newTimesig

    def setWidth(self, width):
        self.__width = width
        self.__redraw()

    def length(self):
        """
        Return the time length of this staff, i.e. the time between the first
        beat of this line and the first beat of the next one.
        """
        return self.__timesig.measureLength()
