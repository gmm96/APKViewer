"""
Builds the in-memory tree of an archive's entries, with per-folder size
aggregation. It works on plain ArchiveEntry values, so it neither knows
nor cares how the archive was read.
"""

from collections.abc import Iterable

from apkviewer.domain.entities.archive_entry import ArchiveEntry
from apkviewer.domain.entities.file_node import FileNode


class FileTreeBuilder:
    def build(self, entries: Iterable[ArchiveEntry]) -> FileNode:
        root = FileNode.create_root()
        for entry in entries:
            self._insert(root, entry)
        self._aggregate(root)
        return root

    @staticmethod
    def _insert(root: FileNode, entry: ArchiveEntry) -> None:
        parts = [part for part in entry.path.split("/") if part]
        if not parts:
            return
        node = root
        for depth, part in enumerate(parts):
            child = node.children.get(part)
            if child is None:
                child = FileNode(name=part, path="/".join(parts[: depth + 1]))
                node.children[part] = child
            node = child
        node.is_file = True
        node.size = entry.size
        node.compressed_size = entry.compressed_size
        node.modified = entry.modified

    def _aggregate(self, node: FileNode) -> None:
        """Bottom-up: a folder's size, compressed size and date come from its children."""
        if node.is_file:
            return
        for child in node.children.values():
            self._aggregate(child)
        node.size = sum(child.size for child in node.children.values())
        node.compressed_size = sum(child.compressed_size for child in node.children.values())
        dates = [child.modified for child in node.children.values() if child.modified is not None]
        node.modified = max(dates, default=None)
