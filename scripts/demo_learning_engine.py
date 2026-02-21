from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app import db
from app.learning_engine import build_blended_plan, build_skill_stats, recommend_next_skills_soft
from app.models import QuizAttempt
from app.quiz_engine import generate_question
from app.skill_graph import SKILL_ORDER, SKILL_PREREQUISITES
from app.story_wrapper import apply_story_wrapper


def _synthetic_attempts() -> list[QuizAttempt]:
    return [
        QuizAttempt(1, 1, None, "counting", "both", 10, 1, 10, "2026-02-01T10:00:00+00:00"),
        QuizAttempt(2, 1, None, "add_subtract", "both", 10, 1, 8, "2026-02-02T10:00:00+00:00"),
        QuizAttempt(3, 1, None, "add_subtract", "both", 10, 1, 9, "2026-02-03T10:00:00+00:00"),
        QuizAttempt(4, 1, None, "multiply", "both", 10, 1, 6, "2026-02-04T10:00:00+00:00"),
    ]


def _attempts_for_profile(profile_id: int) -> list[QuizAttempt]:
    db.init_db()
    return db.list_attempts(profile_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo learning-engine recommendations and blended planning.")
    parser.add_argument("--profile-id", type=int, default=0, help="Use real attempts for a profile id")
    parser.add_argument("--target", default="multiply", help="Target skill for blended plan")
    parser.add_argument("--questions", type=int, default=10, help="Number of planned questions")
    parser.add_argument("--word-sample-skill", default="add_subtract", help="Skill for story-wrapper sample")
    args = parser.parse_args()

    attempts = _attempts_for_profile(args.profile_id) if args.profile_id > 0 else _synthetic_attempts()
    stats = build_skill_stats(attempts, tuple(SKILL_ORDER))

    recommendations = recommend_next_skills_soft(tuple(SKILL_ORDER), SKILL_PREREQUISITES, stats, limit=5)
    plan, policy = build_blended_plan(
        target_skill=args.target,
        num_questions=args.questions,
        skill_order=tuple(SKILL_ORDER),
        prerequisites=SKILL_PREREQUISITES,
        stats=stats,
    )

    print(f"attempts={len(attempts)} source={'profile' if args.profile_id > 0 else 'synthetic'}")
    print("recommendations=", ", ".join(recommendations) if recommendations else "none")

    for skill in recommendations[:3]:
        item = stats[skill]
        print(
            f"  {skill}: mastery={item.mastery} weighted={item.weighted_accuracy:.1f}% "
            f"recent={item.recent_accuracy:.1f}% perfect_attempts={item.perfect_attempts}"
        )

    print(
        f"blend_policy target={args.target} core/prereq/review="
        f"{policy.core_pct}/{policy.prereq_pct}/{policy.review_pct}"
    )
    label_counts = Counter(item.label for item in plan)
    print(
        f"plan_counts Core={label_counts.get('Core', 0)} "
        f"Prereq={label_counts.get('Prereq', 0)} Review={label_counts.get('Review', 0)}"
    )
    for idx, item in enumerate(plan[: min(12, len(plan))], start=1):
        print(f"  Q{idx:02d}: {item.label:<6} skill={item.skill}")

    sample = generate_question(args.word_sample_skill, 1, "typed", preferred_mode="word")
    if sample.mode != "word":
        import random

        sample = apply_story_wrapper(sample, rng=random)
    print(f"word_sample_skill={args.word_sample_skill} mode={sample.mode}")
    print(f"word_sample_prompt={sample.prompt.splitlines()[0][:180]}")


if __name__ == "__main__":
    main()
