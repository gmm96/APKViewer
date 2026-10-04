"""
Build configuration of an APK: ABIs, hardware requirements, locales and
screen densities. Empty tuples mean "nothing found".
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfigurationInfo:
    architectures: tuple[str, ...]
    hardware_requirements: tuple[str, ...]
    locales: tuple[str, ...]
    screen_densities: tuple[str, ...]
