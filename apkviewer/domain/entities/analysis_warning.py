"""
Something the analysis could not read, so that "nothing found" can be told
apart from "could not look". Each warning belongs to the area of the UI it
affects.
"""

from dataclasses import dataclass
from enum import Enum


class AnalysisArea(Enum):
    INFO = "info"              # Info tab
    SECURITY = "security"      # Security tab
    PERMISSIONS = "permissions"  # Permissions tab
    COMPONENTS = "components"  # Components and Intents tabs
    ICON = "icon"              # the header icon (shown with the Info tab)


@dataclass(frozen=True)
class AnalysisWarning:
    area: AnalysisArea
    message: str
