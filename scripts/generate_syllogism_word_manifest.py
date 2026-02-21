from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app import db


LOGIC_CUE_WORDS = (
    "all",
    "no",
    "some",
    "every",
    "any",
    "if",
    "then",
    "therefore",
    "not",
)
LOGIC_CUE_PATTERN = re.compile(r"\b(" + "|".join(LOGIC_CUE_WORDS) + r")\b", flags=re.IGNORECASE)


def _parse_book_ids(raw: str) -> list[int]:
    out: list[int] = []
    for piece in raw.split(","):
        piece = piece.strip()
        if not piece:
            continue
        out.append(int(piece))
    return out


def _normalize_text(text: str) -> str:
    merged = " ".join(str(text).split())
    merged = merged.replace("{", "(").replace("}", ")")
    merged = merged.encode("ascii", "ignore").decode("ascii")
    merged = re.sub(r"\s+", " ", merged)
    return merged.strip()


def _looks_usable(text: str) -> bool:
    if len(text) < 60:
        return False
    letters = sum(1 for ch in text if ch.isalpha())
    if letters < 35:
        return False
    return (float(letters) / float(max(1, len(text)))) >= 0.45


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    chunk = text[:max_chars]
    if " " in chunk:
        chunk = chunk.rsplit(" ", 1)[0]
    return chunk + "..."


def _cue_count(text: str) -> int:
    return len(LOGIC_CUE_PATTERN.findall(text))


def _fetch_candidates(book_ids: list[int], status: str, limit: int) -> list[dict[str, object]]:
    with db.connect() as conn:
        sql = """
            SELECT ec.id AS candidate_id, ec.book_id, ec.location, ec.text, b.title
            FROM exercise_candidates ec
            JOIN books b ON b.id = ec.book_id
            WHERE ec.status = ?
        """
        params: list[object] = [status]
        if book_ids:
            placeholders = ",".join("?" for _ in book_ids)
            sql += f" AND ec.book_id IN ({placeholders})"
            params.extend(book_ids)
        sql += " ORDER BY ec.book_id ASC, ec.id ASC LIMIT ?"
        params.append(int(limit))
        rows = conn.execute(sql, tuple(params)).fetchall()
    return [
        {
            "candidate_id": int(row["candidate_id"]),
            "book_id": int(row["book_id"]),
            "location": str(row["location"]),
            "text": str(row["text"]),
            "title": str(row["title"]),
        }
        for row in rows
    ]


def _mark_templated(candidate_ids: list[int]) -> None:
    if not candidate_ids:
        return
    with db.connect() as conn:
        conn.executemany(
            "UPDATE exercise_candidates SET status = 'templated' WHERE id = ?",
            [(int(candidate_id),) for candidate_id in candidate_ids],
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a first-pass word-mode template manifest from syllogism candidates.")
    parser.add_argument("--out", required=True, help="Output JSON manifest path")
    parser.add_argument("--book-ids", default="", help="Optional comma-separated book ids (e.g. 1,2,3)")
    parser.add_argument("--status", default="new", help="Candidate status filter (default: new)")
    parser.add_argument("--limit", type=int, default=500, help="Max candidates to inspect")
    parser.add_argument("--skill", default="logic_syllogism", help="Template skill id")
    parser.add_argument("--subskill", default="Cue-word counting", help="Template subskill label")
    parser.add_argument("--min-cue-count", type=int, default=1, help="Skip excerpts below this cue-word count")
    parser.add_argument("--max-excerpt-chars", type=int, default=280, help="Maximum excerpt length in prompt")
    parser.add_argument("--inactive", action="store_true", help="Write templates as inactive")
    parser.add_argument("--mark-templated", action="store_true", help="Mark used candidates as templated in DB")
    args = parser.parse_args()

    db.init_db()
    book_ids = _parse_book_ids(args.book_ids) if args.book_ids.strip() else []
    rows = _fetch_candidates(book_ids=book_ids, status=str(args.status), limit=max(1, int(args.limit)))

    templates: list[dict[str, object]] = []
    used_candidate_ids: list[int] = []
    skipped_quality = 0
    skipped_cues = 0

    for row in rows:
        candidate_id = int(row["candidate_id"])
        book_id = int(row["book_id"])
        title = str(row["title"])
        normalized = _normalize_text(str(row["text"]))
        if not _looks_usable(normalized):
            skipped_quality += 1
            continue
        excerpt = _truncate(normalized, max_chars=max(80, int(args.max_excerpt_chars)))
        cues = _cue_count(excerpt)
        if cues < int(args.min_cue_count):
            skipped_cues += 1
            continue

        prompt = (
            f"Syllogism excerpt ({title}): {excerpt}\n"
            "How many logic cue words appear "
            "(all, no, some, every, any, if, then, therefore, not)?"
        )
        explanation = (
            "Count each whole-word cue term exactly once per appearance. "
            f"Total cue words in this excerpt: {cues}."
        )
        templates.append(
            {
                "external_id": f"logic.syllogism.book{book_id}.candidate{candidate_id}.v1",
                "skill": str(args.skill),
                "subskill": str(args.subskill),
                "label": f"Syllogism excerpt #{candidate_id}",
                "mode": "word",
                "prompt_template": prompt,
                "answer_expr": str(cues),
                "constraint_expr": "",
                "explanation_template": explanation,
                "min_level": 1,
                "max_level": 3,
                "choice_spread": 3.0,
                "active": not bool(args.inactive),
                "vars": [],
            }
        )
        used_candidate_ids.append(candidate_id)

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(templates, indent=2), encoding="utf-8")

    if args.mark_templated:
        _mark_templated(used_candidate_ids)

    print(
        f"manifest={out_path} templates={len(templates)} "
        f"source_rows={len(rows)} skipped_quality={skipped_quality} skipped_cues={skipped_cues} "
        f"status_marked={len(used_candidate_ids) if args.mark_templated else 0}"
    )


if __name__ == "__main__":
    main()
