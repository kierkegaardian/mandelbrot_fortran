from __future__ import annotations

import unittest

from app.learning_engine import (
    ModeMix,
    SkillStats,
    apply_word_gap_boost,
    default_mode_mix_for_stage,
    mastery_label,
)


class LearningEngineModeMixTests(unittest.TestCase):
    def test_stage_mix_early(self) -> None:
        self.assertEqual(default_mode_mix_for_stage(None), ModeMix(intuition=45, expression=40, word=15))

    def test_stage_mix_developing(self) -> None:
        stats = SkillStats(
            skill="add_subtract",
            attempts=3,
            total_questions=30,
            correct_questions=18,
            weighted_accuracy=60.0,
            recent_accuracy=60.0,
            perfect_attempts=0,
            perfect_streak=0,
            avg_seconds_per_question=9.5,
            recent_trend=2.0,
            mastery="Developing",
        )
        self.assertEqual(default_mode_mix_for_stage(stats), ModeMix(intuition=30, expression=45, word=25))

    def test_stage_mix_near_mastery(self) -> None:
        stats = SkillStats(
            skill="add_subtract",
            attempts=6,
            total_questions=60,
            correct_questions=56,
            weighted_accuracy=92.0,
            recent_accuracy=94.0,
            perfect_attempts=1,
            perfect_streak=1,
            avg_seconds_per_question=7.2,
            recent_trend=4.0,
            mastery="Proficient",
        )
        self.assertEqual(default_mode_mix_for_stage(stats), ModeMix(intuition=20, expression=40, word=40))

    def test_word_gap_boost_thresholds(self) -> None:
        base = ModeMix(intuition=30, expression=45, word=25)
        self.assertEqual(apply_word_gap_boost(base, 80.0, 73.0), base)
        self.assertEqual(apply_word_gap_boost(base, 80.0, 70.0), ModeMix(intuition=30, expression=35, word=35))
        self.assertEqual(apply_word_gap_boost(base, 80.0, 55.0), ModeMix(intuition=30, expression=25, word=45))

    def test_mastery_label_does_not_require_perfect_attempt(self) -> None:
        self.assertEqual(mastery_label(4, 95.0, 95.0, 0), "Mastered")


if __name__ == "__main__":
    unittest.main()
