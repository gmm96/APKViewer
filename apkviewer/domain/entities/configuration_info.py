"""
Build configuration of an APK: ABIs, hardware requirements, locales and
screen densities. Empty tuples mean "nothing found".
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HardwareFeature:
    """A <uses-feature>; `required` is None when android:required can't be resolved."""
    name: str
    required: bool | None = True  # android:required defaults to true

    def as_text(self) -> str:
        status = {True: "Required", False: "Optional", None: "Required status unknown"}[self.required]
        return f"{self.name} ({status})"


@dataclass(frozen=True)
class ConfigurationInfo:
    architectures: tuple[str, ...]
    hardware_requirements: tuple[HardwareFeature, ...]
    locales: tuple[str, ...]
    screen_densities: tuple[str, ...]
