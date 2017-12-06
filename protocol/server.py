#!/usr/bin/env python3

import json
import music21

from protocol.base.exceptions import DeserializationFailure

def serialize(status, *args):
    return json.dumps(
        [status, [str(arg) for arg in args]]
    )

def deserialize(msg):
    pythonObject = json.loads(msg)
    if type(pythonObject) != list:
        raise DeserializationFailure("Received malformed data: {}".format(msg))
    return pythonObject

# ==============================================================================

