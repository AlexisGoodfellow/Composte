"""Viewport for the entire score."""
from typing import Optional, Tuple

import music21
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt

import client.gui.UIClef as UIClef
import client.gui.UIKeySignature as UIKeySignature
import client.gui.UINote as UINote
import client.gui.UISettings as UISet
import client.gui.UITimeSignature as UITimeSignature
import util.musicFuns as musicFuns
from client.gui.UIMeasure import UIMeasure
from client.gui.UIStaffGroup import UIStaffGroup


class UIScoreViewport(QtWidgets.QGraphicsView):
    """Viewport for displaying the score for a project."""

    def __init__(
        self,
        measuresPerLine=4,
        mode="ptr",
        width=600,
        zoom_min=-4,
        zoom_max=4,
        *args,
        **kwargs,
    ):
        """Initialize the viewport."""
        super(UIScoreViewport, self).__init__(*args, **kwargs)
        self.__width = width
        self.__measuresPerLine = measuresPerLine
        self.__zoom_min = zoom_min
        self.__zoom_max = zoom_max
        self.__zoom = 0

        self.__mode = mode

        self.__selected = None

        self.__measures = []
        self.__lines = []

        self.__scoreScene = QtWidgets.QGraphicsScene(parent=self)
        self.__scoreScene.setBackgroundBrush(QtGui.QBrush(UISet.BG_COLOR))
        self.setScene(self.__scoreScene)

    def update(self, project, startOffset: float, endOffset: float) -> None:  # noqa
        """
        Update the region of the score between startOffset and endOffset.

        If startOffset is None, start at the beginning. If endOffset is None,
        update through the end. If both are None, update the entire score,
        including updating the number of parts.

        :note: Updating sections is not currently supported; all updates redraw
        the entire score.

        :param project: ComposteProject to draw from.
        :param startOffset: First quarter-note offset to be updated.  If None,
            update from start of project.
        :param startOffset: Quarter-note offset after the last one to be
            updated.  If None, update through end of project.
        """
        if startOffset is None and endOffset is None:
            self.clear()
            for part in project.parts:
                cl = UIClef.fromMusic21(part.getClefs()[0])
                ks = UIKeySignature.fromMusic21(part.getKeySignatures()[0])
                ts = UITimeSignature.fromMusic21(part.getTimeSignatures()[0])
                self.addPart(cl, keysig=ks, timesig=ts)

        if startOffset is None:
            st_idx, st_offset = 0, 0
        else:
            st_idx, st_offset = self.__measureIndexFromOffset(startOffset, extend=True)
        if endOffset is None:
            _, en_off1 = self.__endOfDisplay()
            en_off2 = max(map(lambda strm: strm.highestTime, project.parts))
            en_off = max(en_off1, en_off2) + 1
            en_idx, en_offset = self.__measureIndexFromOffset(en_off, extend=True)
            # Pad out the end of the updated region to include the entire last measure.
            mea = self.__measures[0][en_idx]
            en_offset += mea.length()
            en_idx += 1
        else:
            en_idx, en_offset = self.__measureIndexFromOffset(endOffset, extend=True)

        # Erase the contents of the measures to be updated.
        for i in range(st_idx, en_idx):
            while st_idx > len(self.__measures[0]):
                self.addLine()
            for meas in self.__measures:
                meas[i].clear()

        # Insert everything within the time interval being updated back into the
        # appropriate measures.
        for part in range(len(project.parts)):
            for om_item in musicFuns.boundedOffset(
                project.parts[part], (st_offset, en_offset)
            ):
                offs = om_item.offset
                obj = om_item.element

                idx, meaoffs = self.__measureIndexFromOffset(offs, extend=True)
                mea = self.__measures[part][idx]

                if isinstance(obj, music21.clef.Clef):
                    cl = UIClef.fromMusic21(obj)
                    if idx == 0:
                        mea.setClef(cl, newClef=True)
                    else:
                        lastCl = self.__measures[part][idx - 1].clef()
                        mea.setClef(cl, newClef=(cl == lastCl))
                elif isinstance(obj, music21.key.KeySignature):
                    ks = UIKeySignature.fromMusic21(obj)
                    if idx == 0:
                        mea.setKeysig(ks, newKeysig=True)
                    else:
                        lastKs = self.__measures[part][idx - 1].keysig()
                        mea.setKeysig(ks, newKeysig=(ks == lastKs))

                elif isinstance(obj, music21.meter.TimeSignature):
                    if idx == 0:
                        mea.setTimesig(ts, newTimesig=True)
                    else:
                        lastTs = self.__measures[part][idx - 1].timesig()
                        mea.setTimesig(ts, newTimesig=(ts == lastTs))
                elif isinstance(obj, music21.note.Note):
                    ntype = UINote.ntypeFromMusic21(obj)
                    self.insertNote(part, obj.pitch, ntype, offs)

    def __endOfDisplay(self) -> Tuple[int, float]:
        """
        Return the end of the display.

        Specifically, return the index and offset of the beginning of the first
        measure after those that currently exist.

        :returns: (index, offset) of the measure after the last one.
        """
        if len(self.__measures) == 0:
            return (None, None)
        mea_offset = 0
        mea_index = 0
        for mea in self.__measures[0]:
            mea_offset += self.__measures[0][mea_index].length()
            mea_index += 1
        return mea_index, mea_offset

    def __measureIndexFromOffset(
        self, offset: float, extend: bool = False
    ) -> Tuple[Optional[int], Optional[float]]:
        """
        Return the index and offset of the measure containing the given offset.

        Optionally extend the existing measures to continue through this
        measure.

        :param offset: Offset whose measure index is being checked.
        :param extend: When True, extend the measure list through the measure
            which the given offset would be in.

        :returns: (measure_index, measure_offset) of the beginning of the
                  measure containing the given offset.  Returns (None, None)
                  when there are no parts, or when there is no mesaure for the
                  given offset and extend is False.
        """
        if len(self.__measures) == 0:
            return (None, None)
        mea_offset = 0
        mea_index = 0
        while mea_offset <= offset:
            if mea_index >= len(self.__measures[0]):
                if extend:
                    self.addLine()
                else:
                    return (None, None)
            mea = self.__measures[0][mea_index]
            mea_offset += mea.length()
            mea_index += 1

        mea_offset -= mea.length()
        mea_index -= 1

        return mea_index, mea_offset

    def clear(self) -> None:
        """Clear the score."""
        for sg in self.__lines:
            self.__scoreScene.removeItem(sg)
        self.__lines.clear()
        self.__measures.clear()

    def addPart(self, clef, keysig=None, timesig=None) -> None:
        """Add a part to the score."""
        if len(self.__measures) == 0 and (keysig is None or timesig is None):
            raise RuntimeError("Must specify time and key " "signatures for first part")
        elif len(self.__measures) == 0:
            part = []
            for i in range(self.__measuresPerLine):
                mea = UIMeasure(
                    self.__scoreScene,
                    self.__width / self.__measuresPerLine,
                    clef,
                    keysig,
                    timesig,
                    parent=None,
                )
                part.append(mea)
        else:
            part = []
            for m in self.__measures[0]:
                mea = UIMeasure(
                    self.__scoreScene,
                    self.__width / self.__measuresPerLine,
                    clef,
                    m.keysig(),
                    m.timesig(),
                    parent=None,
                )
                part.append(mea)
        self.__measures.append(part)

        if not self.__lines:
            sg = UIStaffGroup(
                self.__scoreScene,
                self.__measures,
                0,
                len(self.__measures[0]),
                parent=None,
            )
            self.__lines.append(sg)
            sg.setPos(0, 0)
            self.__scoreScene.addItem(sg)

        last_sg = None
        for sg in self.__lines:
            sg.refresh()
            if last_sg is not None:
                y = last_sg.boundingRect().height()
                sg.setPos(sg.mapFromItem(last_sg, 0, y))
            else:
                sg.setPos(0, 0)
            last_sg = sg

    def addLine(self):
        """Add a new score line."""
        for part in self.__measures:
            if part:
                lastMeasure = part[-1]
                for i in range(self.__measuresPerLine):
                    mea = UIMeasure(
                        self.__scoreScene,
                        self.__width / self.__measuresPerLine,
                        lastMeasure.clef(),
                        lastMeasure.keysig(),
                        lastMeasure.timesig(),
                        parent=None,
                    )
                    part.append(mea)
            else:
                raise RuntimeError("Empty measure list in " + "UIScoreViewport.addLine")

        sg = UIStaffGroup(
            self.__scoreScene,
            self.__measures,
            len(self.__measures[0]) - self.__measuresPerLine,
            len(self.__measures[0]),
            parent=None,
        )
        y = self.__lines[-1].boundingRect().height()
        sg.setPos(sg.mapFromItem(self.__lines[-1], 0, y))
        self.__lines.append(sg)
        self.__scoreScene.addItem(sg)

    def insertNote(self, part: int, pitch, ntype, offset: float) -> None:
        """
        Insert a note into the score.

        Raises RuntimeError when inserting into an invalid part or at a negative offset.

        :param part: Index of part to be inserted into.
        :param pitch: The pitch of the note to be inserted, as a music21 Pitch.
        :param ntype: The type of note to be inserted; this should be a subclass
            of UINote.UINote.
        :param offset: Quarter-note offset of the start of the note, from the
            beginning of the piece.
        """
        if part >= len(self.__measures):
            raise ValueError("Part index " + str(part) + " does not exist.")
        if offset < 0:
            raise ValueError("Note offset " + str(offset) + " is invalid.")

        mea_index, mea_offset = self.__measureIndexFromOffset(offset, extend=True)
        self.__measures[part][mea_index].insertNote(pitch, ntype, offset - mea_offset)

    def deleteNote(self, part: int, pitch, offset: float) -> bool:
        """
        Remove a note from the score.

        Raises RuntimeError when removing from an invalid part or at a negative offset.
        Return whether the note was successfully removed.

        :param part: Index of part containing the note to be removed.
        :param pitch: The pitch of the note to be removed, as a music21 Pitch.
        :param offset: Quarter-note offset of the start of the note to be
            removed, from the beginning of the piece.

        :returns: True when a note is successfully removed; False if the note to
                  be removed does not exist.
        """
        if part >= len(self.__measures):
            raise RuntimeError("Inserting note into non-existent part")
        if offset < 0:
            raise RuntimeError("Inserting note at negative offset")

        mea_index, mea_offset = self.__measureIndexFromOffset(offset)
        if mea_index is None:
            return False
        return self.__measures[part][mea_index].deleteNote(pitch, offset - mea_offset)

    def parts(self) -> int:
        """Return the number of parts the UIScoreViewport is considering."""
        return len(self.__measures)

    def measures(self) -> int:
        """
        Return the number of measures the UIScoreViewport holds.

        Defaults to 0 if no parts exist.
        """
        if self.parts() > 0:
            return len(self.__measures[0])
        else:
            return 0

    def keyPressEvent(self, ev):
        """Handle keyboard events."""
        mods = QtWidgets.QApplication.keyboardModifiers()
        if mods == Qt.ControlModifier:
            # C-0 : Reset zoom
            if ev.key() == Qt.Key_0:
                self.__zoom = 0
                self.resetTransform()
            # C-- : Zoom out
            if ev.key() == Qt.Key_Minus:
                if self.__zoom != self.__zoom_min:
                    self.scale(1 / 1.25, 1 / 1.25)
                    self.__zoom -= 1
            # C-= : Zoom in
            if ev.key() == Qt.Key_Equal:
                if self.__zoom != self.__zoom_max:
                    self.scale(1.25, 1.25)
                    self.__zoom += 1
