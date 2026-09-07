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

## AppImage

The repository includes a self-contained x86_64 AppImage build. It uses the
system GTK/libadwaita development files only while building, bundles the
Python interpreter, PyGObject, GTK libraries, typelibs, application launcher,
desktop file, metainfo, and icon, and downloads its build tools into the
repository cache rather than installing them system-wide.

### Build prerequisites

On Debian/Ubuntu, install the build prerequisites once:

```sh
sudo apt install gcc curl pkg-config python3 python3-gi \
  gir1.2-gtk-4.0 gir1.2-adw-1 libgtk-4-dev libadwaita-1-dev
```

The builder currently targets x86_64 Linux. `linuxdeploy` and `appimagetool`
are pinned/downloaded by the script; set `APPIMAGE_CACHE_DIR` to reuse a
cache outside the checkout if desired.

### Build and run

```sh
./packaging/build-appimage.sh
./dist/mistria-presence-0.1.0-x86_64.AppImage
```

The versioned file is written to `dist/`, which is ignored by Git. It can be
moved anywhere and does not need installation or execute permissions beyond
the executable bit created by the build. The AppImage still needs a graphical
Linux session, a running Discord desktop client, and Steam for automatic game
detection.

### Desktop integration

AppImages do not register applications automatically. AppImageLauncher or
`appimaged` can integrate the desktop file when the AppImage is placed in a
watched applications directory. For a manual per-user install, extract the
metadata and copy it into the standard XDG locations:

```sh
./dist/mistria-presence-0.1.0-x86_64.AppImage --appimage-extract
mkdir -p ~/.local/share/applications ~/.local/share/metainfo ~/.local/share/icons/hicolor/scalable/apps
cp squashfs-root/usr/share/applications/io.github.mistriapresence.App.desktop ~/.local/share/applications/
cp squashfs-root/usr/share/metainfo/io.github.mistriapresence.App.metainfo.xml ~/.local/share/metainfo/
cp squashfs-root/usr/share/icons/hicolor/scalable/apps/io.github.mistriapresence.App.svg ~/.local/share/icons/hicolor/scalable/apps/
mkdir -p ~/.local/bin
ln -sf "$(realpath ./dist/mistria-presence-0.1.0-x86_64.AppImage)" ~/.local/bin/mistria-presence
rm -rf squashfs-root
```

Ensure `~/.local/bin` is on `PATH` for the desktop shell. The symlink makes
the extracted desktop entry's `Exec=mistria-presence` resolve to the AppImage;
AppImageLauncher and `appimaged` handle this integration automatically.

The AppImage does not install the systemd user service automatically. Login
autostart can be configured by creating a user unit whose `ExecStart` points
to the absolute path of the AppImage. The bundled service template remains
available for normal source/package installations.

### Known limitations

- Builds are currently x86_64-only and should be built on a Linux distribution
  no newer than the oldest distribution intended to run the AppImage.
- GTK and libadwaita are bundled, but graphics drivers, a desktop session,
  Discord IPC, Steam, and the game remain host-provided dependencies.
- A system with FUSE unavailable can usually run the file with
  `APPIMAGE_EXTRACT_AND_RUN=1`; desktop integration tools may still require
  normal AppImage mounting support.

## Troubleshooting

- **Discord disconnected:** start the official Discord Linux client. Flatpak Discord may expose IPC differently; verify `XDG_RUNTIME_DIR` and the `discord-ipc-*` sockets.
- **Game not found:** launch once through Steam, verify the app ID and library folder, or turn off automatic detection and change the executable name.
- **Presence not visible:** confirm the client ID and Developer Portal assets, and enable activity status in Discord.
- **No window on a server:** install GTK4/libadwaita introspection packages and run from a terminal to see the dependency error.
