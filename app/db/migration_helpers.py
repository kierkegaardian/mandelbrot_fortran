from __future__ import annotations

import sqlite3
import uuid

from ._util import _sync_now_text

def _ensure_sync_schema(conn: sqlite3.Connection) -> None:
    _ensure_sync_columns(conn, "profiles", "created_at")
    _ensure_sync_columns(conn, "quiz_sets", "created_at")
    _ensure_sync_columns(conn, "quiz_attempts", "created_at")
    _ensure_sync_columns(conn, "quiz_questions", None)
    _ensure_sync_columns(conn, "assignments", "created_at")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sync_outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_sync_id TEXT NOT NULL,
            action TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            last_attempt_at TEXT,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            synced_at TEXT
        );
        """
    )


def _ensure_sync_columns(conn: sqlite3.Connection, table: str, source_timestamp_column: str | None) -> None:
    _ensure_column(conn, table, "sync_id", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, table, "sync_updated_at", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, table, "sync_deleted", "INTEGER NOT NULL DEFAULT 0")

    select_columns = "id, sync_id, sync_updated_at"
    if source_timestamp_column is not None:
        select_columns += f", {source_timestamp_column} AS source_ts"
    else:
        select_columns += ", NULL AS source_ts"
    rows = conn.execute(f"SELECT {select_columns} FROM {table}").fetchall()
    fallback_updated_at = _sync_now_text()
    for row in rows:
        assignments: list[str] = []
        params: list[object] = []
        if not row["sync_id"]:
            assignments.append("sync_id = ?")
            params.append(str(uuid.uuid4()))
        if not row["sync_updated_at"]:
            source_ts = row["source_ts"]
            assignments.append("sync_updated_at = ?")
            params.append(str(source_ts) if source_ts else fallback_updated_at)
        if assignments:
            params.append(int(row["id"]))
            conn.execute(
                f"UPDATE {table} SET {', '.join(assignments)} WHERE id = ?",
                tuple(params),
            )


def _enqueue_existing_sync_rows(conn: sqlite3.Connection) -> None:
    sync_entities: tuple[tuple[str, str], ...] = (
        ("profiles", "profiles"),
        ("quiz_sets", "quiz_sets"),
        ("assignments", "assignments"),
        ("quiz_attempts", "quiz_attempts"),
        ("quiz_questions", "quiz_questions"),
    )
    for entity_type, table in sync_entities:
        rows = conn.execute(
            f"""
            SELECT entity.id, entity.sync_id, entity.sync_updated_at
            FROM {table} AS entity
            WHERE entity.sync_deleted = 0
              AND entity.sync_id <> ''
              AND NOT EXISTS (
                  SELECT 1
                  FROM sync_outbox AS pending
                  WHERE pending.entity_type = ?
                    AND pending.entity_sync_id = entity.sync_id
              )
            ORDER BY entity.id ASC
            """,
            (entity_type,),
        ).fetchall()
        for row in rows:
            local_id = int(row["id"])
            conn.execute(
                """
                INSERT INTO sync_outbox
                (entity_type, entity_sync_id, action, payload_json, created_at,
                 last_attempt_at, attempt_count, last_error, synced_at)
                VALUES (?, ?, 'upsert', ?, ?, NULL, 0, NULL, NULL)
                """,
                (
                    entity_type,
                    str(row["sync_id"]),
                    f'{{"local_id": {local_id}}}',
                    str(row["sync_updated_at"]),
                ),
            )


def _ensure_external_id_unique_index(conn: sqlite3.Connection) -> None:
    # Enforce uniqueness without requiring ALTER TABLE to add a UNIQUE column.
    # Multiple NULL values are allowed; empty strings should be avoided by the loader.
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_question_templates_external_id
        ON question_templates(external_id)
        WHERE external_id IS NOT NULL;
        """
    )


def _ensure_historical_indexes(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_historical_questions_test_qnum
        ON historical_questions(test_id, question_number);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_historical_questions_category
        ON historical_questions(category);
        """
    )


def _ensure_parent_auth_indexes(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_parent_auth_locked_until
        ON parent_auth(locked_until);
        """
    )


def _ensure_quiz_progress_indexes(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_quiz_attempt_progress_profile_updated
        ON quiz_attempt_progress(profile_id, updated_at DESC);
        """
    )


def _ensure_sync_indexes(conn: sqlite3.Connection) -> None:
    for table in ("profiles", "quiz_sets", "quiz_attempts", "quiz_questions", "assignments"):
        conn.execute(
            f"""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_sync_id
            ON {table}(sync_id);
            """
        )
        conn.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_sync_updated_at
            ON {table}(sync_updated_at DESC);
            """
        )
        conn.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_sync_deleted
            ON {table}(sync_deleted);
            """
        )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sync_outbox_pending
        ON sync_outbox(synced_at, id);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sync_outbox_entity
        ON sync_outbox(entity_type, entity_sync_id, id);
        """
    )


def _ensure_summer_program_indexes(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_summer_programs_profile_status
        ON summer_programs(profile_id, status, updated_at DESC);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_summer_program_tasks_program_sequence
        ON summer_program_tasks(program_id, sequence_index ASC);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_summer_assessment_runs_program_type
        ON summer_assessment_runs(program_id, assessment_type, completed_at DESC);
        """
    )


def _ensure_school_year_indexes(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_school_year_targets_grade
        ON school_year_targets(grade, updated_at DESC);
        """
    )


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    existing = {r["name"] for r in rows}
    if column in existing:
        return
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def _rewrite_skill_id(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    old_skill: str,
    new_skill: str,
) -> None:
    conn.execute(
        f"UPDATE {table} SET {column} = ? WHERE {column} = ?",
        (new_skill, old_skill),
    )

def _schema_version(conn: sqlite3.Connection) -> int:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY CHECK(id = 1),
            version INTEGER NOT NULL
        );
        """
    )
    row = conn.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()
    if row is not None:
        return int(row["version"])
    conn.execute("INSERT INTO schema_version (id, version) VALUES (1, 0)")
    return 0


def _ensure_schema_support(conn: sqlite3.Connection) -> None:
    _ensure_sync_schema(conn)
    _ensure_external_id_unique_index(conn)
    _ensure_historical_indexes(conn)
    _ensure_parent_auth_indexes(conn)
    _ensure_quiz_progress_indexes(conn)
    _ensure_sync_indexes(conn)
    _ensure_summer_program_indexes(conn)
    _ensure_school_year_indexes(conn)
    from ..summer_program_template_seed import ensure_summer_program_templates

    ensure_summer_program_templates(conn)
