"""
Port for putting real files (not text) onto the system clipboard.
"""

from abc import ABC, abstractmethod
from typing import List


class ClipboardFileCopier(ABC):
    @abstractmethod
    def copy(self, file_paths: List[str]) -> bool:
        raise NotImplementedError
