"""
TemporaryWorkspace implementation backed by a system temp directory.
"""

import tempfile

from apkviewer.domain.interfaces.temporary_workspace import TemporaryWorkspace


class TempDirectoryWorkspace(TemporaryWorkspace):
    def __init__(self, prefix: str = "apkviewer_") -> None:
        self._prefix: str = prefix
        self._directory: tempfile.TemporaryDirectory[str] = self._create_directory()

    @property
    def path(self) -> str:
        return self._directory.name

    def reset(self) -> None:
        self._directory.cleanup()
        self._directory = self._create_directory()

    def dispose(self) -> None:
        self._directory.cleanup()

    def _create_directory(self) -> "tempfile.TemporaryDirectory[str]":
        # ignore_cleanup_errors: on Windows a file still opened by an
        # external app cannot be deleted, which must not break the app.
        return tempfile.TemporaryDirectory(prefix=self._prefix, ignore_cleanup_errors=True)
