from __future__ import annotations

import random
import re
import shutil
import subprocess
import threading
from pathlib import Path

from .curriculum import get_curriculum_for_skill
from .paths import data_dir
from .quiz_engine import Question


WORD_WRAPPER_SKILLS = {
    "counting",
    "add_subtract",
    "multiply",
    "divide",
    "ratios",
    "fractions",
    "long_addition",
    "long_subtraction",
    "long_multiplication",
    "long_division",
    "money",
    "integers",
    "order_of_operations",
    "algebra_linear",
    "pre_algebra",
    "algebra_1",
    "algebra_2",
    "geometry_area",
    "statistics",
    "trig_right_triangle",
    "calculus_1",
    "calculus_2",
    "calculus_3",
}

SKILL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "counting": ("count", "objects", "items", "total"),
    "add_subtract": ("sum", "total", "left", "more", "altogether"),
    "multiply": ("each", "groups", "rows", "times"),
    "divide": ("share", "equal", "split", "each"),
    "ratios": ("ratio", "rate", "per", "to"),
    "fractions": ("fraction", "part", "whole", "equal parts"),
    "long_addition": ("sum", "total", "place value"),
    "long_subtraction": ("difference", "borrow", "left"),
    "long_multiplication": ("product", "rows", "place value"),
    "long_division": ("quotient", "remainder", "share"),
    "money": ("dollars", "cents", "cost", "price"),
    "integers": ("negative", "positive", "temperature", "below zero"),
    "order_of_operations": ("expression", "parentheses", "operations"),
    "algebra_linear": ("equation", "variable", "solve", "unknown"),
    "pre_algebra": ("ratio", "fraction", "percent", "rate"),
    "algebra_1": ("equation", "graph", "function", "model"),
    "algebra_2": ("polynomial", "quadratic", "function", "logarithm"),
    "geometry_area": ("area", "perimeter", "triangle", "rectangle"),
    "statistics": ("survey", "sample", "mean", "probability"),
    "trig_right_triangle": ("triangle", "angle", "height", "distance"),
    "calculus_1": ("rate", "change", "slope", "motion"),
    "calculus_2": ("area", "accumulation", "integral", "velocity"),
    "calculus_3": ("surface", "gradient", "partial", "vector"),
}

_PDF_SNIPPETS_CACHE: dict[Path, list[str]] = {}
_LOAD_IN_PROGRESS: set[Path] = set()
_CACHE_LOCK = threading.Lock()


def can_wrap_skill(skill: str) -> bool:
    return skill in WORD_WRAPPER_SKILLS


def apply_story_wrapper(question: Question, *, rng: random.Random) -> Question:
    if not can_wrap_skill(question.skill):
        return question

    story = _pick_story_excerpt(question.skill, rng=rng)
    if story is None:
        return question

    source = get_curriculum_for_skill(question.skill)
    source_text = source.source if source is not None else "Curriculum source"
    wrapped_prompt = (
        f"Story context ({source_text}): {story}\n"
        f"Question: {question.prompt}"
    )
    wrapped_explanation = f"Story-to-math translation: identify the operation, then solve. {question.explanation}"

    return Question(
        skill=question.skill,
        prompt=wrapped_prompt,
        correct_answer=question.correct_answer,
        explanation=wrapped_explanation,
        choices=question.choices,
        visual=question.visual,
        template_id=question.template_id,
        template_external_id=question.template_external_id,
        subskill=question.subskill,
        question_label=question.question_label,
        mode="word",
    )


def _pick_story_excerpt(skill: str, *, rng: random.Random) -> str | None:
    entry = get_curriculum_for_skill(skill)
    if entry is None or not entry.pdf:
        return None

    pdf_path = data_dir() / "reference_pdfs" / entry.pdf
    if not pdf_path.exists():
        return None

    snippets = _load_snippets_for_pdf(pdf_path)
    if not snippets:
        return None
    relevant = [snippet for snippet in snippets if _is_relevant_to_skill(skill, snippet)]
    if relevant:
        return rng.choice(relevant)
    return rng.choice(snippets)


def _load_snippets_for_pdf(pdf_path: Path) -> list[str]:
    with _CACHE_LOCK:
        if pdf_path in _PDF_SNIPPETS_CACHE:
            return _PDF_SNIPPETS_CACHE[pdf_path]

    cache_dir = data_dir() / "ingest" / "story_wrappers"
    cache_dir.mkdir(parents=True, exist_ok=True)
    txt_path = cache_dir / f"{pdf_path.stem}.txt"

    if not txt_path.exists():
        _ensure_background_extract(pdf_path, txt_path)
        return []

    text = txt_path.read_text(encoding="utf-8", errors="replace")
    snippets = _extract_story_snippets(text)
    with _CACHE_LOCK:
        _PDF_SNIPPETS_CACHE[pdf_path] = snippets
    return snippets


def _ensure_background_extract(pdf_path: Path, txt_path: Path) -> None:
    with _CACHE_LOCK:
        if pdf_path in _LOAD_IN_PROGRESS:
            return
        _LOAD_IN_PROGRESS.add(pdf_path)

    def worker() -> None:
        try:
            if shutil.which("pdftotext") is None:
                with _CACHE_LOCK:
                    _PDF_SNIPPETS_CACHE[pdf_path] = []
                return
            subprocess.run(["pdftotext", "-layout", str(pdf_path), str(txt_path)], check=True)
            text = txt_path.read_text(encoding="utf-8", errors="replace")
            snippets = _extract_story_snippets(text)
            with _CACHE_LOCK:
                _PDF_SNIPPETS_CACHE[pdf_path] = snippets
        except Exception:
            with _CACHE_LOCK:
                _PDF_SNIPPETS_CACHE[pdf_path] = []
        finally:
            with _CACHE_LOCK:
                _LOAD_IN_PROGRESS.discard(pdf_path)

    threading.Thread(target=worker, daemon=True).start()


def _extract_story_snippets(text: str) -> list[str]:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    snippets: list[str] = []
    seen: set[str] = set()
    for block in blocks:
        line = " ".join(block.split())
        if not _looks_story_like(line):
            continue
        cleaned = _clean_line(line)
        if cleaned in seen:
            continue
        seen.add(cleaned)
        snippets.append(cleaned)
        if len(snippets) >= 240:
            break
    return snippets


def _looks_story_like(line: str) -> bool:
    if len(line) < 45 or len(line) > 220:
        return False
    if line.count("=") > 1:
        return False
    if re.search(r"\b(x|\+|\-|/|\*)\b", line):
        return False
    if not re.search(r"[A-Za-z]", line):
        return False
    words = {
        "each",
        "total",
        "cost",
        "price",
        "left",
        "share",
        "group",
        "bought",
        "sold",
        "distance",
        "time",
        "minutes",
        "hours",
        "dollars",
        "cents",
        "students",
        "books",
    }
    low = line.lower()
    has_story_word = any(word in low for word in words)
    has_number = bool(re.search(r"\b\d+\b", low))
    return has_story_word and has_number


def _clean_line(line: str) -> str:
    cleaned = re.sub(r"\s+", " ", line).strip()
    cleaned = cleaned.strip("•-:; ")
    return cleaned


def _is_relevant_to_skill(skill: str, snippet: str) -> bool:
    keywords = SKILL_KEYWORDS.get(skill, ())
    if not keywords:
        return True
    low = snippet.lower()
    return any(keyword in low for keyword in keywords)
