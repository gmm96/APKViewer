"""
A vertically scrollable Tkinter frame with mouse-wheel support (Windows,
macOS and Linux/X11-style Button-4/5 wheel events).

Scrolling is only possible while the content is taller than the visible
area; otherwise the scrollbar is hidden and the wheel does nothing.

Several instances can live in the same window (one per tab): the wheel
only scrolls the frame that is under the pointer.
"""

import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    def __init__(self, container: ttk.Frame, *args, **kwargs) -> None:
        super().__init__(container, *args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.canvas: tk.Canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self._scrollbar: ttk.Scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.inner_frame: ttk.Frame = ttk.Frame(self.canvas)
        self.canvas_window: int = self.canvas.create_window(
            (0, 0),
            window=self.inner_frame,
            anchor="nw"
        )

        self.inner_frame.bind("<Configure>", self._update_scrollregion)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self._on_yscroll)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self._scrollbar.grid(row=0, column=1, sticky="ns")

        # add="+": bind_all is application-wide, so every instance must
        # append its handler instead of replacing the previous one.
        self.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.bind_all("<Button-4>", self._on_mousewheel, add="+")
        self.bind_all("<Button-5>", self._on_mousewheel, add="+")

    # --- Layout ----------------------------------------------------------------

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self._update_scrollregion()

    def _update_scrollregion(self, _event: tk.Event | None = None) -> None:
        # The region is never smaller than the viewport: Tk would otherwise
        # let a short content be dragged around inside a taller canvas.
        height = max(self.inner_frame.winfo_reqheight(), self.canvas.winfo_height())
        self.canvas.configure(scrollregion=(0, 0, self.canvas.winfo_width(), height))
        if self._content_fits():
            self.canvas.yview_moveto(0)

    def _content_fits(self) -> bool:
        return self.inner_frame.winfo_reqheight() <= self.canvas.winfo_height()

    def _on_yscroll(self, first: str, last: str) -> None:
        if float(first) <= 0.0 and float(last) >= 1.0:
            self._scrollbar.grid_remove()
        else:
            self._scrollbar.grid()
        self._scrollbar.set(first, last)

    # --- Mouse wheel -----------------------------------------------------------

    def _on_mousewheel(self, event: tk.Event) -> None:
        if self._content_fits() or not self._pointer_is_inside(event):
            return
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    def _pointer_is_inside(self, event: tk.Event) -> bool:
        if not self.winfo_ismapped():
            return False
        try:
            widget = self.winfo_containing(event.x_root, event.y_root)
        except KeyError:  # internal Tk windows (e.g. popup menus) have no Python wrapper
            return False
        while widget is not None:
            if widget is self:
                return True
            widget = widget.master
        return False
