"""Atomic profile mutations paired with sync outbox entries."""

from __future__ import annotations

import uuid

from . import db
from .db.profiles import _ensure_profile_deletable
from .models import Profile
from .sync_store import enqueue_change_on, soft_delete_entity_on


def create_profile(name: str, role: str, created_at: str) -> Profile:
    if role not in {"child", "parent"}:
        raise ValueError("role must be 'child' or 'parent'")
    sync_id = str(uuid.uuid4())
    with db.managed_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO profiles
            (name, role, created_at, sync_id, sync_updated_at, sync_deleted)
            VALUES (?, ?, ?, ?, ?, 0)""",
            (name, role, created_at, sync_id, created_at),
        )
        profile_id = int(cursor.lastrowid)
        enqueue_change_on(
            conn,
            entity_type="profiles",
            local_id=profile_id,
            action="upsert",
            occurred_at=created_at,
            extra={"name": name, "role": role},
            known_sync_id=sync_id,
        )
    return Profile(profile_id, name, role)


def delete_profile(profile_id: int, deleted_at: str) -> None:
    with db.managed_connection() as conn:
        _ensure_profile_deletable(conn, profile_id)
        targets = _profile_delete_targets(conn, profile_id)
        for entity_type, local_id, sync_id in targets:
            soft_delete_entity_on(
                conn,
                entity_type=entity_type,
                local_id=local_id,
                entity_sync_id=sync_id,
                deleted_at=deleted_at,
            )


def _profile_delete_targets(
    conn, profile_id: int
) -> list[tuple[str, int, str]]:
    question_rows = conn.execute(
        """SELECT qq.id, qq.sync_id FROM quiz_questions qq
        JOIN quiz_attempts qa ON qa.id = qq.attempt_id
        WHERE qa.profile_id = ? AND qq.sync_deleted = 0 AND qa.sync_deleted = 0
        ORDER BY qq.id""",
        (int(profile_id),),
    ).fetchall()
    targets = [
        ("quiz_questions", int(row["id"]), str(row["sync_id"]))
        for row in question_rows
        if row["sync_id"]
    ]
    for entity_type, table in (
        ("quiz_attempts", "quiz_attempts"),
        ("assignments", "assignments"),
        ("profiles", "profiles"),
    ):
        rows = conn.execute(
            f"SELECT id, sync_id FROM {table} "
            "WHERE id = ? AND sync_deleted = 0"
            if table == "profiles"
            else f"SELECT id, sync_id FROM {table} "
            "WHERE profile_id = ? AND sync_deleted = 0 ORDER BY id",
            (int(profile_id),),
        ).fetchall()
        targets.extend(
            (entity_type, int(row["id"]), str(row["sync_id"]))
            for row in rows
            if row["sync_id"]
        )
    return targets
