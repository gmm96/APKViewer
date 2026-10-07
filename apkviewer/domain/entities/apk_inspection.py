"""
What an ApkInspector learns by looking inside an APK: everything except
the archive's file tree, which is obtained through a separate port.
"""

from dataclasses import dataclass

from apkviewer.domain.entities.analysis_warning import AnalysisWarning
from apkviewer.domain.entities.application_info import ApplicationInfo
from apkviewer.domain.entities.components import DeclaredComponents
from apkviewer.domain.entities.configuration_info import ConfigurationInfo
from apkviewer.domain.entities.embedded_content import EmbeddedContent
from apkviewer.domain.entities.permission import PermissionsInfo
from apkviewer.domain.entities.security_info import SecurityInfo
from apkviewer.domain.entities.third_party_info import ThirdPartyInfo


@dataclass(frozen=True)
class ApkInspection:
    application: ApplicationInfo
    configuration: ConfigurationInfo
    embedded_content: EmbeddedContent
    security: SecurityInfo
    permissions: PermissionsInfo
    third_party: ThirdPartyInfo
    components: DeclaredComponents
    icon_png: bytes | None
    manifest_xml: str
    warnings: tuple[AnalysisWarning, ...] = ()
