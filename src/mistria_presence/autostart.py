"""Install/remove the optional per-user systemd unit."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

UNIT_NAME = "mistria-presence.service"
UNIT_CONTENT = """[Unit]
Description=Fields of Mistria Discord Rich Presence
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart=mistria-presence
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
"""


def unit_path() -> Path:
    return Path.home() / ".config/systemd/user" / UNIT_NAME


def set_enabled(enabled: bool, source: Path | None = None) -> bool:
    """Copy the packaged unit and ask systemd to enable it, if available."""
    systemctl = shutil.which("systemctl")
    if not systemctl:
        return False
    target = unit_path()
    if enabled:
        target.parent.mkdir(parents=True, exist_ok=True)
        content = source.read_text(encoding="utf-8") if source else UNIT_CONTENT
        target.write_text(content, encoding="utf-8")
        subprocess.run([systemctl, "--user", "daemon-reload"], check=False)
        return subprocess.run([systemctl, "--user", "enable", "--now", UNIT_NAME], check=False).returncode == 0
    subprocess.run([systemctl, "--user", "disable", "--now", UNIT_NAME], check=False)
    return True
