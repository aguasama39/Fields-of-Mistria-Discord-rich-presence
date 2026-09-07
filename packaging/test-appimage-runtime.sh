#!/bin/sh
set -eu

APPIMAGE=${1:?usage: test-appimage-runtime.sh PATH_TO_APPIMAGE}
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
EXTRACT_DIR=$(mktemp -d "${TMPDIR:-/tmp}/mistria-presence-smoke.XXXXXX")
trap 'rm -rf "$EXTRACT_DIR"' EXIT

cd "$EXTRACT_DIR"
APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGE" --appimage-extract >/dev/null
APPDIR="$EXTRACT_DIR/squashfs-root"

# Run the same isolated interpreter setup as the application wrapper. This
# specifically catches missing stdlib modules before GTK starts a display.
export PYTHONHOME="$APPDIR/usr"
export PYTHONNOUSERSITE=1
export PYTHONPATH="$APPDIR/usr/lib/python3/site-packages"
export GI_TYPELIB_PATH="$APPDIR/usr/lib/girepository-1.0"
export LD_LIBRARY_PATH="$APPDIR/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$APPDIR/usr/bin/python3" -S -c \
    'import threading, functools, types; import gi; gi.require_version("Gtk", "4.0"); gi.require_version("Adw", "1"); from gi.repository import Gtk, Adw'
printf '%s\n' 'AppImage Python/GTK startup smoke test passed'
