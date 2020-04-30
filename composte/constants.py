"""Project wide constants."""
from composte.util import musicFuns

LEGAL_NOTE_LENGTHS = [4.0, 3.0, 2.0, 1.5, 1.0, 0.75, 0.5, 0.375, 0.25]

DEBUG_MESSAGES = {
    "delete": (
        "delete/d PART_INDEX PITCH OFFSET\n"
        "    Remove the note in the indicated part at\n"
        "    quarter-note-offset OFFSET and pitch PITCH"
    ),
    "insert": (
        "insert/d PART_INDEX PITCH NOTE_TYPE OFFSET\n"
        "    insert a NOTE_TYPE into the indicated part at\n"
        "    quarter-note-offset OFFSET with given PITCH"
    ),
    "chat": (
        "chat/c MESSAGE\n"
        "    Send MESSAGE (which may contain spaces, but not "
        "    semicolons) to all users\n working on the current "
        "    project"
    ),
    "play": (
        "play/p [PART_INDEX]\n"
        "    Play back the part specified by the given index, "
        "or part 0 if none is specified."
    ),
    "ttsoff": "ttsoff       --  Disable text-to-speech for chat messages.",
    "ttson": "ttson         --  Enable text-to-speech for chat messages.",
    "clear": "clear         --  Clear the debug console history"
}


def MUSIC_FUN_LOOKUP_TABLE(musicObject, args):
    """Lookup table for music functions."""
    return {
        "changeKeySignature": (
            musicFuns.changeKeySignature,
            [float(args[0]), musicObject, int(args[2])],
        ),
        "insertNote": (
            musicFuns.insertNote,
            [float(args[0]), musicObject, args[2], float(args[3])],
        ),
        "removeNote": (musicFuns.removeNote, [float(args[0]), musicObject, args[2]]),
        "insertMetronomeMark": (
            musicFuns.insertMetronomeMark,
            [float(args[0]), musicObject, int(args[1])],
        ),
        "removeMetronomeMark": (
            musicFuns.removeMetronomeMark,
            [float(args[0]), musicObject],
        ),
        "transpose": (musicFuns.transpose, [musicObject, int(args[1])]),
        "insertClef": (musicFuns.insertClef, [float(args[0]), musicObject, args[2]]),
        "removeClef": (musicFuns.removeClef, [float(args[0]), musicObject]),
        "insertMeasures": (
            musicFuns.insertMeasures,
            [float(args[0]), musicObject, float(args[2])],
        ),
        "addInstrument": (
            musicFuns.addInstrument,
            [float(args[0]), musicObject, args[2]],
        ),
        "removeInstrument": (musicFuns.removeInstrument, [float(args[0]), musicObject]),
        "addDynamic": (musicFuns.addDynamic, [float(args[0]), musicObject, args[2]]),
        "removeDynamic": (musicFuns.removeDynamic, [float(args[0]), musicObject]),
        "addLyric": (musicFuns.addLyric, [float(args[0]), musicObject, args[2]]),
    }

