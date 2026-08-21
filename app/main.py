from __future__ import annotations

import argparse
import sys
import time

from . import db, sync_service
from .time_utils import now_iso


def _on_close(root, app) -> None:
    if hasattr(app, "shutdown"):
        app.shutdown()
    root.destroy()


def _run_smoke_test() -> int:
    from .quiz_answers import is_correct_answer
    from .quiz_engine import generate_question

    stamp = int(time.time())
    now = now_iso()
    db.init_db()

    parent = sync_service.create_profile(f"smoke-parent-{stamp}", "parent", now)
    child = sync_service.create_profile(f"smoke-child-{stamp}", "child", now)

    db.set_parent_pin(parent.id, "1234", now)
    if not db.verify_parent_pin("1234", now):
        raise RuntimeError("Parent PIN verification failed for correct PIN.")
    if db.verify_parent_pin("4321", now):
        raise RuntimeError("Parent PIN incorrectly accepted wrong PIN.")

    question = generate_question(
        "pre_algebra",
        2,
        "typed",
        subskill="Ratios, rates, and proportional relationships",
    )
    if not question.correct_answer:
        raise RuntimeError("Generated smoke-test question missing correct answer.")
    if not is_correct_answer(question.correct_answer, question.correct_answer):
        raise RuntimeError("Answer normalizer rejected exact correct answer.")

    write_result = sync_service.record_completed_quiz(
        profile_id=child.id,
        quiz_set_id=None,
        skill=question.skill,
        question_type="typed",
        num_questions=1,
        level=2,
        score=1,
        created_at=now,
        elapsed_seconds=1.0,
        question_results=[
            sync_service.QuestionResultInput(
                skill=question.skill,
                subskill=question.subskill,
                question_label=question.question_label,
                mode=question.mode,
                prompt=question.prompt,
                correct_answer=question.correct_answer,
                user_answer=question.correct_answer,
                is_correct=True,
                explanation=question.explanation,
            )
        ],
        record_progress=question.subskill is not None,
        streak_to_master=3,
        record_daily_review=False,
    )
    attempt_id = write_result.attempt_id

    state_json = '{"version":1,"smoke":true}'
    progress_id = db.save_quiz_progress(child.id, None, 0, state_json, now)
    loaded = db.load_quiz_progress(child.id)
    if loaded is None or loaded[0] != progress_id:
        raise RuntimeError("Quiz progress save/load failed.")
    db.clear_quiz_progress_for_profile(child.id)
    if db.load_quiz_progress(child.id) is not None:
        raise RuntimeError("Quiz progress clear failed.")

    if not db.list_attempts(child.id):
        raise RuntimeError("Attempt write/read roundtrip failed.")

    return 0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run non-interactive smoke checks and exit.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.smoke_test:
        try:
            code = _run_smoke_test()
        except Exception as exc:  # noqa: BLE001
            print(f"[smoke-test] FAILED: {exc}", file=sys.stderr)
            sys.exit(1)
        print("[smoke-test] OK")
        sys.exit(code)

    import tkinter as tk
    from tkinter import messagebox

    from .ui_profile_picker import pick_profile
    from .ui_root import AppShell

    db.init_db()
    root = tk.Tk()
    profile = pick_profile(root)
    if profile is None:
        messagebox.showinfo("Goodbye", "No profile selected. Closing the app.")
        root.destroy()
        sys.exit(0)

    app = AppShell(root, profile)
    root.protocol("WM_DELETE_WINDOW", lambda: _on_close(root, app))
    root.after(200, app.dashboard.render)
    root.mainloop()


if __name__ == "__main__":
    main()
