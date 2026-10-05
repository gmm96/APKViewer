"""
Resolves the best-available launcher icon of an APK and returns it as
PNG bytes, so nothing outside this layer needs an imaging library to
handle it.

The icon is found by following the manifest's icon reference through the
resource table (which works even when the file names are obfuscated, e.g.
`res/tG.png`). When the icon is an adaptive icon without a raster version,
its layers are composed if they are images or colors. Vector layers can't
be rendered, and the reason is reported. Looking for a file called
`ic_launcher` is only the last fallback.
"""

import io
import os
from typing import Any

from androguard.core.apk import APK
from androguard.core.axml import AXMLPrinter
from PIL import Image

from apkviewer.domain.entities.analysis_warning import AnalysisArea
from apkviewer.infrastructure.androguard.analysis_warnings import AnalysisWarningCollector
from apkviewer.infrastructure.androguard.config.android import ANDROID_NS, DPI_SCORES

_RASTER: tuple[str, ...] = (".png", ".webp", ".jpg", ".jpeg")
# Densities from this value up are "anydpi"/"nodpi": not a real screen density.
_NON_DENSITY: int = 0xFFFE
# An adaptive icon is drawn on a 108dp canvas of which launchers show the central 72dp.
_ADAPTIVE_CANVAS: int = 108
_ADAPTIVE_VISIBLE: int = 72

Layer = Image.Image | tuple[int, int, int, int] | None  # an image, a solid RGBA color, or absent


class _UnrenderableLayer(Exception):
    """A layer of an adaptive icon that is not an image or a color (e.g. a vector drawable)."""


class IconExtractor:
    """Finds the highest-resolution launcher icon declared by an APK."""

    _PNG_SAFE_MODES: tuple[str, ...] = ("RGB", "RGBA", "L", "LA", "P")

    def __init__(self, dpi_scores: dict[str, int] | None = None) -> None:
        self._dpi_scores: dict[str, int] = dpi_scores or DPI_SCORES

    def extract(self, apk: APK, warnings: AnalysisWarningCollector | None = None) -> bytes | None:
        """Return the icon (original resolution) encoded as PNG, or None if unavailable."""
        try:
            image, reason = self._find_icon(apk)
        except Exception as exc:  # pylint: disable=broad-except
            image, reason = None, f"The launcher icon could not be read ({type(exc).__name__})."
        if image is None:
            if warnings is not None and reason:
                warnings.add(reason, AnalysisArea.ICON)
            return None
        return self._encode_png(image)

    def resolve_candidates(self, apk: APK) -> list[str]:
        """Raster files the manifest's icon resolves to, best (highest density) first."""
        return [value for _, value in self._resolved_values(apk) if value.lower().endswith(_RASTER)]

    # --- Resolution ---------------------------------------------------------------

    def _find_icon(self, apk: APK) -> tuple[Image.Image | None, str | None]:
        """(image, None) when found; (None, why not) otherwise."""
        for path in self.resolve_candidates(apk):
            image = self._try_load(apk, path)
            if image is not None:
                return image, None

        adaptive, reason = self._compose_adaptive(apk)
        if adaptive is not None:
            return adaptive, None

        image = self._find_best_icon_by_name(apk, self._resolve_icon_base_name(apk))
        if image is not None:
            return image, None
        if reason:
            return None, reason
        if not self._icon_reference(apk):
            return None, "The manifest declares no launcher icon."
        return None, "The launcher icon could not be found or decoded."

    @staticmethod
    def _icon_reference(apk: APK) -> str | None:
        """The icon the launcher shows: the main activity's, else the application's."""
        try:
            main_activity = apk.get_main_activity()
            reference = None
            if main_activity:
                reference = apk.get_attribute_value("activity", "icon", name=main_activity)
            return reference or apk.get_attribute_value("application", "icon")
        except Exception:
            return None

    def _resolved_values(self, apk: APK) -> list[tuple[int, str]]:
        """What the icon reference resolves to: (density rank, file path or value), best first."""
        reference = self._icon_reference(apk)
        if not reference:
            return []
        if not reference.startswith("@"):
            return [(0, reference)]  # already a file path
        return self._resolve_reference(apk, reference)

    def _resolve_reference(self, apk: APK, reference: str) -> list[tuple[int, str]]:
        try:
            resources = apk.get_android_resources()
            if not resources:
                return []
            res_id = int(reference[1:].split(":")[-1], 16)
            resolved = resources.get_resolved_res_configs(res_id)
        except Exception:
            return []
        values = [(self._density_rank(config), value) for config, value in resolved if isinstance(value, str)]
        return sorted(values, key=lambda item: item[0], reverse=True)  # stable for equal densities

    @staticmethod
    def _density_rank(config: Any) -> int:
        try:
            density = int(config.get_density())
        except Exception:
            return 0
        return -1 if density >= _NON_DENSITY else density

    @staticmethod
    def _try_load(apk: APK, path: str) -> Image.Image | None:
        try:
            data = apk.get_file(path)
            return IconExtractor._load(data) if data else None
        except Exception:
            return None

    # --- Adaptive icons -----------------------------------------------------------------

    def _compose_adaptive(self, apk: APK) -> tuple[Image.Image | None, str | None]:
        reason = None
        for _, path in self._resolved_values(apk):
            if not path.lower().endswith(".xml"):
                continue
            try:
                root = AXMLPrinter(apk.get_file(path)).get_xml_obj()
            except Exception:
                continue
            if root is None or root.tag != "adaptive-icon":
                continue
            try:
                background = self._load_layer(apk, root, "background")
                foreground = self._load_layer(apk, root, "foreground")
            except _UnrenderableLayer:
                reason = (
                    "The launcher icon is an adaptive icon made of vector drawables, "
                    "which can't be rendered."
                )
                continue
            image = self._compose(background, foreground)
            if image is not None:
                return image, None
        return None, reason

    def _load_layer(self, apk: APK, root: Any, name: str) -> Layer:
        node = root.find(name)
        if node is None:
            return None
        reference = node.get(f"{ANDROID_NS}drawable")
        if not reference and len(node):  # e.g. <foreground><inset android:drawable=.../></foreground>
            reference = node[0].get(f"{ANDROID_NS}drawable")
        if not reference:
            return None
        if reference.startswith("#"):
            color = self._parse_color(reference)
            if color is None:
                raise _UnrenderableLayer(reference)
            return color

        for _, value in self._resolve_reference(apk, reference):
            if value.lower().endswith(_RASTER):
                image = self._try_load(apk, value)
                if image is not None:
                    return image
            elif value.startswith("#"):
                color = self._parse_color(value)
                if color is not None:
                    return color
        raise _UnrenderableLayer(reference)  # vector drawable, gradient, or unresolvable

    @staticmethod
    def _parse_color(value: str) -> tuple[int, int, int, int] | None:
        digits = value.lstrip("#")
        try:
            if len(digits) == 6:
                return int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16), 255
            if len(digits) == 8:  # #AARRGGBB
                return int(digits[2:4], 16), int(digits[4:6], 16), int(digits[6:8], 16), int(digits[0:2], 16)
        except ValueError:
            pass
        return None

    @staticmethod
    def _compose(background: Layer, foreground: Layer) -> Image.Image | None:
        layers = [layer for layer in (background, foreground) if layer is not None]
        size = next((layer.size for layer in reversed(layers) if isinstance(layer, Image.Image)), None)
        if size is None:
            return None  # only solid colors: there is no icon shape to show

        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        for layer in layers:
            if isinstance(layer, tuple):
                layer_image = Image.new("RGBA", size, layer)
            else:
                layer_image = layer.convert("RGBA")
                if layer_image.size != size:
                    layer_image = layer_image.resize(size, Image.Resampling.LANCZOS)
            canvas = Image.alpha_composite(canvas, layer_image)

        margin_x = round(size[0] * (_ADAPTIVE_CANVAS - _ADAPTIVE_VISIBLE) / 2 / _ADAPTIVE_CANVAS)
        margin_y = round(size[1] * (_ADAPTIVE_CANVAS - _ADAPTIVE_VISIBLE) / 2 / _ADAPTIVE_CANVAS)
        return canvas.crop((margin_x, margin_y, size[0] - margin_x, size[1] - margin_y))

    # --- Last-resort fallback -----------------------------------------------------------------

    def _resolve_icon_base_name(self, apk: APK) -> str:
        xml_elem = apk.get_android_manifest_xml()
        if xml_elem is not None:
            app_tag = xml_elem.find(".//application")
            if app_tag is not None:
                icon_ref = app_tag.get(f"{ANDROID_NS}icon") or app_tag.get(f"{ANDROID_NS}roundIcon")
                if icon_ref and "/" in icon_ref:
                    return icon_ref.split("/")[-1]
        return "ic_launcher"

    def _find_best_icon_by_name(self, apk: APK, base_name: str) -> Image.Image | None:
        matches = [
            f for f in apk.get_files()
            if os.path.splitext(os.path.basename(f))[0] == base_name
            and f.lower().endswith(_RASTER)
        ]
        matches.sort(
            key=lambda p: next((score for dpi, score in self._dpi_scores.items() if dpi in p.lower()), 0),
            reverse=True,
        )
        for match in matches:
            image = self._try_load(apk, match)
            if image is not None:
                return image
        return None

    # --- Images -------------------------------------------------------------------------

    @staticmethod
    def _load(icon_bytes: bytes) -> Image.Image:
        img = Image.open(io.BytesIO(icon_bytes))
        img.load()  # decode now so corrupt images fail here, not later
        return img

    @classmethod
    def _encode_png(cls, image: Image.Image) -> bytes:
        prepared = image if image.mode in cls._PNG_SAFE_MODES else image.convert("RGBA")
        buffer = io.BytesIO()
        prepared.save(buffer, format="PNG")
        return buffer.getvalue()
