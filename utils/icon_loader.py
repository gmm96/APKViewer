"""
Service responsible for loading, tinting, resizing, and padding icons.

Extracted to prevent duplication across UI components that need themed icons.
Follows the Single Responsibility Principle by decoupling image processing
logic from UI layout widgets.
"""

from typing import Optional, Tuple
from PIL import Image, ImageTk

from utils.ui_helpers import AssetPathResolver


class IconLoader:
    """Loads and processes UI icons dynamically."""

    def __init__(self, asset_path_resolver: Optional[AssetPathResolver] = None):
        self._asset_path_resolver = asset_path_resolver or AssetPathResolver()

    def load_icon(
        self,
        relative_path: str,
        size: Tuple[int, int] = (16, 16),
        hex_color: Optional[str] = None,
        padding_left: int = 0,
        padding_right: int = 0,
    ) -> ImageTk.PhotoImage:
        """
        Loads an icon from the given path, tints it to the specified hex color,
        resizes it, and optionally adds transparent horizontal padding.
        """
        path = self._asset_path_resolver.resolve(relative_path)
        img = Image.open(path).convert("RGBA")

        # Extract alpha mask and create a new solid-color image
        if hex_color:
            alpha_mask = img.getchannel("A")
            colored_img = Image.new("RGBA", img.size, color=hex_color)
            colored_img.putalpha(alpha_mask)
            img = colored_img
        
        # Resize using high-quality resampling
        img = img.resize(size, Image.Resampling.LANCZOS)

        # Apply transparent padding if requested via a transparent canvas
        if padding_left > 0 or padding_right > 0:
            canvas_width = padding_left + size[0] + padding_right
            canvas = Image.new("RGBA", (canvas_width, size[1]), (0, 0, 0, 0))
            canvas.paste(img, (padding_left, 0))
            img = canvas

        return ImageTk.PhotoImage(img)
