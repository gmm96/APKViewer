"""
Composition root: the ONLY module that knows every layer.

It picks a concrete implementation for each port and injects them into
the application use cases and the front end. Replacing a layer (another
APK parser, another GUI toolkit, another storage) means changing this
file and nothing else.
"""

import tkinter as tk

from apkviewer.application.analyze_apk import AnalyzeApk
from apkviewer.application.entry_previewer import EntryPreviewer
from apkviewer.application.export_app_info import ExportAppInfo
from apkviewer.application.export_icon import ExportIcon
from apkviewer.application.extract_apk_entries import ExtractApkEntries
from apkviewer.infrastructure.androguard.androguard_apk_inspector import AndroguardApkInspector
from apkviewer.infrastructure.filesystem.local_file_writer import LocalFileWriter
from apkviewer.infrastructure.filesystem.temp_directory_workspace import TempDirectoryWorkspace
from apkviewer.infrastructure.platforms.platform_services_resolver import PlatformServicesResolver
from apkviewer.infrastructure.zip.zip_apk_extractor import ZipApkExtractor
from apkviewer.infrastructure.zip.zip_archive_reader import ZipArchiveReader
from apkviewer.presentation.app import ApkAnalyzerApp


def build_app(root: tk.Tk) -> ApkAnalyzerApp:
    platform_services = PlatformServicesResolver().resolve()
    apk_extractor = ZipApkExtractor()
    file_writer = LocalFileWriter()

    return ApkAnalyzerApp(
        root,
        analyze_apk=AnalyzeApk(AndroguardApkInspector(), ZipArchiveReader()),
        extract_entries=ExtractApkEntries(apk_extractor),
        entry_previewer=EntryPreviewer(
            extractor=apk_extractor,
            workspace=TempDirectoryWorkspace(),
            file_opener=platform_services.create_os_file_opener(),
            clipboard_copier=platform_services.create_clipboard_file_copier(),
        ),
        export_app_info=ExportAppInfo(file_writer),
        export_icon=ExportIcon(file_writer),
        url_opener=platform_services.create_url_opener(),
    )
