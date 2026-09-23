"""
Handles lazy extraction of specific files or directories from an APK.
Uses a pluggable decoder architecture to remain completely agnostic of file formats.
"""
import os
import zipfile
from typing import List

# Handle different Androguard versions dynamically
try:
    from androguard.core.bytecodes.axml import AXMLPrinter
except ImportError:
    try:
        from androguard.core.axml import AXMLPrinter
    except ImportError:
        AXMLPrinter = None


class FileDecoder:
    """Base interface for file decoders."""
    def can_decode(self, data: bytes) -> bool:
        raise NotImplementedError
        
    def decode(self, data: bytes) -> bytes:
        raise NotImplementedError


class AxmlDecoder(FileDecoder):
    """Specialized decoder for Android Binary XML files."""
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


class ApkExtractor:
    def __init__(self, decoders: List[FileDecoder] = None):
        # Inject known special cases here; the extractor remains agnostic
        self._decoders = decoders if decoders is not None else [AxmlDecoder()]

    def extract(self, apk_path: str, internal_paths: List[str], dest_dir: str) -> List[str]:
        extracted_paths = []
        
        try:
            with zipfile.ZipFile(apk_path, "r") as zf:
                all_names = zf.namelist()
                
                for target in internal_paths:
                    if target in all_names:
                        out_path = self._extract_single_file(zf, target, dest_dir)
                        if out_path:
                            extracted_paths.append(out_path)
                    else:
                        prefix = target if target.endswith("/") else f"{target}/"
                        for name in all_names:
                            if name.startswith(prefix):
                                out_path = self._extract_single_file(zf, name, dest_dir)
                                if out_path:
                                    extracted_paths.append(out_path)
        except Exception:
            pass

        return extracted_paths

    def _extract_single_file(self, zf: zipfile.ZipFile, internal_path: str, dest_dir: str) -> str:
        try:
            data = zf.read(internal_path)
            
            # Agnostically run data through any matching decoders
            for decoder in self._decoders:
                if decoder.can_decode(data):
                    data = decoder.decode(data)
                    break

            out_path = os.path.normpath(os.path.join(dest_dir, internal_path))
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            
            with open(out_path, "wb") as f:
                f.write(data)
                
            return out_path
        except Exception:
            return None
