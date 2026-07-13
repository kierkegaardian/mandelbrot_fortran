from __future__ import annotations

from contextlib import closing
import json
import sqlite3
import unittest

from app.early_math_catalog import early_math_specs
from app.curriculum import curriculum_pdf_path
from app.paths import data_dir
from app.quiz_content import ContentUnavailableError
from app.quiz_engine import SKILLS, generate_question
from app.skill_graph import subskills_for
from tests.early_math_test_utils import imported_early_math_data_dir


def _db_path():
    return data_dir() / "app.db"


def _curriculum_index_path():
    return data_dir() / "curriculum_index.json"

TEMPLATE_BACKED_SKILLS = (
    "stats_percent",
    "stats_mean",
    "stats_probability",
    "sat_math",
    "psat_math",
    "gre_quant",
)
TEMPLATE_INTUITION_SKILLS = (
    "stats_percent",
    "stats_mean",
    "stats_probability",
    "sat_math",
    "psat_math",
    "gre_quant",
)
PRE_ALGEBRA_SOURCE_BACKED_SUBSKILLS = (
    "Expressions and variables",
    "One-step equations",
    "Two-step equations and inequalities",
    "Ratios, rates, and proportional relationships",
    "Percent problems",
    "Exponents, roots, and scientific notation",
    "Coordinate plane and function tables",
)
FOCUSED_TEMPLATE_REGRESSION_SKILLS = (
    "sat_math",
    "psat_math",
    "gre_quant",
)
NATIVE_COLLAPSED_SUBSKILLS = {
    "trig_right_triangle": "Right-triangle trig ratios",
    "calculus_1": "Average rate of change between two points",
    "calculus_2": "Definite integral of a linear function",
    "calculus_3": "Partial derivative with respect to x at a point",
}


class PedagogicalIntegrityTests(unittest.TestCase):
    def _active_template_count(self, skill: str, *, subskill: str | None = None, mode: str | None = None) -> int:
        clauses = ["active = 1", "skill = ?"]
        params: list[object] = [skill]
        if subskill is not None:
            clauses.append("subskill = ?")
            params.append(subskill)
        if mode is not None:
            clauses.append("mode = ?")
            params.append(mode)
        query = "SELECT COUNT(*) FROM question_templates WHERE " + " AND ".join(clauses)
        with closing(sqlite3.connect(_db_path())) as conn:
            row = conn.execute(query, tuple(params)).fetchone()
        assert row is not None
        return int(row[0])

    def _curriculum_index_by_skill(self) -> dict[str, dict[str, object]]:
        entries = json.loads(_curriculum_index_path().read_text(encoding="utf-8"))
        return {str(item["skill"]): item for item in entries}

    def test_template_backed_exposed_subskills_have_active_templates(self) -> None:
        for skill in TEMPLATE_BACKED_SKILLS:
            for subskill in subskills_for(skill):
                with self.subTest(skill=skill, subskill=subskill):
                    self.assertGreater(self._active_template_count(skill, subskill=subskill), 0)

    def test_template_backed_skills_have_real_intuition_items(self) -> None:
        for skill in TEMPLATE_INTUITION_SKILLS:
            with self.subTest(skill=skill):
                self.assertGreater(self._active_template_count(skill, mode="intuition"), 0)

    def test_focused_template_backed_subskills_generate_without_falling_through(self) -> None:
        for skill in FOCUSED_TEMPLATE_REGRESSION_SKILLS:
            subskill = subskills_for(skill)[0]
            with self.subTest(skill=skill, subskill=subskill):
                question = generate_question(skill, 2, "typed", subskill=subskill)
                self.assertEqual(question.skill, skill)
                self.assertEqual(question.subskill, subskill)

    def test_pre_algebra_key_subskills_have_active_source_templates(self) -> None:
        for subskill in PRE_ALGEBRA_SOURCE_BACKED_SUBSKILLS:
            with self.subTest(subskill=subskill):
                self.assertGreater(self._active_template_count("pre_algebra", subskill=subskill), 0)

    def test_early_math_catalog_subskills_have_importable_templates(self) -> None:
        with imported_early_math_data_dir() as temp_data_dir:
            db_path = temp_data_dir / "app.db"
            for spec in early_math_specs():
                with self.subTest(skill=spec.skill, subskill=spec.subskill):
                    with closing(sqlite3.connect(db_path)) as conn:
                        row = conn.execute(
                            """
                            SELECT COUNT(*)
                            FROM question_templates
                            WHERE active = 1 AND skill = ? AND subskill = ?
                            """,
                            (spec.skill, spec.subskill),
                        ).fetchone()
                    assert row is not None
                    self.assertGreater(int(row[0]), 0)

    def test_native_collapsed_tracks_generate_explicit_subskills(self) -> None:
        for skill, subskill in NATIVE_COLLAPSED_SUBSKILLS.items():
            with self.subTest(skill=skill, subskill=subskill):
                question = generate_question(skill, 2, "typed", subskill=subskill)
                self.assertEqual(question.skill, skill)
                self.assertEqual(question.subskill, subskill)

    def test_template_only_missing_subskill_raises_content_unavailable(self) -> None:
        with self.assertRaises(ContentUnavailableError):
            generate_question("sat_math", 2, "typed", subskill="Confidence intervals")

    def test_exposed_nonlegacy_skills_have_curriculum_entries_and_local_pdfs(self) -> None:
        by_skill = self._curriculum_index_by_skill()
        for skill in SKILLS:
            with self.subTest(skill=skill):
                self.assertIn(skill, by_skill)
                self.assertIsNotNone(curriculum_pdf_path(skill))

    def test_long_arithmetic_skills_use_basic_arithmetic_source(self) -> None:
        by_skill = self._curriculum_index_by_skill()
        self.assertEqual(by_skill["long_subtraction"]["pdf"], "basic_arithmetic_student_workbook.pdf")
        self.assertEqual(by_skill["long_multiplication"]["pdf"], "basic_arithmetic_student_workbook.pdf")


if __name__ == "__main__":
    unittest.main()
