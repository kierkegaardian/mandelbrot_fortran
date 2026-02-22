from __future__ import annotations

import unittest

from app.learning_engine import (
    SkillStats,
    build_blended_plan,
    build_free_mode_plan,
    build_skill_stats,
    frontier_skills,
    recommend_next_skill_paths,
    recommend_next_skills_soft,
)
from app.models import QuizAttempt


class LearningEngineSignalTests(unittest.TestCase):
    def test_build_skill_stats_tracks_streak_speed_and_trend(self) -> None:
        attempts = [
            QuizAttempt(1, 1, None, "add_subtract", "both", 10, 1, 6, "2026-02-18T01:00:00+00:00", 100.0),
            QuizAttempt(2, 1, None, "add_subtract", "both", 10, 1, 7, "2026-02-18T02:00:00+00:00", 120.0),
            QuizAttempt(3, 1, None, "add_subtract", "both", 10, 1, 10, "2026-02-18T03:00:00+00:00", 80.0),
            QuizAttempt(4, 1, None, "add_subtract", "both", 10, 1, 10, "2026-02-18T04:00:00+00:00", 70.0),
        ]
        stats = build_skill_stats(attempts, ("add_subtract",))
        item = stats["add_subtract"]
        self.assertEqual(item.perfect_attempts, 2)
        self.assertEqual(item.perfect_streak, 2)
        self.assertAlmostEqual(item.avg_seconds_per_question or 0.0, 9.25, places=2)
        self.assertGreater(item.recent_trend, 0.0)

    def test_recommendation_prioritizes_low_subskill_coverage(self) -> None:
        stats = {
            "skill_a": SkillStats("skill_a", 3, 30, 21, 70.0, 70.0, 1, 0, 8.0, 0.0, "Developing"),
            "skill_b": SkillStats("skill_b", 3, 30, 21, 70.0, 70.0, 1, 0, 8.0, 0.0, "Developing"),
        }
        recommended = recommend_next_skills_soft(
            ("skill_a", "skill_b"),
            {"skill_a": (), "skill_b": ()},
            stats,
            subskill_coverage={"skill_a": 0.9, "skill_b": 0.1},
            limit=1,
        )
        self.assertEqual(recommended, ["skill_b"])

    def test_branch_recommendation_includes_reason_and_unlock_signal(self) -> None:
        stats = {
            "foundation": SkillStats("foundation", 4, 40, 36, 90.0, 90.0, 1, 1, 7.0, 1.0, "Proficient"),
            "branch_a": SkillStats("branch_a", 0, 0, 0, 0.0, 0.0, 0, 0, None, 0.0, "Not started"),
            "branch_b": SkillStats("branch_b", 0, 0, 0, 0.0, 0.0, 0, 0, None, 0.0, "Not started"),
            "capstone": SkillStats("capstone", 0, 0, 0, 0.0, 0.0, 0, 0, None, 0.0, "Not started"),
        }
        recommendations = recommend_next_skill_paths(
            ("foundation", "branch_a", "branch_b", "capstone"),
            {
                "foundation": (),
                "branch_a": (("foundation", 1.0),),
                "branch_b": (("foundation", 1.0),),
                "capstone": (("branch_a", 1.0), ("branch_b", 1.0)),
            },
            stats,
            subskill_coverage={"branch_a": 0.9, "branch_b": 0.1},
            limit=1,
        )
        self.assertEqual(recommendations[0].skill, "branch_b")
        self.assertTrue(any(reason.startswith("Builds on Foundation") for reason in recommendations[0].reasons))
        self.assertTrue(any(reason.startswith("Unlocks ") for reason in recommendations[0].reasons))

    def test_blend_policy_enforces_review_floor_when_pool_exists(self) -> None:
        stats = {
            "target": SkillStats("target", 2, 20, 14, 70.0, 70.0, 0, 0, 9.0, -2.0, "Developing"),
            "review_skill": SkillStats("review_skill", 2, 20, 18, 90.0, 90.0, 1, 1, 7.0, 1.0, "Proficient"),
        }
        items, _policy = build_blended_plan(
            target_skill="target",
            num_questions=6,
            skill_order=("target", "review_skill"),
            prerequisites={"target": (("review_skill", 1.0),), "review_skill": ()},
            stats=stats,
        )
        review_count = sum(1 for item in items if item.label == "Review")
        self.assertGreaterEqual(review_count, 1)

    def test_free_mode_plan_has_preview_prereq_review_labels(self) -> None:
        stats = {
            "target": SkillStats("target", 3, 30, 24, 80.0, 80.0, 1, 1, 8.0, 1.0, "Developing"),
            "next_skill": SkillStats("next_skill", 1, 10, 7, 70.0, 70.0, 0, 0, 10.0, -2.0, "Developing"),
            "review_skill": SkillStats("review_skill", 4, 40, 36, 90.0, 90.0, 2, 2, 7.0, 2.0, "Proficient"),
        }
        items, _policy = build_free_mode_plan(
            target_skill="target",
            num_questions=10,
            skill_order=("target", "next_skill", "review_skill"),
            prerequisites={"target": (("review_skill", 1.0),), "next_skill": (), "review_skill": ()},
            stats=stats,
        )
        labels = {item.label for item in items}
        self.assertIn("Core", labels)
        self.assertIn("Preview", labels)
        self.assertIn("Prereq", labels)
        self.assertIn("Review", labels)

    def test_frontier_skills_prefers_branch_ready_nodes(self) -> None:
        stats = {
            "counting": SkillStats("counting", 3, 30, 30, 98.0, 100.0, 3, 3, 6.0, 1.0, "Mastered"),
            "add_subtract": SkillStats("add_subtract", 3, 30, 27, 90.0, 90.0, 1, 1, 7.0, 1.0, "Proficient"),
            "multiply": SkillStats("multiply", 0, 0, 0, 0.0, 0.0, 0, 0, None, 0.0, "Not started"),
            "divide": SkillStats("divide", 0, 0, 0, 0.0, 0.0, 0, 0, None, 0.0, "Not started"),
        }
        frontier = frontier_skills(
            ("counting", "add_subtract", "multiply", "divide"),
            {
                "counting": (),
                "add_subtract": (("counting", 1.0),),
                "multiply": (("add_subtract", 1.0),),
                "divide": (("add_subtract", 1.0),),
            },
            stats,
        )
        self.assertEqual(frontier[0], "multiply")
        self.assertIn("divide", frontier)


if __name__ == "__main__":
    unittest.main()
