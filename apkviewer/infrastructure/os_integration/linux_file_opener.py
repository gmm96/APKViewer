"""
Linux implementation of OsFileOpener: xdg-open for plain opens, and the
freedesktop OpenURI portal (via dbus-next) to show the desktop's native
"Open with..." picker.
"""

import asyncio
import os
import subprocess

from apkviewer.domain.interfaces.os_file_opener import OsFileOpener


class LinuxFileOpener(OsFileOpener):
    def open(self, path: str) -> None:
        subprocess.Popen(["xdg-open", path])

    def open_with(self, path: str) -> None:
        asyncio.run(self._open_with_portal(path))

    async def _open_with_portal(self, path: str) -> None:
        try:
            from dbus_next.aio.message_bus import MessageBus
            from dbus_next.constants import MessageType
            from dbus_next.message import Message
            from dbus_next.signature import Variant
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
                if reply is None:
                    raise RuntimeError("No reply received from D-Bus call.")

                if reply.message_type == MessageType.ERROR:
                    raise RuntimeError(f"{reply.error_name}: {reply.body[0] if reply.body else ''}")
                if reply.message_type != MessageType.METHOD_RETURN:
                    raise RuntimeError(f"Unexpected D-Bus reply type: {reply.message_type}")
            finally:
                bus.disconnect()
        finally:
            os.close(fd)
