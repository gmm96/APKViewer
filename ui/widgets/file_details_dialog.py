"""
Popup dialog showing the parsed details of selected file(s) or folder(s).
"""
import tkinter as tk
from tkinter import ttk

from ui.widgets.modal_dialog_support import ModalDialogPositioner


class FileDetailsDialog:
    """Builds and shows the modal 'Details' popup for files/folders."""

    def __init__(self, parent: tk.Misc, positioner: ModalDialogPositioner = None):
        self._parent = parent
        self._positioner = positioner or ModalDialogPositioner()

    def show(self, items_data: list, summary: dict = None) -> None:
        if not items_data:
            return

        dialog = tk.Toplevel(self._parent)
        dialog.title("Item Details" if len(items_data) == 1 else "Multiple Items Details")
        dialog.minsize(350, 180)
        dialog.transient(self._parent)

        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        if len(items_data) == 1:
            self._build_single_item(main_frame, items_data[0])
        else:
            self._build_multi_item(main_frame, items_data, summary)

        ttk.Button(main_frame, text="Close", command=dialog.destroy).grid(
            row=10, column=0, columnspan=2, pady=(20, 0)
        )

        self._positioner.center_on_parent(dialog, self._parent)
        self._positioner.show_as_modal(dialog)

    def _build_single_item(self, parent: ttk.Frame, item: dict) -> None:
        fields = {
            "Name:": item.get("name", ""),
            "Type:": item.get("type", ""),
            "Size:": item.get("size", ""),
            "Compressed:": item.get("compressed", ""),
            "Modified:": item.get("modified", ""),
        }
        self._render_grid(parent, fields)

    def _build_multi_item(self, parent: ttk.Frame, items: list, summary: dict = None) -> None:
        fields = {"Items Selected:": str(len(items))}

        if summary:
            # Real totals, computed from the raw byte counts - not the
            # already-formatted per-row strings, which can't be summed
            # directly (e.g. "1.5 KB" + "900 B").
            fields["Files:"] = str(summary.get("file_count", 0))
            fields["Folders:"] = str(summary.get("folder_count", 0))
            fields["Total size:"] = summary.get("total_size", "-")
            fields["Total compressed:"] = summary.get("total_compressed", "-")
        else:
            fields["Notice:"] = (
                "Multiple selections shown.\nDetailed metrics are available\n"
                "by inspecting items individually."
            )

        self._render_grid(parent, fields)

    @staticmethod
    def _render_grid(parent: ttk.Frame, fields: dict) -> None:
        row_idx = 0
        for label_text, value_text in fields.items():
            ttk.Label(parent, text=label_text, width=15, font=("", 0, "bold")).grid(
                row=row_idx, column=0, sticky="nw", pady=5
            )
            ttk.Label(parent, text=str(value_text), wraplength=250).grid(
                row=row_idx, column=1, sticky="w", pady=5, padx=(10, 0)
            )
            row_idx += 1
        parent.columnconfigure(1, weight=1)
