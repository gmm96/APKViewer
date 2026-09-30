"""
Use case: save the analysis sections as a plain text report.
"""

from apkviewer.application.app_info_serializer import AppInfoSerializer
from apkviewer.domain.entities.analysis_result import AnalysisResult
from apkviewer.domain.interfaces.file_writer import FileWriter


class ExportAppInfo:
    def __init__(self, writer: FileWriter, serializer: AppInfoSerializer | None = None) -> None:
        self._writer: FileWriter = writer
        self._serializer: AppInfoSerializer = serializer or AppInfoSerializer()

    def execute(self, result: AnalysisResult, dest_path: str) -> None:
        self._writer.write_text(dest_path, self._serializer.format(result.sections))
