from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app import db
from app.paths import data_dir
from app.time_utils import now_iso


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a textbook PDF into exercise candidates.")
    parser.add_argument("--pdf", required=True, help="Path to PDF (typically in data/reference_pdfs/...)")
    parser.add_argument("--title", required=True, help="Book title (display name)")
    parser.add_argument("--source", required=True, help="Book author/year/etc.")
    parser.add_argument("--pdf-filename", default="", help="Stored filename for DB metadata (defaults to basename)")
    parser.add_argument("--max-candidates", type=int, default=2000, help="Max candidates to store from this ingest")
    args = parser.parse_args()

    db.init_db()

    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    pdf_filename = args.pdf_filename.strip() or pdf_path.name
    book = db.create_book(args.title.strip(), args.source.strip(), pdf_filename, now_iso())

    ingest_dir = data_dir() / "ingest" / f"book_{book.id}"
    ingest_dir.mkdir(parents=True, exist_ok=True)
    out_txt = ingest_dir / "pdftotext.txt"

    # Use pdftotext (poppler) which is already installed in this environment.
    subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), str(out_txt)],
        check=True,
    )

    text = out_txt.read_text(encoding="utf-8", errors="replace")
    blocks = _candidate_blocks(text)
    saved = 0
    for idx, block in enumerate(blocks, start=1):
        if saved >= int(args.max_candidates):
            break
        location = f"block:{idx}"
        db.add_exercise_candidate(book.id, location, block, "new", now_iso())
        saved += 1

    print(f"book_id={book.id} candidates_saved={saved} extracted_text={out_txt}")


def _candidate_blocks(text: str) -> list[str]:
    # Heuristic: split into paragraph-like blocks, then keep blocks that look like exercises.
    raw_blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    candidates: list[str] = []
    for b in raw_blocks:
        b2 = _normalize_block(b)
        if not b2:
            continue
        if _looks_like_exercise(b2):
            candidates.append(b2)
    return candidates


def _normalize_block(block: str) -> str:
    lines = [ln.rstrip() for ln in block.splitlines()]
    lines = [ln for ln in lines if ln.strip()]
    # Collapse multiple spaces to one for easier downstream matching.
    out = " ".join(" ".join(lines).split())
    return out.strip()


def _looks_like_exercise(block: str) -> bool:
    if len(block) < 10 or len(block) > 500:
        return False
    if "?" in block:
        return True
    if re.search(r"\\b(solve|find|simplify|evaluate|compute)\\b", block, flags=re.IGNORECASE):
        return True
    if re.search(r"\\b\\d+\\s*[\\+\\-\\*/x]\\s*\\d+\\b", block):
        return True
    if "=" in block and re.search(r"\\b\\d+\\b", block):
        return True
    return False


if __name__ == "__main__":
    main()
