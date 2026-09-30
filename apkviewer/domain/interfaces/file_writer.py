"""
Port for writing a user-chosen file. Implementations raise OSError when
the file cannot be written.
"""

from abc import ABC, abstractmethod


class FileWriter(ABC):
    @abstractmethod
    def write_text(self, path: str, content: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def write_bytes(self, path: str, data: bytes) -> None:
        raise NotImplementedError
