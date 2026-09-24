"""
Shared behaviour for the app's Toplevel popup dialogs: centering on the
parent window, and forcing focus so a Toplevel actually behaves like a
modal dialog.

Both `FileDetailsDialog` and `IntentDetailsDialog` needed exactly this
logic, byte-for-byte identical - it now lives here once instead of being
copy-pasted into every dialog class.
"""
import tkinter as tk


class ModalDialogPositioner:
    @staticmethod
    def center_on_parent(dialog: tk.Toplevel, parent: tk.Misc) -> None:
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    @staticmethod
    def show_as_modal(dialog: tk.Toplevel) -> None:
        dialog.deiconify()
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.after(150, lambda: dialog.attributes("-topmost", False))
        dialog.focus_force()
        dialog.grab_set()
