"""
Wrapper for musicFuns.py.

All json data is assumed deserialized by the time these utility functions are invoked.
Furthermore, the project on which to perform the desired function must have been
determined before these functions are called.
"""

import json
from typing import Callable, List, Optional, Tuple, Any

import music21

from composte.constants import LEGAL_NOTE_LENGTHS, MUSIC_FUN_LOOKUP_TABLE
from network.base.exceptions import GenericError


def unpackFun(project, partIndex, fname, args):
    """
    Determine which function to call.

    Casts all arguments to the correct types.
    """
    try:
        if partIndex is not None and partIndex != "None":
            musicObject = project.parts[int(partIndex)]
        else:
            musicObject = project.parts

        return (
            MUSIC_FUN_LOOKUP_TABLE(musicObject, args)[fname]
            if fname in MUSIC_FUN_LOOKUP_TABLE
            else (None, None)
        )
    except ValueError as e:
        raise GenericError from e


def handle_bad_offset(offset: Optional[str]) -> None:
    """Handle offsets that are invalid."""
    if offset is not None and offset != "None":
        if float(offset) < 0.0:
            raise GenericError


def update_project(unpacked: Tuple[Callable, List[Any]]) -> List[float]:
    function, arguments = unpacked
    try:
        return function(*arguments)
    except music21.exceptions21.Music21Exception:
        raise GenericError


def performMusicFun(
    project_id, fname, args, partIndex=None, offset=None, fetchProject=None
):
    """
    Wrap all music functions.

    The name of the function to be called (as a string) is the first argument,
    and the arguments to the function (as a list) is the second.
    """
    # Fetch the project before anything else
    # for ease of use
    project = fetchProject(project_id)
    args = json.loads(args)
    if fname == "chat":
        return ("ok", "")  # Why not make a chat server too?

    unpacked = unpackFun(project, partIndex, fname, args)
    if (unpacked[0], unpacked[1]) == (None, None):
        return ("fail", "INVALID OPERATION")

    handle_bad_offset(offset)

    # Last-minute note length validation hack
    if fname == "insertNote":
        if unpacked[1][3] not in LEGAL_NOTE_LENGTHS:
            return ("fail", "INVALID NOTE LENGTH")

    updateOffsets = update_project(unpacked)

    # End error handling
    return ("ok", updateOffsets)
