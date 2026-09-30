"""
Port for a scratch directory where files are extracted so they can be
opened or copied without asking the user for a destination.
"""

from abc import ABC, abstractmethod


class TemporaryWorkspace(ABC):
    @property
    @abstractmethod
    def path(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        """Discard everything stored so far; the workspace stays usable."""
        raise NotImplementedError

    @abstractmethod
    def dispose(self) -> None:
        """Release the workspace for good (call on shutdown)."""
        raise NotImplementedError
