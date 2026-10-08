"""
Extracts the permissions an APK requests (<uses-permission>) and declares
(<permission>), and sorts them into the three groups the UI shows.

Android decides the protection level, label and description of its own
permissions (see AospPermissionCatalog). For the permissions the app
declares itself, those come from the manifest, with resource references
resolved through the app's resource table.
"""

from typing import Any

from androguard.core.apk import APK

from apkviewer.domain.entities.analysis_warning import AnalysisArea
from apkviewer.domain.entities.permission import (
    Permission,
    PermissionOrigin,
    PermissionsInfo,
    parse_protection_level,
)
from apkviewer.infrastructure.androguard.analysis_warnings import AnalysisWarningCollector
from apkviewer.infrastructure.androguard.aosp_permission_catalog import AospPermissionCatalog
from apkviewer.infrastructure.androguard.config.android import ANDROID_NS
from apkviewer.infrastructure.androguard.resource_reference_resolver import ResourceReferenceResolver


class PermissionsExtractor:
    def __init__(self, catalog: AospPermissionCatalog | None = None) -> None:
        self._catalog: AospPermissionCatalog = catalog or AospPermissionCatalog()

    def extract(self, apk: APK, warnings: AnalysisWarningCollector | None = None) -> PermissionsInfo:
        self._catalog.set_fallback(dict(getattr(apk, "permission_module", {}) or {}))
        try:
            root = apk.get_android_manifest_xml()
        except Exception:
            root = None
        if root is None:
            if warnings is not None:
                warnings.add(
                    "The manifest is missing or corrupted: no permissions could be listed.",
                    AnalysisArea.PERMISSIONS,
                )
            return PermissionsInfo()

        resolver = ResourceReferenceResolver(apk)
        requested = self._requested(root)
        declared = self._declared(root, resolver)

        framework: list[Permission] = []
        app_ops: list[Permission] = []
        custom: dict[str, Permission] = {}
        for name, max_sdk in requested.items():
            entry = self._catalog.lookup(name)
            if name in declared:
                custom[name] = self._with_origin(declared[name], max_sdk, PermissionOrigin.DECLARED_AND_REQUESTED)
            elif entry is None:
                custom[name] = Permission(name, None, max_sdk=max_sdk)
            else:
                permission = Permission(
                    name=name,
                    protection=parse_protection_level(entry.get("protectionLevel")),
                    label=self._clean(entry.get("label")) or self._clean(entry.get("description")),
                    max_sdk=max_sdk,
                )
                (app_ops if permission.is_app_op else framework).append(permission)
        for name, permission in declared.items():
            custom.setdefault(name, permission)

        by_name = lambda permission: permission.name.lower()  # noqa: E731
        return PermissionsInfo(
            permissions=tuple(sorted(framework, key=by_name)),
            app_ops=tuple(sorted(app_ops, key=by_name)),
            custom_permissions=tuple(sorted(custom.values(), key=by_name)),
        )

    # --- Manifest ---------------------------------------------------------------------------

    @staticmethod
    def _requested(root: Any) -> dict[str, str | None]:
        """name -> maxSdkVersion, from every <uses-permission*> (also the -sdk-23 variants)."""
        requested: dict[str, str | None] = {}
        for node in root:
            tag = node.tag
            if not isinstance(tag, str) or not tag.startswith("uses-permission"):
                continue
            name = node.get(f"{ANDROID_NS}name")
            if name and name not in requested:
                requested[name] = node.get(f"{ANDROID_NS}maxSdkVersion") or None
        return requested

    def _declared(self, root: Any, resolver: ResourceReferenceResolver) -> dict[str, Permission]:
        """The permissions the app defines with <permission>."""
        declared: dict[str, Permission] = {}
        for node in root.iter("permission"):
            name = node.get(f"{ANDROID_NS}name")
            if not name:
                continue
            declared[name] = Permission(
                name=name,
                protection=parse_protection_level(node.get(f"{ANDROID_NS}protectionLevel")),
                label=self._text(node.get(f"{ANDROID_NS}label"), resolver)
                or self._text(node.get(f"{ANDROID_NS}description"), resolver),
                origin=PermissionOrigin.DECLARED,
            )
        return declared

    @staticmethod
    def _text(value: str | None, resolver: ResourceReferenceResolver) -> str | None:
        if not value:
            return None
        text = resolver.literal(value)
        return PermissionsExtractor._clean(text if text is not None else value)

    @staticmethod
    def _clean(text: Any) -> str | None:
        if not isinstance(text, str):
            return None
        collapsed = " ".join(text.split())
        return collapsed or None

    @staticmethod
    def _with_origin(permission: Permission, max_sdk: str | None, origin: PermissionOrigin) -> Permission:
        return Permission(
            permission.name, permission.protection, permission.label, max_sdk, origin,
        )
