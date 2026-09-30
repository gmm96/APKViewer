"""
Everything a front end needs after analyzing one APK. It only holds plain
data (no third-party types), so any presentation layer can consume it.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from apkviewer.domain.entities.file_node import FileNode


@dataclass(frozen=True)
class AnalysisResult:
    apk_path: str
    package_name: str
    app_name: str
    icon_png: bytes | None
    sections: Mapping[str, Mapping[str, Any]]
    manifest_xml: str
    file_tree: FileNode

    @property
    def default_name(self) -> str:
        """Name suggested for exported files/folders ("app" when the APK declares no package)."""
        return self.package_name or "app"
