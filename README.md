# Mistria Presence

Linux-only Discord Rich Presence for the Steam release of **Fields of Mistria**. It is a native Python GTK4/libadwaita settings application with a small, replaceable Steam detector and Discord local IPC transport. Windows and macOS are intentionally not supported.

## Prerequisites

- Linux with Python 3.11 or newer
- GTK 4 and libadwaita 1 introspection bindings
- A running Discord desktop client for live presence
- Steam and the Linux version of Fields of Mistria for automatic detection

On Debian/Ubuntu, install the system bindings with:

```sh
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
```

Some desktop environments need `libayatana-appindicator3` if you add an AppIndicator frontend. The current build keeps the process alive when its window is closed; this is the most portable Linux background behavior, while desktop shells may show it in their application list.

## Setup and Development

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

Run checks:

```sh
pytest
ruff check .
mypy src
```

The core modules do not require GTK, so tests run headlessly. `MemoryTransport` is provided for tests and development without Discord IPC.

## Running

```sh
mistria-presence
# or
python -m mistria_presence
```

Settings are stored atomically at `$XDG_CONFIG_HOME/mistria-presence/settings.json`, or `~/.config/mistria-presence/settings.json` when `XDG_CONFIG_HOME` is not set. The default Discord application ID is a placeholder application; use your own application ID and configure matching image keys in the Discord Developer Portal.

The detector checks the standard Linux Steam library locations, follows `libraryfolders.vdf`, verifies app ID `2142790`, and checks the configured executable with `pgrep`. If Steam is installed elsewhere, disable automatic detection and set the executable field manually. A missing process, Steam installation, or Discord IPC socket is reported in the status rows and never crashes the background process.

## Background and Login

Closing the window hides it when **Keep running when closed** is enabled. The process continues polling and clears activity when the game exits. The **Launch at login** setting installs and enables `data/mistria-presence.service` as a per-user systemd unit when `systemctl --user` is available. It can also be installed manually:

```sh
mkdir -p ~/.config/systemd/user
cp data/mistria-presence.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now mistria-presence.service
```

## Packaging and Installation

Build a wheel or source archive:

```sh
python -m pip install build
python -m build
```

For a local desktop install, install the package into a virtual environment and copy the desktop file to `~/.local/share/applications/`:

```sh
python -m pip install .
mkdir -p ~/.local/share/applications
cp data/io.github.mistriapresence.App.desktop ~/.local/share/applications/
```

Distribution packages should place the executable on `PATH`, the desktop file in `/usr/share/applications/`, the metainfo file in `/usr/share/metainfo/`, and the service template in `/usr/lib/systemd/user/`. No Windows or macOS packaging is provided.

## Troubleshooting

- **Discord disconnected:** start the official Discord Linux client. Flatpak Discord may expose IPC differently; verify `XDG_RUNTIME_DIR` and the `discord-ipc-*` sockets.
- **Game not found:** launch once through Steam, verify the app ID and library folder, or turn off automatic detection and change the executable name.
- **Presence not visible:** confirm the client ID and Developer Portal assets, and enable activity status in Discord.
- **No window on a server:** install GTK4/libadwaita introspection packages and run from a terminal to see the dependency error.
