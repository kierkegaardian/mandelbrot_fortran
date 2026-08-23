from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from app import db
from app.summer_program_template_seed import EXPRESSION_TARGETS, WORD_TARGETS
from scripts.import_template_manifest import import_manifest


REPO_ROOT = Path(__file__).resolve().parents[1]
LINEAR_PREVIEW_MANIFEST = REPO_ROOT / "scripts" / "template_manifests" / "linear_relationships_preview_v1.json"
FUNCTIONS_PREVIEW_MANIFEST = REPO_ROOT / "scripts" / "template_manifests" / "functions_patterns_preview_v1.json"
ALGEBRA_1_CAPSTONE_MANIFEST = REPO_ROOT / "scripts" / "template_manifests" / "algebra_1_preview_capstone_v1.json"
GEOMETRY_MEASUREMENT_MANIFEST = REPO_ROOT / "scripts" / "template_manifests" / "geometry_measurement_preview_v1.json"
COORDINATE_GEOMETRY_MANIFEST = REPO_ROOT / "scripts" / "template_manifests" / "coordinate_geometry_preview_v1.json"


class SummerProgramTemplateSeedTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        tmp_path = self._tmp.name

        def _tmp_config() -> db.DbConfig:
            return db.DbConfig(path=f"{tmp_path}/test_app.db")

        self.enterContext(db.override_db_config(_tmp_config))
        db.init_db()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _count(self, skill: str, subskill: str, mode: str) -> int:
        with db.managed_connection() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*)
                FROM question_templates
                WHERE active = 1 AND skill = ? AND subskill = ? AND mode = ?
                """,
                (skill, subskill, mode),
            ).fetchone()
        assert row is not None
        return int(row[0])

    def test_expression_targets_are_seeded_to_minimums(self) -> None:
        for (skill, subskill), target in EXPRESSION_TARGETS.items():
            with self.subTest(skill=skill, subskill=subskill):
                self.assertGreaterEqual(self._count(skill, subskill, "expression"), target)

    def test_word_targets_are_seeded_to_minimums(self) -> None:
        for (skill, subskill), target in WORD_TARGETS.items():
            with self.subTest(skill=skill, subskill=subskill):
                self.assertGreaterEqual(self._count(skill, subskill, "word"), target)

    def test_linear_preview_manifest_imports_and_replaces_cleanly(self) -> None:
        inserted, replaced = import_manifest(LINEAR_PREVIEW_MANIFEST)
        self.assertEqual(inserted, 6)
        self.assertEqual(replaced, 0)

        inserted, replaced = import_manifest(LINEAR_PREVIEW_MANIFEST)
        self.assertEqual(inserted, 6)
        self.assertEqual(replaced, 6)

        expected = {
            ("algebra_linear", "Slope from points", "expression"),
            ("algebra_linear", "Slope-intercept interpretation", "expression"),
            ("algebra_linear", "Direct variation", "expression"),
            ("algebra_linear", "Rate and unit-rate modeling", "expression"),
            ("algebra_linear", "Word problems with linear models", "expression"),
            ("algebra_linear", "Word problems with linear models", "word"),
        }
        for skill, subskill, mode in expected:
            with self.subTest(skill=skill, subskill=subskill, mode=mode):
                self.assertGreaterEqual(self._count(skill, subskill, mode), 1)

    def test_functions_preview_manifest_imports_and_replaces_cleanly(self) -> None:
        inserted, replaced = import_manifest(FUNCTIONS_PREVIEW_MANIFEST)
        self.assertEqual(inserted, 8)
        self.assertEqual(replaced, 0)

        inserted, replaced = import_manifest(FUNCTIONS_PREVIEW_MANIFEST)
        self.assertEqual(inserted, 8)
        self.assertEqual(replaced, 8)

        expected = {
            ("algebra_1", "Functions", "expression"),
            ("algebra_1", "Functions", "word"),
            ("algebra_1", "Sequences", "expression"),
            ("algebra_1", "Sequences", "word"),
            ("algebra_1", "Linear equations & graphs", "expression"),
            ("algebra_1", "Linear equations & graphs", "word"),
            ("algebra_1", "Solving equations & inequalities", "expression"),
            ("algebra_1", "Solving equations & inequalities", "word"),
        }
        for skill, subskill, mode in expected:
            with self.subTest(skill=skill, subskill=subskill, mode=mode):
                self.assertGreaterEqual(self._count(skill, subskill, mode), 1)

    def test_algebra_1_capstone_manifest_imports_and_replaces_cleanly(self) -> None:
        inserted, replaced = import_manifest(ALGEBRA_1_CAPSTONE_MANIFEST)
        self.assertEqual(inserted, 6)
        self.assertEqual(replaced, 0)

        inserted, replaced = import_manifest(ALGEBRA_1_CAPSTONE_MANIFEST)
        self.assertEqual(inserted, 6)
        self.assertEqual(replaced, 6)

        expected = {
            ("algebra_1", "Slope from points", "expression"),
            ("algebra_1", "Slope from points", "word"),
            ("algebra_1", "Slope-intercept form", "expression"),
            ("algebra_1", "Slope-intercept form", "word"),
            ("algebra_1", "Graphing linear inequalities", "expression"),
            ("algebra_1", "Graphing linear inequalities", "word"),
        }
        for skill, subskill, mode in expected:
            with self.subTest(skill=skill, subskill=subskill, mode=mode):
                self.assertGreaterEqual(self._count(skill, subskill, mode), 1)

    def test_geometry_measurement_manifest_imports_and_replaces_cleanly(self) -> None:
        inserted, replaced = import_manifest(GEOMETRY_MEASUREMENT_MANIFEST)
        self.assertEqual(inserted, 10)
        self.assertEqual(replaced, 0)

        inserted, replaced = import_manifest(GEOMETRY_MEASUREMENT_MANIFEST)
        self.assertEqual(inserted, 10)
        self.assertEqual(replaced, 10)

        expected = {
            ("geometry_area", "Perimeter and missing sides", "expression"),
            ("geometry_area", "Perimeter and missing sides", "word"),
            ("geometry_area", "Area of triangles and parallelograms", "expression"),
            ("geometry_area", "Area of triangles and parallelograms", "word"),
            ("geometry_area", "Circumference and area of circles", "expression"),
            ("geometry_area", "Circumference and area of circles", "word"),
            ("geometry_area", "Surface area and volume", "expression"),
            ("geometry_area", "Surface area and volume", "word"),
            ("geometry_area", "Pythagorean theorem", "expression"),
            ("geometry_area", "Pythagorean theorem", "word"),
        }
        for skill, subskill, mode in expected:
            with self.subTest(skill=skill, subskill=subskill, mode=mode):
                self.assertGreaterEqual(self._count(skill, subskill, mode), 1)

    def test_coordinate_geometry_manifest_imports_and_replaces_cleanly(self) -> None:
        inserted, replaced = import_manifest(COORDINATE_GEOMETRY_MANIFEST)
        self.assertEqual(inserted, 10)
        self.assertEqual(replaced, 0)

        inserted, replaced = import_manifest(COORDINATE_GEOMETRY_MANIFEST)
        self.assertEqual(inserted, 10)
        self.assertEqual(replaced, 10)

        expected = {
            ("geometry_area", "Coordinate geometry distance and midpoint", "expression"),
            ("geometry_area", "Coordinate geometry distance and midpoint", "word"),
            ("geometry_area", "Transformations and congruence", "expression"),
            ("geometry_area", "Transformations and congruence", "word"),
            ("geometry_area", "Similarity and scale factor", "expression"),
            ("geometry_area", "Similarity and scale factor", "word"),
            ("geometry_area", "Analytic geometry and coordinate proofs", "expression"),
            ("geometry_area", "Analytic geometry and coordinate proofs", "word"),
            ("algebra_linear", "Slope from points", "expression"),
            ("algebra_linear", "Slope from points", "word"),
        }
        for skill, subskill, mode in expected:
            with self.subTest(skill=skill, subskill=subskill, mode=mode):
                self.assertGreaterEqual(self._count(skill, subskill, mode), 1)


if __name__ == "__main__":
    unittest.main()
