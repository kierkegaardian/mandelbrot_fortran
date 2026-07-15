from __future__ import annotations

from .assignments import (
    assignment_completion_analytics,
    create_assignment,
    evaluate_assignments_for_attempt,
    get_next_active_assignment,
    list_assignments,
    set_assignment_active,
)
from .attempts import add_question_result, create_attempt, list_attempts, mode_accuracy_by_skill
from .books import add_exercise_candidate, create_book, list_books, list_exercise_candidates
from .connection import (
    DbConfig,
    connect,
    db_config,
    get_db_config,
    override_db_config,
    reset_db_config,
    set_db_config,
)
from .daily_goals import daily_goal_status, list_daily_goal_history, record_daily_review_completion
from .historical import (
    apply_historical_answer_key,
    list_historical_questions,
    list_historical_questions_for_test,
    list_historical_tests,
    replace_historical_questions,
    upsert_historical_test,
)
from .profiles import create_profile, delete_profile, list_profiles
from .progress import list_subskill_progress, upsert_subskill_progress
from .quiz_sets import create_quiz_set, delete_quiz_set, list_quiz_sets, update_quiz_set
from .schema import init_db
from .templates import (
    add_template_var,
    create_question_template,
    delete_template_by_external_id,
    delete_templates_by_identity,
    list_all_question_templates,
    list_question_templates,
    list_template_vars,
)
from .worksheets import create_worksheet, skill_progress_pipeline


__all__ = (
    "DbConfig",
    "add_exercise_candidate",
    "add_question_result",
    "add_template_var",
    "apply_historical_answer_key",
    "assignment_completion_analytics",
    "connect",
    "create_assignment",
    "create_attempt",
    "create_book",
    "create_profile",
    "create_question_template",
    "create_quiz_set",
    "create_worksheet",
    "daily_goal_status",
    "db_config",
    "delete_profile",
    "delete_quiz_set",
    "delete_template_by_external_id",
    "delete_templates_by_identity",
    "evaluate_assignments_for_attempt",
    "get_db_config",
    "get_next_active_assignment",
    "init_db",
    "list_all_question_templates",
    "list_assignments",
    "list_attempts",
    "list_books",
    "list_daily_goal_history",
    "list_exercise_candidates",
    "list_historical_questions",
    "list_historical_questions_for_test",
    "list_historical_tests",
    "list_profiles",
    "list_question_templates",
    "list_quiz_sets",
    "list_subskill_progress",
    "list_template_vars",
    "mode_accuracy_by_skill",
    "override_db_config",
    "record_daily_review_completion",
    "replace_historical_questions",
    "reset_db_config",
    "set_assignment_active",
    "set_db_config",
    "skill_progress_pipeline",
    "update_quiz_set",
    "upsert_historical_test",
    "upsert_subskill_progress",
)
