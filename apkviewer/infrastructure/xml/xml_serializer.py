"""
Contract abstracting which XML library serializes an XML tree into bytes,
so ManifestFormatter doesn't depend on a concrete library.
"""

from abc import ABC, abstractmethod
from typing import Any


class XmlSerializer(ABC):
    @abstractmethod
    def serialize(self, xml_root: Any) -> bytes:
        raise NotImplementedError
