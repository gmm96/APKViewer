"""
Filters a file tree by a text query.
"""

from dataclasses import replace

from apkviewer.domain.entities.file_node import FileNode


class FileTreeFilter:
    def filter(self, root: FileNode, query: str) -> FileNode:
        """Return a filtered copy of the tree, keeping only nodes matching `query`."""
        normalized_query = (query or "").strip().lower()
        if not normalized_query:
            return root
        return self._filter_node(root, normalized_query, force_include=False)

    def _filter_node(self, node: FileNode, query: str, force_include: bool) -> FileNode:
        kept: dict[str, FileNode] = {}
        for name, child in node.children.items():
            include = force_include or query in name.lower()
            if child.is_file:
                if include:
                    kept[name] = child
                continue
            filtered = self._filter_node(child, query, include)
            if filtered.children or include:
                kept[name] = filtered
        return replace(node, children=kept)
