"""
Right-click "Copy" context menu shared by every read-only Text widget in
the app (manifest viewer, list fields, etc.). Also makes Ctrl+C behave
consistently with it, since these widgets are read-only (state="disabled")
and don't reliably get Tk's default copy binding.
"""
import tkinter as tk

from config import MARKED_LINE_TAG


class TextContextMenu:
    """
    Attach to any Text widget with `attach(widget)`. Right-click (or
    Ctrl+C) will copy the current selection, or the currently marked line
    if nothing is selected.
    """

    def __init__(self, root: tk.Misc):
        self._menu = tk.Menu(root, tearoff=0)
        self._menu.add_command(label="Copy Text", command=self._copy_from_active)
        self._active_widget = None

    def attach(self, widget: tk.Text):
        widget.bind("<Button-3>", self._show)
        widget.bind("<Control-c>", self._on_ctrl_c)

    def _show(self, event):
        self._active_widget = event.widget
        self._menu.tk_popup(event.x_root, event.y_root)

    def _on_ctrl_c(self, event):
        self._copy_from(event.widget)
        return "break"

    def _copy_from_active(self):
        if self._active_widget is not None:
            self._copy_from(self._active_widget)

    def _copy_from(self, widget: tk.Text):
        try:
            if widget.tag_ranges(tk.SEL):
                text_to_copy = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            else:
                marked = widget.tag_ranges(MARKED_LINE_TAG)
                text_to_copy = widget.get(marked[0], marked[1]) if marked else ""

            text_to_copy = self._strip_trailing_padding(text_to_copy)

            if text_to_copy:
                widget.clipboard_clear()
                widget.clipboard_append(text_to_copy)
        except Exception:
            pass

    @staticmethod
    def _strip_trailing_padding(text: str) -> str:
        """
        Drop trailing spaces from each copied line. ManifestPanel pads
        every line to a uniform width (to keep its horizontal scrollbar
        stable - see ManifestPanel._pad_lines_to_equal_width); this makes
        sure that invisible padding never ends up on the clipboard.
        """
        return "\n".join(line.rstrip(" ") for line in text.split("\n"))
