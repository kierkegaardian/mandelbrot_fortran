"""Parent-role validation shared by Family Sync service operations."""

from __future__ import annotations

from . import db


def is_parent_profile(profile_id: int | None) -> bool:
    if profile_id is None:
        return False
    return any(
        item.id == int(profile_id) and item.role == "parent"
        for item in db.list_profiles()
    )
