"""Durable last-write-wins records for synchronized deletes."""

from __future__ import annotations

import sqlite3


def deleted_at_for(
    conn: sqlite3.Connection, entity_type: str, entity_sync_id: str
) -> str | None:
    row = conn.execute(
        """SELECT deleted_at FROM sync_tombstones
        WHERE entity_type = ? AND entity_sync_id = ?""",
        (entity_type, entity_sync_id),
    ).fetchone()
    return str(row["deleted_at"]) if row is not None else None


def record_tombstone_on(
    conn: sqlite3.Connection,
    *,
    entity_type: str,
    entity_sync_id: str,
    deleted_at: str,
) -> None:
    conn.execute(
        """INSERT INTO sync_tombstones
        (entity_type, entity_sync_id, deleted_at) VALUES (?, ?, ?)
        ON CONFLICT(entity_type, entity_sync_id)
        DO UPDATE SET deleted_at = excluded.deleted_at""",
        (entity_type, entity_sync_id, deleted_at),
    )


def clear_tombstone_on(
    conn: sqlite3.Connection, entity_type: str, entity_sync_id: str
) -> None:
    conn.execute(
        """DELETE FROM sync_tombstones
        WHERE entity_type = ? AND entity_sync_id = ?""",
        (entity_type, entity_sync_id),
    )
