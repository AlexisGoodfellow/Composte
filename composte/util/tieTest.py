import music21

import musicFuns

s = music21.stream.Stream()
musicFuns.insertNote(0.0, s, "C#4", 1.0)
musicFuns.insertNote(1.0, s, "C#4", 1.0)
musicFuns.insertNote(2.0, s, "C#4", 1.0)
musicFuns.insertNote(3.0, s, "C#4", 1.0)
musicFuns.insertNote(4.0, s, "C#4", 1.0)
musicFuns.insertNote(5.0, s, "C#4", 1.0)
musicFuns.insertNote(6.0, s, "C#4", 1.0)
musicFuns.insertNote(7.0, s, "C#4", 1.0)
musicFuns.insertNote(8.0, s, "C#4", 1.0)
musicFuns.updateTieStatus(0.0, s, "C#4")
musicFuns.updateTieStatus(1.0, s, "C#4")
musicFuns.updateTieStatus(2.0, s, "C#4")
musicFuns.updateTieStatus(3.0, s, "C#4")
musicFuns.updateTieStatus(4.0, s, "C#4")
musicFuns.updateTieStatus(5.0, s, "C#4")
musicFuns.updateTieStatus(6.0, s, "C#4")
musicFuns.updateTieStatus(7.0, s, "C#4")
x = musicFuns.insertNote(1.5, s, "E-5", 4.0)

print(x)

musicFuns.playback(s)
s.show()
