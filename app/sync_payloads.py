from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import db
from .sync_store import SyncOutboxEntry


@dataclass(frozen=True)
class LocalDeleteTarget:
    entity_type: str
    local_id: int
    entity_sync_id: str


def build_outbound_change(entry: SyncOutboxEntry) -> dict[str, Any] | None:
    if entry.action == "delete":
        return {
            "entity_type": entry.entity_type,
            "entity_sync_id": entry.entity_sync_id,
            "action": "delete",
            "updated_at": str(entry.payload.get("deleted_at") or entry.created_at),
            "data": {"deleted_at": str(entry.payload.get("deleted_at") or entry.created_at)},
        }

    local_id = entry.payload.get("local_id")
    if not isinstance(local_id, int):
        return None
    with db.managed_connection() as conn:
        payload = _load_payload(conn, entry.entity_type, int(local_id))
    if payload is None:
        return None
    return {
        "entity_type": entry.entity_type,
        "entity_sync_id": entry.entity_sync_id,
        "action": "upsert",
        "updated_at": str(payload.pop("sync_updated_at")),
        "data": payload,
    }


def dependent_delete_targets_for_profile(profile_id: int) -> list[LocalDeleteTarget]:
    with db.managed_connection() as conn:
        question_rows = conn.execute(
            """
            SELECT qq.id, qq.sync_id
            FROM quiz_questions qq
            JOIN quiz_attempts qa ON qa.id = qq.attempt_id
            WHERE qa.profile_id = ? AND qq.sync_deleted = 0 AND qa.sync_deleted = 0
            ORDER BY qq.id ASC
            """,
            (int(profile_id),),
        ).fetchall()
        attempt_rows = conn.execute(
            """
            SELECT id, sync_id
            FROM quiz_attempts
            WHERE profile_id = ? AND sync_deleted = 0
            ORDER BY id ASC
            """,
            (int(profile_id),),
        ).fetchall()
        assignment_rows = conn.execute(
            """
            SELECT id, sync_id
            FROM assignments
            WHERE profile_id = ? AND sync_deleted = 0
            ORDER BY id ASC
            """,
            (int(profile_id),),
        ).fetchall()
    targets = [
        LocalDeleteTarget("quiz_questions", int(row["id"]), str(row["sync_id"]))
        for row in question_rows
        if row["sync_id"]
    ]
    targets.extend(
        LocalDeleteTarget("quiz_attempts", int(row["id"]), str(row["sync_id"]))
        for row in attempt_rows
        if row["sync_id"]
    )
    targets.extend(
        LocalDeleteTarget("assignments", int(row["id"]), str(row["sync_id"]))
        for row in assignment_rows
        if row["sync_id"]
    )
    return targets


def _load_payload(conn, entity_type: str, local_id: int) -> dict[str, Any] | None:
    if entity_type == "profiles":
        row = conn.execute(
            """
            SELECT name, role, created_at, sync_updated_at
            FROM profiles
            WHERE id = ? AND sync_deleted = 0
            """,
            (local_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "name": str(row["name"]),
            "role": str(row["role"]),
            "created_at": str(row["created_at"]),
            "sync_updated_at": str(row["sync_updated_at"]),
        }

    if entity_type == "quiz_sets":
        row = conn.execute(
            """
            SELECT name, skill, question_type, num_questions, level,
                   mode_intuition_pct, mode_expression_pct, mode_word_pct,
                   created_at, sync_updated_at
            FROM quiz_sets
            WHERE id = ? AND sync_deleted = 0
            """,
            (local_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "name": str(row["name"]),
            "skill": str(row["skill"]),
            "question_type": str(row["question_type"]),
            "num_questions": int(row["num_questions"]),
            "level": int(row["level"]),
            "mode_intuition_pct": _as_int_or_none(row["mode_intuition_pct"]),
            "mode_expression_pct": _as_int_or_none(row["mode_expression_pct"]),
            "mode_word_pct": _as_int_or_none(row["mode_word_pct"]),
            "created_at": str(row["created_at"]),
            "sync_updated_at": str(row["sync_updated_at"]),
        }

    if entity_type == "assignments":
        row = conn.execute(
            """
            SELECT a.skill, a.subskill, a.target_type, a.target_value, a.level, a.num_questions, a.question_type,
                   a.mode_intuition_pct, a.mode_expression_pct, a.mode_word_pct, a.active, a.notes, a.created_at,
                   a.completed_at, a.sync_updated_at, p.sync_id AS profile_sync_id
            FROM assignments a
            JOIN profiles p ON p.id = a.profile_id
            WHERE a.id = ? AND a.sync_deleted = 0
            """,
            (local_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "profile_sync_id": str(row["profile_sync_id"]),
            "skill": str(row["skill"]),
            "subskill": _as_str_or_none(row["subskill"]),
            "target_type": str(row["target_type"]),
            "target_value": float(row["target_value"]),
            "level": int(row["level"]),
            "num_questions": int(row["num_questions"]),
            "question_type": str(row["question_type"]),
            "mode_intuition_pct": _as_int_or_none(row["mode_intuition_pct"]),
            "mode_expression_pct": _as_int_or_none(row["mode_expression_pct"]),
            "mode_word_pct": _as_int_or_none(row["mode_word_pct"]),
            "active": bool(row["active"]),
            "notes": str(row["notes"]),
            "created_at": str(row["created_at"]),
            "completed_at": _as_str_or_none(row["completed_at"]),
            "sync_updated_at": str(row["sync_updated_at"]),
        }

    if entity_type == "quiz_attempts":
        row = conn.execute(
            """
            SELECT qa.skill, qa.question_type, qa.num_questions, qa.level, qa.score, qa.elapsed_seconds,
                   qa.created_at, qa.sync_updated_at,
                   p.sync_id AS profile_sync_id,
                   qs.sync_id AS quiz_set_sync_id
            FROM quiz_attempts qa
            JOIN profiles p ON p.id = qa.profile_id
            LEFT JOIN quiz_sets qs ON qs.id = qa.quiz_set_id
            WHERE qa.id = ? AND qa.sync_deleted = 0
            """,
            (local_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "profile_sync_id": str(row["profile_sync_id"]),
            "quiz_set_sync_id": _as_str_or_none(row["quiz_set_sync_id"]),
            "skill": str(row["skill"]),
            "question_type": str(row["question_type"]),
            "num_questions": int(row["num_questions"]),
            "level": int(row["level"]),
            "score": int(row["score"]),
            "elapsed_seconds": float(row["elapsed_seconds"]) if row["elapsed_seconds"] is not None else None,
            "created_at": str(row["created_at"]),
            "sync_updated_at": str(row["sync_updated_at"]),
        }

    if entity_type == "quiz_questions":
        row = conn.execute(
            """
            SELECT qq.skill, qq.subskill, qq.question_label, qq.mode, qq.prompt, qq.correct_answer,
                   qq.user_answer, qq.is_correct, qq.explanation, qq.sync_updated_at,
                   qa.sync_id AS attempt_sync_id
            FROM quiz_questions qq
            JOIN quiz_attempts qa ON qa.id = qq.attempt_id
            WHERE qq.id = ? AND qq.sync_deleted = 0
            """,
            (local_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "attempt_sync_id": str(row["attempt_sync_id"]),
            "skill": str(row["skill"]),
            "subskill": _as_str_or_none(row["subskill"]),
            "question_label": str(row["question_label"]),
            "mode": str(row["mode"]),
            "prompt": str(row["prompt"]),
            "correct_answer": str(row["correct_answer"]),
            "user_answer": str(row["user_answer"]),
            "is_correct": bool(row["is_correct"]),
            "explanation": str(row["explanation"]),
            "sync_updated_at": str(row["sync_updated_at"]),
        }

    raise ValueError(f"Unsupported sync entity type: {entity_type}")


def _as_int_or_none(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _as_str_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text or None
