"""Entity-specific writes used by the transactional remote apply boundary."""

from __future__ import annotations

from typing import Any

from .sync_apply_support import (
    DEPENDENCY_DELETED,
    DEPENDENCY_MISSING,
    float_or_none,
    int_or_none,
    lookup_dependency,
    required_str,
    str_or_none,
)

APPLIED = "applied"
DEFERRED = "deferred"
STALE = "stale"


def apply_upsert(
    conn,
    entity_type: str,
    sync_id: str,
    updated_at: str,
    payload: dict[str, Any],
    existing_id: int | None,
) -> str:
    if entity_type == "profiles":
        return _profile(conn, sync_id, updated_at, payload, existing_id)
    if entity_type == "quiz_sets":
        return _quiz_set(conn, sync_id, updated_at, payload, existing_id)
    if entity_type == "assignments":
        return _assignment(conn, sync_id, updated_at, payload, existing_id)
    if entity_type == "quiz_attempts":
        return _attempt(conn, sync_id, updated_at, payload, existing_id)
    if entity_type == "quiz_questions":
        return _question(conn, sync_id, updated_at, payload, existing_id)
    raise ValueError(f"Unsupported sync entity type: {entity_type}")


def _profile(conn, sync_id, updated_at, payload, existing_id) -> str:
    role = required_str(payload.get("role"))
    if role not in {"child", "parent"}:
        raise ValueError("Remote profile role must be 'child' or 'parent'.")
    if existing_id is not None:
        current = conn.execute(
            "SELECT role FROM profiles WHERE id = ?", (existing_id,)
        ).fetchone()
        if current is not None and str(current["role"]) != role:
            raise ValueError("Remote profile role changes are not supported.")
    values = (required_str(payload.get("name")), role, required_str(payload.get("created_at")))
    if existing_id is None:
        conn.execute(
            """INSERT INTO profiles
            (name, role, created_at, sync_id, sync_updated_at, sync_deleted)
            VALUES (?, ?, ?, ?, ?, 0)""",
            (*values, sync_id, updated_at),
        )
    else:
        conn.execute(
            """UPDATE profiles SET name=?, role=?, created_at=?,
            sync_updated_at=?, sync_deleted=0 WHERE id=?""",
            (*values, updated_at, existing_id),
        )
    return APPLIED


def _quiz_set(conn, sync_id, updated_at, payload, existing_id) -> str:
    values = (
        required_str(payload.get("name")),
        required_str(payload.get("skill")),
        required_str(payload.get("question_type")),
        int(payload.get("num_questions")),
        int(payload.get("level")),
        int_or_none(payload.get("mode_intuition_pct")),
        int_or_none(payload.get("mode_expression_pct")),
        int_or_none(payload.get("mode_word_pct")),
        required_str(payload.get("created_at")),
    )
    if existing_id is None:
        conn.execute(
            """INSERT INTO quiz_sets
            (name, skill, question_type, num_questions, level,
             mode_intuition_pct, mode_expression_pct, mode_word_pct,
             created_at, sync_id, sync_updated_at, sync_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
            (*values, sync_id, updated_at),
        )
    else:
        conn.execute(
            """UPDATE quiz_sets SET name=?, skill=?, question_type=?,
            num_questions=?, level=?, mode_intuition_pct=?, mode_expression_pct=?,
            mode_word_pct=?, created_at=?, sync_updated_at=?, sync_deleted=0 WHERE id=?""",
            (*values, updated_at, existing_id),
        )
    return APPLIED


def _assignment(conn, sync_id, updated_at, payload, existing_id) -> str:
    dependency, profile_id = lookup_dependency(
        conn, "profiles", required_str(payload.get("profile_sync_id"))
    )
    if dependency == DEPENDENCY_DELETED:
        return STALE
    if dependency == DEPENDENCY_MISSING or profile_id is None:
        return DEFERRED
    values = (
        profile_id,
        required_str(payload.get("skill")),
        str_or_none(payload.get("subskill")),
        required_str(payload.get("target_type")),
        float(payload.get("target_value")),
        int(payload.get("level")),
        int(payload.get("num_questions")),
        required_str(payload.get("question_type")),
        int_or_none(payload.get("mode_intuition_pct")),
        int_or_none(payload.get("mode_expression_pct")),
        int_or_none(payload.get("mode_word_pct")),
        1 if required_bool(payload.get("active")) else 0,
        str(payload.get("notes", "")),
        required_str(payload.get("created_at")),
        str_or_none(payload.get("completed_at")),
    )
    if existing_id is None:
        conn.execute(
            """INSERT INTO assignments
            (profile_id, skill, subskill, target_type, target_value, level,
             num_questions, question_type, mode_intuition_pct, mode_expression_pct,
             mode_word_pct, active, notes, created_at, completed_at,
             sync_id, sync_updated_at, sync_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
            (*values, sync_id, updated_at),
        )
    else:
        conn.execute(
            """UPDATE assignments SET profile_id=?, skill=?, subskill=?, target_type=?,
            target_value=?, level=?, num_questions=?, question_type=?, mode_intuition_pct=?,
            mode_expression_pct=?, mode_word_pct=?, active=?, notes=?, created_at=?,
            completed_at=?, sync_updated_at=?, sync_deleted=0 WHERE id=?""",
            (*values, updated_at, existing_id),
        )
    return APPLIED


def _attempt(conn, sync_id, updated_at, payload, existing_id) -> str:
    dependency, profile_id = lookup_dependency(
        conn, "profiles", required_str(payload.get("profile_sync_id"))
    )
    if dependency == DEPENDENCY_DELETED:
        return STALE
    if dependency == DEPENDENCY_MISSING or profile_id is None:
        return DEFERRED
    quiz_set_sync_id = str_or_none(payload.get("quiz_set_sync_id"))
    quiz_set_id = None
    if quiz_set_sync_id:
        quiz_dependency, quiz_set_id = lookup_dependency(
            conn, "quiz_sets", quiz_set_sync_id
        )
        if quiz_dependency == DEPENDENCY_MISSING:
            return DEFERRED
        if quiz_dependency == DEPENDENCY_DELETED:
            quiz_set_id = None
    values = (
        profile_id,
        quiz_set_id,
        required_str(payload.get("skill")),
        required_str(payload.get("question_type")),
        int(payload.get("num_questions")),
        int(payload.get("level")),
        int(payload.get("score")),
        float_or_none(payload.get("elapsed_seconds")),
        required_str(payload.get("created_at")),
    )
    if existing_id is None:
        conn.execute(
            """INSERT INTO quiz_attempts
            (profile_id, quiz_set_id, skill, question_type, num_questions, level,
             score, elapsed_seconds, created_at, sync_id, sync_updated_at, sync_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
            (*values, sync_id, updated_at),
        )
    else:
        conn.execute(
            """UPDATE quiz_attempts SET profile_id=?, quiz_set_id=?, skill=?,
            question_type=?, num_questions=?, level=?, score=?, elapsed_seconds=?,
            created_at=?, sync_updated_at=?, sync_deleted=0 WHERE id=?""",
            (*values, updated_at, existing_id),
        )
    return APPLIED


def _question(conn, sync_id, updated_at, payload, existing_id) -> str:
    dependency, attempt_id = lookup_dependency(
        conn, "quiz_attempts", required_str(payload.get("attempt_sync_id"))
    )
    if dependency == DEPENDENCY_DELETED:
        return STALE
    if dependency == DEPENDENCY_MISSING or attempt_id is None:
        return DEFERRED
    values = (
        attempt_id,
        required_str(payload.get("skill")),
        str_or_none(payload.get("subskill")),
        required_str(payload.get("question_label")),
        required_str(payload.get("mode")),
        required_str(payload.get("prompt")),
        required_str(payload.get("correct_answer")),
        required_str(payload.get("user_answer")),
        1 if required_bool(payload.get("is_correct")) else 0,
        required_str(payload.get("explanation")),
    )
    if existing_id is None:
        conn.execute(
            """INSERT INTO quiz_questions
            (attempt_id, skill, subskill, question_label, mode, prompt,
             correct_answer, user_answer, is_correct, explanation,
             sync_id, sync_updated_at, sync_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
            (*values, sync_id, updated_at),
        )
    else:
        conn.execute(
            """UPDATE quiz_questions SET attempt_id=?, skill=?, subskill=?,
            question_label=?, mode=?, prompt=?, correct_answer=?, user_answer=?,
            is_correct=?, explanation=?, sync_updated_at=?, sync_deleted=0 WHERE id=?""",
            (*values, updated_at, existing_id),
        )
    return APPLIED


def required_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    raise ValueError("Remote sync boolean must be true, false, 0, or 1.")
