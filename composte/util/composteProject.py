import music21
import uuid
import json
import base64
from network.base.exceptions import GenericError

# from copy import deepcopy


class ComposteProject:
    def __init__(self, metadata, parts=None, projectID=None):
        """ Initializes the Project with an empty stream,
            a list of subscribers consisting solely of the owner,
            and a dictionary of metadata about the score. """
        self.metadata = metadata

        if parts is not None:
            self.parts = parts
        else:
            s = music21.stream.Stream()
            s.insert(0.0, music21.key.KeySignature(0))
            s.insert(0.0, music21.meter.TimeSignature("4/4"))
            s.insert(0.0, music21.tempo.MetronomeMark("", 120, 1.0))
            s.insert(0.0, music21.clef.clefFromString("treble"))
            s.insert(0.0, music21.instrument.fromString("piano"))
            self.parts = [s]
        if projectID is not None:
            self.projectID = projectID
        else:
            self.projectID = uuid.uuid4()

    def addPart(self):
        """ Adds a new part to a project. """
        s = music21.stream.Stream()
        s.insert(0.0, music21.key.keySignature(0))
        s.insert(0.0, music21.meter.TimeSignature("4/4"))
        s.insert(0.0, music21.tempo.MetronomeMark("", 120, 1.0))
        s.insert(0.0, music21.clef.clefFromString("treble"))
        s.insert(0.0, music21.instrument.fromString("piano"))
        self.parts.append(s)

    def updateMetadata(self, fieldName, fieldValue):
        """ Allow updates to project metadata. """
        self.metadata[fieldName] = str(fieldValue)

    def swapParts(self, firstPart, secondPart):
        """ Swaps two parts in a project. This is purely cosmetic: all
            it will affect is the order in which parts are presented on
            the GUI. firstPart and secondPart are both 0-indexed integers
            representing the indicies of the parts to swap. """
        if int(firstPart) < len(self.parts) and int(secondPart) < len(self.parts):
            tmp = self.parts[firstPart]
            self.parts[firstPart] = self.parts[secondPart]
            self.parts[secondPart] = tmp
        else:
            raise GenericError

    def removePart(self, partToRemove):
        """ Remove a part from a project. partToRemove is a 0-indexed
            integer representing the index of the part to remove. """
        if int(partToRemove) < len(self.parts):
            del self.parts[partToRemove]
        else:
            raise GenericError

    def serialize(self):
        """ Construct three JSON objects representing the fields of
            a ComposteProject. Intended to be stored in three
            discrete database fields. Returns a tuple containing the
            serialized JSON objects. """
        bits = [music21.converter.freezeStr(part) for part in self.parts]
        bytes_ = [base64.b64encode(bit).decode() for bit in bits]
        parts = json.dumps(bytes_)
        metadata = json.dumps(self.metadata)
        uuid = str(self.projectID)
        return (metadata, parts, uuid)


def deserializeProject(serializedProject):
    """ Deserialize a serialized music21 composteProject
        into a composteProject object. """
    (metadata, parts, id_) = serializedProject
    bits = json.loads(parts)
    bytes_ = [base64.b64decode(bit.encode()) for bit in bits]
    parts = [music21.converter.thawStr(byte) for byte in bytes_]
    metadata = json.loads(metadata)
    id_ = uuid.UUID(id_)
    return ComposteProject(metadata, parts, id_)
