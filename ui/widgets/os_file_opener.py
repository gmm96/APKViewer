"""
Platform-specific "open this file with its default app" and "open this
file with... (native OS picker)" integrations.

Previously this logic lived inline inside `FilesContextMenu`, mixing OS
integration concerns with menu/UI concerns. It's extracted here as its own
Strategy hierarchy - the same shape as `utils.clipboard_service` - so the
context menu only has to depend on the `OsFileOpener` abstraction and can
be unit-tested with a fake one.
"""
import asyncio
import os
import subprocess
import sys
from abc import ABC, abstractmethod


class OsFileOpener(ABC):
    """Opens a file with its default application, or with an OS-native app picker."""

    @abstractmethod
    def open(self, path: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def open_with(self, path: str) -> None:
        """Show the OS's native 'Open with...' picker for a single file."""
        raise NotImplementedError


class WindowsFileOpener(OsFileOpener):
    def open(self, path: str) -> None:
        os.startfile(path)

    def open_with(self, path: str) -> None:
        import ctypes
        from ctypes import wintypes

        class OPENASINFO(ctypes.Structure):
            _fields_ = [
                ("pcszFile", wintypes.LPCWSTR),
                ("pcszClass", wintypes.LPCWSTR),
                ("oaifInFlags", wintypes.DWORD),
            ]

        OAIF_EXEC = 0x00000004
        OAIF_HIDE_REGISTRATION = 0x00000020

        info = OPENASINFO(path, None, OAIF_EXEC | OAIF_HIDE_REGISTRATION)

        shell32 = ctypes.WinDLL("shell32", use_last_error=True)
        shell32.SHOpenWithDialog.argtypes = [wintypes.HWND, ctypes.POINTER(OPENASINFO)]
        shell32.SHOpenWithDialog.restype = wintypes.HRESULT

        hr = shell32.SHOpenWithDialog(None, ctypes.byref(info))
        if hr != 0:
            raise OSError(f"SHOpenWithDialog failed with HRESULT 0x{hr & 0xffffffff:08X}")


class MacFileOpener(OsFileOpener):
    def open(self, path: str) -> None:
        subprocess.Popen(["open", path])

    def open_with(self, path: str) -> None:
        subprocess.Popen(["open", "-R", path])


class LinuxFileOpener(OsFileOpener):
    """Uses xdg-open for plain opens, and the freedesktop OpenURI portal
    (via dbus-next) to show the desktop's native 'Open with...' picker."""

    def open(self, path: str) -> None:
        subprocess.Popen(["xdg-open", path])

    def open_with(self, path: str) -> None:
        asyncio.run(self._open_with_portal(path))

    async def _open_with_portal(self, path: str) -> None:
        try:
            from dbus_next import Message, MessageType, Variant
            from dbus_next.aio import MessageBus
        except ImportError as exc:
            raise RuntimeError(
                "The Python package 'dbus-next' is required for Open With on Linux."
            ) from exc

        fd = os.open(path, os.O_RDONLY)
        try:
            bus = await MessageBus(negotiate_unix_fd=True).connect()
            try:
                message = Message(
                    destination="org.freedesktop.portal.Desktop",
                    path="/org/freedesktop/portal/desktop",
                    interface="org.freedesktop.portal.OpenURI",
                    member="OpenFile",
                    signature="sha{sv}",
                    body=["", 0, {"ask": Variant("b", True)}],
                    unix_fds=[fd],
                )
                reply = await bus.call(message)

                if reply.message_type == MessageType.ERROR:
                    raise RuntimeError(f"{reply.error_name}: {reply.body[0] if reply.body else ''}")
                if reply.message_type != MessageType.METHOD_RETURN:
                    raise RuntimeError(f"Unexpected D-Bus reply type: {reply.message_type}")
            finally:
                bus.disconnect()
        finally:
            os.close(fd)


class UnsupportedFileOpener(OsFileOpener):
    def open(self, path: str) -> None:
        raise RuntimeError(f"Opening files is not supported on platform: {sys.platform}")

    def open_with(self, path: str) -> None:
        raise RuntimeError(f"Open With is not supported on platform: {sys.platform}")


def default_os_file_opener() -> OsFileOpener:
    """Resolves the right `OsFileOpener` for the running platform."""
    if sys.platform == "win32":
        return WindowsFileOpener()
    if sys.platform == "darwin":
        return MacFileOpener()
    if sys.platform.startswith("linux"):
        return LinuxFileOpener()
    return UnsupportedFileOpener()
