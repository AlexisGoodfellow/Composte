"""Server serialization protocol."""
import json
from typing import Any, List

from protocol.base.exceptions import DeserializationFailure


def serialize(status: str, *args: List[Any]) -> str:
    """Serialize messages sent to clients from the server as a list."""
    return json.dumps([status, [str(arg) for arg in args]])


def deserialize(msg: str) -> List[Any]:
    """Deserialize a message received from a server as a list."""
    try:
        pythonObject = json.loads(msg)
    except json.decoder.JSONDecodeError:
        return ["fail", msg]
    if type(pythonObject) != list:
        raise DeserializationFailure("Received malformed data: {}".format(msg))
    return pythonObject
