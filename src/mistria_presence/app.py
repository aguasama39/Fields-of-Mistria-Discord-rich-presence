"""GTK4/libadwaita settings application."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any

from .config import Settings, load_settings, save_settings
from .detection import detect
from .autostart import set_enabled
from .presence import PresenceSnapshot, build_payload
from .transport import DiscordIPC, PresenceTransport

try:
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, GLib, Gtk
except (ImportError, ValueError):  # Allows config/detection use on headless machines.
    Adw = GLib = Gtk = None  # type: ignore[assignment]


class PresenceController:
    def __init__(self, settings: Settings | None = None, transport: PresenceTransport | None = None) -> None:
        self.settings = settings or load_settings()
        self.transport = transport or DiscordIPC()
        self.snapshot = PresenceSnapshot()
        self.connected = False
        self.game_running = False

    def refresh(self) -> str:
        status = detect(self.settings.game_executable)
        self.game_running = status.running
        if not self.settings.enabled or not status.running:
            self.snapshot = PresenceSnapshot()
            if self.connected:
                self.transport.clear()
            return "Disabled" if not self.settings.enabled else status.message
        try:
            if self.snapshot.started_at is None:
                self.snapshot = PresenceSnapshot(int(time.time()))
            if not self.connected:
                self.transport.connect(self.settings.client_id)
                self.connected = True
            self.transport.set_activity(build_payload(self.settings, self.snapshot))
            return "Connected to Discord"
        except (ConnectionError, OSError, TimeoutError) as error:
            self.connected = False
            return str(error)

    def save(self) -> None:
        save_settings(self.settings)


if Gtk is not None:

    class Window(Adw.ApplicationWindow):  # type: ignore[misc]
        def __init__(self, application: Any, controller: PresenceController) -> None:
            super().__init__(application=application, title="Mistria Presence", default_width=620, default_height=700)
            self.controller = controller
            self.widgets: dict[str, Gtk.Widget] = {}
            self.set_content(self._build())
            self._refresh()

        def _build(self) -> Gtk.Widget:
            page = Adw.PreferencesPage()
            page.set_margin_top(18)
            page.set_margin_bottom(18)
            page.set_margin_start(18)
            page.set_margin_end(18)

            overview = Adw.PreferencesGroup(title="Overview", description="Linux Steam detection and Discord connection")
            self.status = Adw.ActionRow(title="Discord", subtitle="Checking local IPC")
            self.game_status = Adw.ActionRow(title="Game", subtitle="Checking Steam")
            for row in (self.status, self.game_status):
                row.add_prefix(Gtk.Label(label="●"))
                overview.add(row)
            page.add(overview)

            presence = Adw.PreferencesGroup(title="Rich Presence")
            self._switch(presence, "enabled", "Enable Rich Presence", "Send activity while the game is running")
            self._entry(presence, "client_id", "Application ID", "Discord developer application client ID")
            self._entry(presence, "display_text", "Display name", "Shown by Discord in your profile")
            self._entry(presence, "details", "Details", "What are you doing?")
            self._entry(presence, "state", "State", "A short status line")
            page.add(presence)

            appearance = Adw.PreferencesGroup(title="Timestamps and Assets")
            self._switch(appearance, "show_timestamps", "Show elapsed time", "Include a session start timestamp")
            self._switch(appearance, "show_party", "Show party size", "Include party size in the activity")
            self._entry(appearance, "party_size", "Party size", "Current players")
            self._entry(appearance, "party_max", "Party maximum", "Maximum players")
            self._entry(appearance, "large_image", "Large image key", "Asset key configured in Discord")
            self._entry(appearance, "large_text", "Large image tooltip", "Tooltip for the large image")
            self._entry(appearance, "small_image", "Small image key", "Optional asset key")
            self._entry(appearance, "small_text", "Small image tooltip", "Tooltip for the small image")
            page.add(appearance)

            system = Adw.PreferencesGroup(title="System")
            self._switch(system, "auto_detect", "Detect Steam game automatically", "Use the Linux Steam library and process list")
            self._entry(system, "game_executable", "Game executable", "Change this for a custom launch")
            self._switch(system, "launch_at_login", "Launch at login", "Managed through the included user service")
            self._switch(system, "close_to_tray", "Keep running when closed", "Continue background detection after closing this window")
            page.add(system)

            save = Gtk.Button(label="Save settings")
            save.add_css_class("suggested-action")
            save.set_margin_top(12)
            save.connect("clicked", lambda _button: self._save())
            save_group = Adw.PreferencesGroup()
            save_group.add(save)
            page.add(save_group)
            return page

        def _entry(self, group: Any, name: str, title: str, subtitle: str) -> None:
            row = Adw.EntryRow(title=title)
            row.set_text(str(getattr(self.controller.settings, name)))
            row.set_tooltip_text(subtitle)
            def update(entry: Any) -> None:
                value: Any = entry.get_text()
                if isinstance(getattr(self.controller.settings, name), int):
                    try:
                        value = max(0, int(value))
                    except ValueError:
                        return
                setattr(self.controller.settings, name, value)
            row.connect("changed", update)
            group.add(row)
            self.widgets[name] = row

        def _switch(self, group: Any, name: str, title: str, subtitle: str) -> None:
            row = Adw.SwitchRow(title=title, subtitle=subtitle, active=getattr(self.controller.settings, name))
            row.connect("notify::active", lambda switch, _param: setattr(self.controller.settings, name, switch.get_active()))
            group.add(row)
            self.widgets[name] = row

        def _save(self) -> None:
            self.controller.save()
            unit = Path(__file__).resolve().parents[2] / "data/mistria-presence.service"
            set_enabled(self.controller.settings.launch_at_login, unit if unit.exists() else None)
            self._refresh()

        def _refresh(self) -> bool:
            message = self.controller.refresh()
            self.status.set_subtitle(message)
            self.game_status.set_subtitle("Running" if self.controller.game_running else "Not running")
            return True

        def close_request(self) -> bool:
            if self.controller.settings.close_to_tray:
                self.hide()
                return True
            return False


    class Application(Adw.Application):  # type: ignore[misc]
        def __init__(self) -> None:
            super().__init__(application_id="io.github.mistriapresence.App")
            self.controller = PresenceController()
            self.window: Window | None = None
            self.hold()

        def do_activate(self) -> None:
            if self.window is None:
                self.window = Window(self, self.controller)
                self.window.connect("close-request", lambda window: window.close_request())
            self.window.present()
            GLib.timeout_add_seconds(15, self.window._refresh)


def main() -> int:
    if Gtk is None:
        raise SystemExit("GTK4/libadwaita is required. See README.md for Linux prerequisites.")
    return Application().run(None)
