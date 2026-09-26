"""
Port for a pluggable per-file decoder used while extracting entries from
an APK's zip archive (e.g. decoding Android Binary XML into plain XML).
"""

from abc import ABC, abstractmethod


class FileDecoder(ABC):
    @abstractmethod
    def can_decode(self, data: bytes) -> bool:
        raise NotImplementedError

    @abstractmethod
    def decode(self, data: bytes) -> bytes:
        raise NotImplementedError
