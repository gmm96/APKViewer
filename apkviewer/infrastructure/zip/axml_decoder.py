"""
Specialized decoder for Android Binary XML (AXML) files, turning them
back into plain readable XML bytes.
"""

from androguard.core.axml import AXMLPrinter

from apkviewer.domain.interfaces import FileDecoder


class AxmlDecoder(FileDecoder):
    def can_decode(self, data: bytes) -> bool:
        return data.startswith(b"\x03\x00\x08\x00") and AXMLPrinter is not None

    def decode(self, data: bytes) -> bytes:
        try:
            printer = AXMLPrinter(data)
            decoded = printer.get_xml() if hasattr(printer, "get_xml") else printer.get_buff()
            if decoded is not None:
                return decoded.encode("utf-8") if isinstance(decoded, str) else decoded
        except Exception:
            pass
        return data
