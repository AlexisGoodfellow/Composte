import music21

# Create the stream
s = music21.stream.Stream()
# Make two notes with a tie between them
note1 = music21.note.Note("C#4", 1.0)
note1.tie = music21.tie.Tie("start")
note2 = music21.note.Note("C#4", 2.0)
note2.tie = music21.tie.Tie("stop")
# Insert the notes in the stream
s.insert(0.0, note1)
s.insert(1.0, note2)
# Attempt to playback the stream
music21.midi.realtime.StreamPlayer(s).play()  # 2 notes play instead of 1
# Check the score in a GUI to make sure the tie is present
s.show()
