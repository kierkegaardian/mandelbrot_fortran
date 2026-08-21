from __future__ import annotations

from datetime import datetime, timezone

def _parse_iso_utc(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso_day_utc(value: str) -> str:
    parsed = _parse_iso_utc(value)
    if parsed is None:
        return datetime.now(timezone.utc).date().isoformat()
    return parsed.date().isoformat()


def _sync_now_text() -> str:
    return datetime.now(timezone.utc).isoformat()
