"""Quiz-launch adapters kept outside the application-shell layout."""

from __future__ import annotations


def _mode_mix(
    intuition: int | None,
    expression: int | None,
    word: int | None,
) -> tuple[int, int, int] | None:
    if intuition is None or expression is None or word is None:
        return None
    return int(intuition), int(expression), int(word)


class ShellQuizLaunchersMixin:
    def launch_daily_review(self, skill: str, subskill: str | None) -> None:
        self.notebook.select(self.quiz.controls_frame)
        self.quiz.apply_preset(
            track="All",
            skill=skill,
            subskill=subskill,
            num_questions=5,
            level=1,
            question_type="both",
            launch_context="daily_review",
        )
        self.quiz.start_quiz()

    def launch_assignment_quiz(
        self,
        skill: str,
        subskill: str | None,
        level: int,
        num_questions: int,
        question_type: str,
        mode_intuition_pct: int | None = None,
        mode_expression_pct: int | None = None,
        mode_word_pct: int | None = None,
    ) -> None:
        self.notebook.select(self.quiz.controls_frame)
        self.quiz.apply_preset(
            track="All",
            skill=skill,
            subskill=subskill,
            num_questions=num_questions,
            level=level,
            question_type=question_type,
            strategy="learning_blend",
            mode_mix_override=_mode_mix(
                mode_intuition_pct, mode_expression_pct, mode_word_pct
            ),
            launch_context="assignment",
        )
        self.quiz.start_quiz()

    def launch_quiz_set(
        self,
        skill: str,
        num_questions: int,
        level: int,
        question_type: str,
        mode_intuition_pct: int | None = None,
        mode_expression_pct: int | None = None,
        mode_word_pct: int | None = None,
    ) -> None:
        self.notebook.select(self.quiz.controls_frame)
        self.quiz.apply_preset(
            track="All",
            skill=skill,
            subskill="Any",
            num_questions=num_questions,
            level=level,
            question_type=question_type,
            strategy="focused",
            mode_mix_override=_mode_mix(
                mode_intuition_pct, mode_expression_pct, mode_word_pct
            ),
            launch_context="quiz_set",
        )
        self.quiz.start_quiz()

    def launch_skill_map_quiz(self, skill: str) -> None:
        self.notebook.select(self.quiz.controls_frame)
        self.quiz.apply_preset(
            track="All",
            skill=skill,
            subskill="Any",
            num_questions=5,
            level=1,
            question_type="both",
            strategy="learning_blend",
            launch_context="skill_map",
        )
        self.quiz.start_quiz()
