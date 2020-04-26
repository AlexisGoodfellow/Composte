#!/usr/bin/env python3

import json

import music21

from protocol.base.exceptions import DeserializationFailure


def serialize(status, *args):
    """
    Serialize messages sent to clients from the server as a list
    [ status, [ *args ] ]
    """
    return json.dumps([status, [str(arg) for arg in args]])


def deserialize(msg):
    """
    Deserialize a message received from a server as a list [ status, [ *args ] ]
    """
    try:
        pythonObject = json.loads(msg)
    except json.decoder.JSONDecodeError as e:
        return ("fail", msg)
    if type(pythonObject) != list:
        raise DeserializationFailure("Received malformed data: {}".format(msg))
    return pythonObject


# ==============================================================================
