"""
Bottom status bar showing the current operation state.
"""

import tkinter as tk
from tkinter import ttk


class StatusBar(ttk.Frame):
    def __init__(self, parent: tk.Tk) -> None:
        super().__init__(parent, relief="sunken", borderwidth=1)
        self.label: ttk.Label = ttk.Label(self, text="Ready.", foreground="gray")
        self.label.pack(side="left", padx=10, pady=2)

    def set_status(self, message: str, color: str = "gray") -> None:
        self.label.config(text=message, foreground=color)
