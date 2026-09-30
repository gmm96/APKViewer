"""
Use case: extract selected entries (or the whole APK) into a folder.
"""

from collections.abc import Sequence

from apkviewer.domain.interfaces.apk_extractor import ApkExtractor


class ExtractApkEntries:
    def __init__(self, extractor: ApkExtractor) -> None:
        self._extractor: ApkExtractor = extractor

    def execute(self, apk_path: str, dest_dir: str, entry_paths: Sequence[str] | None = None) -> list[str]:
        """Extract `entry_paths` (or the whole APK when None) into `dest_dir`."""
        if entry_paths is None:
            return self._extractor.extract_all(apk_path, dest_dir)
        return self._extractor.extract(apk_path, entry_paths, dest_dir)
