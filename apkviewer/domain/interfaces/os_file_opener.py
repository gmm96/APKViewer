"""
Port for "open this file with its default application" and "open this
file with... (native OS picker)" integrations, so UI code depends only on
this abstraction and can be unit-tested with a fake implementation.
"""

from abc import ABC, abstractmethod


class OsFileOpener(ABC):
    @abstractmethod
    def open(self, path: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def open_with(self, path: str) -> None:
        """Show the OS's native 'Open with...' picker for a single file."""
        raise NotImplementedError
