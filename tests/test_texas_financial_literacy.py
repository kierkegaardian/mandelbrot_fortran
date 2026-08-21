from __future__ import annotations

import unittest

from app.explanations import explanation_for
from app.quiz_engine import generate_question
from app.school_year_assessment import generate_texas_grade_assessment
from app.texas_grade_goals import quiz_ready_goals, texas_grade_plan
from app.ui_arithmetic import khan_url_for_selection, lesson_link_state
from app.ui_settings import UiSettings


EXPECTED_FINANCIAL_REFS: dict[int, str] = {
    1: "1.9",
    2: "2.11",
    3: "3.9",
    4: "4.10",
    5: "5.10",
    6: "6.14",
    7: "7.13",
}


class TexasFinancialLiteracyTests(unittest.TestCase):
    def test_every_grade_has_quiz_ready_personal_finance_goal(self) -> None:
        for grade, ref_root in EXPECTED_FINANCIAL_REFS.items():
            goals = [
                goal
                for goal in quiz_ready_goals(grade)
                if goal.skill == "financial_literacy" and any(ref.startswith(ref_root) for ref in goal.standard_refs)
            ]
            with self.subTest(grade=grade):
                self.assertEqual(1, len(goals))
                self.assertTrue(goals[0].subskills)

    def test_financial_literacy_subskills_generate_with_intuition_and_links(self) -> None:
        subskills = {
            subskill
            for grade in EXPECTED_FINANCIAL_REFS
            for goal in texas_grade_plan(grade).goals
            if goal.skill == "financial_literacy"
            for subskill in goal.subskills
        }
        for subskill in sorted(subskills):
            with self.subTest(subskill=subskill):
                question = generate_question("financial_literacy", 2, "mc", subskill=subskill)
                self.assertEqual("financial_literacy", question.skill)
                self.assertEqual(subskill, question.subskill)
                self.assertTrue(question.correct_answer)

                explanation = explanation_for("financial_literacy", subskill)
                self.assertTrue(explanation.mental_model)
                self.assertTrue(explanation.common_mistake)
                self.assertTrue(explanation.try_this)
                self.assertTrue(khan_url_for_selection("financial_literacy", subskill).startswith("https://"))

    def test_external_financial_literacy_links_stay_parent_controlled(self) -> None:
        subskill = "Budget percentages, net worth, interest, and incentives"
        disabled = lesson_link_state(
            "financial_literacy",
            subskill,
            UiSettings(show_external_links=False, enforce_offline_mode=False),
        )
        enabled = lesson_link_state(
            "financial_literacy",
            subskill,
            UiSettings(show_external_links=True, enforce_offline_mode=False),
        )

        self.assertFalse(disabled.enabled)
        self.assertTrue(enabled.enabled)
        self.assertEqual(khan_url_for_selection("financial_literacy", subskill), enabled.url)

    def test_assessment_packets_include_personal_finance_items(self) -> None:
        grade_one = generate_texas_grade_assessment(1, include_stretch=False, questions_per_subskill=1)
        grade_seven = generate_texas_grade_assessment(7, include_stretch=False, questions_per_subskill=1)

        g1_keys = {(item.goal.code, item.subskill) for item in grade_one.items}
        g7_keys = {(item.goal.code, item.subskill) for item in grade_seven.items}

        self.assertIn(("g1_personal_finance", "Income, gifts, wants, and needs"), g1_keys)
        self.assertIn(("g7_personal_finance", "Budget percentages, net worth, interest, and incentives"), g7_keys)
        self.assertFalse(any("content gap" in note for note in grade_one.skipped))


if __name__ == "__main__":
    unittest.main()
