from __future__ import annotations

import uuid

from ..models import Profile
from .connection import managed_connection

def list_profiles() -> list[Profile]:
    with managed_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, role FROM profiles WHERE sync_deleted = 0 ORDER BY role DESC, name ASC"
        ).fetchall()
    return [Profile(int(r["id"]), r["name"], r["role"]) for r in rows]


def create_profile(name: str, role: str, created_at: str) -> Profile:
    if role not in {"child", "parent"}:
        raise ValueError("role must be 'child' or 'parent'")
    sync_id = str(uuid.uuid4())
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO profiles (name, role, created_at, sync_id, sync_updated_at, sync_deleted)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (name, role, created_at, sync_id, created_at),
        )
        profile_id = int(cur.lastrowid)
    return Profile(profile_id, name, role)


def delete_profile(profile_id: int) -> None:
    with managed_connection() as conn:
        conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
