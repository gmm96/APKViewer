"""
Port for putting real files (not text) onto the system clipboard.
"""

from abc import ABC, abstractmethod


class ClipboardFileCopier(ABC):
    @abstractmethod
    def copy(self, file_paths: list[str]) -> bool:
        raise NotImplementedError
