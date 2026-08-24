from __future__ import annotations

from ..models import Book, ExerciseCandidate, HistoricalQuestion, HistoricalTest
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


def upsert_historical_test(
    *,
    exam_code: str,
    title: str,
    exam_type: str,
    year: int | None,
    pdf_path: str,
    source: str,
    created_at: str,
) -> int:
    with managed_connection() as conn:
        row = conn.execute(
            "SELECT id FROM historical_tests WHERE exam_code = ?",
            (exam_code,),
        ).fetchone()
        if row is None:
            cur = conn.execute(
                """
                INSERT INTO historical_tests (exam_code, title, exam_type, year, pdf_path, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (exam_code, title, exam_type, year, pdf_path, source, created_at),
            )
            return int(cur.lastrowid)
        test_id = int(row["id"])
        conn.execute(
            """
            UPDATE historical_tests
            SET title = ?, exam_type = ?, year = ?, pdf_path = ?, source = ?
            WHERE id = ?
            """,
            (title, exam_type, year, pdf_path, source, test_id),
        )
        return test_id


def replace_historical_questions(
    test_id: int,
    questions: list[dict[str, object]],
) -> int:
    with managed_connection() as conn:
        conn.execute("DELETE FROM historical_questions WHERE test_id = ?", (int(test_id),))
        inserted = 0
        for q in questions:
            conn.execute(
                """
                INSERT INTO historical_questions
                (test_id, question_number, section, category, prompt, choice_a, choice_b, choice_c, choice_d, choice_e,
                 correct_answer, explanation, source_page)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(test_id),
                    int(q.get("question_number", inserted + 1)),
                    str(q.get("section", "General")),
                    str(q.get("category", "unknown")),
                    str(q.get("prompt", "")).strip(),
                    q.get("choice_a"),
                    q.get("choice_b"),
                    q.get("choice_c"),
                    q.get("choice_d"),
                    q.get("choice_e"),
                    q.get("correct_answer"),
                    str(q.get("explanation", "")),
                    q.get("source_page"),
                ),
            )
            inserted += 1
        return inserted


def list_historical_tests(
    exam_type: str | None = None,
) -> list[HistoricalTest]:
    with managed_connection() as conn:
        if exam_type is None or exam_type == "all":
            rows = conn.execute(
                """
                SELECT id, exam_code, title, exam_type, year, pdf_path, source
                FROM historical_tests
                ORDER BY COALESCE(year, 0) DESC, title ASC
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, exam_code, title, exam_type, year, pdf_path, source
                FROM historical_tests
                WHERE exam_type = ?
                ORDER BY COALESCE(year, 0) DESC, title ASC
                """,
                (exam_type,),
            ).fetchall()
    return [
        HistoricalTest(
            int(r["id"]),
            str(r["exam_code"]),
            str(r["title"]),
            str(r["exam_type"]),
            int(r["year"]) if r["year"] is not None else None,
            str(r["pdf_path"]),
            str(r["source"]),
        )
        for r in rows
    ]


def list_historical_questions(
    *,
    exam_type: str = "all",
    category: str = "all",
    limit: int = 50,
) -> list[HistoricalQuestion]:
    limit = max(1, int(limit))
    params: list[object] = []
    where: list[str] = []
    if exam_type != "all":
        where.append("ht.exam_type = ?")
        params.append(exam_type)
    if category != "all":
        where.append("hq.category = ?")
        params.append(category)
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    with managed_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT hq.id, hq.test_id, hq.question_number, hq.section, hq.category, hq.prompt,
                   hq.choice_a, hq.choice_b, hq.choice_c, hq.choice_d, hq.choice_e,
                   hq.correct_answer, hq.explanation, hq.source_page
            FROM historical_questions hq
            JOIN historical_tests ht ON ht.id = hq.test_id
            {where_sql}
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
    return [
        HistoricalQuestion(
            int(r["id"]),
            int(r["test_id"]),
            int(r["question_number"]),
            str(r["section"]),
            str(r["category"]),
            str(r["prompt"]),
            r["choice_a"],
            r["choice_b"],
            r["choice_c"],
            r["choice_d"],
            r["choice_e"],
            r["correct_answer"],
            str(r["explanation"] or ""),
            int(r["source_page"]) if r["source_page"] is not None else None,
        )
        for r in rows
    ]


def list_historical_questions_for_test(test_id: int) -> list[HistoricalQuestion]:
    with managed_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, test_id, question_number, section, category, prompt,
                   choice_a, choice_b, choice_c, choice_d, choice_e,
                   correct_answer, explanation, source_page
            FROM historical_questions
            WHERE test_id = ?
            ORDER BY question_number ASC, id ASC
            """,
            (int(test_id),),
        ).fetchall()
    return [
        HistoricalQuestion(
            int(r["id"]),
            int(r["test_id"]),
            int(r["question_number"]),
            str(r["section"]),
            str(r["category"]),
            str(r["prompt"]),
            r["choice_a"],
            r["choice_b"],
            r["choice_c"],
            r["choice_d"],
            r["choice_e"],
            r["correct_answer"],
            str(r["explanation"] or ""),
            int(r["source_page"]) if r["source_page"] is not None else None,
        )
        for r in rows
    ]


def apply_historical_answer_key(*, exam_code: str, answers: dict[int, str]) -> int:
    if not answers:
        return 0
    with managed_connection() as conn:
        row = conn.execute(
            "SELECT id FROM historical_tests WHERE exam_code = ?",
            (str(exam_code),),
        ).fetchone()
        if row is None:
            return 0
        test_id = int(row["id"])
        updated = 0
        for qnum, answer in answers.items():
            ans = str(answer).strip().upper()
            if ans not in {"A", "B", "C", "D", "E"}:
                continue
            cur = conn.execute(
                """
                UPDATE historical_questions
                SET correct_answer = ?
                WHERE test_id = ? AND question_number = ?
                """,
                (ans, test_id, int(qnum)),
            )
            updated += int(cur.rowcount)
        return updated


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
