from __future__ import annotations

import unittest

from app.explanations import ARITHMETIC_MODE_EXPLANATIONS, explanation_for
from app.quiz_engine import generate_question
from app.skill_graph import subskills_for
from app.statistics_catalog import STATISTICS_SUBSKILLS
from app.ui_arithmetic import khan_url_for_selection, lesson_link_state
from app.ui_settings import UiSettings


STATISTICS_ROADMAP_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {
    "Data collection, distributions, center/spread, standard deviation": (
        ("statistics", "Data collection and study design"),
        ("statistics", "Distributions and standard deviation"),
        ("data_analysis", "Center, spread, and shape"),
        ("data_analysis", "Median, range, and IQR"),
        ("data_analysis", "Variability in data"),
    ),
    "Probability rules, combinatorics, expected value": (
        ("statistics", "Probability rules"),
        ("statistics", "Combinatorics"),
        ("statistics", "Expected value"),
        ("stats_probability", "Probability models"),
    ),
    "Sampling, confidence intervals, hypothesis tests": (
        ("statistics", "Sampling and margin of error"),
        ("statistics", "Confidence intervals"),
        ("statistics", "Hypothesis tests"),
        ("data_analysis", "Sample inferences from displays"),
    ),
    "Correlation/regression; interpreting results": (
        ("statistics", "Correlation and regression"),
    ),
}


class StatisticsScopeTests(unittest.TestCase):
    def test_statistics_roadmap_groups_are_visible(self) -> None:
        visible = {
            (skill, subskill)
            for skill in ("statistics", "data_analysis", "stats_probability")
            for subskill in subskills_for(skill)
        }

        self.assertEqual(STATISTICS_SUBSKILLS, subskills_for("statistics"))
        for group, subskills in STATISTICS_ROADMAP_GROUPS.items():
            with self.subTest(group=group):
                self.assertTrue(set(subskills).issubset(visible))

    def test_statistics_subskills_generate_mc_and_typed_questions(self) -> None:
        for subskill in STATISTICS_SUBSKILLS:
            for question_type in ("mc", "typed"):
                with self.subTest(subskill=subskill, question_type=question_type):
                    question = generate_question("statistics", 2, question_type, subskill=subskill)
                    self.assertEqual("statistics", question.skill)
                    self.assertEqual(subskill, question.subskill)
                    self.assertTrue(question.correct_answer)
                    if question_type == "mc":
                        self.assertIsNotNone(question.choices)
                        self.assertEqual(4, len(question.choices or ()))

    def test_statistics_subskills_have_specific_intuition_and_links(self) -> None:
        generic = ARITHMETIC_MODE_EXPLANATIONS["statistics"]
        links_off = UiSettings(show_external_links=False, enforce_offline_mode=False)
        links_on = UiSettings(show_external_links=True, enforce_offline_mode=False)

        for subskill in STATISTICS_SUBSKILLS:
            with self.subTest(subskill=subskill):
                explanation = explanation_for("statistics", subskill)
                self.assertTrue(explanation.mental_model)
                self.assertTrue(explanation.common_mistake)
                self.assertTrue(explanation.try_this)
                self.assertNotEqual(generic.mental_model, explanation.mental_model)

                url = khan_url_for_selection("statistics", subskill)
                self.assertTrue(url.startswith("https://www.khanacademy.org/"))
                self.assertFalse(lesson_link_state("statistics", subskill, links_off).enabled)
                enabled = lesson_link_state("statistics", subskill, links_on)
                self.assertTrue(enabled.enabled)
                self.assertEqual(url, enabled.url)


if __name__ == "__main__":
    unittest.main()
