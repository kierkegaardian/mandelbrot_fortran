from __future__ import annotations

import unittest

from app.explanations import ARITHMETIC_MODE_EXPLANATIONS, explanation_for
from app.quiz_engine import TRIG_PRECALCULUS_SUBSKILLS, generate_question
from app.skill_graph import subskills_for
from app.ui_arithmetic import khan_url_for_selection, lesson_link_state
from app.ui_settings import UiSettings


PRECALCULUS_ROADMAP_GROUPS: dict[str, tuple[str, ...]] = {
    "Unit circle, trig functions/graphs, identities, inverse trig": (
        "Right-triangle trig ratios",
        "Unit circle trig values",
        "Trig functions and graphs",
        "Trig identities",
        "Inverse trig",
    ),
    "Vectors, matrices (intro), polar coordinates": (
        "Vectors",
        "Matrices and linear transformations",
        "Polar coordinates",
    ),
}


class PrecalculusScopeTests(unittest.TestCase):
    def test_precalculus_roadmap_groups_are_visible(self) -> None:
        visible = set(subskills_for("trig_right_triangle"))

        self.assertEqual(TRIG_PRECALCULUS_SUBSKILLS, subskills_for("trig_right_triangle"))
        for group, subskills in PRECALCULUS_ROADMAP_GROUPS.items():
            with self.subTest(group=group):
                self.assertTrue(set(subskills).issubset(visible))

    def test_precalculus_subskills_generate_mc_and_typed_questions(self) -> None:
        for subskill in TRIG_PRECALCULUS_SUBSKILLS:
            for question_type in ("mc", "typed"):
                with self.subTest(subskill=subskill, question_type=question_type):
                    question = generate_question("trig_right_triangle", 2, question_type, subskill=subskill)
                    self.assertEqual("trig_right_triangle", question.skill)
                    self.assertEqual(subskill, question.subskill)
                    self.assertTrue(question.correct_answer)
                    if question_type == "mc":
                        self.assertIsNotNone(question.choices)
                        self.assertEqual(4, len(question.choices or ()))

    def test_precalculus_subskills_have_specific_intuition_and_links(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["trig_right_triangle"]
        links_off = UiSettings(show_external_links=False, enforce_offline_mode=False)
        links_on = UiSettings(show_external_links=True, enforce_offline_mode=False)

        for subskill in TRIG_PRECALCULUS_SUBSKILLS:
            with self.subTest(subskill=subskill):
                explanation = explanation_for("trig_right_triangle", subskill)
                self.assertTrue(explanation.mental_model)
                self.assertTrue(explanation.common_mistake)
                self.assertTrue(explanation.try_this)
                self.assertNotEqual(generic.mental_model, explanation.mental_model)

                url = khan_url_for_selection("trig_right_triangle", subskill)
                self.assertTrue(url.startswith("https://www.khanacademy.org/"))
                self.assertFalse(lesson_link_state("trig_right_triangle", subskill, links_off).enabled)
                enabled = lesson_link_state("trig_right_triangle", subskill, links_on)
                self.assertTrue(enabled.enabled)
                self.assertEqual(url, enabled.url)


if __name__ == "__main__":
    unittest.main()
