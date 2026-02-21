from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import db  # noqa: E402


PAIR_RE = re.compile(r"\b(\d{1,3})\s*[\).:-]?\s*([A-E])\b", re.IGNORECASE)


def _infer_exam_code(path: Path) -> str:
    stem = path.stem.lower()
    stem = stem.replace(" ", "_")
    noise = [
        "answer_explanations",
        "score_explanations",
        "answer_key",
        "answers",
        "answer",
        "scoring_guide",
        "scoring",
        "key",
    ]
    for token in noise:
        stem = stem.replace(token, "")
    stem = re.sub(r"[-_]{2,}", "-", stem)
    stem = stem.strip("-_ ")
    return stem


def _parse_pairs_from_text(text: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for line in text.splitlines():
        pairs = PAIR_RE.findall(line)
        if not pairs:
            continue
        for qnum, answer in pairs:
            out[int(qnum)] = str(answer).upper()
    # Handle explanation style blocks:
    # "QUESTION 12 ... Choice C is the best answer"
    block_re = re.compile(
        r"QUESTION\s+(\d{1,3}).{0,320}?Choice\s+([A-E])\s+is\s+the\s+best\s+answer",
        re.IGNORECASE | re.DOTALL,
    )
    for qnum, answer in block_re.findall(text):
        out[int(qnum)] = str(answer).upper()
    return out


def _parse_txt(path: Path) -> dict[int, str]:
    return _parse_pairs_from_text(path.read_text(encoding="utf-8", errors="ignore"))


def _parse_pdf(path: Path) -> dict[int, str]:
    proc = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"pdftotext failed for {path}: {proc.stderr.strip()}")
    return _parse_pairs_from_text(proc.stdout)


def _parse_json(path: Path) -> dict[str, dict[int, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    grouped: dict[str, dict[int, str]] = {}
    if isinstance(payload, dict):
        # Either {"exam_code":"...","answers":{"1":"A"}} or {"exam_code":{"1":"A"}}
        if "exam_code" in payload and "answers" in payload:
            exam_code = str(payload["exam_code"]).strip().lower()
            answers = payload["answers"]
            if isinstance(answers, dict):
                grouped[exam_code] = {int(k): str(v).upper() for k, v in answers.items()}
            return grouped
        for exam_code, answers in payload.items():
            if isinstance(answers, dict):
                grouped[str(exam_code).strip().lower()] = {int(k): str(v).upper() for k, v in answers.items()}
        return grouped
    if isinstance(payload, list):
        # [{"exam_code":"x","question_number":1,"answer":"A"}, ...]
        for row in payload:
            if not isinstance(row, dict):
                continue
            exam = str(row.get("exam_code", "")).strip().lower()
            if not exam:
                continue
            qnum = int(row.get("question_number", 0))
            ans = str(row.get("answer", "")).strip().upper()
            if qnum <= 0 or ans not in {"A", "B", "C", "D", "E"}:
                continue
            grouped.setdefault(exam, {})[qnum] = ans
    return grouped


def _parse_csv(path: Path) -> dict[str, dict[int, str]]:
    grouped: dict[str, dict[int, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            exam = str(row.get("exam_code", "")).strip().lower()
            q = str(row.get("question_number", "")).strip()
            ans = str(row.get("answer", "")).strip().upper()
            if not exam or not q or ans not in {"A", "B", "C", "D", "E"}:
                continue
            grouped.setdefault(exam, {})[int(q)] = ans
    return grouped


def ingest_path(path: Path) -> tuple[int, int, int]:
    """
    Returns (files_processed, exams_updated, answers_updated)
    """
    files = [path] if path.is_file() else sorted(p for p in path.glob("*") if p.is_file())
    files_processed = 0
    exams_updated = 0
    answers_updated = 0

    for file in files:
        suffix = file.suffix.lower()
        per_exam: dict[str, dict[int, str]] = {}
        if suffix == ".csv":
            per_exam = _parse_csv(file)
        elif suffix == ".json":
            per_exam = _parse_json(file)
        elif suffix in {".txt", ".text"}:
            per_exam[_infer_exam_code(file)] = _parse_txt(file)
        elif suffix == ".pdf":
            per_exam[_infer_exam_code(file)] = _parse_pdf(file)
        else:
            continue
        files_processed += 1
        for exam_code, answers in per_exam.items():
            if not exam_code or not answers:
                continue
            updated = db.apply_historical_answer_key(exam_code=exam_code, answers=answers)
            if updated > 0:
                exams_updated += 1
                answers_updated += updated
    return files_processed, exams_updated, answers_updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest dedicated historical answer keys (SAT/PSAT/GRE).")
    parser.add_argument(
        "--path",
        default="data/reference_pdfs/historical_keys",
        help="Path to answer key file or folder (.csv, .json, .txt, .pdf)",
    )
    args = parser.parse_args()

    db.init_db()
    target = Path(args.path)
    if not target.exists():
        print(f"path does not exist: {target}")
        return 0

    files, exams, answers = ingest_path(target)
    print(f"files_processed={files} exams_updated={exams} answers_updated={answers} path={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
