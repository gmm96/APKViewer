"""
Extracts the core application identity, SDK versions, and physical file metrics.
"""

import os
from datetime import datetime
from typing import Any

from androguard.core.apk import APK
from apkviewer.infrastructure.androguard.analysis_section_extractor import AnalysisSectionExtractor


class ApplicationInfoExtractor(AnalysisSectionExtractor):
    def __init__(self) -> None:
        pass

    def extract(self, apk: APK) -> dict[str, Any]:
        path = apk.get_filename()
        info: dict[str, Any] = {
            "App Name": apk.get_app_name(),
            "Package Name": apk.get_package(),
            "Version Name": apk.get_androidversion_name(),
            "Version Code": apk.get_androidversion_code(),
            "Min SDK": apk.get_min_sdk_version(),
            "Target SDK": apk.get_target_sdk_version(),
        }
        max_sdk = apk.get_max_sdk_version()
        if max_sdk:
            info["Max SDK"] = max_sdk
        info["File Name"] = os.path.basename(path) if path else "Unknown"
        info["File Path"] = os.path.realpath(path) if path else "Unknown"
        info["File Size"] = self._get_file_size(path)
        info["Last Modified"] = self._get_last_modified_date(path)
        return info

    def _get_file_size(self, path: str | None) -> int:
        if not path or not os.path.exists(path):
            return -1
        try:
            return os.path.getsize(path)
        except OSError:
            return -1

    @staticmethod
    def _get_last_modified_date(path: str | None) -> datetime:
        if not path or not os.path.exists(path):
            return datetime.min
        try:
            return datetime.fromtimestamp(os.path.getmtime(path))
        except OSError:
            return datetime.min
