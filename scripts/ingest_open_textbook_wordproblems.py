from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app import db  # noqa: E402
from app.paths import data_dir  # noqa: E402
from app.time_utils import now_iso  # noqa: E402


@dataclass(frozen=True)
class SourceCatalogItem:
    source_id: str
    title: str
    source: str
    license: str
    url: str
    pdf_filename: str
    answer_key_likely: bool
    books_rag_resource_id: str
    books_rag_sha256: str


def load_catalog(path: Path) -> list[SourceCatalogItem]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: list[SourceCatalogItem] = []
    for item in raw:
        books_rag_resource_id = str(item.get("books_rag_resource_id", "")).strip()
        books_rag_sha256 = str(item.get("books_rag_sha256", "")).strip().lower()
        if bool(books_rag_resource_id) != bool(books_rag_sha256):
            raise ValueError("Books RAG resource ID and SHA-256 must be provided together")
        if books_rag_sha256 and re.fullmatch(r"[0-9a-f]{64}", books_rag_sha256) is None:
            raise ValueError(f"invalid Books RAG SHA-256 for {books_rag_resource_id}")
        out.append(
            SourceCatalogItem(
                source_id=str(item.get("id", "")).strip(),
                title=str(item.get("title", "")).strip(),
                source=str(item.get("source", "")).strip(),
                license=str(item.get("license", "")).strip(),
                url=str(item.get("url", "")).strip(),
                pdf_filename=str(item.get("pdf_filename", "")).strip(),
                answer_key_likely=bool(item.get("answer_key_likely", False)),
                books_rag_resource_id=books_rag_resource_id,
                books_rag_sha256=books_rag_sha256,
            )
        )
    return [item for item in out if item.source_id and item.title and item.pdf_filename]


def extract_answer_key_map(text: str) -> dict[int, str]:
    answers: dict[int, str] = {}
    answer_sections = re.split(r"(?i)\banswer(?:s)?\s*key\b", text)
    if len(answer_sections) >= 2:
        candidates = answer_sections[-1]
    else:
        candidates = text
    for line in candidates.splitlines():
        cleaned = " ".join(line.strip().split())
        if not cleaned:
            continue
        match = re.match(r"^(\d{1,4})[\.\)\-:\s]+([A-Ea-e]|-?\d+(?:\.\d+)?(?:/\d+)?)\b", cleaned)
        if match is None:
            continue
        qnum = int(match.group(1))
        answer = match.group(2).upper()
        answers[qnum] = answer
    return answers


def extract_word_problem_candidates(text: str, min_words: int = 8) -> list[tuple[int | None, str]]:
    raw_blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    out: list[tuple[int | None, str]] = []
    for block in raw_blocks:
        merged = _normalize_block(block)
        if not merged:
            continue
        qnum = _question_number(merged)
        body = _drop_leading_question_number(merged)
        if not _looks_like_word_problem(body, min_words=min_words):
            continue
        out.append((qnum, body))
    return out


def ingest_source(
    source: SourceCatalogItem,
    *,
    max_candidates: int,
    refresh_text: bool,
    dry_run: bool,
    min_words: int,
) -> tuple[int, int, int]:
    pdf_path = data_dir() / "reference_pdfs" / source.pdf_filename
    if not pdf_path.exists():
        print(f"skip source={source.source_id} missing_pdf={pdf_path}")
        return (0, 0, 0)
    if source.books_rag_sha256:
        actual_sha256 = _sha256_file(pdf_path)
        if actual_sha256 != source.books_rag_sha256:
            raise ValueError(
                f"Books RAG identity mismatch for {source.source_id}: "
                f"expected {source.books_rag_sha256}, got {actual_sha256}"
            )

    ingest_dir = data_dir() / "ingest" / "open_textbooks" / source.source_id
    ingest_dir.mkdir(parents=True, exist_ok=True)
    out_txt = ingest_dir / "pdftotext.txt"
    if refresh_text or (not out_txt.exists()):
        subprocess.run(["pdftotext", "-layout", str(pdf_path), str(out_txt)], check=True)

    text = out_txt.read_text(encoding="utf-8", errors="replace")
    answer_key = extract_answer_key_map(text) if source.answer_key_likely else {}
    candidates = extract_word_problem_candidates(text, min_words=min_words)[: max(1, int(max_candidates))]

    if dry_run:
        print(
            f"source={source.source_id} dry_run=1 candidates={len(candidates)} "
            f"answer_keys={len(answer_key)} text={out_txt}"
        )
        return (0, len(candidates), len(answer_key))

    db.init_db()
    book_id = _ensure_book(source)
    with db.connect() as conn:
        conn.execute(
            "DELETE FROM exercise_candidates WHERE book_id = ? AND location LIKE ?",
            (book_id, f"open-src:{source.source_id}:%"),
        )

    inserted = 0
    for idx, (qnum, body) in enumerate(candidates, start=1):
        if inserted >= max(1, int(max_candidates)):
            break
        key = answer_key.get(int(qnum)) if qnum is not None else None
        location = f"open-src:{source.source_id}:q{qnum if qnum is not None else idx}"
        candidate_text = body
        if key:
            candidate_text = f"{body} [answer_key={key}]"
        db.add_exercise_candidate(book_id, location, candidate_text, "new", now_iso())
        inserted += 1

    print(
        f"source={source.source_id} book_id={book_id} inserted={inserted} "
        f"answer_keys={len(answer_key)} text={out_txt}"
    )
    return (inserted, len(candidates), len(answer_key))


def _ensure_book(source: SourceCatalogItem) -> int:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT id FROM books WHERE title = ? AND source = ? AND pdf_filename = ?",
            (source.title, source.source, source.pdf_filename),
        ).fetchone()
    if row is not None:
        return int(row["id"])
    created = db.create_book(source.title, source.source, source.pdf_filename, now_iso())
    return int(created.id)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_block(block: str) -> str:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    return " ".join(" ".join(lines).split()).strip()


def _question_number(block: str) -> int | None:
    match = re.match(r"^(\d{1,4})[\.\)]\s+", block)
    if match is None:
        return None
    return int(match.group(1))


def _drop_leading_question_number(block: str) -> str:
    return re.sub(r"^\d{1,4}[\.\)]\s+", "", block).strip()


def _looks_like_word_problem(text: str, *, min_words: int) -> bool:
    if len(text) < 24:
        return False
    words = text.split()
    if len(words) < int(min_words):
        return False
    if not re.search(r"\d", text):
        return False
    if not re.search(r"[?]", text) and not re.search(
        r"\b(find|solve|compute|determine|how many|how much|what is)\b",
        text,
        flags=re.IGNORECASE,
    ):
        return False
    if not re.search(
        r"\b(dollar|mile|hour|minute|total|cost|price|distance|group|share|average|probability|percent|area|volume)\b",
        text,
        flags=re.IGNORECASE,
    ):
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest word-problem candidates from open/public textbook PDFs.")
    parser.add_argument("--catalog", default="scripts/source_catalog.json", help="Path to source catalog JSON.")
    parser.add_argument("--source-id", default="", help="Optional source id filter from catalog.")
    parser.add_argument("--max-candidates", type=int, default=400, help="Max candidates to ingest per source.")
    parser.add_argument("--min-words", type=int, default=8, help="Minimum words for candidate problems.")
    parser.add_argument("--refresh-text", action="store_true", help="Re-run pdftotext even if cached.")
    parser.add_argument("--dry-run", action="store_true", help="Preview counts without DB writes.")
    args = parser.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        raise SystemExit(f"catalog not found: {catalog_path}")
    sources = load_catalog(catalog_path)
    if args.source_id:
        sources = [item for item in sources if item.source_id == args.source_id]
    if not sources:
        raise SystemExit("no sources selected")

    total_inserted = 0
    total_candidates = 0
    total_keys = 0
    for source in sources:
        inserted, candidates, keys = ingest_source(
            source,
            max_candidates=int(args.max_candidates),
            refresh_text=bool(args.refresh_text),
            dry_run=bool(args.dry_run),
            min_words=int(args.min_words),
        )
        total_inserted += inserted
        total_candidates += candidates
        total_keys += keys

    print(
        f"done sources={len(sources)} inserted={total_inserted} "
        f"candidates={total_candidates} answer_keys={total_keys}"
    )


if __name__ == "__main__":
    main()
