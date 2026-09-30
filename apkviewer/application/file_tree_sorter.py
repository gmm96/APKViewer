"""
Decides how the children of a file-tree node are ordered.

This is pure ordering logic with no dependency on any UI toolkit: the
front end only translates its own column identifiers into a FileSortKey.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from apkviewer.domain.entities.file_node import FileNode


class FileSortKey(Enum):
    NAME = "name"
    TYPE = "type"
    SIZE = "size"
    COMPRESSED = "compressed"
    MODIFIED = "modified"


class FileTreeSorter:
    """
    Directories are always grouped before files (as in most file
    explorers); only the ordering *within* each group follows the selected
    key and direction. Numeric keys sort by raw byte count and the modified
    key by its datetime, never by a formatted string.
    """

    DEFAULT_KEY: FileSortKey = FileSortKey.NAME

    def __init__(self) -> None:
        self.key: FileSortKey = self.DEFAULT_KEY
        self.reverse: bool = False

    def toggle(self, key: FileSortKey) -> None:
        """Sort by `key`; requesting the same key again flips the direction."""
        if self.key == key:
            self.reverse = not self.reverse
        else:
            self.key = key
            self.reverse = False

    def sorted_children(self, node: FileNode) -> list[FileNode]:
        children = list(node.children.values())
        folders = [child for child in children if not child.is_file]
        files = [child for child in children if child.is_file]
        folders.sort(key=self._sort_key, reverse=self.reverse)
        files.sort(key=self._sort_key, reverse=self.reverse)
        return folders + files

    def _sort_key(self, node: FileNode) -> tuple[Any, str]:
        # The name is a tiebreaker that keeps the order stable/predictable.
        return (self._key_value(node), node.name.lower())

    def _key_value(self, node: FileNode) -> Any:
        if self.key == FileSortKey.TYPE:
            return node.extension
        if self.key == FileSortKey.SIZE:
            return node.size
        if self.key == FileSortKey.COMPRESSED:
            return node.compressed_size
        if self.key == FileSortKey.MODIFIED:
            return node.modified or datetime.min
        return node.name.lower()
