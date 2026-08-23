from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import webbrowser
from tkinter import messagebox

from . import db
from .paths import data_dir, worksheets_dir


def refresh_historical_tests(panel) -> None:
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
    panel._historical_tests = dict(sorted(out.items(), key=lambda kv: kv[0].lower()))
    labels = list(panel._historical_tests.keys())
    panel.historical_combo.config(values=labels)
    if labels and panel.historical_test_var.get() not in panel._historical_tests:
        panel.historical_test_var.set(labels[0])
    if not labels:
        panel.historical_test_var.set("")


def open_historical_test(panel) -> None:
    if not panel._historical_tests:
        messagebox.showerror(
            "No SAT/PSAT/GRE PDFs found",
            "Drop PDF files with 'sat', 'psat', or 'gre' in filename under data/reference_pdfs/historical/ and refresh.",
        )
        return
    label = panel.historical_test_var.get().strip()
    path = panel._historical_tests.get(label)
    if path is None:
        messagebox.showerror("No test selected", "Pick a historical SAT/PSAT/GRE test first.")
        return
    webbrowser.open(f"file://{path}")


def ingest_historical_pdfs(panel) -> None:
    script = Path("scripts/ingest_historical_tests.py")
    if not script.exists():
        messagebox.showerror("Missing ingest script", "scripts/ingest_historical_tests.py was not found.")
        return
    if shutil.which("pdftotext") is None:
        messagebox.showerror(
            "Missing dependency",
            "pdftotext is not installed. Install poppler-utils to ingest historical PDFs.",
        )
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


def ingest_historical_answer_keys(panel) -> None:
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


def print_historical_test(panel) -> None:
    label = panel.historical_test_var.get().strip()
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
