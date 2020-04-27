import base64
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple

import music21

from composte.network.base.exceptions import GenericError


class ComposteProject:
    """Object representing the entire composte project."""

    def __init__(
        self,
        metadata: Dict[str, Any],
        parts: Optional[List[music21.part.Part]] = None,
        project_id: Optional[uuid.UUID] = None,
    ):
        """
        Initialize the Project.

        The project starts with:
            - An empty stream
            - A list of subscribers consisting solely of the owner
            - A dictionary of metadata about the score
        """
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
        if project_id is not None:
            self.project_id = project_id
        else:
            self.project_id = uuid.uuid4()

    def addPart(self) -> None:
        """Add a new part to a project."""
        s = music21.stream.Stream()
        s.insert(0.0, music21.key.keySignature(0))
        s.insert(0.0, music21.meter.TimeSignature("4/4"))
        s.insert(0.0, music21.tempo.MetronomeMark("", 120, 1.0))
        s.insert(0.0, music21.clef.clefFromString("treble"))
        s.insert(0.0, music21.instrument.fromString("piano"))
        self.parts.append(s)

    def updateMetadata(self, fieldName: str, fieldValue: Any) -> None:
        """Allow updates to project metadata."""
        self.metadata[fieldName] = str(fieldValue)

    def swapParts(self, firstPart: int, secondPart: int) -> None:
        """
        Swap two parts in a project.

        This is purely cosmetic: all it will affect is the order in which parts
        are presented on the GUI. firstPart and secondPart are both 0-indexed.
        """
        if int(firstPart) < len(self.parts) and int(secondPart) < len(self.parts):
            tmp = self.parts[firstPart]
            self.parts[firstPart] = self.parts[secondPart]
            self.parts[secondPart] = tmp
        else:
            raise GenericError

    def removePart(self, partToRemove: int) -> None:
        """Remove a part from a project. partToRemove is 0-indexed."""
        if int(partToRemove) < len(self.parts):
            del self.parts[partToRemove]
        else:
            raise GenericError

    def serialize(self) -> Tuple[str, str, str]:
        """
        Construct three JSON objects representing the fields of a ComposteProject.

        Intended to be stored in three discrete database fields.

        Returns a tuple containing the serialized JSON objects.
        """
        bits = [music21.converter.freezeStr(part) for part in self.parts]
        bytes_ = [base64.b64encode(bit).decode() for bit in bits]
        parts = json.dumps(bytes_)
        metadata = json.dumps(self.metadata)
        uuid = str(self.project_id)
        return (metadata, parts, uuid)


def deserializeProject(serializedProject: Tuple[str, str, str]) -> ComposteProject:
    """Deserialize a serialized music21 composteProject to a composteProject object."""
    (metadata, parts, id_) = serializedProject
    bits = json.loads(parts)
    bytes_ = [base64.b64decode(bit.encode()) for bit in bits]
    reconstructed_parts = [music21.converter.thawStr(byte) for byte in bytes_]
    reconstructed_metadata = json.loads(metadata)
    project_id = uuid.UUID(id_)
    return ComposteProject(reconstructed_metadata, reconstructed_parts, project_id)
