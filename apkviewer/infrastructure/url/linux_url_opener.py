"""
Linux UrlOpener: asks the desktop to open the URL through the freedesktop
OpenURI portal, identifying the application's window as the parent of the
request. That identification is what lets the desktop treat the launch as
the result of a user interaction and bring the browser to the foreground;
without it the browser is opened in the background.
"""

import asyncio

from apkviewer.domain.interfaces import UrlOpener, WindowHandleProvider

from .webbrowser_url_opener import WebBrowserUrlOpener


class LinuxUrlOpener(UrlOpener):
    def __init__(
        self,
        window_handle_provider: WindowHandleProvider | None = None,
        fallback: UrlOpener | None = None,
    ) -> None:
        self._window_handle_provider: WindowHandleProvider | None = window_handle_provider
        self._fallback: UrlOpener = fallback or WebBrowserUrlOpener()

    def open(self, url: str) -> None:
        parent_window = self._window_handle_provider.get_handle() if self._window_handle_provider else ""
        try:
            asyncio.run(self._open_with_portal(url, parent_window))
        except Exception:
            # Portal or dbus-next unavailable: degrade gracefully.
            self._fallback.open(url)

    @staticmethod
    async def _open_with_portal(url: str, parent_window: str) -> None:
        from dbus_next.aio.message_bus import MessageBus
        from dbus_next.constants import MessageType
        from dbus_next.message import Message

        bus = await MessageBus().connect()
        try:
            message = Message(
                destination="org.freedesktop.portal.Desktop",
                path="/org/freedesktop/portal/desktop",
                interface="org.freedesktop.portal.OpenURI",
                member="OpenURI",
                signature="ssa{sv}",
                body=[parent_window, url, {}],
            )
            reply = await bus.call(message)
            if reply is None:
                raise RuntimeError("No reply received from D-Bus call.")
            if reply.message_type == MessageType.ERROR:
                raise RuntimeError(f"{reply.error_name}: {reply.body[0] if reply.body else ''}")
        finally:
            bus.disconnect()
