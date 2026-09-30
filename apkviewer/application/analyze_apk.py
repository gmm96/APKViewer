"""
Use case: analyze an APK and return everything a front end needs to show it.
"""

from apkviewer.application.file_tree_builder import FileTreeBuilder
from apkviewer.domain.entities.analysis_result import AnalysisResult
from apkviewer.domain.interfaces.apk_inspector import ApkInspector
from apkviewer.domain.interfaces.archive_reader import ArchiveReader


class AnalyzeApk:
    def __init__(
        self,
        inspector: ApkInspector,
        archive_reader: ArchiveReader,
        tree_builder: FileTreeBuilder | None = None,
    ) -> None:
        self._inspector: ApkInspector = inspector
        self._archive_reader: ArchiveReader = archive_reader
        self._tree_builder: FileTreeBuilder = tree_builder or FileTreeBuilder()

    def execute(self, apk_path: str) -> AnalysisResult:
        inspection = self._inspector.inspect(apk_path)
        file_tree = self._tree_builder.build(self._archive_reader.list_entries(apk_path))
        return AnalysisResult(
            apk_path=apk_path,
            package_name=inspection.package_name,
            app_name=inspection.app_name,
            icon_png=inspection.icon_png,
            sections=inspection.sections,
            manifest_xml=inspection.manifest_xml,
            file_tree=file_tree,
        )
