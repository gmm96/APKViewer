"""
Port for asking the operating system which color scheme (light or dark)
the user has selected.
"""

from abc import ABC, abstractmethod

from apkviewer.domain.entities.color_scheme import ColorScheme


class SystemColorSchemeDetector(ABC):
    @abstractmethod
    def detect(self) -> ColorScheme:
        """Return the OS scheme; LIGHT whenever it cannot be determined."""
        raise NotImplementedError
