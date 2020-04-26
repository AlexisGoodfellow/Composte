#!/usr/bin/python3

import sys

import music21

from util.composteProject import ComposteProject

from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
import PyQt5.QtCore as QtCore

import client.gui.UIScoreViewport as UIScoreViewport
from client.gui.UIMeasure import UIMeasure
import client.gui.UIClef as UIClef
import client.gui.UITimeSignature as UITimeSignature
import client.gui.UINote as UINote

WIDTH = 1000

if __name__ == "__main__":
    app = QApplication(sys.argv)
    vp = UIScoreViewport.UIScoreViewport(measuresPerLine=5, width=WIDTH)

    parts = []
    pr = music21.stream.Stream()
    pr.append(music21.clef.TrebleClef())
    pr.append(music21.key.KeySignature(0))
    pr.append(music21.meter.TimeSignature("4/4"))
    pr.insert(music21.note.Note("D5", type="half", dots=1))
    pr.append(music21.note.Note("E5", type="quarter"))
    pr.append(music21.note.Note("C5", type="16th", dots=1))
    parts.append(pr)
    pr = music21.stream.Stream()
    pr.append(music21.clef.TrebleClef())
    pr.append(music21.key.KeySignature(0))
    pr.append(music21.meter.TimeSignature("4/4"))
    pr.append(music21.note.Note("C#5", type="quarter"))
    pr.append(music21.note.Note("D-5", type="quarter"))
    pr.append(music21.note.Note("E#5", type="quarter"))
    pr.append(music21.note.Note("F#5", type="quarter"))
    pr.append(music21.note.Note("E#4", type="half"))
    pr.append(music21.note.Note("G#4", type="half"))
    parts.append(pr)

    project = ComposteProject("", parts=parts)

    vp.update(project, None, None)
    vp.show()
    exit(app.exec_())
