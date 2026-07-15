"""Curriculum, historical-test, and preset controls for quizzes."""

from __future__ import annotations

from pathlib import Path
import subprocess
import tkinter as tk
from tkinter import messagebox
import webbrowser

from . import db
from .curriculum import curriculum_pdf_path, get_curriculum_for_skill
from .paths import data_dir, worksheets_dir
from .skill_graph import SKILLS, skills_in_track, subskills_for


class QuizSetupMixin:
    def _update_curriculum_label(self) -> None:
        skill = self.skill_var.get()
        entry = get_curriculum_for_skill(skill)
        if entry is None:
            self.curriculum_label.config(text="No source mapped for this skill.")
            return
        topics = ", ".join(entry.topics)
        self.curriculum_label.config(text=f"{entry.label}: {topics} ({entry.source})")

    def _open_curriculum_pdf(self) -> None:
        path = curriculum_pdf_path(self.skill_var.get())
        if path is None:
            messagebox.showerror("No curriculum file", "No local PDF found for this skill.")
            return
        webbrowser.open(f"file://{path}")

    def _refresh_historical_tests(self) -> None:
        root = data_dir() / "reference_pdfs"
        candidates: list[Path] = []
        for folder in (root / "historical", root):
            if folder.exists():
                candidates.extend(sorted(folder.glob("*.pdf")))
        out: dict[str, Path] = {}
        for path in candidates:
            name = path.name.lower()
            if "answer" in name or "key" in name or "solution" in name:
                continue
            if any(token in name for token in ("sat", "psat", "gre")):
                label = path.stem.replace("_", " ").replace("-", " ").strip()
                out[label] = path
        self._historical_tests = dict(sorted(out.items(), key=lambda kv: kv[0].lower()))
        labels = list(self._historical_tests.keys())
        self.historical_combo.config(values=labels)
        if labels and self.historical_test_var.get() not in self._historical_tests:
            self.historical_test_var.set(labels[0])
        if not labels:
            self.historical_test_var.set("")

    def _open_historical_test(self) -> None:
        if not self._historical_tests:
            messagebox.showerror(
                "No SAT/PSAT/GRE PDFs found",
                "Drop PDF files with 'sat', 'psat', or 'gre' in filename under data/reference_pdfs/historical/ and refresh.",
            )
            return
        label = self.historical_test_var.get().strip()
        path = self._historical_tests.get(label)
        if path is None:
            messagebox.showerror("No test selected", "Pick a historical SAT/PSAT/GRE test first.")
            return
        webbrowser.open(f"file://{path}")

    def _ingest_historical_pdfs(self) -> None:
        script = Path("scripts/ingest_historical_tests.py")
        if not script.exists():
            messagebox.showerror("Missing ingest script", "scripts/ingest_historical_tests.py was not found.")
            return
        root = data_dir() / "reference_pdfs" / "historical"
        if not root.exists():
            messagebox.showerror("Missing folder", f"Create folder first: {root}")
            return
        proc = subprocess.run(
            ["python", str(script), "--path", str(root)],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            messagebox.showerror("Ingest failed", proc.stderr.strip() or proc.stdout.strip() or "Unknown error")
            return
        messagebox.showinfo("Ingest complete", proc.stdout.strip() or "Historical PDFs ingested.")

    def _ingest_historical_answer_keys(self) -> None:
        script = Path("scripts/ingest_historical_answer_keys.py")
        if not script.exists():
            messagebox.showerror("Missing ingest script", "scripts/ingest_historical_answer_keys.py was not found.")
            return
        root = data_dir() / "reference_pdfs" / "historical_keys"
        if not root.exists():
            messagebox.showerror("Missing folder", f"Create folder first: {root}")
            return
        proc = subprocess.run(
            ["python", str(script), "--path", str(root)],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            messagebox.showerror("Answer key ingest failed", proc.stderr.strip() or proc.stdout.strip() or "Unknown error")
            return
        messagebox.showinfo("Answer keys ingested", proc.stdout.strip() or "Historical answer keys ingested.")

    def _print_historical_test(self) -> None:
        label = self.historical_test_var.get().strip()
        if not label:
            messagebox.showerror("No test selected", "Pick a historical SAT/PSAT/GRE test first.")
            return
        tests = db.list_historical_tests(exam_type="all")
        test = next((t for t in tests if t.title.lower() == label.lower()), None)
        if test is None:
            messagebox.showerror("Not indexed", "Ingest this historical PDF first using 'Ingest PDFs'.")
            return
        questions = db.list_historical_questions_for_test(test.id)
        if not questions:
            messagebox.showerror("No questions", "No parsed questions found for this test.")
            return
        out_dir = worksheets_dir()
        safe = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in test.exam_code)
        out = out_dir / f"historical_test_{safe}.html"
        parts = [
            "<html><head><meta charset='utf-8'><title>Historical Test</title></head><body>",
            f"<h1>{test.title}</h1>",
            "<p>Print Test Mode (answers hidden)</p>",
        ]
        for q in questions:
            parts.append(f"<h3>{q.question_number}. {q.prompt}</h3>")
            choices = [q.choice_a, q.choice_b, q.choice_c, q.choice_d, q.choice_e]
            letters = ["A", "B", "C", "D", "E"]
            for letter, choice in zip(letters, choices):
                if choice:
                    parts.append(f"<p>{letter}. {choice}</p>")
            parts.append("<hr/>")
        parts.append("</body></html>")
        out.write_text("\n".join(parts), encoding="utf-8")
        webbrowser.open(f"file://{out}")

    def _template_only_quiz_skills(self) -> list[str]:
        skills = {
            str(item.skill)
            for item in db.list_all_question_templates(active_only=True)
            if item.skill and item.skill not in SKILLS and item.skill != "mixed"
        }
        return sorted(skills)

    def _quiz_skill_values_for_track(self, track: str) -> list[str]:
        skills = list(skills_in_track(track))
        if track == "All":
            skills.extend(self._template_only_quiz_skills())
            # Preserve canonical skill order while including template-only skills.
            merged = list(dict.fromkeys(skills))
            merged.append("mixed")
            return merged
        return skills

    def _apply_track_filter(self) -> None:
        track = self.track_var.get()
        values = self._quiz_skill_values_for_track(track)
        if not values:
            values = ["counting"]
        if self.skill_var.get() not in values and "mixed" in values:
            self.skill_var.set("mixed")
        elif self.skill_var.get() not in values:
            self.skill_var.set(values[0] if values else "counting")
        self.skill_combo.config(values=values if values else ["counting"])
        self._refresh_subskills()

    def _on_track_change(self) -> None:
        self._apply_track_filter()
        self._on_skill_change()

    def _on_skill_change(self) -> None:
        self._update_curriculum_label()
        self._refresh_subskills()

    def _refresh_subskills(self) -> None:
        skill = self.skill_var.get()
        options = ["Any", *subskills_for(skill)]
        if self.subskill_var.get() not in options:
            self.subskill_var.set("Any")
        self.subskill_combo.config(values=options)

    def apply_preset(
        self,
        *,
        track: str | None = None,
        skill: str | None = None,
        subskill: str | None = None,
        num_questions: int | None = None,
        level: int | None = None,
        question_type: str | None = None,
        strategy: str | None = None,
        mode_mix_override: tuple[int, int, int] | None = None,
        launch_context: str | None = None,
    ) -> None:
        if track is not None:
            self.track_var.set(track)
        self._apply_track_filter()
        if skill is not None:
            self.skill_var.set(skill)
        self._on_skill_change()
        if subskill is not None:
            self.subskill_var.set(subskill)
        if num_questions is not None:
            self.num_var.set(int(num_questions))
        if level is not None:
            self.level_var.set(int(level))
        if question_type is not None:
            self.type_var.set(str(question_type))
        if strategy is not None:
            self.strategy_var.set(str(strategy))
        else:
            self.strategy_var.set("focused")
        self._mode_mix_override = mode_mix_override
        if launch_context is not None:
            self._launch_context = str(launch_context)
