"""
Semantic importance of a status-bar message; the palette decides its color.
"""

from enum import Enum


class StatusLevel(Enum):
    NEUTRAL = "neutral"
    INFO = "info"
    SUCCESS = "success"
    ERROR = "error"
