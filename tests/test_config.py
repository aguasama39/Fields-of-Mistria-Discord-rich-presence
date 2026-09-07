from pathlib import Path

from mistria_presence.config import Settings, load_settings, save_settings


def test_settings_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    expected = Settings(details="Fishing", show_party=True, party_size=2)
    save_settings(expected, path)
    assert load_settings(path) == expected


def test_invalid_config_uses_defaults(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("not json", encoding="utf-8")
    assert load_settings(path) == Settings()
