"""Persistent, backwards-compatible configuration."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

DEFAULT_CLIENT_ID = "1267820993756624936"


@dataclass
class Settings:
    enabled: bool = True
    client_id: str = DEFAULT_CLIENT_ID
    display_text: str = "Fields of Mistria"
    details: str = "Exploring Mistria"
    state: str = "Adventuring"
    show_timestamps: bool = True
    show_party: bool = False
    party_size: int = 1
    party_max: int = 4
    large_image: str = "mistria"
    large_text: str = "Fields of Mistria"
    small_image: str = "steam"
    small_text: str = "Playing on Steam"
    auto_detect: bool = True
    game_executable: str = "FieldsOfMistria.x86_64"
    launch_at_login: bool = False
    close_to_tray: bool = True


def config_path(env: dict[str, str] | None = None) -> Path:
    env = os.environ if env is None else env
    base = env.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(base) / "mistria-presence" / "settings.json"


def load_settings(path: Path | None = None) -> Settings:
    target = path or config_path()
    try:
        data: dict[str, Any] = json.loads(target.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return Settings()
    allowed = {field.name for field in fields(Settings)}
    values = {key: value for key, value in data.items() if key in allowed}
    try:
        return Settings(**values)
    except (TypeError, ValueError):
        return Settings()


def save_settings(settings: Settings, path: Path | None = None) -> Path:
    target = path or config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="settings.", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(asdict(settings), stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target
