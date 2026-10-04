"""
Building blocks of an <intent-filter> and the flattened "exported intent"
view derived from them.
"""

from dataclasses import dataclass

from apkviewer.domain.entities.component_kind import ComponentKind


@dataclass(frozen=True)
class IntentData:
    """
    A <data> element of an intent filter. Every attribute is optional; the
    path*/mimeGroup/ssp* ones only exist in recent Android versions (API 31+).
    """
    scheme: str | None = None
    host: str | None = None
    port: str | None = None
    path: str | None = None
    path_prefix: str | None = None
    path_pattern: str | None = None
    path_suffix: str | None = None
    path_advanced_pattern: str | None = None
    ssp: str | None = None
    ssp_prefix: str | None = None
    ssp_pattern: str | None = None
    ssp_suffix: str | None = None
    ssp_advanced_pattern: str | None = None
    mime_type: str | None = None
    mime_group: str | None = None

    def as_pairs(self) -> list[tuple[str, str]]:
        """The attributes that are set, as (manifest attribute name, value)."""
        pairs = (
            ("scheme", self.scheme),
            ("host", self.host),
            ("port", self.port),
            ("path", self.path),
            ("pathPrefix", self.path_prefix),
            ("pathPattern", self.path_pattern),
            ("pathSuffix", self.path_suffix),
            ("pathAdvancedPattern", self.path_advanced_pattern),
            ("ssp", self.ssp),
            ("sspPrefix", self.ssp_prefix),
            ("sspPattern", self.ssp_pattern),
            ("sspSuffix", self.ssp_suffix),
            ("sspAdvancedPattern", self.ssp_advanced_pattern),
            ("mimeType", self.mime_type),
            ("mimeGroup", self.mime_group),
        )
        return [(name, value) for name, value in pairs if value]

    def as_text(self) -> str:
        """One-line, URI-like description, e.g. 'https://host/path*' or 'image/*'."""
        mime_group = f"mimeGroup:{self.mime_group}" if self.mime_group else None
        parts = (self._uri_text(), self.mime_type, mime_group)
        return " + ".join(part for part in parts if part)

    def _uri_text(self) -> str:
        ssp = self._ssp_text()
        if ssp:  # opaque URIs such as tel: or mailto:
            return f"{self.scheme}:{ssp}" if self.scheme else ssp

        uri = f"{self.scheme}://" if self.scheme else ""
        uri += self.host or ""
        if self.port:
            uri += f":{self.port}"
        path = self._path_text()
        if path and uri and not path.startswith("/"):
            path = "/" + path  # e.g. pathSuffix=".html" -> host/*.html
        return uri + path

    def _ssp_text(self) -> str:
        options = (
            self.ssp,
            f"{self.ssp_prefix}*" if self.ssp_prefix else None,
            self.ssp_pattern,
            f"*{self.ssp_suffix}" if self.ssp_suffix else None,
            self.ssp_advanced_pattern,
        )
        return "|".join(option for option in options if option)

    def _path_text(self) -> str:
        options = (
            self.path,
            f"{self.path_prefix}*" if self.path_prefix else None,
            self.path_pattern,
            f"*{self.path_suffix}" if self.path_suffix else None,
            self.path_advanced_pattern,
        )
        return "|".join(option for option in options if option)


@dataclass(frozen=True)
class ExportedIntent:
    """One action of one intent filter of an exported component."""
    name: str
    component_name: str
    component_kind: ComponentKind
    categories: tuple[str, ...] = ()
    data: tuple[IntentData, ...] = ()
    auto_verify: bool = False
