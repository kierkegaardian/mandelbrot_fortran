from __future__ import annotations

import unittest

from app.calculus_catalog import CALCULUS_1_SUBSKILLS, CALCULUS_2_SUBSKILLS, CALCULUS_3_SUBSKILLS
from app.explanations import ARITHMETIC_MODE_EXPLANATIONS, explanation_for
from app.quiz_engine import generate_question
from app.skill_graph import subskills_for
from app.ui_arithmetic import khan_url_for_selection, lesson_link_state
from app.ui_settings import UiSettings


CALCULUS_ROADMAP_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {
    "Limits and continuity": (
        ("calculus_1", "Limits and continuity"),
    ),
    "Derivatives: rules + geometric meaning (slope/velocity)": (
        ("calculus_1", "Average rate of change between two points"),
        ("calculus_1", "Derivative rules"),
        ("calculus_1", "Derivative as slope and velocity"),
    ),
    "Integrals: area/accumulation + basic techniques": (
        ("calculus_2", "Definite integral of a linear function"),
        ("calculus_2", "Accumulation and area under curves"),
        ("calculus_2", "Basic integration techniques"),
    ),
    "Applications: optimization, motion, area between curves": (
        ("calculus_1", "Optimization"),
        ("calculus_1", "Derivative as slope and velocity"),
        ("calculus_2", "Area between curves"),
        ("calculus_3", "Multivariable optimization"),
    ),
}


class CalculusScopeTests(unittest.TestCase):
    def test_calculus_roadmap_groups_are_visible(self) -> None:
        visible = {
            (skill, subskill)
            for skill in ("calculus_1", "calculus_2", "calculus_3")
            for subskill in subskills_for(skill)
        }

        self.assertEqual(CALCULUS_1_SUBSKILLS, subskills_for("calculus_1"))
        self.assertEqual(CALCULUS_2_SUBSKILLS, subskills_for("calculus_2"))
        self.assertEqual(CALCULUS_3_SUBSKILLS, subskills_for("calculus_3"))
        for group, subskills in CALCULUS_ROADMAP_GROUPS.items():
            with self.subTest(group=group):
                self.assertTrue(set(subskills).issubset(visible))

    def test_calculus_subskills_generate_mc_and_typed_questions(self) -> None:
        for skill in ("calculus_1", "calculus_2", "calculus_3"):
            for subskill in subskills_for(skill):
                for question_type in ("mc", "typed"):
                    with self.subTest(skill=skill, subskill=subskill, question_type=question_type):
                        question = generate_question(skill, 2, question_type, subskill=subskill)
                        self.assertEqual(skill, question.skill)
                        self.assertEqual(subskill, question.subskill)
                        self.assertTrue(question.correct_answer)
                        if question_type == "mc":
                            self.assertIsNotNone(question.choices)
                            self.assertEqual(4, len(question.choices or ()))

    def test_calculus_subskills_have_specific_intuition_and_links(self) -> None:
        links_off = UiSettings(show_external_links=False, enforce_offline_mode=False)
        links_on = UiSettings(show_external_links=True, enforce_offline_mode=False)

        for skill in ("calculus_1", "calculus_2", "calculus_3"):
            generic = ARITHMETIC_MODE_EXPLANATIONS[skill]
            for subskill in subskills_for(skill):
                with self.subTest(skill=skill, subskill=subskill):
                    explanation = explanation_for(skill, subskill)
                    self.assertTrue(explanation.mental_model)
                    self.assertTrue(explanation.common_mistake)
                    self.assertTrue(explanation.try_this)
                    self.assertNotEqual(generic.mental_model, explanation.mental_model)

                    url = khan_url_for_selection(skill, subskill)
                    self.assertTrue(url.startswith("https://www.khanacademy.org/"))
                    self.assertFalse(lesson_link_state(skill, subskill, links_off).enabled)
                    enabled = lesson_link_state(skill, subskill, links_on)
                    self.assertTrue(enabled.enabled)
                    self.assertEqual(url, enabled.url)


if __name__ == "__main__":
    unittest.main()
