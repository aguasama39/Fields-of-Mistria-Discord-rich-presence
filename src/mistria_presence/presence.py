"""Discord payload generation, independent of the transport."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from .config import Settings


@dataclass(frozen=True)
class PresenceSnapshot:
    started_at: int | None = None


def build_payload(settings: Settings, snapshot: PresenceSnapshot | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "details": settings.details or settings.display_text,
        "state": settings.state,
        "assets": {},
    }
    if settings.show_timestamps:
        payload["timestamps"] = {"start": (snapshot or PresenceSnapshot(int(time.time()))).started_at}
    if settings.large_image:
        payload["assets"]["large_image"] = settings.large_image
        payload["assets"]["large_text"] = settings.large_text
    if settings.small_image:
        payload["assets"]["small_image"] = settings.small_image
        payload["assets"]["small_text"] = settings.small_text
    if settings.show_party:
        payload["party"] = {"size": [settings.party_size, settings.party_max]}
    return payload
