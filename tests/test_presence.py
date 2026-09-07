from mistria_presence.config import Settings
from mistria_presence.presence import PresenceSnapshot, build_payload


def test_payload_contains_configured_sections() -> None:
    settings = Settings(show_party=True, party_size=2, party_max=4)
    payload = build_payload(settings, PresenceSnapshot(123))
    assert payload["details"] == settings.details
    assert payload["timestamps"] == {"start": 123}
    assert payload["party"] == {"size": [2, 4]}
    assert payload["assets"]["large_image"] == "mistria"


def test_payload_can_omit_optional_values() -> None:
    settings = Settings(show_timestamps=False, show_party=False, large_image="", small_image="")
    payload = build_payload(settings)
    assert "timestamps" not in payload
    assert "party" not in payload
    assert payload["assets"] == {}
