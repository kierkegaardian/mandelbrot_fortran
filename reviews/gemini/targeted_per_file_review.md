# Gemini Targeted Per-File Review (Diff-Based)

Generated: 2026-02-18T05:22:20Z

## app/learning_engine.py

The following technical review of `app/learning_engine.py` identifies issues related to progression logic, statistical sensitivity, and scoring biases.

### [P1] Hard retake bottleneck in "soft" recommendation logic
Lines 82-95: The `recommend_next_skills_soft` function contains a logic block that forces a "hard" progression gate. If any skill in `skill_order` has been attempted but never perfected (`perfect_attempts == 0`), the function returns early with only those retake candidates. This completely prevents the recommendation of new skills or progression to other ready topics until every previously touched skill is perfected, which contradicts the "soft" designation and may frustrate users.

### [P1] Statistical "stickiness" due to low EWMA alpha
Lines 377, 414-420: The Exponentially Weighted Moving Average (`_ewma`) uses an `alpha` of `0.25`. Because the implementation initializes the score with the first attempt's value (`score = float(values[0])`), the very first attempt retains 75% influence after the second attempt and nearly 24% after five attempts. Given that `mastery_label` (line 404) weights this "sticky" average at 70%, a user who starts poorly will find it mathematically difficult to reach "Proficient" or "Mastered" status even with a significant streak of recent high scores.

### [P2] Scoring bias against entry-level skills
Lines 423-440: The `_prereq_readiness` function returns a default score of `20.0` for skills with no prerequisites (line 426). However, a skill whose prerequisites are all "Mastered" will result in a readiness score of `30.0` (line 439: `1.0 * 30.0`). This creates a systemic bias in `recommend_next_skills_soft` that favors continuing existing learning paths over starting new, independent "entry-level" skills that have no dependencies.

### [P2] Incomplete history in `build_skill_stats`
Lines 68-71: The `build_skill_stats` function only generates statistics for skills explicitly present in the provided `skill_order`. If the curriculum has been updated (skills renamed or removed), any historical attempts for those skills are silently dropped from the returned dictionary. This can lead to a loss of user progress data or "invisible" attempts if the learning engine is used to analyze historical performance across curriculum versions.

### [P2] Linear position penalty outweighs performance metrics
Line 118: The recommendation score is penalized by `-(idx * 0.2)` based on the skill's index in the curriculum. In a large curriculum (e.g., 50+ skills), the penalty for skills later in the list (-10.0 or more) can easily negate high `recent_performance` (max ~21.25) or `downward_trend` (max ~35.0) bonuses. This makes the recommendation engine heavily biased towards the static order rather than the user's actual performance gaps.

### [P2] "Review" item suppression in small blended plans
Lines 212-214: In `build_blended_plan`, `core_count` and `prereq_count` are calculated using `round()`, and `review_count` is the remaining residual. For small `num_questions` (e.g., 2 or 3), rounding up both the core and prereq counts frequently reduces the `review_count` to 0, even if the policy intended for a 15% review component. While mitigated for plans where `total >= 6` (line 226), short quizzes will consistently lack variety.

### [P3] Strict "Mastered" requirement for perfect attempts
Lines 405-406: The "Mastered" label requires `perfect_attempts >= 1`. In a system with large question banks, a user might maintain a 98% average over dozens of attempts but never achieve a 100% "perfect" score due to the probability of hitting a single difficult item. Capping such users at "Proficient" regardless of their high volume and weighted accuracy may be demotivating.

**Residual Risks & Assumptions:**
*   **Performance:** `build_skill_stats` performs a sort on the entire attempt history for every skill every time it is called; this may become a bottleneck if a user accumulates thousands of attempts.
*   **Prerequisite Weights:** `_prereq_edges` assumes weight defaults to `1.0` if not specified, which is consistent but requires that the `prerequisites` dictionary follows a specific schema not strictly enforced by types here.

---

## app/ui_quiz.py

