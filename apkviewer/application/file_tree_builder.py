"""
Builds an in-memory tree representation of an APK's internal zip entries,
with per-node size aggregation.
"""

import zipfile
from datetime import datetime
from typing import Any


class FileTreeBuilder:
    def build(self, apk_path: str) -> dict[str, dict[str, Any]]:
        """Read the APK as a zip file and build a nested dict tree of its entries."""
        root_node = {}
        try:
            with zipfile.ZipFile(apk_path, "r") as zf:
                for info in zf.infolist():
                    if info.is_dir() or not info.filename:
                        continue
                    self._insert_entry(root_node, info)
        except Exception:
            pass
        self._aggregate_folder_sizes(root_node)
        return root_node

    def _insert_entry(self, root_node: dict[str, dict[str, Any]], info: zipfile.ZipInfo) -> None:
        parts = [p for p in info.filename.split("/") if p]
        if not parts:
            return
        node = root_node
        for i, part in enumerate(parts):
            is_last = i == len(parts) - 1
            if part not in node:
                node[part] = {"__children__": {}, "__is_file__": False, "__size__": 0}
            if is_last:
                node[part]["__is_file__"] = True
                node[part]["__size__"] = info.file_size
                node[part]["__compressed__"] = info.compress_size
                node[part]["__modified__"] = self._format_mtime(info.date_time)
            node = node[part]["__children__"]

    @staticmethod
    def _format_mtime(date_time_tuple: tuple[int, int, int, int, int, int]) -> str:
        try:
            return datetime(*date_time_tuple).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return ""

    def _aggregate_folder_sizes(self, node_dict: dict[str, dict[str, Any]]) -> tuple[int, int, str]:
        """
        Recursively sum size/compressed size and find the most recent
        modification date for every folder node, bottom-up.
        """
        total_size = 0
        total_compressed = 0
        latest_modified = ""
        for meta in node_dict.values():
            if meta.get("__is_file__"):
                total_size += meta.get("__size__", 0)
                total_compressed += meta.get("__compressed__", 0)
                mtime = meta.get("__modified__", "")
            else:
                folder_size, folder_comp, mtime = self._aggregate_folder_sizes(meta.get("__children__", {}))
                meta["__size__"] = folder_size
                meta["__compressed__"] = folder_comp
                meta["__modified__"] = mtime
                total_size += folder_size
                total_compressed += folder_comp
            if mtime > latest_modified:
                latest_modified = mtime
        return total_size, total_compressed, latest_modified
