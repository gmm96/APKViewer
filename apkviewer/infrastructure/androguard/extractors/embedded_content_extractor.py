"""
Scans the strings of the DEX files to extract hardcoded HTTP/HTTPS URLs.
"""

import re

from apkviewer.domain.entities.embedded_content import EmbeddedContent
from apkviewer.infrastructure.androguard.dex_reader import DexContents


class EmbeddedContentExtractor:
    _URL_REGEX: re.Pattern = re.compile(r"https?://[\w\-\.\:]+(?:/[\w\-\.\:\/\?\=\&\%\#\+]*)?")

    def extract(self, dex: DexContents) -> EmbeddedContent:
        urls: set[str] = set()
        for text in dex.strings:
            if "http://" in text or "https://" in text:
                urls.update(self._URL_REGEX.findall(text))
        return EmbeddedContent(urls=tuple(sorted(urls)))
