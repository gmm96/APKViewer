"""
Presentation-side row of a RecordTablePanel: one text per column and,
optionally, nested rows shown when it is expanded.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RecordNode:
    iid: str
    cells: tuple[str, ...]
    children: tuple["RecordNode", ...] = ()
    category: str | None = None  # lets a panel show only some of the top-level rows
    open_by_default: bool = False  # whether its nested rows start expanded
    style: str | None = None       # name of a row style (see RecordTablePanel.row_styles)

    @classmethod
    def create_root(cls) -> "RecordNode":
        return cls(iid="", cells=())

    def contains(self, query_lower: str) -> bool:
        """True if any cell of this row or of a nested row matches the (lower-case) query."""
        return any(query_lower in cell.lower() for cell in self.cells) or any(
            child.contains(query_lower) for child in self.children
        )
