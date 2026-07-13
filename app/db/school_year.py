from __future__ import annotations

from ..models import SchoolYearTarget
from .connection import managed_connection

def get_school_year_target(profile_id: int) -> SchoolYearTarget | None:
    with managed_connection() as conn:
        row = conn.execute(
            """
            SELECT profile_id, grade, stretch_enabled, updated_at
            FROM school_year_targets
            WHERE profile_id = ?
            """,
            (int(profile_id),),
        ).fetchone()
    if row is None:
        return None
    return SchoolYearTarget(
        profile_id=int(row["profile_id"]),
        grade=int(row["grade"]),
        stretch_enabled=bool(row["stretch_enabled"]),
        updated_at=str(row["updated_at"]),
    )


def save_school_year_target(profile_id: int, grade: int, stretch_enabled: bool, updated_at: str) -> SchoolYearTarget:
    grade = int(grade)
    if grade < 1 or grade > 7:
        raise ValueError("Texas school-year grade must be between 1 and 7.")
    with managed_connection() as conn:
        row = conn.execute(
            "SELECT role FROM profiles WHERE id = ?",
            (int(profile_id),),
        ).fetchone()
        if row is None:
            raise ValueError("Profile not found.")
        if str(row["role"]) != "child":
            raise ValueError("School-year targets can only be set for child profiles.")
        conn.execute(
            """
            INSERT INTO school_year_targets (profile_id, grade, stretch_enabled, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(profile_id) DO UPDATE SET
                grade = excluded.grade,
                stretch_enabled = excluded.stretch_enabled,
                updated_at = excluded.updated_at
            """,
            (int(profile_id), grade, int(bool(stretch_enabled)), updated_at),
        )
    return SchoolYearTarget(
        profile_id=int(profile_id),
        grade=grade,
        stretch_enabled=bool(stretch_enabled),
        updated_at=updated_at,
    )

