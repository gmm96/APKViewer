"""
Extracts the core application identity, SDK versions, and physical file metrics.
"""

import os
from datetime import datetime

from androguard.core.apk import APK

from apkviewer.domain.entities.application_info import ApplicationInfo


class ApplicationInfoExtractor:
    def extract(self, apk: APK) -> ApplicationInfo:
        path = apk.get_filename()
        return ApplicationInfo(
            app_name=apk.get_app_name() or "",
            package_name=apk.get_package() or "",
            version_name=apk.get_androidversion_name(),
            version_code=apk.get_androidversion_code(),
            min_sdk=apk.get_min_sdk_version(),
            target_sdk=apk.get_target_sdk_version(),
            max_sdk=apk.get_max_sdk_version() or None,
            file_name=os.path.basename(path) if path else None,
            file_path=os.path.realpath(path) if path else None,
            file_size=self._file_size(path),
            last_modified=self._last_modified(path),
        )

    @staticmethod
    def _file_size(path: str | None) -> int | None:
        if not path:
            return None
        try:
            return os.path.getsize(path)
        except OSError:
            return None

    @staticmethod
    def _last_modified(path: str | None) -> datetime | None:
        if not path:
            return None
        try:
            return datetime.fromtimestamp(os.path.getmtime(path))
        except OSError:
            return None
