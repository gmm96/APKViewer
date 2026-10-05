"""
Everything a front end needs after analyzing one APK. It only holds plain
data (no third-party types), so any presentation layer can consume it.
"""

from dataclasses import dataclass

from apkviewer.domain.entities.analysis_warning import AnalysisArea
from apkviewer.domain.entities.apk_inspection import ApkInspection
from apkviewer.domain.entities.file_node import FileNode


@dataclass(frozen=True)
class AnalysisResult:
    apk_path: str
    inspection: ApkInspection
    file_tree: FileNode

    @property
    def app_name(self) -> str:
        return self.inspection.application.app_name

    @property
    def package_name(self) -> str:
        return self.inspection.application.package_name

    @property
    def icon_png(self) -> bytes | None:
        return self.inspection.icon_png

    @property
    def manifest_xml(self) -> str:
        return self.inspection.manifest_xml

    def warning_messages(self, *areas: AnalysisArea) -> list[str]:
        """The messages of the warnings that affect any of those areas."""
        return [w.message for w in self.inspection.warnings if w.area in areas]

    @property
    def default_name(self) -> str:
        """Name suggested for exported files/folders ("app" when the APK declares no package)."""
        return self.package_name or "app"
