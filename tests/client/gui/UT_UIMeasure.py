#!/usr/bin/python3

import sys

import music21

from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
import PyQt5.QtCore as QtCore

from client.gui.UIMeasure import UIMeasure
import client.gui.UIClef as UIClef
import client.gui.UITimeSignature as UITimeSignature
import client.gui.UIKeySignature as UIKeySignature
import client.gui.UINote as UINote

WIDTH = 200

if __name__ == "__main__":
    app = QApplication(sys.argv)
    scene = QGraphicsScene(parent=app)
    view = QGraphicsView(scene, parent=None)

    mea = UIMeasure(
        scene,
        WIDTH,
        UIClef.treble(),
        UIKeySignature.C(),
        UITimeSignature.UITimeSignature(4, 4),
        parent=None,
    )

    mea2 = UIMeasure(
        scene,
        WIDTH,
        UIClef.treble(),
        UIKeySignature.C(),
        UITimeSignature.UITimeSignature(4, 4),
        parent=mea,
    )

    mea3 = UIMeasure(
        scene,
        WIDTH,
        UIClef.treble(),
        UIKeySignature.C(),
        UITimeSignature.UITimeSignature(4, 4),
        parent=mea2,
    )

    mea.setPos(0, 0)
    mea2.setPos(mea.width(), 0)
    mea3.setPos(mea2.width(), 0)
    scene.addItem(mea)

    mea.insertNote(music21.pitch.Pitch("C4"), UINote.UINote_Whole, 0)
    mea.insertNote(music21.pitch.Pitch("E4"), UINote.UINote_Whole, 0)
    mea.insertNote(music21.pitch.Pitch("G4"), UINote.UINote_Whole, 0)
    mea.insertNote(music21.pitch.Pitch("C5"), UINote.UINote_Whole, 0)

    mea2.insertNote(music21.pitch.Pitch("B5"), UINote.UINote_Quarter, 1)
    mea2.insertNote(music21.pitch.Pitch("C5"), UINote.UINote_Quarter, 2)
    mea2.insertNote(music21.pitch.Pitch("D5"), UINote.UINote_Quarter, 3)
    mea3.insertNote(music21.pitch.Pitch("D5"), UINote.UINote_Half, 1)

    view.show()

    exit(app.exec_())
