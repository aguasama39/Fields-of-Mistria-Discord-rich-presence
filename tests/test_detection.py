from pathlib import Path

from mistria_presence.detection import APP_ID, find_install


def test_find_install_in_primary_library(tmp_path: Path) -> None:
    steam = tmp_path / ".local/share/Steam/steamapps"
    install = steam / "common/Fields of Mistria"
    install.mkdir(parents=True)
    (steam / f"appmanifest_{APP_ID}.acf").write_text('"appid" "2142790"', encoding="utf-8")
    assert find_install(tmp_path) == install


def test_missing_steam_is_safe(tmp_path: Path) -> None:
    assert find_install(tmp_path) is None
