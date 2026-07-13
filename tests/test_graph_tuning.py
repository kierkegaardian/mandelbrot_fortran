from __future__ import annotations

import unittest

from app.graph_tuning import build_monthly_graph_tuning_report, render_monthly_graph_tuning_markdown
from app.models import QuizAttempt


def _attempt(attempt_id: int, skill: str, score: int, total: int, created_at: str) -> QuizAttempt:
    return QuizAttempt(
        id=attempt_id,
        profile_id=1,
        quiz_set_id=None,
        skill=skill,
        question_type="both",
        num_questions=total,
        level=1,
        score=score,
        created_at=created_at,
        elapsed_seconds=120.0,
    )


class GraphTuningTests(unittest.TestCase):
    def test_monthly_report_increases_prereq_weight_from_recent_weak_evidence(self) -> None:
        report = build_monthly_graph_tuning_report(
            attempts=[
                _attempt(1, "target", 5, 10, "2026-05-01T12:00:00+00:00"),
                _attempt(2, "target", 6, 10, "2026-06-20T12:00:00+00:00"),
                _attempt(3, "target", 6, 10, "2026-06-22T12:00:00+00:00"),
                _attempt(4, "prereq", 5, 10, "2026-06-21T12:00:00+00:00"),
                _attempt(5, "prereq", 6, 10, "2026-06-23T12:00:00+00:00"),
            ],
            skill_order=("prereq", "target"),
            prerequisites={"target": (("prereq", "required_for_readiness", 0.8),), "prereq": ()},
            now_iso_text="2026-06-26T12:00:00+00:00",
        )

        self.assertEqual(report.attempt_count, 4)
        self.assertEqual(len(report.suggestions), 1)
        suggestion = report.suggestions[0]
        self.assertEqual(suggestion.action, "increase")
        self.assertEqual(suggestion.target_skill, "target")
        self.assertEqual(suggestion.prerequisite_skill, "prereq")
        self.assertGreater(suggestion.suggested_delta, 0)

    def test_monthly_report_tapers_when_target_and_prereq_are_stable(self) -> None:
        report = build_monthly_graph_tuning_report(
            attempts=[
                _attempt(1, "target", 9, 10, "2026-06-20T12:00:00+00:00"),
                _attempt(2, "target", 10, 10, "2026-06-22T12:00:00+00:00"),
                _attempt(3, "prereq", 9, 10, "2026-06-21T12:00:00+00:00"),
                _attempt(4, "prereq", 10, 10, "2026-06-23T12:00:00+00:00"),
            ],
            skill_order=("prereq", "target"),
            prerequisites={"target": (("prereq", "required_for_readiness", 0.8),), "prereq": ()},
            now_iso_text="2026-06-26T12:00:00+00:00",
        )

        self.assertEqual(len(report.suggestions), 1)
        self.assertEqual(report.suggestions[0].action, "taper")
        self.assertLess(report.suggestions[0].suggested_delta, 0)

    def test_monthly_report_markdown_is_parent_reviewable(self) -> None:
        report = build_monthly_graph_tuning_report(
            attempts=[
                _attempt(1, "target", 6, 10, "2026-06-20T12:00:00+00:00"),
                _attempt(2, "target", 6, 10, "2026-06-22T12:00:00+00:00"),
                _attempt(3, "prereq", 5, 10, "2026-06-21T12:00:00+00:00"),
            ],
            skill_order=("prereq", "target"),
            prerequisites={"target": (("prereq", 0.8),), "prereq": ()},
            now_iso_text="2026-06-26T12:00:00+00:00",
        )

        markdown = render_monthly_graph_tuning_markdown(report)

        self.assertIn("# Monthly Graph Tuning Review", markdown)
        self.assertIn("Recent attempts reviewed: 3", markdown)
        self.assertIn("| target | prereq | increase | +0.10 |", markdown)


if __name__ == "__main__":
    unittest.main()
