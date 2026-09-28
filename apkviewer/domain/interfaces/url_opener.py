"""
Port for "open this URL in the user's default web browser", so UI code
depends on an abstraction instead of the `webbrowser` module.
"""

from abc import ABC, abstractmethod


class UrlOpener(ABC):
    @abstractmethod
    def open(self, url: str) -> None:
        """Open `url` in the default browser. Raises RuntimeError on failure."""
        raise NotImplementedError
