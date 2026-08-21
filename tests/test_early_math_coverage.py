from __future__ import annotations

from contextlib import closing
import sqlite3
import unittest

from app.early_math_catalog import EARLY_MATH_SKILLS, early_math_specs, spec_for
from app.skill_graph import skills_in_track, subskills_for

from tests.early_math_test_utils import imported_early_math_data_dir


class EarlyMathCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temp_data = imported_early_math_data_dir()
        cls._data_dir = cls._temp_data.__enter__()
        cls._db_path = cls._data_dir / "app.db"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temp_data.__exit__(None, None, None)

    def _active_template_count(self, skill: str, subskill: str, *, mode: str | None = None) -> int:
        clauses = ["active = 1", "skill = ?", "subskill = ?"]
        params: list[object] = [skill, subskill]
        if mode is not None:
            clauses.append("mode = ?")
            params.append(mode)
        query = "SELECT COUNT(*) FROM question_templates WHERE " + " AND ".join(clauses)
        with closing(sqlite3.connect(self._db_path)) as conn:
            row = conn.execute(query, tuple(params)).fetchone()
        assert row is not None
        return int(row[0])

    def test_every_arithmetic_and_prealgebra_subskill_has_a_catalog_spec(self) -> None:
        for track in ("Arithmetic", "Pre-Algebra"):
            for skill in skills_in_track(track):
                self.assertIn(skill, EARLY_MATH_SKILLS)
                for subskill in subskills_for(skill):
                    with self.subTest(track=track, skill=skill, subskill=subskill):
                        self.assertIsNotNone(spec_for(skill, subskill))

    def test_every_catalog_spec_has_khan_mapping_or_source_rationale(self) -> None:
        for spec in early_math_specs():
            with self.subTest(skill=spec.skill, subskill=spec.subskill):
                self.assertTrue(spec.khan_assignable_url or spec.source_ids)
                if spec.khan_assignable_url:
                    self.assertTrue(spec.khan_assignable_url.startswith("https://www.khanacademy.org/"))

    def test_required_modes_exist_after_manifest_import(self) -> None:
        for spec in early_math_specs():
            with self.subTest(skill=spec.skill, subskill=spec.subskill):
                self.assertGreaterEqual(self._active_template_count(spec.skill, spec.subskill, mode="expression"), 2)
                for mode in spec.required_modes:
                    self.assertGreater(self._active_template_count(spec.skill, spec.subskill, mode=mode), 0)


if __name__ == "__main__":
    unittest.main()
