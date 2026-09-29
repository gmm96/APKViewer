"""
Actions behind the Help menu: project links and the About dialog.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional

from apkviewer.config.about import ISSUES_URL, REPOSITORY_URL
from apkviewer.domain.interfaces.url_opener import UrlOpener
from .about_dialog import AboutDialog


class HelpMenu:
    def __init__(
        self,
        parent: tk.Misc,
        url_opener: UrlOpener,
        about_dialog: Optional[AboutDialog] = None,
        repository_url: str = REPOSITORY_URL,
        issues_url: str = ISSUES_URL,
    ) -> None:
        self._parent: tk.Misc = parent
        self._url_opener: UrlOpener = url_opener
        self._about_dialog: AboutDialog = about_dialog or AboutDialog(parent)
        self._repository_url: str = repository_url
        self._issues_url: str = issues_url

    def open_source_code(self) -> None:
        self._open_url(self._repository_url)

    def report_issue(self) -> None:
        self._open_url(self._issues_url)

    def show_about(self) -> None:
        self._about_dialog.show()

    def _open_url(self, url: str) -> None:
        try:
            self._url_opener.open(url)
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self._parent)
