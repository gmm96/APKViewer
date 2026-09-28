"""
Facade for the application's configuration constants, so the rest of the
codebase can simply do ``from apkviewer.config import X`` without caring
which file a given constant actually lives in.
"""

from .about import ISSUES_URL, PROJECT_DESCRIPTION, PROJECT_NAME, REPOSITORY_URL
from .android import ANDROID_NS, DPI_SCORES
from .layout import ICON_SIZE, LABEL_WIDTH, MARKED_LINE_TAG, MIN_LIST_LINES
from .theme import (
    COLOR_FOLDER_BG,
    COLOR_MARK_BG,
    COLOR_PLACEHOLDER_BG,
    COLOR_PLACEHOLDER_BORDER,
    COLOR_TEXT_BG,
    COLOR_XML_ATTR,
    COLOR_XML_COMMENT,
    COLOR_XML_TAG,
    COLOR_XML_VALUE,
    FONT_MONO,
    FONT_MONO_SMALL,
    FONT_MONO_SMALL_ITALIC,
    FONT_SUBTITLE,
    FONT_TITLE
)
from .trackers import KNOWN_TRACKERS

__all__ = [
    "ICON_SIZE",
    "MIN_LIST_LINES",
    "LABEL_WIDTH",
    "MARKED_LINE_TAG",
    "FONT_TITLE",
    "FONT_SUBTITLE",
    "FONT_MONO",
    "FONT_MONO_SMALL",
    "FONT_MONO_SMALL_ITALIC",
    "COLOR_PLACEHOLDER_BG",
    "COLOR_PLACEHOLDER_BORDER",
    "COLOR_TEXT_BG",
    "COLOR_MARK_BG",
    "COLOR_FOLDER_BG",
    "COLOR_XML_TAG",
    "COLOR_XML_ATTR",
    "COLOR_XML_VALUE",
    "COLOR_XML_COMMENT",
    "ANDROID_NS",
    "DPI_SCORES",
    "KNOWN_TRACKERS",
    "PROJECT_NAME",
    "PROJECT_DESCRIPTION",
    "REPOSITORY_URL",
    "ISSUES_URL",
]
