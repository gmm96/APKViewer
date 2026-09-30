"""
What an ApkInspector learns by looking inside an APK: everything except
the archive's file tree, which is obtained through a separate port.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApkInspection:
    package_name: str
    app_name: str
    icon_png: bytes | None
    sections: dict[str, dict[str, Any]]
    manifest_xml: str
