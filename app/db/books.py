from __future__ import annotations

from ..models import Book, ExerciseCandidate
from .connection import managed_connection


def create_book(title: str, source: str, pdf_filename: str, created_at: str) -> Book:
    with managed_connection() as conn:
        cur = conn.execute(
            "INSERT INTO books (title, source, pdf_filename, created_at) VALUES (?, ?, ?, ?)",
            (title, source, pdf_filename, created_at),
        )
        book_id = int(cur.lastrowid)
    return Book(book_id, title, source, pdf_filename)

def list_books() -> list[Book]:
    with managed_connection() as conn:
        rows = conn.execute("SELECT id, title, source, pdf_filename FROM books ORDER BY id DESC").fetchall()
    return [Book(int(r["id"]), r["title"], r["source"], r["pdf_filename"]) for r in rows]

def add_exercise_candidate(book_id: int, location: str, text: str, status: str, created_at: str) -> int:
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO exercise_candidates (book_id, location, text, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (book_id, location, text, status, created_at),
        )
        return int(cur.lastrowid)

def list_exercise_candidates(book_id: int, status: str = "new", limit: int = 200) -> list[ExerciseCandidate]:
    limit = max(1, int(limit))
    with managed_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, book_id, location, text, status
            FROM exercise_candidates
            WHERE book_id = ? AND status = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (book_id, status, limit),
        ).fetchall()
    return [
        ExerciseCandidate(int(r["id"]), int(r["book_id"]), r["location"], r["text"], r["status"]) for r in rows
    ]
