"""
Port that exposes the identifier of the application's main window in the
format desktop services expect (e.g. the parent_window argument of the
freedesktop portals). Lets infrastructure ask "which window is mine?"
without depending on any GUI toolkit.
"""

from abc import ABC, abstractmethod


class WindowHandleProvider(ABC):
    @abstractmethod
    def get_handle(self) -> str:
        """Return the window identifier, or an empty string if unknown."""
        raise NotImplementedError
