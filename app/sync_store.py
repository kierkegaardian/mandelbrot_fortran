from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from . import db

_ENTITY_TABLES: dict[str, str] = {
    "profiles": "profiles",
    "quiz_sets": "quiz_sets",
    "assignments": "assignments",
    "quiz_attempts": "quiz_attempts",
    "quiz_questions": "quiz_questions",
}


@dataclass(frozen=True)
class SyncOutboxEntry:
    id: int
    entity_type: str
    entity_sync_id: str
    action: str
    payload_json: str
    created_at: str
    last_attempt_at: str | None
    attempt_count: int
    last_error: str | None
    synced_at: str | None

    @property
    def payload(self) -> dict[str, Any]:
        try:
            data = json.loads(self.payload_json)
        except json.JSONDecodeError:
            return {}
        if isinstance(data, dict):
            return data
        return {}


def entity_sync_id(entity_type: str, local_id: int) -> str | None:
    table = _table_for_entity(entity_type)
    with db.managed_connection() as conn:
        row = conn.execute(
            f"SELECT sync_id FROM {table} WHERE id = ?",
            (int(local_id),),
        ).fetchone()
    if row is None:
        return None
    sync_id = row["sync_id"]
    return str(sync_id) if sync_id else None


def enqueue_change(
    *,
    entity_type: str,
    local_id: int,
    action: str,
    occurred_at: str,
    extra: dict[str, Any] | None = None,
    known_sync_id: str | None = None,
) -> int:
    sync_id = known_sync_id or entity_sync_id(entity_type, local_id)
    if not sync_id:
        raise ValueError(f"No sync id found for {entity_type}#{int(local_id)}")
    payload: dict[str, Any] = {"local_id": int(local_id)}
    if extra:
        payload.update(extra)
    payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    with db.managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO sync_outbox
            (entity_type, entity_sync_id, action, payload_json, created_at, last_attempt_at, attempt_count, last_error, synced_at)
            VALUES (?, ?, ?, ?, ?, NULL, 0, NULL, NULL)
            """,
            (entity_type, sync_id, action, payload_json, occurred_at),
        )
        return int(cur.lastrowid)


def count_pending_changes() -> int:
    with db.managed_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM sync_outbox WHERE synced_at IS NULL",
        ).fetchone()
    if row is None:
        return 0
    return int(row["count"] or 0)


def list_pending_changes(limit: int = 100) -> list[SyncOutboxEntry]:
    with db.managed_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, entity_type, entity_sync_id, action, payload_json, created_at,
                   last_attempt_at, attempt_count, last_error, synced_at
            FROM sync_outbox
            WHERE synced_at IS NULL
            ORDER BY id ASC
            LIMIT ?
            """,
            (max(1, int(limit)),),
        ).fetchall()
    return [_row_to_sync_outbox_entry(row) for row in rows]


def mark_changes_synced(outbox_ids: list[int], synced_at: str) -> None:
    ids = [int(item) for item in outbox_ids]
    if not ids:
        return
    placeholders = ", ".join("?" for _ in ids)
    with db.managed_connection() as conn:
        conn.execute(
            f"""
            UPDATE sync_outbox
            SET synced_at = ?, last_attempt_at = ?, attempt_count = attempt_count + 1, last_error = NULL
            WHERE id IN ({placeholders})
            """,
            (synced_at, synced_at, *ids),
        )


def record_change_failure(outbox_id: int, attempted_at: str, error_message: str) -> None:
    with db.managed_connection() as conn:
        conn.execute(
            """
            UPDATE sync_outbox
            SET last_attempt_at = ?, attempt_count = attempt_count + 1, last_error = ?
            WHERE id = ?
            """,
            (attempted_at, error_message, int(outbox_id)),
        )


def _table_for_entity(entity_type: str) -> str:
    table = _ENTITY_TABLES.get(entity_type)
    if table is None:
        raise ValueError(f"Unsupported sync entity type: {entity_type}")
    return table


def _row_to_sync_outbox_entry(row) -> SyncOutboxEntry:
    return SyncOutboxEntry(
        id=int(row["id"]),
        entity_type=str(row["entity_type"]),
        entity_sync_id=str(row["entity_sync_id"]),
        action=str(row["action"]),
        payload_json=str(row["payload_json"]),
        created_at=str(row["created_at"]),
        last_attempt_at=str(row["last_attempt_at"]) if row["last_attempt_at"] is not None else None,
        attempt_count=int(row["attempt_count"]),
        last_error=str(row["last_error"]) if row["last_error"] is not None else None,
        synced_at=str(row["synced_at"]) if row["synced_at"] is not None else None,
    )
