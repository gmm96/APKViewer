"""
Use case: save the launcher icon of an analyzed APK as a PNG file.
"""

from apkviewer.domain.entities.analysis_result import AnalysisResult
from apkviewer.domain.interfaces.file_writer import FileWriter


class ExportIcon:
    def __init__(self, writer: FileWriter) -> None:
        self._writer: FileWriter = writer

    def execute(self, result: AnalysisResult, dest_path: str) -> None:
        if result.icon_png is None:
            raise ValueError("The analyzed APK has no raster icon to export.")
        self._writer.write_bytes(dest_path, result.icon_png)
