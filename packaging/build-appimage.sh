#!/bin/sh
set -eu

# Build from a Linux system that has the GTK development packages installed.
# Tools are downloaded into .cache/appimage-tools and never installed globally.

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BUILD_DIR="${APPIMAGE_BUILD_DIR:-$ROOT/.build/appimage}"
CACHE_DIR="${APPIMAGE_CACHE_DIR:-$ROOT/.cache/appimage-tools}"
DIST_DIR="${APPIMAGE_DIST_DIR:-$ROOT/dist}"
LINUXDEPLOY_VERSION="${LINUXDEPLOY_VERSION:-1-alpha-20251107-1}"
APPIMAGETOOL_VERSION="${APPIMAGETOOL_VERSION:-1.9.1}"

die() {
    printf '%s\n' "build-appimage: $*" >&2
    exit 1
}

command -v python3 >/dev/null 2>&1 || die "python3 is required"
command -v gcc >/dev/null 2>&1 || die "gcc is required to discover GTK runtime libraries"
command -v pkg-config >/dev/null 2>&1 || die "pkg-config is required"
pkg-config --exists gtk4 libadwaita-1 || die "GTK4/libadwaita development packages are required"

VERSION=$(python3 -c 'import re; text=open("pyproject.toml", encoding="utf-8").read(); print(re.search(r"^version = \"([^\"]+)\"", text, re.M).group(1))' < "$ROOT/pyproject.toml")
ARCH=$(uname -m)
[ "$ARCH" = x86_64 ] || die "only x86_64 AppImages are currently supported"

mkdir -p "$CACHE_DIR" "$BUILD_DIR" "$DIST_DIR"

download_tool() {
    name=$1
    url=$2
    destination="$CACHE_DIR/$name"
    if [ ! -x "$destination" ]; then
        command -v curl >/dev/null 2>&1 || die "curl is required to download build tools"
        curl --fail --location --retry 3 --output "$destination.tmp" "$url"
        mv "$destination.tmp" "$destination"
        chmod +x "$destination"
    fi
    printf '%s\n' "$destination"
}

LINUXDEPLOY=$(download_tool linuxdeploy-x86_64 "https://github.com/linuxdeploy/linuxdeploy/releases/download/$LINUXDEPLOY_VERSION/linuxdeploy-x86_64.AppImage")
APPIMAGETOOL=$(download_tool appimagetool-x86_64 "https://github.com/AppImage/appimagetool/releases/download/$APPIMAGETOOL_VERSION/appimagetool-x86_64.AppImage")

rm -rf "$BUILD_DIR/AppDir"
APPDIR="$BUILD_DIR/AppDir"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib/python3/site-packages" "$APPDIR/usr/share/applications" \
    "$APPDIR/usr/share/metainfo" "$APPDIR/usr/share/icons/hicolor" "$APPDIR/usr/lib/girepository-1.0"

cp "$ROOT/packaging/AppRun" "$APPDIR/AppRun"
cp "$ROOT/packaging/mistria-presence" "$APPDIR/usr/bin/mistria-presence"
cp "$ROOT/data/io.github.mistriapresence.App.desktop" "$APPDIR/usr/share/applications/"
cp "$ROOT/data/io.github.mistriapresence.App.metainfo.xml" "$APPDIR/usr/share/metainfo/"
cp -a "$ROOT/data/icons/hicolor/." "$APPDIR/usr/share/icons/hicolor/"
cp -a "$ROOT/src/mistria_presence" "$APPDIR/usr/lib/python3/site-packages/"
chmod +x "$APPDIR/AppRun" "$APPDIR/usr/bin/mistria-presence"

# Copy the exact Python installation used for the build. linuxdeploy then finds
# its ELF dependencies, while the wrapper makes the interpreter relocatable.
PYTHON_BIN=$(command -v python3)
PYTHON_PREFIX=$(python3 -c 'import sys; print(sys.prefix)')
PYTHON_VERSION=$(python3 -c 'import sys; print(f"python{sys.version_info.major}.{sys.version_info.minor}")')
cp "$PYTHON_BIN" "$APPDIR/usr/bin/python3"
cp -a "$PYTHON_PREFIX/lib/$PYTHON_VERSION" "$APPDIR/usr/lib/"

GI_DIR=$(python3 -c 'import gi, pathlib; print(pathlib.Path(gi.__file__).parent)')
cp -a "$GI_DIR" "$APPDIR/usr/lib/python3/dist-packages"

for typelib_dir in /usr/lib/*/girepository-1.0 /usr/lib/girepository-1.0; do
    if [ -d "$typelib_dir" ]; then
        cp -a "$typelib_dir"/*.typelib "$APPDIR/usr/lib/girepository-1.0/" 2>/dev/null || true
    fi
done

# A tiny GTK-linked ELF gives linuxdeploy a complete dependency graph even
# though PyGObject loads GTK lazily at runtime.
gcc "$ROOT/packaging/gtk-probe.c" -o "$BUILD_DIR/gtk-probe" $(pkg-config --cflags --libs gtk4 libadwaita-1)
APPIMAGE_EXTRACT_AND_RUN=1 "$LINUXDEPLOY" --appdir "$APPDIR" --executable "$APPDIR/usr/bin/python3" --executable "$BUILD_DIR/gtk-probe" --desktop-file "$APPDIR/usr/share/applications/io.github.mistriapresence.App.desktop"
rm -f "$APPDIR/usr/bin/gtk-probe"

OUTPUT="$DIST_DIR/mistria-presence-$VERSION-$ARCH.AppImage"
rm -f "$OUTPUT"
APPIMAGE_EXTRACT_AND_RUN=1 ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$OUTPUT"
chmod +x "$OUTPUT"
printf '%s\n' "Built $OUTPUT"
