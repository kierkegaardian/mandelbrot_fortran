"""Tests for the newly added place_value and measurement skills (G2/G3)."""

from __future__ import annotations

import unittest


class TestPlaceValueSkillIntegration(unittest.TestCase):
    """Verify place_value is wired into all required data structures."""

    def test_in_skills_list(self) -> None:
        from app.quiz_engine import SKILLS
        self.assertIn("place_value", SKILLS)

    def test_has_label(self) -> None:
        from app.skill_graph import SKILL_LABELS
        self.assertIn("place_value", SKILL_LABELS)
        self.assertIn("Place Value", SKILL_LABELS["place_value"])

    def test_in_arithmetic_skills(self) -> None:
        from app.skill_graph import ARITHMETIC_SKILLS
        self.assertIn("place_value", ARITHMETIC_SKILLS)

    def test_in_skill_tracks(self) -> None:
        from app.skill_graph import SKILL_TRACKS
        self.assertIn("place_value", SKILL_TRACKS["Arithmetic"])

    def test_has_prerequisite_edges(self) -> None:
        from app.skill_graph import SKILL_PREREQUISITE_EDGES
        self.assertIn("place_value", SKILL_PREREQUISITE_EDGES)
        sources = [edge[0] for edge in SKILL_PREREQUISITE_EDGES["place_value"]]
        self.assertIn("counting", sources)

    def test_has_subskills(self) -> None:
        from app.skill_graph import SKILL_SUBSKILLS
        self.assertIn("place_value", SKILL_SUBSKILLS)
        subs = SKILL_SUBSKILLS["place_value"]
        self.assertIn("Ones, tens, and hundreds identification", subs)
        self.assertIn("Expanded form", subs)
        self.assertIn("Compare numbers by place value", subs)

    def test_has_explanation(self) -> None:
        from app.explanations import ARITHMETIC_MODE_EXPLANATIONS
        self.assertIn("place_value", ARITHMETIC_MODE_EXPLANATIONS)
        exp = ARITHMETIC_MODE_EXPLANATIONS["place_value"]
        self.assertTrue(exp.mental_model)
        self.assertTrue(exp.common_mistake)
        self.assertTrue(exp.try_this)

    def test_khan_url_registered(self) -> None:
        from app.ui_arithmetic import KHAN_URL_BY_SKILL
        self.assertIn("place_value", KHAN_URL_BY_SKILL)
        self.assertTrue(KHAN_URL_BY_SKILL["place_value"].startswith("https://"))


class TestMeasurementSkillIntegration(unittest.TestCase):
    """Verify measurement is wired into all required data structures."""

    def test_in_skills_list(self) -> None:
        from app.quiz_engine import SKILLS
        self.assertIn("measurement", SKILLS)

    def test_has_label(self) -> None:
        from app.skill_graph import SKILL_LABELS
        self.assertIn("measurement", SKILL_LABELS)
        self.assertIn("Measurement", SKILL_LABELS["measurement"])

    def test_in_arithmetic_skills(self) -> None:
        from app.skill_graph import ARITHMETIC_SKILLS
        self.assertIn("measurement", ARITHMETIC_SKILLS)

    def test_in_skill_tracks(self) -> None:
        from app.skill_graph import SKILL_TRACKS
        self.assertIn("measurement", SKILL_TRACKS["Arithmetic"])

    def test_has_prerequisite_edges(self) -> None:
        from app.skill_graph import SKILL_PREREQUISITE_EDGES
        self.assertIn("measurement", SKILL_PREREQUISITE_EDGES)
        sources = [edge[0] for edge in SKILL_PREREQUISITE_EDGES["measurement"]]
        self.assertIn("add_subtract", sources)

    def test_has_subskills(self) -> None:
        from app.skill_graph import SKILL_SUBSKILLS
        self.assertIn("measurement", SKILL_SUBSKILLS)
        subs = SKILL_SUBSKILLS["measurement"]
        self.assertIn("Length unit conversion", subs)
        self.assertIn("Time reading and arithmetic", subs)
        self.assertIn("Capacity and weight units", subs)
        self.assertIn("Temperature basics", subs)

    def test_has_explanation(self) -> None:
        from app.explanations import ARITHMETIC_MODE_EXPLANATIONS
        self.assertIn("measurement", ARITHMETIC_MODE_EXPLANATIONS)
        exp = ARITHMETIC_MODE_EXPLANATIONS["measurement"]
        self.assertTrue(exp.mental_model)
        self.assertTrue(exp.common_mistake)
        self.assertTrue(exp.try_this)

    def test_khan_url_registered(self) -> None:
        from app.ui_arithmetic import KHAN_URL_BY_SKILL
        self.assertIn("measurement", KHAN_URL_BY_SKILL)
        self.assertTrue(KHAN_URL_BY_SKILL["measurement"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()
