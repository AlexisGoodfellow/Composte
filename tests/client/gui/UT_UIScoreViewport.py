#!/usr/bin/python3

import sys

import music21
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

import client.gui.UIClef as UIClef
import client.gui.UIKeySignature as UIKeySignature
import client.gui.UINote as UINote
import client.gui.UIScoreViewport as UIScoreViewport
import client.gui.UITimeSignature as UITimeSignature
from client.gui.UIMeasure import UIMeasure

WIDTH = 200

if __name__ == "__main__":
    app = QApplication(sys.argv)
    vp = UIScoreViewport.UIScoreViewport(measuresPerLine=5, width=1000)
    vp.addPart(
        UIClef.treble(), UIKeySignature.C(), UITimeSignature.UITimeSignature(4, 4)
    )
    vp.addPart(
        UIClef.treble(), UIKeySignature.C(), UITimeSignature.UITimeSignature(4, 4)
    )
    vp.addPart(
        UIClef.treble(), UIKeySignature.C(), UITimeSignature.UITimeSignature(4, 4)
    )
    vp.addLine()
    vp.show()
    exit(app.exec_())
