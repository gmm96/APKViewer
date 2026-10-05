"""
Extracts the components declared in the manifest (activities, services,
receivers and providers) together with their intent filters.

Attribute values are made readable here (resource references resolved,
enums and flag masks turned into names). What the values mean for each
Android version (e.g. the default of `exported`) is decided by ExportState.
"""

from typing import Any

from androguard.core.apk import APK

from apkviewer.domain.entities.analysis_warning import AnalysisArea
from apkviewer.domain.entities.component_kind import ComponentKind
from apkviewer.domain.entities.components import (
    Component,
    DeclaredComponents,
    IntentFilter,
    ManifestElement,
)
from apkviewer.domain.entities.export_state import ExportState
from apkviewer.domain.entities.exported_intent import IntentData
from apkviewer.infrastructure.androguard.analysis_warnings import AnalysisWarningCollector
from apkviewer.infrastructure.androguard.config.android import ANDROID_NS
from apkviewer.infrastructure.androguard.manifest_value_formatter import ManifestValueFormatter
from apkviewer.infrastructure.androguard.resource_reference_resolver import ResourceReferenceResolver

# targetSdkVersion given as a codename (a preview build) is newer than any numbered release.
_PREVIEW_SDK: int = 10_000


class ComponentsExtractor:
    _KINDS: dict[str, ComponentKind] = {
        "activity": ComponentKind.ACTIVITY,
        "activity-alias": ComponentKind.ACTIVITY_ALIAS,
        "service": ComponentKind.SERVICE,
        "receiver": ComponentKind.RECEIVER,
        "provider": ComponentKind.PROVIDER,
    }
    _CATEGORY_PREFIX: str = "android.intent.category."
    # Attributes already shown as dedicated fields of Component.
    _DEDICATED_ATTRIBUTES: frozenset[str] = frozenset({"name", "exported", "permission"})

    def extract(
        self, apk: APK, warnings: AnalysisWarningCollector | None = None
    ) -> DeclaredComponents:
        pkg_name = apk.get_package() or ""
        target_sdk = self._target_sdk(apk)
        formatter = ManifestValueFormatter(ResourceReferenceResolver(apk))
        components: list[Component] = []
        try:
            xml_root = apk.get_android_manifest_xml()
            if xml_root is None:
                self._warn(warnings, "The manifest is missing or corrupted: no components could be listed.")
                return DeclaredComponents()
            for tag, kind in self._KINDS.items():
                for node in xml_root.iter(tag):
                    components.append(self._to_component(node, kind, pkg_name, target_sdk, formatter))
        except Exception as exc:
            self._warn(
                warnings,
                f"The manifest could not be read completely ({type(exc).__name__}): "
                "the list of components may be incomplete.",
            )

        order = list(ComponentKind)
        unique = dict.fromkeys(components)
        return DeclaredComponents(
            tuple(sorted(unique, key=lambda c: (order.index(c.kind), c.name.lower())))
        )

    @staticmethod
    def _warn(warnings: AnalysisWarningCollector | None, message: str) -> None:
        if warnings is not None:
            warnings.add(message, AnalysisArea.COMPONENTS)

    @staticmethod
    def _target_sdk(apk: APK) -> int | None:
        """targetSdkVersion, falling back to minSdkVersion (what Android does); None if neither is readable."""
        for getter in (apk.get_target_sdk_version, apk.get_min_sdk_version):
            try:
                raw = getter()
            except Exception:
                continue
            if raw is None:
                continue
            try:
                return int(raw)
            except (TypeError, ValueError):
                return _PREVIEW_SDK
        return None

    def _to_component(
        self,
        node: Any,
        kind: ComponentKind,
        pkg_name: str,
        target_sdk: int | None,
        formatter: ManifestValueFormatter,
    ) -> Component:
        filters = tuple(self._to_filter(f) for f in node.findall("intent-filter"))
        permission = node.get(f"{ANDROID_NS}permission")
        return Component(
            name=self._resolve_name(node, pkg_name),
            kind=kind,
            export_state=ExportState.resolve(
                kind, formatter.declared(node.get(f"{ANDROID_NS}exported")), bool(filters), target_sdk
            ),
            permission=formatter.format("permission", permission) if permission else None,
            intent_filters=filters,
            attributes=self._attributes(node, formatter, self._DEDICATED_ATTRIBUTES),
            elements=tuple(
                ManifestElement(child.tag, self._attributes(child, formatter))
                for child in node
                if isinstance(child.tag, str) and child.tag != "intent-filter"  # skips comments
            ),
        )

    @staticmethod
    def _attributes(
        node: Any, formatter: ManifestValueFormatter, skip: frozenset[str] = frozenset()
    ) -> tuple[tuple[str, str], ...]:
        """The attributes of a node as (local name, readable value), without the XML namespace."""
        pairs = ((key.rsplit("}", 1)[-1], str(value)) for key, value in node.attrib.items())
        return tuple((name, formatter.format(name, value)) for name, value in pairs if name not in skip)

    @staticmethod
    def _resolve_name(node: Any, pkg_name: str) -> str:
        name = node.get(f"{ANDROID_NS}name", "Unknown")
        if name.startswith("."):
            return pkg_name + name
        if "." not in name and name != "Unknown":
            return f"{pkg_name}.{name}"
        return name

    def _to_filter(self, filter_node: Any) -> IntentFilter:
        actions: list[str] = []
        categories: list[str] = []
        data: list[IntentData] = []
        for node in filter_node:
            name = node.get(f"{ANDROID_NS}name")
            if node.tag == "action" and name:
                actions.append(name)
            elif node.tag == "category" and name:
                categories.append(name.replace(self._CATEGORY_PREFIX, ""))
            elif node.tag == "data":
                data.append(self._to_intent_data(node))
        auto_verify = (filter_node.get(f"{ANDROID_NS}autoVerify") or "").lower() == "true"
        return IntentFilter(tuple(actions), tuple(categories), tuple(data), auto_verify)

    @staticmethod
    def _to_intent_data(node: Any) -> IntentData:
        def attr(name: str) -> str | None:
            return node.get(f"{ANDROID_NS}{name}") or None

        return IntentData(
            scheme=attr("scheme"),
            host=attr("host"),
            port=attr("port"),
            path=attr("path"),
            path_prefix=attr("pathPrefix"),
            path_pattern=attr("pathPattern"),
            path_suffix=attr("pathSuffix"),
            path_advanced_pattern=attr("pathAdvancedPattern"),
            ssp=attr("ssp"),
            ssp_prefix=attr("sspPrefix"),
            ssp_pattern=attr("sspPattern"),
            ssp_suffix=attr("sspSuffix"),
            ssp_advanced_pattern=attr("sspAdvancedPattern"),
            mime_type=attr("mimeType"),
            mime_group=attr("mimeGroup"),
        )
