"""
Builds the neutral placeholder image shown before an APK icon is loaded.
"""

from PIL import Image, ImageDraw, ImageTk

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.config.layout import ICON_SIZE


class PlaceholderIconFactory:
    def __init__(self, size: tuple[int, int] = ICON_SIZE) -> None:
        self._size: tuple[int, int] = size

    def create(self, palette: ThemePalette) -> ImageTk.PhotoImage:
        img = Image.new("RGB", self._size, color=palette.placeholder_bg)
        draw = ImageDraw.Draw(img)
        draw.rectangle(
            [0, 0, self._size[0] - 1, self._size[1] - 1],
            outline=palette.placeholder_border,
            width=2,
        )
        return ImageTk.PhotoImage(img)
