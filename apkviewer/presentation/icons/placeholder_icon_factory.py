"""
Builds the neutral placeholder image shown before an APK icon is loaded.
"""

from PIL import Image, ImageDraw, ImageTk

from apkviewer.config import COLOR_PLACEHOLDER_BG, COLOR_PLACEHOLDER_BORDER, ICON_SIZE


class PlaceholderIconFactory:
    def __init__(
            self,
            size: tuple[int, int] = ICON_SIZE,
            bg_color: str = COLOR_PLACEHOLDER_BG,
            border_color: str = COLOR_PLACEHOLDER_BORDER
        ) -> None:
        self._size: tuple[int, int] = size
        self._bg_color: str = bg_color
        self._border_color: str = border_color

    def create(self) -> ImageTk.PhotoImage:
        img = Image.new("RGB", self._size, color=self._bg_color)
        draw = ImageDraw.Draw(img)
        draw.rectangle(
            [0, 0, self._size[0] - 1, self._size[1] - 1],
            outline=self._border_color,
            width=2,
        )
        return ImageTk.PhotoImage(img)
