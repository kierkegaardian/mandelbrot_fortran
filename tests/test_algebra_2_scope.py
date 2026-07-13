from __future__ import annotations

import unittest

from app.algebra_2_generators import ALGEBRA_2_SUBSKILLS
from app.explanations import ARITHMETIC_MODE_EXPLANATIONS, explanation_for
from app.quiz_engine import generate_question
from app.skill_graph import subskills_for
from app.ui_arithmetic import khan_url_for_selection, lesson_link_state
from app.ui_settings import UiSettings


ALGEBRA_2_ROADMAP_GROUPS: dict[str, tuple[str, ...]] = {
    "Functions: domain/range, inverse, composition": (
        "Domain and range",
        "Inverse and composition",
        "Transformations of functions",
        "Modeling",
    ),
    "Exponentials/logarithms and growth/decay models": (
        "Rational exponents and radicals",
        "Exponential models",
        "Logarithms",
    ),
    "Rational expressions, complex numbers, sequences/series": (
        "Polynomial arithmetic",
        "Complex numbers",
        "Polynomial factorization",
        "Polynomial division",
        "Polynomial graphs",
        "Rational expressions",
        "Rational functions",
        "Sequences and series",
    ),
}


class Algebra2ScopeTests(unittest.TestCase):
    def test_algebra_2_roadmap_groups_are_visible(self) -> None:
        visible = set(subskills_for("algebra_2"))
        self.assertEqual(ALGEBRA_2_SUBSKILLS, subskills_for("algebra_2"))
        for group, subskills in ALGEBRA_2_ROADMAP_GROUPS.items():
            with self.subTest(group=group):
                self.assertTrue(set(subskills).issubset(visible))

    def test_algebra_2_subskills_generate_mc_and_typed_questions(self) -> None:
        for subskill in ALGEBRA_2_SUBSKILLS:
            for question_type in ("mc", "typed"):
                with self.subTest(subskill=subskill, question_type=question_type):
                    question = generate_question("algebra_2", 2, question_type, subskill=subskill)
                    self.assertEqual("algebra_2", question.skill)
                    self.assertEqual(subskill, question.subskill)
                    self.assertTrue(question.correct_answer)
                    if question_type == "mc":
                        self.assertIsNotNone(question.choices)
                        self.assertEqual(4, len(question.choices or ()))

    def test_algebra_2_subskills_have_specific_intuition_and_links(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["algebra_2"]
        links_off = UiSettings(show_external_links=False, enforce_offline_mode=False)
        links_on = UiSettings(show_external_links=True, enforce_offline_mode=False)

        for subskill in ALGEBRA_2_SUBSKILLS:
            with self.subTest(subskill=subskill):
                explanation = explanation_for("algebra_2", subskill)
                self.assertTrue(explanation.mental_model)
                self.assertTrue(explanation.common_mistake)
                self.assertTrue(explanation.try_this)
                self.assertNotEqual(generic.mental_model, explanation.mental_model)

                url = khan_url_for_selection("algebra_2", subskill)
                self.assertTrue(url.startswith("https://www.khanacademy.org/"))
                self.assertFalse(lesson_link_state("algebra_2", subskill, links_off).enabled)
                enabled = lesson_link_state("algebra_2", subskill, links_on)
                self.assertTrue(enabled.enabled)
                self.assertEqual(url, enabled.url)


if __name__ == "__main__":
    unittest.main()
