from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import db  # noqa: E402


QUESTION_RE = re.compile(r"^\s*(\d{1,3})[\).]\s+(.*)")
CHOICE_RE = re.compile(r"^\s*([A-E])[\).]\s+(.*)")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _exam_type_from_name(name: str) -> str | None:
    lower = name.lower().replace("-", "_").replace(" ", "_")
    if re.search(r"(^|_)psat(_|$)", lower):
        return "psat"
    if re.search(r"(^|_)gre(_|$)", lower):
        return "gre"
    if re.search(r"(^|_)sat(_|$)", lower):
        return "sat"
    return None


def _category_from_prompt(prompt: str) -> str:
    p = prompt.lower()
    math_tokens = (
        "solve", "equation", "integer", "fraction", "ratio", "percent", "probability",
        "triangle", "slope", "graph", "mean", "median", "algebra", "geometry",
    )
    verbal_tokens = ("passage", "author", "paragraph", "inference", "tone", "vocabulary", "reading")
    writing_tokens = ("grammar", "sentence", "revision", "punctuation", "usage")
    if any(t in p for t in math_tokens):
        return "math"
    if any(t in p for t in writing_tokens):
        return "writing"
    if any(t in p for t in verbal_tokens):
        return "verbal"
    return "unknown"


def _extract_text(pdf_path: Path) -> str:
    cmd = ["pdftotext", "-layout", str(pdf_path), "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"pdftotext failed for {pdf_path}: {proc.stderr.strip()}")
    return proc.stdout


def _extract_answer_key(text: str) -> dict[int, str]:
    key: dict[int, str] = {}
    # Parse compact patterns like "1 A 2 C 3 D ..." typically in answer-key sections.
    for line in text.splitlines():
        pairs = re.findall(r"\b(\d{1,3})\s*[\).:-]?\s*([A-E])\b", line)
        if len(pairs) >= 4:
            for qnum, ans in pairs:
                key[int(qnum)] = ans.upper()
    return key


def _parse_questions(text: str, exam_type: str) -> list[dict[str, object]]:
    lines = text.splitlines()
    answer_key = _extract_answer_key(text)
    questions: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    prompt_lines: list[str] = []
    choices: dict[str, str] = {}

    def flush() -> None:
        nonlocal current, prompt_lines, choices
        if current is None:
            return
        prompt = " ".join(s.strip() for s in prompt_lines if s.strip())
        if len(prompt) < 20:
            current = None
            prompt_lines = []
            choices = {}
            return
        qnum = int(current["question_number"])
        questions.append(
            {
                "question_number": qnum,
                "section": str(current.get("section", "General")),
                "category": _category_from_prompt(prompt),
                "prompt": prompt,
                "choice_a": choices.get("A"),
                "choice_b": choices.get("B"),
                "choice_c": choices.get("C"),
                "choice_d": choices.get("D"),
                "choice_e": choices.get("E"),
                "correct_answer": answer_key.get(qnum),
                "explanation": f"Historical {exam_type.upper()} item.",
                "source_page": None,
            }
        )
        current = None
        prompt_lines = []
        choices = {}

    for raw in lines:
        line = raw.rstrip()
        qmatch = QUESTION_RE.match(line)
        if qmatch:
            flush()
            current = {"question_number": int(qmatch.group(1)), "section": "General"}
            prompt_lines = [qmatch.group(2).strip()]
            choices = {}
            continue
        if current is None:
            continue
        cmatch = CHOICE_RE.match(line)
        if cmatch:
            choices[cmatch.group(1).upper()] = cmatch.group(2).strip()
            continue
        if line.strip():
            prompt_lines.append(line.strip())
    flush()
    return questions


def ingest_one(pdf_path: Path) -> tuple[int, int]:
    exam_type = _exam_type_from_name(pdf_path.name)
    if exam_type is None:
        return (0, 0)
    text = _extract_text(pdf_path)
    questions = _parse_questions(text, exam_type)
    if not questions:
        return (0, 0)
    year_match = re.search(r"(19|20)\d{2}", pdf_path.stem)
    year = int(year_match.group(0)) if year_match else None
    title = pdf_path.stem.replace("_", " ").replace("-", " ").strip()
    exam_code = pdf_path.stem.lower().replace(" ", "_")
    test_id = db.upsert_historical_test(
        exam_code=exam_code,
        title=title,
        exam_type=exam_type,
        year=year,
        pdf_path=str(pdf_path),
        source="historical_pdf",
        created_at=_now_iso(),
    )
    inserted = db.replace_historical_questions(test_id, questions)
    return (1, inserted)


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest SAT/PSAT/GRE historical PDFs into local DB.")
    parser.add_argument(
        "--path",
        default="data/reference_pdfs/historical",
        help="Directory containing historical SAT/PSAT/GRE PDFs",
    )
    args = parser.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"path does not exist: {root}")
        return 0

    test_count = 0
    question_count = 0
    skipped = 0
    for pdf in sorted(root.glob("*.pdf")):
        try:
            t, q = ingest_one(pdf)
            test_count += t
            question_count += q
        except Exception as exc:
            skipped += 1
            print(f"skip {pdf}: {type(exc).__name__}: {exc}")
    print(
        f"ingested_tests={test_count} ingested_questions={question_count} skipped={skipped} path={root}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
