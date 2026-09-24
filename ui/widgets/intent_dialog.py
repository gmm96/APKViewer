"""
Popup dialog showing the parsed details of a single intent-filter action.
"""
import tkinter as tk
from tkinter import messagebox, ttk

from config import FONT_MONO
from ui.widgets.modal_dialog_support import ModalDialogPositioner


class IntentActionParser:
    """Turns a formatted "action ( key='value', ... )" line back into a dict."""

    def parse(self, line_text: str) -> dict:
        action = line_text
        extras_str = ""

        if " ( " in action and action.endswith(" )"):
            action, extras_str = action.split(" ( ", 1)
            extras_str = extras_str[:-2]

        fields = {"Action": action}

        if extras_str:
            for extra in extras_str.split(", "):
                if "=" not in extra:
                    continue
                key, value = extra.split("=", 1)
                key = key.strip().capitalize()
                value = value.strip().strip("'").strip('"')

                if key in fields:
                    fields[key] += f", {value}"
                else:
                    fields[key] = value

        return fields


class IntentDetailsDialog:
    """Builds and shows the modal 'Intent Details' popup on demand."""

    def __init__(
        self,
        parent: tk.Misc,
        parser: IntentActionParser = None,
        positioner: ModalDialogPositioner = None,
    ):
        self._parent = parent
        self._parser = parser or IntentActionParser()
        self._positioner = positioner or ModalDialogPositioner()

    def open(self, line_text: str) -> None:
        try:
            fields = self._parser.parse(line_text)
            dialog = self._build_dialog(fields)
            self._positioner.center_on_parent(dialog, self._parent)
            self._positioner.show_as_modal(dialog)
        except Exception as exc:
            messagebox.showerror("Parse Error", f"Could not load intent details:\n{exc}")

    def _build_dialog(self, fields: dict) -> tk.Toplevel:
        dialog = tk.Toplevel(self._parent)
        dialog.title("Intent Details")
        dialog.minsize(550, 150)
        dialog.transient(self._parent)

        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        row_idx = 0
        for label_text, value_text in fields.items():
            ttk.Label(main_frame, text=label_text, width=15).grid(row=row_idx, column=0, sticky="w", pady=5)

            entry = ttk.Entry(main_frame, font=FONT_MONO)
            entry.insert(0, str(value_text))
            entry.configure(state="readonly")
            entry.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=(10, 0))

            main_frame.columnconfigure(1, weight=1)
            row_idx += 1

        ttk.Button(main_frame, text="Close", command=dialog.destroy).grid(
            row=row_idx, column=0, columnspan=2, pady=(20, 0)
        )
        return dialog
