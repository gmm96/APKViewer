"""
One palette per color scheme. `window_bg`, `text_fg` and the selection
colors mirror the Forest theme (forest-light.tcl / forest-dark.tcl) so
classic Tk widgets blend with the themed ttk ones.
"""

from apkviewer.domain.entities.color_scheme import ColorScheme

from .theme_palette import ThemePalette

LIGHT_PALETTE: ThemePalette = ThemePalette(
    window_bg="#ffffff",
    text_bg="#fcfcfc",
    text_fg="#313131",
    disabled_fg="#a0a0a0",
    secondary_fg="#666666",
    selection_bg="#217346",
    selection_fg="#ffffff",
    mark_bg="#d4ecdc",
    folder_bg="#eef3f8",
    placeholder_bg="#e0e0e0",
    placeholder_border="#cccccc",
    icon_tint="#313131",
    xml_tag="#0033B3",
    xml_attr="#871094",
    xml_value="#067D17",
    xml_comment="#8C8C8C",
    status_neutral="#666666",
    status_info="#1a5fb4",
    status_success="#1b7f3b",
    status_error="#c01c28",
)

DARK_PALETTE: ThemePalette = ThemePalette(
    window_bg="#313131",
    text_bg="#2a2a2a",
    text_fg="#eeeeee",
    disabled_fg="#6b6b6b",
    secondary_fg="#a0a0a0",
    selection_bg="#217346",
    selection_fg="#ffffff",
    mark_bg="#2f4f3a",
    folder_bg="#3a3d41",
    placeholder_bg="#424242",
    placeholder_border="#555555",
    icon_tint="#eeeeee",
    xml_tag="#6fa8ff",
    xml_attr="#c792ea",
    xml_value="#a5d6a7",
    xml_comment="#8a8a8a",
    status_neutral="#a0a0a0",
    status_info="#78aeed",
    status_success="#57e389",
    status_error="#ff7b72",
)

PALETTES: dict[ColorScheme, ThemePalette] = {
    ColorScheme.LIGHT: LIGHT_PALETTE,
    ColorScheme.DARK: DARK_PALETTE,
}
