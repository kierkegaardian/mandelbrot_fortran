from __future__ import annotations

import unittest

from app.data_analysis import DATA_ANALYSIS_SUBSKILLS
from app.explanations import explanation_for
from app.quiz_engine import generate_question
from app.ui_arithmetic import khan_url_for_selection, lesson_link_state
from app.ui_settings import UiSettings


class DataAnalysisSkillTests(unittest.TestCase):
    def test_data_analysis_subskills_generate_questions(self) -> None:
        for subskill in DATA_ANALYSIS_SUBSKILLS:
            with self.subTest(subskill=subskill):
                question = generate_question("data_analysis", 2, "mc", subskill=subskill)
                self.assertEqual("data_analysis", question.skill)
                self.assertEqual(subskill, question.subskill)
                self.assertTrue(question.correct_answer)

    def test_data_analysis_subskills_have_intuition_and_khan_links(self) -> None:
        for subskill in DATA_ANALYSIS_SUBSKILLS:
            with self.subTest(subskill=subskill):
                explanation = explanation_for("data_analysis", subskill)
                self.assertTrue(explanation.mental_model)
                self.assertTrue(explanation.common_mistake)
                self.assertTrue(explanation.try_this)
                self.assertTrue(khan_url_for_selection("data_analysis", subskill).startswith("https://"))

    def test_data_analysis_external_links_remain_parent_controlled(self) -> None:
        subskill = "Box plots"
        disabled = lesson_link_state(
            "data_analysis",
            subskill,
            UiSettings(show_external_links=False, enforce_offline_mode=False),
        )
        offline = lesson_link_state(
            "data_analysis",
            subskill,
            UiSettings(show_external_links=True, enforce_offline_mode=True),
        )
        enabled = lesson_link_state(
            "data_analysis",
            subskill,
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )

        self.assertFalse(disabled.enabled)
        self.assertFalse(offline.enabled)
        self.assertTrue(enabled.enabled)
        self.assertEqual(khan_url_for_selection("data_analysis", subskill), enabled.url)


if __name__ == "__main__":
    unittest.main()
