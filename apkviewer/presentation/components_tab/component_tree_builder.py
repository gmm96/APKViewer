"""
Maps the component/intent entities into RecordNode rows. Pure functions
of the entities: no Tk involved, so they are easy to test.
"""

from collections.abc import Sequence
from dataclasses import replace

from apkviewer.domain.entities.component_kind import ComponentKind
from apkviewer.domain.entities.components import (
    Component,
    DeclaredComponents,
    IntentFilter,
    ManifestElement,
)
from apkviewer.domain.entities.export_state import ExportState
from apkviewer.domain.entities.exported_intent import ExportedIntent
from apkviewer.presentation.common.tree.record_node import RecordNode


class ComponentTreeBuilder:
    # (category key, label) of the groups the components tab can restrict to.
    GROUPS: tuple[tuple[str, str], ...] = (
        ("activity", "Activities"),
        ("service", "Services"),
        ("receiver", "Receivers"),
        ("provider", "Providers"),
    )
    _KIND_GROUPS: dict[ComponentKind, str] = {
        ComponentKind.ACTIVITY: "activity",
        ComponentKind.ACTIVITY_ALIAS: "activity",
        ComponentKind.SERVICE: "service",
        ComponentKind.RECEIVER: "receiver",
        ComponentKind.PROVIDER: "provider",
    }

    _MAX_INLINE_ATTRIBUTES: int = 3
    _EXPORT_LABELS: dict[ExportState, str] = {
        ExportState.EXPORTED: "yes",
        ExportState.NOT_EXPORTED: "no",
        ExportState.IMPLICIT_EXPORTED: "yes (implicit)",
        ExportState.IMPLICIT_NOT_EXPORTED: "no (implicit)",
        ExportState.UNRESOLVED: "unknown",
    }

    def build_components(self, components: DeclaredComponents) -> RecordNode:
        rows = tuple(
            self._component_row(f"component:{index}", component)
            for index, component in enumerate(components.items)
        )
        return replace(RecordNode.create_root(), children=rows)

    def build_intents(self, intents: Sequence[ExportedIntent]) -> RecordNode:
        rows = tuple(
            RecordNode(
                iid=f"intent:{index}",
                cells=(
                    intent.name,
                    intent.component_name,
                    intent.component_kind.value,
                    ", ".join(intent.categories),
                    ", ".join(text for text in (d.as_text() for d in intent.data) if text),
                    "yes" if intent.auto_verify else "",
                ),
            )
            for index, intent in enumerate(intents)
        )
        return replace(RecordNode.create_root(), children=rows)

    # --- Components ------------------------------------------------------------

    def _component_row(self, iid: str, component: Component) -> RecordNode:
        children = [
            self._field(f"{iid}/attribute:{name}", name, value)
            for name, value in component.attributes
        ]
        children += [
            self._element_row(f"{iid}/element{index}", element)
            for index, element in enumerate(component.elements)
        ]
        children += [
            self._filter_row(f"{iid}/filter{index}", intent_filter)
            for index, intent_filter in enumerate(component.intent_filters)
        ]
        return RecordNode(
            iid=iid,
            cells=(
                component.name,
                component.kind.value,
                self._EXPORT_LABELS[component.export_state],
                component.permission or "—",
            ),
            children=tuple(children),
            category=self._KIND_GROUPS[component.kind],
        )

    def _element_row(self, iid: str, element: ManifestElement) -> RecordNode:
        """Small elements (meta-data...) fit one line; bigger ones expand into their attributes."""
        if len(element.attributes) <= self._MAX_INLINE_ATTRIBUTES:
            text = ", ".join(f"{name}={value}" for name, value in element.attributes)
            return RecordNode(iid, (f"{element.tag} = {text}" if text else element.tag,))
        return RecordNode(
            iid,
            (element.tag,),
            children=tuple(
                self._field(f"{iid}/{name}", name, value) for name, value in element.attributes
            ),
        )

    def _filter_row(self, iid: str, intent_filter: IntentFilter) -> RecordNode:
        """One line per property; the properties that hold several values list them with commas."""
        data = [text for text in (d.as_text() for d in intent_filter.data) if text]
        properties = (
            ("actions", ", ".join(intent_filter.actions)),
            ("categories", ", ".join(intent_filter.categories)),
            ("data", ", ".join(data)),
            ("autoVerify", "true" if intent_filter.auto_verify else ""),
        )
        return RecordNode(
            iid,
            ("Intent filter",),
            children=tuple(
                self._field(f"{iid}/{key}", key, value) for key, value in properties if value
            ),
        )

    @staticmethod
    def _field(iid: str, key: str, value: str) -> RecordNode:
        return RecordNode(iid, (f"{key} = {value}",))
