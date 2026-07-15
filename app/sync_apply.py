"""Transactional application of remote Family Sync changes."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from . import db
from .skill_graph import SUBSKILL_STREAK_TO_MASTER
from .sync_apply_support import (
    ENTITY_ORDER,
    apply_delete,
    is_newer,
    required_str,
    table_for,
)
from .sync_apply_upserts import apply_upsert
from .sync_progress import rebuild_subskill_progress
from .sync_tombstones import clear_tombstone_on, deleted_at_for

APPLIED = "applied"
STALE = "stale"
DEFERRED = "deferred"
UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class ApplyResult:
    applied: int = 0
    stale_skipped: int = 0
    deferred: int = 0
    unsupported: int = 0


class _DeferredBatch(RuntimeError):
    def __init__(self, result: ApplyResult) -> None:
        super().__init__("Remote batch has retryable missing dependencies.")
        self.result = result


def apply_remote_changes(changes: Sequence[dict[str, Any]]) -> ApplyResult:
    grouped: dict[str, list[dict[str, Any]]] = {
        entity: [] for entity in ENTITY_ORDER
    }
    unsupported = 0
    for item in changes:
        entity_type = str(item.get("entity_type", ""))
        if entity_type in grouped:
            grouped[entity_type].append(item)
        else:
            unsupported += 1

    try:
        applied = stale = deferred = 0
        with db.managed_connection() as conn:
            for entity_type in ENTITY_ORDER:
                for change in grouped[entity_type]:
                    outcome = _apply_change(conn, entity_type, change)
                    applied += int(outcome == APPLIED)
                    stale += int(outcome == STALE)
                    deferred += int(outcome == DEFERRED)
                    unsupported += int(outcome == UNSUPPORTED)
            result = ApplyResult(applied, stale, deferred, unsupported)
            if deferred:
                raise _DeferredBatch(result)
            if applied:
                rebuild_subskill_progress(
                    conn, streak_to_master=SUBSKILL_STREAK_TO_MASTER
                )
        return result
    except _DeferredBatch as exc:
        return ApplyResult(
            applied=0,
            stale_skipped=exc.result.stale_skipped,
            deferred=exc.result.deferred,
            unsupported=exc.result.unsupported,
        )


def _apply_change(conn, entity_type: str, change: dict[str, Any]) -> str:
    sync_id = required_str(change.get("entity_sync_id"))
    action = required_str(change.get("action"))
    updated_at = required_str(change.get("updated_at"))
    payload = change.get("payload")
    payload_dict = payload if isinstance(payload, dict) else {}

    if action == "delete":
        return apply_delete(conn, entity_type, sync_id, updated_at)
    if action != "upsert":
        return UNSUPPORTED

    existing = conn.execute(
        f"SELECT id, sync_updated_at FROM {table_for(entity_type)} WHERE sync_id = ?",
        (sync_id,),
    ).fetchone()
    tombstone_at = deleted_at_for(conn, entity_type, sync_id)
    if tombstone_at and not is_newer(updated_at, tombstone_at):
        return STALE
    if existing is not None and not is_newer(
        updated_at, str(existing["sync_updated_at"] or "")
    ):
        return STALE

    outcome = apply_upsert(
        conn,
        entity_type,
        sync_id,
        updated_at,
        payload_dict,
        int(existing["id"]) if existing is not None else None,
    )
    if outcome == APPLIED:
        clear_tombstone_on(conn, entity_type, sync_id)
    return outcome


__all__ = ("ApplyResult", "apply_remote_changes")
