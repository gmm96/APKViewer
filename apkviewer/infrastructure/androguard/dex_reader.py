"""
Reads the strings and class names of every DEX file of an APK exactly once.
The extractors that need code-level data (embedded URLs, trackers) share
this result.

DEX files are read directly from their string / type / class tables
instead of through androguard's DEX object, which builds the whole
class/method model (about 20 s for a 7-DEX app) when only these two lists
are needed. It also keeps working with DEX versions the library can't parse.
"""

import struct
from dataclasses import dataclass

from androguard.core.apk import APK

from apkviewer.domain.entities.analysis_warning import AnalysisArea
from apkviewer.infrastructure.androguard.analysis_warnings import AnalysisWarningCollector

_HEADER_SIZE: int = 0x70
_CLASS_DEF_WORDS: int = 8  # a class_def_item is 8 uint32 (32 bytes); the first is the class type


@dataclass(frozen=True)
class DexContents:
    strings: tuple[str, ...] = ()
    class_names: tuple[str, ...] = ()  # type descriptors, e.g. "Lcom/example/Main;"


class DexReader:
    def read(self, apk: APK, warnings: AnalysisWarningCollector | None = None) -> DexContents:
        strings: list[str] = []
        class_names: list[str] = []
        for number, dex_bytes in enumerate(apk.get_all_dex(), start=1):
            dex_strings, dex_classes, problem = self._parse(dex_bytes)
            strings.extend(dex_strings)
            class_names.extend(dex_classes)
            if problem and warnings is not None:
                warnings.add(
                    f"DEX file #{number} {problem}: embedded URLs and trackers may be incomplete.",
                    AnalysisArea.INFO, AnalysisArea.SECURITY,
                )
        return DexContents(strings=tuple(strings), class_names=tuple(class_names))

    @classmethod
    def _parse(cls, data: bytes) -> tuple[list[str], list[str], str | None]:
        """(strings, class names, problem) of one DEX; whatever can't be read comes back empty."""
        if len(data) < _HEADER_SIZE or not data.startswith(b"dex\n"):
            return [], [], "is not a valid DEX file"
        try:
            (string_count, string_off, type_count, type_off,
             _, _, _, _, _, _, class_count, class_off) = struct.unpack_from("<12I", data, 56)
            strings = cls._read_strings(data, string_count, string_off)
        except (struct.error, IndexError):
            return [], [], "could not be read (corrupt string table)"

        try:
            type_to_string = struct.unpack_from(f"<{type_count}I", data, type_off)
            class_words = struct.unpack_from(f"<{class_count * _CLASS_DEF_WORDS}I", data, class_off)
            class_names = [strings[type_to_string[idx]] for idx in class_words[::_CLASS_DEF_WORDS]]
        except (struct.error, IndexError):
            return strings, [], "has unreadable class tables"
        return strings, class_names, None

    @staticmethod
    def _read_strings(data: bytes, count: int, table_off: int) -> list[str]:
        strings: list[str] = []
        find = data.find
        for offset in struct.unpack_from(f"<{count}I", data, table_off):
            pos = offset
            while data[pos] & 0x80:  # skip the ULEB128 length prefix
                pos += 1
            pos += 1
            end = find(b"\0", pos)
            raw = data[pos:end if end >= 0 else len(data)]
            if b"\xc0" in raw:  # MUTF-8 stores an embedded NUL as C0 80
                raw = raw.replace(b"\xc0\x80", b"\0")
            strings.append(raw.decode("utf-8", "replace"))
        return strings
