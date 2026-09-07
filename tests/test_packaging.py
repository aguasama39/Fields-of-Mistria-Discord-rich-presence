from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_arch_package_declares_runtime_assets() -> None:
    pkgbuild = (ROOT / "aur/PKGBUILD").read_text(encoding="utf-8")

    for dependency in ("python>=3.10", "gtk4", "libadwaita", "python-gobject"):
        assert dependency in pkgbuild
    for asset in (
        "io.github.mistriapresence.App.desktop",
        "io.github.mistriapresence.App.metainfo.xml",
        "data/icons/hicolor/${size}x${size}/apps/io.github.mistriapresence.App.png",
        "mistria-presence.service",
    ):
        assert asset in pkgbuild


def test_arch_launcher_does_not_enable_services() -> None:
    pkgbuild = (ROOT / "aur/PKGBUILD").read_text(encoding="utf-8")

    assert "systemctl enable" not in pkgbuild
    assert "PYTHONPATH=/usr/lib/mistria-presence" in pkgbuild


def test_binary_arch_package_uses_published_appimage() -> None:
    package_dir = ROOT / "aur-bin"
    pkgbuild = (package_dir / "PKGBUILD").read_text(encoding="utf-8")

    assert "pkgname=mistria-presence-bin" in pkgbuild
    assert "pkgver=0.1.1" in pkgbuild
    assert "arch=('x86_64')" in pkgbuild
    assert "https://github.com/aguasama39/Fields-of-Mistria-Discord-rich-presence/releases/download/v0.1.1/mistria-presence-0.1.0-x86_64.AppImage" in pkgbuild
    assert "0010461dd73b1cdfce3a771c6636b1ef4fd76dacd99dc2e6db444aaf79e6abaf" in pkgbuild
    assert "python -m" not in pkgbuild
    assert "python-build" not in pkgbuild
    assert "python-setuptools" not in pkgbuild
    assert "${startdir}/" in pkgbuild


def test_binary_arch_package_installs_runtime_integration() -> None:
    package_dir = ROOT / "aur-bin"
    pkgbuild = (package_dir / "PKGBUILD").read_text(encoding="utf-8")

    for asset in (
        "mistria-presence",
        "io.github.mistriapresence.App.desktop",
        "io.github.mistriapresence.App.metainfo.xml",
        "mistria-presence.service",
    ):
        assert asset in pkgbuild
        if asset == "mistria-presence":
            assert (package_dir / asset).is_file()

    assert 'for size in 16 32 48 64 128 256; do' in pkgbuild
    for size in (16, 32, 48, 64, 128, 256):
        assert (package_dir / f"icons/hicolor/{size}x{size}/apps/io.github.mistriapresence.App.png").is_file()

    launcher = (package_dir / "mistria-presence").read_text(encoding="utf-8")
    assert "exec /opt/mistria-presence/mistria-presence-0.1.0-x86_64.AppImage \"$@\"" in launcher
    assert "systemctl enable" not in pkgbuild
