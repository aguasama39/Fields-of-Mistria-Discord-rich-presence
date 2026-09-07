"""Steam process and library detection for Linux."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

APP_ID = "2142790"


@dataclass(frozen=True)
class GameStatus:
    running: bool
    install_path: Path | None = None
    process: str | None = None
    message: str = "Game not detected"


def _steam_roots(home: Path) -> list[Path]:
    roots = [home / ".local/share/Steam", home / ".steam/steam", home / ".steam/steam"]
    return list(dict.fromkeys(roots))


def _library_paths(home: Path) -> list[Path]:
    result: list[Path] = []
    for root in _steam_roots(home):
        result.append(root / "steamapps")
        manifest = root / "steamapps/libraryfolders.vdf"
        if manifest.exists():
            text = manifest.read_text(encoding="utf-8", errors="replace")
            for match in re.finditer(r'"path"\s+"([^"]+)"', text):
                result.append(Path(match.group(1)) / "steamapps")
    return list(dict.fromkeys(result))


def find_install(home: Path | None = None) -> Path | None:
    home = home or Path.home()
    for steamapps in _library_paths(home):
        manifest = steamapps / f"appmanifest_{APP_ID}.acf"
        if manifest.exists():
            install = steamapps / "common" / "Fields of Mistria"
            if install.is_dir():
                return install
    return None


def is_running(executable: str = "FieldsOfMistria.x86_64") -> bool:
    """Use pgrep when available; failure means safely not running."""
    try:
        result = subprocess.run(["pgrep", "-x", executable], capture_output=True, text=True, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def detect(executable: str = "FieldsOfMistria.x86_64", home: Path | None = None) -> GameStatus:
    install = find_install(home)
    running = is_running(executable)
    if running:
        return GameStatus(True, install, executable, "Fields of Mistria is running")
    if install:
        return GameStatus(False, install, message="Game installed, but not running")
    return GameStatus(False, message="Steam game not found")
