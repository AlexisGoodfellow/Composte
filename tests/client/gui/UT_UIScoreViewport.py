#!/usr/bin/python3

import sys

import music21

from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
import PyQt5.QtCore as QtCore

import client.gui.UIScoreViewport as UIScoreViewport
from client.gui.UIMeasure import UIMeasure
import client.gui.UIClef as UIClef
import client.gui.UITimeSignature as UITimeSignature
import client.gui.UIKeySignature as UIKeySignature
import client.gui.UINote as UINote

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
