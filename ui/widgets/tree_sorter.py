"""
Decides how sibling entries of the Files tree are ordered.
"""
import os


class FileTreeSorter:
    """
    Sorts one level of file-tree siblings by a chosen column.

    Directories are always grouped before files (as in most file
    explorers); only the ordering *within* each group follows the
    selected column and direction. Numeric columns (size, compressed)
    sort by their raw byte count, and the modified column sorts by its
    "%Y-%m-%d %H:%M:%S" string, which is chronologically ordered as-is -
    neither is ever compared alphabetically against a formatted string.
    """

    DEFAULT_COLUMN = "#0"

    def __init__(self):
        self.column = self.DEFAULT_COLUMN
        self.reverse = False

    def toggle(self, column: str) -> None:
        """Sort by `column`; clicking the same column again flips direction."""
        if self.column == column:
            self.reverse = not self.reverse
        else:
            self.column = column
            self.reverse = False

    def sorted_entries(self, node_dict: dict) -> list:
        items = list(node_dict.items())
        folders = [item for item in items if not item[1].get("__is_file__", False)]
        files = [item for item in items if item[1].get("__is_file__", False)]

        folders.sort(key=self._sort_key, reverse=self.reverse)
        files.sort(key=self._sort_key, reverse=self.reverse)
        return folders + files

    def _sort_key(self, item):
        name, meta = item
        # `name.lower()` as a tiebreaker keeps the order stable/predictable
        # whenever two entries share the same value for the chosen column.
        return (self._column_value(name, meta), name.lower())

    def _column_value(self, name: str, meta: dict):
        if self.column == "#0":
            return name.lower()
        if self.column == "type":
            if meta.get("__is_file__", False):
                return os.path.splitext(name)[1].lstrip(".").upper()
            return ""
        if self.column in ("size", "compressed"):
            return meta.get(f"__{self.column}__", 0)
        if self.column == "modified":
            return meta.get("__modified__", "")
        return name.lower()
