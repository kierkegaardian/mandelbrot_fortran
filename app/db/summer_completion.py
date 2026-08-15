"""Connection-aware Summer task outcome writes for atomic quiz completion."""

from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3

from ..summer_program_defs import (
    FOUNDATION_BRIDGE_LANE,
    PLACEMENT_REVIEW_PENDING,
    PLACEMENT_STRANDS,
    PREALGEBRA_FINISH_LANE,
)


@dataclass(frozen=True, slots=True)
class SummerCompletionResult:
    completed: bool
    program_id: int | None


def apply_summer_task_outcome_on(
    conn: sqlite3.Connection,
    *,
    task_id: int | None,
    attempt_id: int,
    score: int,
    num_questions: int,
    completed_at: str,
    strand_scores_json: str,
) -> SummerCompletionResult:
    if task_id is None:
        return SummerCompletionResult(False, None)
    row = conn.execute(
        """SELECT t.id, t.program_id, t.task_kind, t.target_score_pct,
        t.notes_json, p.student_age_years
        FROM summer_program_tasks t
        JOIN summer_programs p ON p.id = t.program_id
        WHERE t.id = ?""",
        (int(task_id),),
    ).fetchone()
    if row is None:
        raise ValueError("Summer Program task was not found.")
    score_pct = 100.0 * float(score) / float(max(1, num_questions))
    target = (
        float(row["target_score_pct"])
        if row["target_score_pct"] is not None
        else None
    )
    passed = target is None or score_pct >= target
    strands = _scores(strand_scores_json)
    notes = _notes(str(row["notes_json"]))
    for key in (
        "attempt_id",
        "score_pct",
        "required_score_pct",
        "strand_results",
        "weak_strands",
        "block_reason",
        "next_action",
    ):
        notes.pop(key, None)
    notes.update(
        {
            "attempt_id": int(attempt_id),
            "score_pct": score_pct,
            "strand_results": strands,
        }
    )
    task_kind = str(row["task_kind"])
    if not passed:
        notes["required_score_pct"] = target
        notes["weak_strands"] = list(_weak_strands(strands))
        notes["block_reason"] = f"{task_kind.replace('_', ' ').title()} target not met."
        notes["next_action"] = "Review the weak strands, then retry this task."
    elif task_kind == "placement_assessment":
        notes["weak_strands"] = list(_weak_strands(strands))
        notes["next_action"] = "Parent review needed after placement."
    conn.execute(
        """UPDATE summer_program_tasks SET status = ?, notes_json = ? WHERE id = ?""",
        (
            "completed" if passed else "blocked",
            json.dumps(notes, ensure_ascii=True, sort_keys=True),
            int(task_id),
        ),
    )
    program_id = int(row["program_id"])
    if task_kind.endswith("_assessment"):
        assessment_type = task_kind.removesuffix("_assessment")
        conn.execute(
            """INSERT INTO summer_assessment_runs
            (program_id, assessment_type, score_pct, passed,
             strand_results_json, completed_at) VALUES (?, ?, ?, ?, ?, ?)""",
            (
                program_id,
                assessment_type,
                score_pct,
                int(passed),
                json.dumps(strands, ensure_ascii=True, sort_keys=True),
                completed_at,
            ),
        )
        if assessment_type == "placement":
            recommendation = _recommended_lane(
                score_pct, strands, row["student_age_years"]
            )
            conn.execute(
                """UPDATE summer_programs SET placement_recommendation = ?,
                placement_review_status = ?, placement_reviewed_at = NULL,
                updated_at = ? WHERE id = ?""",
                (
                    recommendation,
                    PLACEMENT_REVIEW_PENDING,
                    completed_at,
                    program_id,
                ),
            )
    return SummerCompletionResult(True, program_id)


def existing_summer_outcome_on(
    conn: sqlite3.Connection, task_id: int | None, attempt_id: int
) -> SummerCompletionResult:
    if task_id is None:
        return SummerCompletionResult(False, None)
    row = conn.execute(
        "SELECT program_id, notes_json FROM summer_program_tasks WHERE id = ?",
        (int(task_id),),
    ).fetchone()
    if row is None:
        return SummerCompletionResult(False, None)
    notes = _notes(str(row["notes_json"]))
    return SummerCompletionResult(
        int(notes.get("attempt_id", -1)) == int(attempt_id), int(row["program_id"])
    )


def _recommended_lane(overall: float, strands: dict[str, float], age: object) -> str:
    candidate = (
        PREALGEBRA_FINISH_LANE
        if overall >= 70.0
        and all(strands.get(strand, 0.0) >= 50.0 for strand in PLACEMENT_STRANDS)
        else FOUNDATION_BRIDGE_LANE
    )
    if age is not None and int(age) < 8 and overall < 85.0:
        return FOUNDATION_BRIDGE_LANE
    return candidate


def _notes(raw: str) -> dict[str, object]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _scores(raw: str) -> dict[str, float]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Summer strand scores are invalid.") from exc
    if not isinstance(value, dict):
        raise ValueError("Summer strand scores must be an object.")
    return {str(key): float(score) for key, score in value.items()}


def _weak_strands(scores: dict[str, float]) -> tuple[str, ...]:
    ordered = sorted(scores.items(), key=lambda item: item[1])
    return tuple(key for key, value in ordered if value < 70.0)[:3]
