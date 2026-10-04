"""
Third-party code bundled in an APK.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ThirdPartyInfo:
    libraries: tuple[str, ...]
    trackers: tuple[str, ...]
