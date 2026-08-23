from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from . import db
from .skill_graph import SUBSKILL_STREAK_TO_MASTER

ENTITY_ORDER = ("profiles", "quiz_sets", "assignments", "quiz_attempts", "quiz_questions")


def apply_remote_changes(changes: Sequence[dict[str, Any]]) -> int:
    total_applied = 0
    grouped: dict[str, list[dict[str, Any]]] = {entity: [] for entity in ENTITY_ORDER}
    for item in changes:
        entity_type = str(item.get("entity_type", ""))
        if entity_type in grouped:
            grouped[entity_type].append(item)

    with db.managed_connection() as conn:
        for entity_type in ENTITY_ORDER:
            for change in grouped[entity_type]:
                if _apply_change(conn, entity_type, change):
                    total_applied += 1
        _rebuild_subskill_progress(conn, streak_to_master=SUBSKILL_STREAK_TO_MASTER)
    return total_applied


def _apply_change(conn, entity_type: str, change: dict[str, Any]) -> bool:
    sync_id = _required_str(change.get("entity_sync_id"))
    action = _required_str(change.get("action"))
    updated_at = _required_str(change.get("updated_at"))
    payload = change.get("payload")
    payload_dict = payload if isinstance(payload, dict) else {}

    if action == "delete":
        return _apply_delete(conn, entity_type, sync_id)
    if action != "upsert":
        return False

    existing = conn.execute(
        f"SELECT id, sync_updated_at FROM {_table_for(entity_type)} WHERE sync_id = ?",
        (sync_id,),
    ).fetchone()
    if existing is not None and str(existing["sync_updated_at"] or "") > updated_at:
        return False

    if entity_type == "profiles":
        values = (
            _required_str(payload_dict.get("name")),
            _required_str(payload_dict.get("role")),
            _required_str(payload_dict.get("created_at")),
            sync_id,
            updated_at,
        )
        if existing is None:
            conn.execute(
                """
                INSERT INTO profiles (name, role, created_at, sync_id, sync_updated_at, sync_deleted)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                values,
            )
        else:
            conn.execute(
                """
                UPDATE profiles
                SET name = ?, role = ?, created_at = ?, sync_updated_at = ?, sync_deleted = 0
                WHERE id = ?
                """,
                (values[0], values[1], values[2], updated_at, int(existing["id"])),
            )
        return True

    if entity_type == "quiz_sets":
        values = (
            _required_str(payload_dict.get("name")),
            _required_str(payload_dict.get("skill")),
            _required_str(payload_dict.get("question_type")),
            int(payload_dict.get("num_questions")),
            int(payload_dict.get("level")),
            _int_or_none(payload_dict.get("mode_intuition_pct")),
            _int_or_none(payload_dict.get("mode_expression_pct")),
            _int_or_none(payload_dict.get("mode_word_pct")),
            _required_str(payload_dict.get("created_at")),
            sync_id,
            updated_at,
        )
        if existing is None:
            conn.execute(
                """
                INSERT INTO quiz_sets
                (name, skill, question_type, num_questions, level, mode_intuition_pct, mode_expression_pct, mode_word_pct,
                 created_at, sync_id, sync_updated_at, sync_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                values,
            )
        else:
            conn.execute(
                """
                UPDATE quiz_sets
                SET name = ?, skill = ?, question_type = ?, num_questions = ?, level = ?,
                    mode_intuition_pct = ?, mode_expression_pct = ?, mode_word_pct = ?,
                    created_at = ?, sync_updated_at = ?, sync_deleted = 0
                WHERE id = ?
                """,
                (*values[:9], updated_at, int(existing["id"])),
            )
        return True

    if entity_type == "assignments":
        profile_id = _lookup_local_id(conn, "profiles", _required_str(payload_dict.get("profile_sync_id")))
        if profile_id is None:
            return False
        values = (
            int(profile_id),
            _required_str(payload_dict.get("skill")),
            _str_or_none(payload_dict.get("subskill")),
            _required_str(payload_dict.get("target_type")),
            float(payload_dict.get("target_value")),
            int(payload_dict.get("level")),
            int(payload_dict.get("num_questions")),
            _required_str(payload_dict.get("question_type")),
            _int_or_none(payload_dict.get("mode_intuition_pct")),
            _int_or_none(payload_dict.get("mode_expression_pct")),
            _int_or_none(payload_dict.get("mode_word_pct")),
            1 if bool(payload_dict.get("active")) else 0,
            str(payload_dict.get("notes", "")),
            _required_str(payload_dict.get("created_at")),
            _str_or_none(payload_dict.get("completed_at")),
            sync_id,
            updated_at,
        )
        if existing is None:
            conn.execute(
                """
                INSERT INTO assignments
                (profile_id, skill, subskill, target_type, target_value, level, num_questions, question_type,
                 mode_intuition_pct, mode_expression_pct, mode_word_pct, active, notes, created_at, completed_at,
                 sync_id, sync_updated_at, sync_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                values,
            )
        else:
            conn.execute(
                """
                UPDATE assignments
                SET profile_id = ?, skill = ?, subskill = ?, target_type = ?, target_value = ?, level = ?, num_questions = ?,
                    question_type = ?, mode_intuition_pct = ?, mode_expression_pct = ?, mode_word_pct = ?, active = ?,
                    notes = ?, created_at = ?, completed_at = ?, sync_updated_at = ?, sync_deleted = 0
                WHERE id = ?
                """,
                (*values[:15], updated_at, int(existing["id"])),
            )
        return True

    if entity_type == "quiz_attempts":
        profile_id = _lookup_local_id(conn, "profiles", _required_str(payload_dict.get("profile_sync_id")))
        if profile_id is None:
            return False
        quiz_set_sync_id = _str_or_none(payload_dict.get("quiz_set_sync_id"))
        quiz_set_id = _lookup_local_id(conn, "quiz_sets", quiz_set_sync_id) if quiz_set_sync_id else None
        values = (
            int(profile_id),
            quiz_set_id,
            _required_str(payload_dict.get("skill")),
            _required_str(payload_dict.get("question_type")),
            int(payload_dict.get("num_questions")),
            int(payload_dict.get("level")),
            int(payload_dict.get("score")),
            _float_or_none(payload_dict.get("elapsed_seconds")),
            _required_str(payload_dict.get("created_at")),
            sync_id,
            updated_at,
        )
        if existing is None:
            conn.execute(
                """
                INSERT INTO quiz_attempts
                (profile_id, quiz_set_id, skill, question_type, num_questions, level, score, elapsed_seconds, created_at,
                 sync_id, sync_updated_at, sync_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                values,
            )
        else:
            conn.execute(
                """
                UPDATE quiz_attempts
                SET profile_id = ?, quiz_set_id = ?, skill = ?, question_type = ?, num_questions = ?, level = ?, score = ?,
                    elapsed_seconds = ?, created_at = ?, sync_updated_at = ?, sync_deleted = 0
                WHERE id = ?
                """,
                (*values[:9], updated_at, int(existing["id"])),
            )
        return True

    if entity_type == "quiz_questions":
        attempt_id = _lookup_local_id(conn, "quiz_attempts", _required_str(payload_dict.get("attempt_sync_id")))
        if attempt_id is None:
            return False
        values = (
            int(attempt_id),
            _required_str(payload_dict.get("skill")),
            _str_or_none(payload_dict.get("subskill")),
            _required_str(payload_dict.get("question_label")),
            _required_str(payload_dict.get("mode")),
            _required_str(payload_dict.get("prompt")),
            _required_str(payload_dict.get("correct_answer")),
            _required_str(payload_dict.get("user_answer")),
            1 if bool(payload_dict.get("is_correct")) else 0,
            _required_str(payload_dict.get("explanation")),
            sync_id,
            updated_at,
        )
        if existing is None:
            conn.execute(
                """
                INSERT INTO quiz_questions
                (attempt_id, skill, subskill, question_label, mode, prompt, correct_answer, user_answer, is_correct,
                 explanation, sync_id, sync_updated_at, sync_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                values,
            )
        else:
            conn.execute(
                """
                UPDATE quiz_questions
                SET attempt_id = ?, skill = ?, subskill = ?, question_label = ?, mode = ?, prompt = ?, correct_answer = ?,
                    user_answer = ?, is_correct = ?, explanation = ?, sync_updated_at = ?, sync_deleted = 0
                WHERE id = ?
                """,
                (*values[:10], updated_at, int(existing["id"])),
            )
        return True

    return False


def _apply_delete(conn, entity_type: str, sync_id: str) -> bool:
    table = _table_for(entity_type)
    row = conn.execute(f"SELECT id FROM {table} WHERE sync_id = ?", (sync_id,)).fetchone()
    if row is None:
        return False
    conn.execute(f"DELETE FROM {table} WHERE id = ?", (int(row["id"]),))
    return True


def _lookup_local_id(conn, table: str, sync_id: str | None) -> int | None:
    if not sync_id:
        return None
    row = conn.execute(f"SELECT id FROM {table} WHERE sync_id = ?", (sync_id,)).fetchone()
    if row is None:
        return None
    return int(row["id"])


def _table_for(entity_type: str) -> str:
    if entity_type not in ENTITY_ORDER:
        raise ValueError(f"Unsupported sync entity type: {entity_type}")
    return entity_type


def _required_str(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Missing required sync field.")
    return text


def _str_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _rebuild_subskill_progress(conn, streak_to_master: int) -> None:
    conn.execute("DELETE FROM skill_subskill_progress")
    rows = conn.execute(
        """
        SELECT qa.profile_id, qq.skill, qq.subskill, qq.is_correct, qa.created_at, qq.id
        FROM quiz_questions qq
        JOIN quiz_attempts qa ON qa.id = qq.attempt_id
        WHERE qq.subskill IS NOT NULL
          AND qq.sync_deleted = 0
          AND qa.sync_deleted = 0
        ORDER BY qa.created_at ASC, qq.id ASC
        """
    ).fetchall()
    state: dict[tuple[int, str, str], tuple[int, int, bool, str]] = {}
    for row in rows:
        key = (int(row["profile_id"]), str(row["skill"]), str(row["subskill"]))
        current_streak, best_streak, mastered, _updated_at = state.get(key, (0, 0, False, str(row["created_at"])))
        is_correct = bool(row["is_correct"])
        next_streak = current_streak + 1 if is_correct else 0
        next_best = max(best_streak, next_streak)
        next_mastered = bool(mastered or next_streak >= streak_to_master)
        state[key] = (next_streak, next_best, next_mastered, str(row["created_at"]))

    for (profile_id, skill, subskill), (current_streak, best_streak, mastered, updated_at) in state.items():
        conn.execute(
            """
            INSERT INTO skill_subskill_progress
            (profile_id, skill, subskill, current_streak, best_streak, mastered, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (profile_id, skill, subskill, current_streak, best_streak, 1 if mastered else 0, updated_at),
        )
