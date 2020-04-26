#!/usr/bin/python3

import sys

import music21

from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
import PyQt5.QtCore as QtCore

from client.gui.UIMeasure import UIMeasure
from client.gui.UIStaff import UIStaff
import client.gui.UIClef as UIClef
import client.gui.UITimeSignature as UITimeSignature
import client.gui.UIKeySignature as UIKeySignature
import client.gui.UINote as UINote

WIDTH = 200

if __name__ == "__main__":
    app = QApplication(sys.argv)
    scene = QGraphicsScene(parent=app)
    view = QGraphicsView(scene, parent=None)

    meas = [
        UIMeasure(
            scene,
            WIDTH,
            UIClef.treble(),
            UIKeySignature.C(),
            UITimeSignature.UITimeSignature(4, 4),
        ),
        UIMeasure(
            scene,
            WIDTH,
            UIClef.treble(),
            UIKeySignature.C(),
            UITimeSignature.UITimeSignature(4, 4),
        ),
        UIMeasure(
            scene,
            WIDTH,
            UIClef.treble(),
            UIKeySignature.C(),
            UITimeSignature.UITimeSignature(4, 4),
        ),
    ]

    st = UIStaff(meas, 0, len(meas))
    scene.addItem(st)

    meas[0].insertNote(music21.pitch.Pitch("C4"), UINote.UINote_Whole, 0)
    meas[0].insertNote(music21.pitch.Pitch("E4"), UINote.UINote_Whole, 0)
    meas[0].insertNote(music21.pitch.Pitch("G4"), UINote.UINote_Whole, 0)
    meas[0].insertNote(music21.pitch.Pitch("C5"), UINote.UINote_Whole, 0)

    meas[1].insertNote(music21.pitch.Pitch("B5"), UINote.UINote_Quarter, 1)
    meas[1].insertNote(music21.pitch.Pitch("C5"), UINote.UINote_Quarter, 2)
    meas[1].insertNote(music21.pitch.Pitch("D5"), UINote.UINote_Quarter, 3)
    meas[2].insertNote(music21.pitch.Pitch("D5"), UINote.UINote_Half, 1)

    view.show()

    exit(app.exec_())
