"""
Handles lazy extraction of specific files or directories from an APK.
Uses a pluggable decoder architecture (see AxmlDecoder) to remain
completely agnostic of file formats.
"""

import os
import zipfile

from apkviewer.domain.interfaces import FileDecoder

from .axml_decoder import AxmlDecoder


class ApkExtractor:
    def __init__(self, decoders: list[FileDecoder] | None = None) -> None:
        # Inject known special cases here; the extractor remains agnostic
        self._decoders = decoders if decoders is not None else [AxmlDecoder()]

    def extract(self, apk_path: str, internal_paths: list[str], dest_dir: str) -> list[str]:
        extracted_paths = []

        # Intentionally NOT wrapped in a blanket try/except: if the APK
        # itself can't even be opened (missing, corrupt, permission denied),
        # that's a real error the caller needs to know about and show to the
        # user - not something to silently swallow into "0 files extracted".
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

        return extracted_paths

    def _extract_single_file(self, zf: zipfile.ZipFile, internal_path: str, dest_dir: str) -> str | None:
        dest_dir_abs = os.path.abspath(dest_dir)
        out_path = os.path.abspath(os.path.join(dest_dir_abs, *internal_path.split("/")))

        # "Zip Slip" guard: APKs are untrusted input for this tool, so a
        # crafted entry name such as "../../../../etc/passwd" must never be
        # allowed to write outside the directory the user chose to extract
        # into. os.path.normpath alone (a previous approach) does NOT
        # protect against this - it happily resolves ".." components.
        try:
            if os.path.commonpath([dest_dir_abs, out_path]) != dest_dir_abs:
                return None
        except ValueError:
            return None  # e.g. different drives on Windows - definitely not contained

        try:
            data = zf.read(internal_path)
        except Exception:
            return None  # one unreadable entry shouldn't abort the whole batch

        # Agnostically run data through any matching decoders
        for decoder in self._decoders:
            if decoder.can_decode(data):
                data = decoder.decode(data)
                break

        try:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(data)
        except OSError:
            return None

        return out_path
