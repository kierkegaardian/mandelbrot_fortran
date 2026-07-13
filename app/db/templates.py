from __future__ import annotations

from ..models import QuestionTemplate, TemplateVar
from .connection import managed_connection

def has_active_question_templates(skill: str, *, subskill: str | None = None, mode: str | None = None) -> bool:
    with managed_connection() as conn:
        clauses = ["active = 1", "skill = ?"]
        params: list[object] = [skill]
        if subskill is not None:
            clauses.append("subskill = ?")
            params.append(subskill)
        if mode is not None:
            clauses.append("mode = ?")
            params.append(mode)
        query = "SELECT 1 FROM question_templates WHERE " + " AND ".join(clauses) + " LIMIT 1"
        row = conn.execute(query, tuple(params)).fetchone()
    return row is not None


def template_modes_for_skill(skill: str, *, subskill: str | None = None) -> tuple[str, ...]:
    with managed_connection() as conn:
        if subskill is None:
            rows = conn.execute(
                """
                SELECT DISTINCT mode
                FROM question_templates
                WHERE active = 1 AND skill = ?
                ORDER BY mode ASC
                """,
                (skill,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT DISTINCT mode
                FROM question_templates
                WHERE active = 1 AND skill = ? AND subskill = ?
                ORDER BY mode ASC
                """,
                (skill, subskill),
            ).fetchall()
    return tuple(str(row["mode"]) for row in rows if row["mode"])

def create_question_template(
    *,
    book_id: int | None,
    external_id: str | None,
    skill: str,
    subskill: str,
    label: str,
    mode: str,
    prompt_template: str,
    answer_expr: str,
    constraint_expr: str,
    explanation_template: str,
    min_level: int,
    max_level: int,
    choice_spread: float,
    active: bool,
    created_at: str,
) -> int:
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO question_templates
            (book_id, external_id, skill, subskill, label, mode, prompt_template, answer_expr, constraint_expr, explanation_template,
             min_level, max_level, choice_spread, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                book_id,
                external_id,
                skill,
                subskill,
                label,
                mode,
                prompt_template,
                answer_expr,
                constraint_expr,
                explanation_template,
                int(min_level),
                int(max_level),
                float(choice_spread),
                int(bool(active)),
                created_at,
            ),
        )
        return int(cur.lastrowid)


def add_template_var(
    template_id: int, name: str, kind: str, min_value: float, max_value: float, step: float
) -> None:
    if kind not in {"int", "float"}:
        raise ValueError("kind must be 'int' or 'float'")
    with managed_connection() as conn:
        conn.execute(
            """
            INSERT INTO template_vars (template_id, name, kind, min_value, max_value, step)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (template_id, name, kind, float(min_value), float(max_value), float(step)),
        )


def list_question_templates(
    skill: str,
    level: int,
    subskill: str | None = None,
    mode: str | None = None,
) -> list[QuestionTemplate]:
    level = int(level)
    with managed_connection() as conn:
        if subskill is None and mode is None:
            rows = conn.execute(
                """
                SELECT id, book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
                       min_level, max_level, choice_spread, mode, active
                FROM question_templates
                WHERE active = 1 AND skill = ? AND ? BETWEEN min_level AND max_level
                ORDER BY id DESC
                """,
                (skill, level),
            ).fetchall()
        elif subskill is None and mode is not None:
            rows = conn.execute(
                """
                SELECT id, book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
                       min_level, max_level, choice_spread, mode, active
                FROM question_templates
                WHERE active = 1 AND skill = ? AND ? BETWEEN min_level AND max_level AND mode = ?
                ORDER BY id DESC
                """,
                (skill, level, mode),
            ).fetchall()
        elif subskill is not None and mode is None:
            rows = conn.execute(
                """
                SELECT id, book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
                       min_level, max_level, choice_spread, mode, active
                FROM question_templates
                WHERE active = 1 AND skill = ? AND subskill = ? AND ? BETWEEN min_level AND max_level
                ORDER BY id DESC
                """,
                (skill, subskill, level),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
                       min_level, max_level, choice_spread, mode, active
                FROM question_templates
                WHERE active = 1 AND skill = ? AND subskill = ? AND ? BETWEEN min_level AND max_level AND mode = ?
                ORDER BY id DESC
                """,
                (skill, subskill, level, mode),
            ).fetchall()
    return [
        QuestionTemplate(
            int(r["id"]),
            int(r["book_id"]) if r["book_id"] is not None else None,
            r["external_id"],
            r["skill"],
            r["subskill"],
            r["label"],
            r["prompt_template"],
            r["answer_expr"],
            r["constraint_expr"],
            r["explanation_template"],
            int(r["min_level"]),
            int(r["max_level"]),
            float(r["choice_spread"]),
            r["mode"],
            bool(r["active"]),
        )
        for r in rows
    ]

def delete_templates_by_identity(*, skill: str, subskill: str, label: str) -> int:
    with managed_connection() as conn:
        cur = conn.execute(
            """
            DELETE FROM question_templates
            WHERE skill = ? AND subskill = ? AND label = ?
            """,
            (skill, subskill, label),
        )
        return int(cur.rowcount)


def delete_template_by_external_id(external_id: str) -> int:
    with managed_connection() as conn:
        cur = conn.execute("DELETE FROM question_templates WHERE external_id = ?", (external_id,))
        return int(cur.rowcount)


def list_template_vars(template_id: int) -> list[TemplateVar]:
    with managed_connection() as conn:
        rows = conn.execute(
            """
            SELECT template_id, name, kind, min_value, max_value, step
            FROM template_vars
            WHERE template_id = ?
            ORDER BY name ASC
            """,
            (int(template_id),),
        ).fetchall()
    return [
        TemplateVar(
            int(r["template_id"]),
            r["name"],
            r["kind"],
            float(r["min_value"]),
            float(r["max_value"]),
            float(r["step"]),
        )
        for r in rows
    ]


def list_all_question_templates(active_only: bool = True) -> list[QuestionTemplate]:
    with managed_connection() as conn:
        if active_only:
            rows = conn.execute(
                """
                SELECT id, book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
                       min_level, max_level, choice_spread, mode, active
                FROM question_templates
                WHERE active = 1
                ORDER BY skill ASC, id ASC
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, book_id, external_id, skill, subskill, label, prompt_template, answer_expr, constraint_expr, explanation_template,
                       min_level, max_level, choice_spread, mode, active
                FROM question_templates
                ORDER BY skill ASC, id ASC
                """
            ).fetchall()
    return [
        QuestionTemplate(
            int(r["id"]),
            int(r["book_id"]) if r["book_id"] is not None else None,
            r["external_id"],
            r["skill"],
            r["subskill"],
            r["label"],
            r["prompt_template"],
            r["answer_expr"],
            r["constraint_expr"],
            r["explanation_template"],
            int(r["min_level"]),
            int(r["max_level"]),
            float(r["choice_spread"]),
            r["mode"],
            bool(r["active"]),
        )
        for r in rows
    ]

