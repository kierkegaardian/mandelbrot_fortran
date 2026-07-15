"""Validation, lookup, and delete helpers for remote sync apply."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from .sync_tombstones import deleted_at_for, record_tombstone_on

ENTITY_ORDER = (
    "profiles",
    "quiz_sets",
    "assignments",
    "quiz_attempts",
    "quiz_questions",
)
DEPENDENCY_ACTIVE = "active"
DEPENDENCY_DELETED = "deleted"
DEPENDENCY_MISSING = "missing"


def apply_delete(
    conn: sqlite3.Connection,
    entity_type: str,
    sync_id: str,
    updated_at: str,
) -> str:
    table = table_for(entity_type)
    row = conn.execute(
        f"SELECT id, sync_updated_at FROM {table} WHERE sync_id = ?", (sync_id,)
    ).fetchone()
    tombstone_at = deleted_at_for(conn, entity_type, sync_id)
    if tombstone_at and not is_newer(updated_at, tombstone_at):
        return "stale"
    if row is not None and is_newer(str(row["sync_updated_at"] or ""), updated_at):
        return "stale"
    if row is not None:
        conn.execute(
            f"UPDATE {table} SET sync_deleted = 1, sync_updated_at = ? WHERE id = ?",
            (updated_at, int(row["id"])),
        )
    record_tombstone_on(
        conn,
        entity_type=entity_type,
        entity_sync_id=sync_id,
        deleted_at=updated_at,
    )
    return "applied"


def lookup_dependency(
    conn: sqlite3.Connection, table: str, sync_id: str | None
) -> tuple[str, int | None]:
    if not sync_id:
        return DEPENDENCY_MISSING, None
    row = conn.execute(
        f"SELECT id, sync_deleted FROM {table} WHERE sync_id = ?", (sync_id,)
    ).fetchone()
    if row is not None:
        if int(row["sync_deleted"]):
            return DEPENDENCY_DELETED, None
        return DEPENDENCY_ACTIVE, int(row["id"])
    if deleted_at_for(conn, table, sync_id) is not None:
        return DEPENDENCY_DELETED, None
    return DEPENDENCY_MISSING, None


def is_newer(local_updated_at: str, remote_updated_at: str) -> bool:
    """Compare ISO timestamps by instant, not by their textual UTC offset."""
    if not local_updated_at:
        return False
    return _parse_timestamp(local_updated_at) > _parse_timestamp(remote_updated_at)


def _parse_timestamp(value: str) -> datetime:
    cleaned = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError as exc:
        raise ValueError(f"Invalid sync timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def table_for(entity_type: str) -> str:
    if entity_type not in ENTITY_ORDER:
        raise ValueError(f"Unsupported sync entity type: {entity_type}")
    return entity_type


def required_str(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Missing required sync field.")
    return text


def str_or_none(value: object) -> str | None:
    if value is None:
        return None
    return str(value).strip() or None


def int_or_none(value: object) -> int | None:
    return None if value is None else int(value)


def float_or_none(value: object) -> float | None:
    return None if value is None else float(value)
