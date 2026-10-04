"""
Content hardcoded inside the APK's code.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddedContent:
    urls: tuple[str, ...]
