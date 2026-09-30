"""
A node (file or folder) of the tree that represents an archive's content.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FileNode:
    name: str
    path: str
    is_file: bool = False
    size: int = 0
    compressed_size: int = 0
    modified: datetime | None = None
    children: dict[str, "FileNode"] = field(default_factory=dict)

    @classmethod
    def create_root(cls) -> "FileNode":
        """Return the (nameless) root that holds the top-level entries."""
        return cls(name="", path="")

    @property
    def extension(self) -> str:
        """Upper-case extension without the dot; empty for folders and extension-less files."""
        if not self.is_file:
            return ""
        return os.path.splitext(self.name)[1].lstrip(".").upper()

    def find(self, path: str) -> "FileNode | None":
        """Return the descendant located at the '/'-separated `path`, or None."""
        node: FileNode = self
        for part in path.split("/"):
            if not part:
                continue
            child = node.children.get(part)
            if child is None:
                return None
            node = child
        return node
