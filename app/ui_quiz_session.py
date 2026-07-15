"""Versioned persistence and recovery for in-progress quiz sessions."""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox
from typing import Any, cast

from . import db
from .quiz_engine import Question
from .quiz_recovery import MistakeRecoveryState
from .time_utils import now_iso
from .ui_quiz_session_codec import (
    InvalidQuizProgress,
    bounded_int as _bounded_int,
    optional_text as _optional_text,
    question_from_payload,
    question_to_payload,
    text_or as _text_or,
)


class QuizSessionMixin:
    _question_to_payload = staticmethod(question_to_payload)
    _question_from_payload = staticmethod(question_from_payload)

    def _build_progress_state(self) -> str:
        answers = [
            {"question_index": index, "answer": answer, "correct": correct}
            for index, (_question, answer, correct) in enumerate(self._answers)
        ]
        recovery: dict[str, object] | None = None
        if self._mistake_recovery is not None:
            state = self._mistake_recovery
            recovery = {
                "phase": state.phase,
                "incorrect_answer": state.incorrect_answer,
                "source_question": self._question_to_payload(state.source_question),
                "followup_question": (
                    self._question_to_payload(state.followup_question)
                    if state.followup_question is not None
                    else None
                ),
            }
        payload = {
            "version": 1,
            "track": self.track_var.get(),
            "skill": self.skill_var.get(),
            "subskill": self.subskill_var.get(),
            "question_type": self.type_var.get(),
            "strategy": self.strategy_var.get(),
            "num_questions": len(self._questions),
            "level": int(self.level_var.get()),
            "meta": self.meta_var.get(),
            "attempt_skill": self._attempt_skill,
            "record_attempt": bool(self._record_attempt),
            "record_progress": bool(self._record_progress),
            "launch_context": self._launch_context,
            "index": int(self._index),
            "score": int(self._score),
            "completion_created_at": self._completion_created_at,
            "questions": [self._question_to_payload(q) for q in self._questions],
            "answers": answers,
            "mistake_recovery": recovery,
        }
        return json.dumps(payload, ensure_ascii=True, sort_keys=True)

    def _persist_quiz_progress(self) -> None:
        profile = self._profile_getter()
        if profile is None or not self._questions:
            return
        self._quiz_progress_attempt_id = db.save_quiz_progress(
            profile.id,
            self._quiz_progress_attempt_id,
            self._index,
            self._build_progress_state(),
            now_iso(),
        )

    def _clear_quiz_progress(self) -> None:
        if self._quiz_progress_attempt_id is None:
            return
        db.clear_quiz_progress(self._quiz_progress_attempt_id)
        self._quiz_progress_attempt_id = None

    def _discard_invalid_progress(self, attempt_id: int, detail: str) -> None:
        db.clear_quiz_progress(attempt_id)
        self._quiz_progress_attempt_id = None
        messagebox.showwarning(
            "Saved quiz could not be resumed",
            f"The damaged resume record was discarded safely.\n\n{detail}",
        )

    def _try_resume_saved_quiz(self, profile_id: int) -> bool:
        saved = db.load_quiz_progress(profile_id)
        if saved is None:
            return False
        attempt_id, _saved_index, state_json = saved
        try:
            payload = json.loads(state_json)
            restored = self._parse_progress_payload(payload)
        except (json.JSONDecodeError, InvalidQuizProgress, TypeError, ValueError) as exc:
            self._discard_invalid_progress(attempt_id, str(exc))
            return False
        if not messagebox.askyesno(
            "Resume quiz", "Resume your in-progress quiz from last session?"
        ):
            db.clear_quiz_progress(attempt_id)
            self._quiz_progress_attempt_id = None
            return False
        self._restore_progress(attempt_id, payload, restored)
        return True

    def _parse_progress_payload(
        self, payload: object
    ) -> tuple[list[Question], list[tuple[int, str, bool]], MistakeRecoveryState | None]:
        if not isinstance(payload, dict) or payload.get("version") != 1:
            raise InvalidQuizProgress("Unsupported saved-quiz format.")
        raw_questions = payload.get("questions")
        if not isinstance(raw_questions, list) or not raw_questions:
            raise InvalidQuizProgress("Saved quiz has no questions.")
        questions = [self._question_from_payload(item) for item in raw_questions]
        index = _bounded_int(payload.get("index"), 0, len(questions) - 1, "index")
        score = _bounded_int(payload.get("score"), 0, len(questions), "score")
        answers = self._parse_answers(payload.get("answers"), questions)
        recovery = self._parse_recovery(payload.get("mistake_recovery"))
        if score != sum(1 for _index, _answer, correct in answers if correct):
            raise InvalidQuizProgress("Saved score does not match saved answers.")
        if len(answers) not in {index, index + 1}:
            raise InvalidQuizProgress("Saved question index does not match saved answers.")
        if recovery is not None and (
            len(answers) != index + 1 or answers[-1][2]
        ):
            raise InvalidQuizProgress("Mistake recovery is not attached to a wrong answer.")
        if payload.get("num_questions") != len(questions):
            raise InvalidQuizProgress("Saved question count does not match its questions.")
        for key in ("record_attempt", "record_progress"):
            if not isinstance(payload.get(key, True), bool):
                raise InvalidQuizProgress(f"Saved {key} flag is invalid.")
        return questions, answers, recovery

    def _parse_answers(
        self, raw: object, questions: list[Question]
    ) -> list[tuple[int, str, bool]]:
        if not isinstance(raw, list) or len(raw) > len(questions):
            raise InvalidQuizProgress("Saved answers are invalid.")
        answers: list[tuple[int, str, bool]] = []
        for expected, item in enumerate(raw):
            if not isinstance(item, dict):
                raise InvalidQuizProgress("Saved answer is not an object.")
            index = _bounded_int(
                item.get("question_index"), 0, len(questions) - 1, "answer index"
            )
            if index != expected or not isinstance(item.get("answer"), str):
                raise InvalidQuizProgress("Saved answers are out of order.")
            if not isinstance(item.get("correct"), bool):
                raise InvalidQuizProgress("Saved answer result is invalid.")
            answers.append((index, str(item["answer"]), bool(item["correct"])))
        return answers

    def _parse_recovery(self, raw: object) -> MistakeRecoveryState | None:
        if raw is None:
            return None
        if not isinstance(raw, dict) or raw.get("phase") not in {
            "redo", "followup", "complete"
        }:
            raise InvalidQuizProgress("Mistake-recovery state is invalid.")
        if not isinstance(raw.get("incorrect_answer"), str):
            raise InvalidQuizProgress("Mistake-recovery answer is invalid.")
        source = self._question_from_payload(raw.get("source_question"))
        followup_raw = raw.get("followup_question")
        followup = (
            self._question_from_payload(followup_raw)
            if followup_raw is not None
            else None
        )
        if raw["phase"] == "followup" and followup is None:
            raise InvalidQuizProgress("Mistake-recovery follow-up is missing.")
        return MistakeRecoveryState(
            phase=str(raw["phase"]),
            source_question=source,
            incorrect_answer=str(raw["incorrect_answer"]),
            followup_question=followup,
        )

    def _restore_progress(
        self,
        attempt_id: int,
        payload: dict[str, Any],
        restored: tuple[list[Question], list[tuple[int, str, bool]], MistakeRecoveryState | None],
    ) -> None:
        questions, raw_answers, recovery = restored
        self._quiz_progress_attempt_id = attempt_id
        self.track_var.set(_text_or(payload.get("track"), "All"))
        self._apply_track_filter()
        self.skill_var.set(_text_or(payload.get("skill"), questions[0].skill))
        self._on_skill_change()
        self.subskill_var.set(_text_or(payload.get("subskill"), "Any"))
        self.type_var.set(_text_or(payload.get("question_type"), "both"))
        self.strategy_var.set(_text_or(payload.get("strategy"), "focused"))
        self.num_var.set(_bounded_int(payload.get("num_questions"), 1, 100, "question count"))
        self.level_var.set(_bounded_int(payload.get("level"), 1, 20, "level"))
        self._questions = questions
        self._index = _bounded_int(payload.get("index"), 0, len(questions) - 1, "index")
        self._score = _bounded_int(payload.get("score"), 0, len(questions), "score")
        self._answers = [(questions[i], answer, correct) for i, answer, correct in raw_answers]
        self._attempt_skill = _optional_text(payload.get("attempt_skill"))
        self._record_attempt = cast(bool, payload.get("record_attempt", True))
        self._record_progress = cast(bool, payload.get("record_progress", True))
        self._launch_context = _text_or(payload.get("launch_context"), "manual")
        self._completion_created_at = _optional_text(payload.get("completion_created_at"))
        self._mistake_recovery = recovery
        self._quiz_started_monotonic = None
        self.summary_box.config(state=tk.NORMAL)
        self.summary_box.delete("1.0", tk.END)
        self.summary_box.config(state=tk.DISABLED)
        self.feedback_var.set("Resumed in-progress quiz.")
        self._show_resumed_step()

    def _show_resumed_step(self) -> None:
        state = self._mistake_recovery
        if state is not None:
            question = state.followup_question or state.source_question
            prefix = "Recovery Practice" if state.followup_question else "Try it again"
            self._render_recovery_question(question, prompt_prefix=prefix)
            self.recovery_var.set(self._recovery_text(question, phase=state.phase))
            if state.phase == "complete":
                self.submit_btn.state(["disabled"])
                self.next_btn.state(["!disabled"])
            else:
                self.submit_btn.config(
                    text="Try Again" if state.phase == "redo" else "Submit Follow-up"
                )
                self.submit_btn.state(["!disabled"])
                self.next_btn.state(["disabled"])
            self.stuck_btn.state(["disabled"])
            return
        self._show_question()
        if self._index < len(self._answers):
            self.feedback_var.set("Answer already recorded. Click Next to continue.")
            self.submit_btn.state(["disabled"])
            self.stuck_btn.state(["disabled"])
            self.next_btn.state(["!disabled"])
