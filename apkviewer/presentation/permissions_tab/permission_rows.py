"""
Maps permissions into RecordNode rows for the permission tables. Pure
functions of the entities: no Tk involved.
"""

from collections.abc import Sequence
from dataclasses import replace

from apkviewer.domain.entities.permission import Permission
from apkviewer.presentation.common.tree.record_node import RecordNode

DANGEROUS_STYLE: str = "dangerous"


class PermissionRowBuilder:
    def build(self, permissions: Sequence[Permission], with_origin: bool = False) -> RecordNode:
        """One row per permission; `with_origin` adds the Origin column (custom permissions)."""
        rows = tuple(
            RecordNode(
                iid=f"permission:{index}",
                cells=self._cells(permission, with_origin),
                style=DANGEROUS_STYLE if permission.is_dangerous else None,
            )
            for index, permission in enumerate(permissions)
        )
        return replace(RecordNode.create_root(), children=rows)

    @staticmethod
    def _cells(permission: Permission, with_origin: bool) -> tuple[str, ...]:
        cells = [permission.name, permission.type_text]
        if with_origin:
            cells.append(permission.origin.value)
        cells += [
            permission.max_sdk or "",
            permission.label or "",
            permission.description or "",
        ]
        return tuple(cells)
