"""
Tinted icons shown inside text fields: copy, copied (feedback after a copy)
and clear (an X, drawn in code so it needs no asset file). Also owns the
ttk style that reserves room at the right end of those fields so long
text never runs under an icon.
"""

from tkinter import ttk

from PIL import Image, ImageDraw, ImageTk

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.icons.icon_loader import IconLoader

COPY_ICON_PATH: str = "assets/icons/outline/copy_content.png"
ICON_SIZE: tuple[int, int] = (16, 16)
ENTRY_STYLE: str = "IconEntry.TEntry"
ENTRY_ICON_AREA: int = 30  # pixels kept free at the right end of the field's text area


class FieldIcons:
    def __init__(self, icon_loader: IconLoader, palette: ThemePalette) -> None:
        self._icon_loader: IconLoader = icon_loader
        self.copy: ImageTk.PhotoImage
        self.copied: ImageTk.PhotoImage
        self.clear: ImageTk.PhotoImage
        self.apply_palette(palette)

    def apply_palette(self, palette: ThemePalette) -> None:
        self.copy = self._icon_loader.load_icon(
            COPY_ICON_PATH, size=ICON_SIZE, hex_color=palette.secondary_fg
        )
        self.copied = self._icon_loader.load_icon(
            COPY_ICON_PATH, size=ICON_SIZE, hex_color=palette.status_success
        )
        self.clear = self._draw_clear(palette.secondary_fg)
        self.configure_entry_style()

    @staticmethod
    def configure_entry_style() -> None:
        # ttk keeps style settings per theme, so this is repeated on every theme change.
        ttk.Style().configure(ENTRY_STYLE, padding=(1, 1, ENTRY_ICON_AREA, 1))

    @staticmethod
    def _draw_clear(color: str, size: int = 14) -> ImageTk.PhotoImage:
        scale = 4  # drawn large and scaled down for smooth lines
        side = size * scale
        image = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        margin, width = 3 * scale, round(1.6 * scale)
        draw.line([(margin, margin), (side - margin, side - margin)], fill=color, width=width)
        draw.line([(margin, side - margin), (side - margin, margin)], fill=color, width=width)
        return ImageTk.PhotoImage(image.resize((size, size), Image.Resampling.LANCZOS))
