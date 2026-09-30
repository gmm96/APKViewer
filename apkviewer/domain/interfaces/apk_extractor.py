"""
Port for writing entries of an APK to disk.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence


class ApkExtractor(ABC):
    @abstractmethod
    def extract(self, apk_path: str, internal_paths: Sequence[str], dest_dir: str) -> list[str]:
        """Extract the given files/folders into `dest_dir`; return the written paths."""
        raise NotImplementedError

    @abstractmethod
    def extract_all(self, apk_path: str, dest_dir: str) -> list[str]:
        """Extract every file of the APK into `dest_dir`; return the written paths."""
        raise NotImplementedError
