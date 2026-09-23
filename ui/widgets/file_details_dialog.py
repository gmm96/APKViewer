"""
Popup dialog showing the parsed details of selected file(s) or folder(s).
"""
import tkinter as tk
from tkinter import ttk


class FileDetailsDialog:
    """Builds and shows the modal 'Details' popup for files/folders."""

    def __init__(self, parent: tk.Misc):
        self._parent = parent

    def show(self, items_data: list) -> None:
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
            self._build_multi_item(main_frame, items_data)

        ttk.Button(main_frame, text="Close", command=dialog.destroy).grid(
            row=10, column=0, columnspan=2, pady=(20, 0)
        )
        
        self._center_on_parent(dialog)
        self._focus(dialog)

    def _build_single_item(self, parent: ttk.Frame, item: dict) -> None:
        fields = {
            "Name:": item.get("name", ""),
            "Type:": item.get("type", ""),
            "Size:": item.get("size", ""),
            "Compressed:": item.get("compressed", ""),
            "Modified:": item.get("modified", ""),
        }
        self._render_grid(parent, fields)

    def _build_multi_item(self, parent: ttk.Frame, items: list) -> None:
        fields = {
            "Items Selected:": str(len(items)),
            "Notice:": "Multiple selections shown.\nDetailed metrics are available\nby inspecting items individually.",
        }
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

    def _center_on_parent(self, dialog: tk.Toplevel) -> None:
        dialog.update_idletasks()
        x = self._parent.winfo_x() + (self._parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self._parent.winfo_y() + (self._parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    @staticmethod
    def _focus(dialog: tk.Toplevel) -> None:
        dialog.deiconify()
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.after(150, lambda: dialog.attributes("-topmost", False))
        dialog.focus_force()
        dialog.grab_set()
