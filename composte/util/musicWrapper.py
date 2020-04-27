# Wrapper for musicFuns.py
# All json data is assumed to be deserialized by
# the time these utility functions are invoked.
# Furthermore, the project on which to perform
# the desired function must have been determined
# before these functions are called.

import json

import music21

from network.base.exceptions import GenericError
from util import musicFuns


def performMusicFun(
    projectID, fname, args, partIndex=None, offset=None, fetchProject=None
):
    """
    Wrapper for all music functions.

    The name of the function to be called (as a string) is the first argument,
    and the arguments to the function (as a list) is the second.
    """
    # Fetch the project before anything else
    # for ease of use
    project = fetchProject(projectID)
    args = json.loads(args)
    if fname == "chat":
        return ("ok", "")  # Why not make a chat server too?

    def unpackFun(fname, args):
        """
        Determine which function to call.

        Casts all arguments to the correct types.
        """
        try:
            if partIndex is not None and partIndex != "None":
                musicObject = project.parts[int(partIndex)]
            else:
                musicObject = project.parts

            if fname == "changeKeySignature":
                return (
                    musicFuns.changeKeySignature,
                    [float(args[0]), musicObject, int(args[2])],
                )
            elif fname == "insertNote":
                return (
                    musicFuns.insertNote,
                    [float(args[0]), musicObject, args[2], float(args[3])],
                )
            elif fname == "removeNote":
                return (musicFuns.removeNote, [float(args[0]), musicObject, args[2]])
            elif fname == "insertMetronomeMark":
                return (
                    musicFuns.insertMetronomeMark,
                    [float(args[0]), musicObject, int(args[1])],
                )
            elif fname == "removeMetronomeMark":
                return (musicFuns.removeMetronomeMark, [float(args[0]), musicObject])
            elif fname == "transpose":
                return (musicFuns.transpose, [musicObject, int(args[1])])
            elif fname == "insertClef":
                return (musicFuns.insertClef, [float(args[0]), musicObject, args[2]])
            elif fname == "removeClef":
                return (musicFuns.removeClef, [float(args[0]), musicObject])
            elif fname == "insertMeasures":
                return (
                    musicFuns.insertMeasures,
                    [float(args[0]), musicObject, float(args[2])],
                )
            elif fname == "addInstrument":
                return (musicFuns.addInstrument, [float(args[0]), musicObject, args[2]])
            elif fname == "removeInstrument":
                return (musicFuns.removeInstrument, [float(args[0]), musicObject])
            elif fname == "addDynamic":
                return (musicFuns.addDynamic, [float(args[0]), musicObject, args[2]])
            elif fname == "removeDynamic":
                return (musicFuns.removeDynamic, [float(args[0]), musicObject])
            elif fname == "addLyric":
                return (musicFuns.addLyric, [float(args[0]), musicObject, args[2]])
            else:
                return (None, None)
        except ValueError as e:
            raise GenericError from e

    (function, arguments) = unpackFun(fname, args)
    # Begin error handling
    if (function, arguments) == (None, None):
        return ("fail", "INVALID OPERATION")

    if offset is not None and offset != "None":
        if float(offset) < 0.0:
            raise GenericError

    # Last-minute note length validation hack
    legalLengths = [4.0, 3.0, 2.0, 1.5, 1.0, 0.75, 0.5, 0.375, 0.25]
    if fname == "insertNote":
        if arguments[3] not in legalLengths:
            return ("fail", "INVALID NOTE LENGTH")

    try:
        updateOffsets = function(*arguments)
    except music21.exceptions21.Music21Exception:
        raise GenericError

    # End error handling
    return ("ok", updateOffsets)
