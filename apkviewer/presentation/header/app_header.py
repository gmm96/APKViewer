"""
Top header: app icon, name/package labels and the "Load APK" button.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional
from collections.abc import Callable

from PIL import ImageTk

from apkviewer.config.theme import FONT_SUBTITLE, FONT_TITLE
from apkviewer.presentation.icons.placeholder_icon_factory import PlaceholderIconFactory


class AppHeader(ttk.Frame):
    def __init__(
            self,
            parent: ttk.Frame,
            on_load_click: Callable[[], None],
            icon_factory: Optional[PlaceholderIconFactory] = None
        ) -> None:
        super().__init__(parent)
        self._icon_factory: PlaceholderIconFactory = icon_factory or PlaceholderIconFactory()
        self._placeholder_icon: ImageTk.PhotoImage = self._icon_factory.create()
        self._current_icon: Optional[ImageTk.PhotoImage] = None

        left = ttk.Frame(self)
        left.pack(side=tk.LEFT, fill=tk.Y)

        self.icon_label: ttk.Label = ttk.Label(left, image=self._placeholder_icon)
        self.icon_label.pack(side=tk.LEFT, padx=(0, 15))

        text_frame = ttk.Frame(left)
        text_frame.pack(side=tk.LEFT, expand=True, fill=tk.Y)

        self.name_label: ttk.Label = ttk.Label(text_frame, text="No APK Loaded", font=FONT_TITLE)
        self.name_label.pack(side=tk.TOP, anchor="sw", expand=True)

        self.package_label: ttk.Label = ttk.Label(
            text_frame,
            text="Select an application file to begin analysis.",
            font=FONT_SUBTITLE,
            foreground="#666666",
        )
        self.package_label.pack(side=tk.TOP, anchor="nw", expand=True)

        self.load_button: ttk.Button = ttk.Button(self, text="Load APK", command=on_load_click)
        self.load_button.pack(side=tk.RIGHT)

    def reset_to_placeholder(self, file_name: str) -> None:
        self._current_icon = None
        self.icon_label.config(image=self._placeholder_icon)
        self.name_label.config(text="Analyzing APK...")
        self.package_label.config(text=file_name)

    def show_error(self) -> None:
        self.name_label.config(text="Error loading APK")

    def set_loading_enabled(self, enabled: bool) -> None:
        self.load_button.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def show_result(self, app_name: str, package_name: str, icon_image=None) -> None:
        if icon_image is not None:
            self._current_icon = ImageTk.PhotoImage(icon_image)
            self.icon_label.config(image=self._current_icon)

        self.name_label.config(text=app_name or "Unknown App")
        self.package_label.config(text=package_name or "Unknown Package")
