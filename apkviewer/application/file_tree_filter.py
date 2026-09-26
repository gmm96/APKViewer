"""
Filters a file-tree dict (as built by FileTreeBuilder) by a text query.
"""

from typing import Any


class FileTreeFilter:
    def filter(self, node_dict: dict[str, Any], query: str) -> dict[str, Any]:
        """Return a filtered copy of the tree, keeping only nodes matching `query`."""
        normalized_query = (query or "").strip().lower()
        if not normalized_query:
            return node_dict
        return self._filter_recursive(node_dict, normalized_query, force_include=False)

    def _filter_recursive(self, node_dict: dict[str, Any], query: str, force_include: bool) -> dict[str, Any]:
        filtered = {}
        for name, meta in node_dict.items():
            matches_name = query in name.lower()
            should_include = force_include or matches_name
            if meta.get("__is_file__"):
                if should_include:
                    filtered[name] = meta
            else:
                children = self._filter_recursive(meta.get("__children__", {}), query, should_include)
                if children or should_include:
                    new_meta = dict(meta)
                    new_meta["__children__"] = children
                    filtered[name] = new_meta
        return filtered
