PRAGMA foreign_keys = ON;

-- Frozen app.db schema immediately before Family Sync metadata (schema v11).
CREATE TABLE profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE quiz_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    skill TEXT NOT NULL,
    question_type TEXT NOT NULL,
    num_questions INTEGER NOT NULL,
    level INTEGER NOT NULL,
    mode_intuition_pct INTEGER,
    mode_expression_pct INTEGER,
    mode_word_pct INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE quiz_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    quiz_set_id INTEGER,
    skill TEXT NOT NULL,
    question_type TEXT NOT NULL,
    num_questions INTEGER NOT NULL,
    level INTEGER NOT NULL,
    score INTEGER NOT NULL,
    elapsed_seconds REAL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY(quiz_set_id) REFERENCES quiz_sets(id) ON DELETE SET NULL
);

CREATE TABLE quiz_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    skill TEXT NOT NULL,
    subskill TEXT,
    question_label TEXT NOT NULL DEFAULT 'Core',
    mode TEXT NOT NULL DEFAULT 'expression',
    prompt TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    user_answer TEXT NOT NULL,
    is_correct INTEGER NOT NULL,
    explanation TEXT NOT NULL,
    FOREIGN KEY(attempt_id) REFERENCES quiz_attempts(id) ON DELETE CASCADE
);

CREATE TABLE worksheets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    quiz_set_id INTEGER,
    skill TEXT NOT NULL,
    question_type TEXT NOT NULL,
    num_questions INTEGER NOT NULL,
    level INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY(quiz_set_id) REFERENCES quiz_sets(id) ON DELETE SET NULL
);

CREATE TABLE skill_subskill_progress (
    profile_id INTEGER NOT NULL,
    skill TEXT NOT NULL,
    subskill TEXT NOT NULL,
    current_streak INTEGER NOT NULL DEFAULT 0,
    best_streak INTEGER NOT NULL DEFAULT 0,
    mastered INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (profile_id, skill, subskill),
    FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    pdf_filename TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE exercise_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    location TEXT NOT NULL,
    text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
);

CREATE TABLE question_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    external_id TEXT,
    skill TEXT NOT NULL,
    subskill TEXT NOT NULL,
    label TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'expression',
    prompt_template TEXT NOT NULL,
    answer_expr TEXT NOT NULL,
    constraint_expr TEXT NOT NULL DEFAULT '',
    explanation_template TEXT NOT NULL,
    min_level INTEGER NOT NULL DEFAULT 1,
    max_level INTEGER NOT NULL DEFAULT 3,
    choice_spread REAL NOT NULL DEFAULT 4.0,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE SET NULL
);

CREATE TABLE template_vars (
    template_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    min_value REAL NOT NULL,
    max_value REAL NOT NULL,
    step REAL NOT NULL DEFAULT 1,
    PRIMARY KEY (template_id, name),
    FOREIGN KEY(template_id) REFERENCES question_templates(id) ON DELETE CASCADE
);

CREATE TABLE assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    skill TEXT NOT NULL,
    subskill TEXT,
    target_type TEXT NOT NULL,
    target_value REAL NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    num_questions INTEGER NOT NULL DEFAULT 5,
    question_type TEXT NOT NULL DEFAULT 'both',
    mode_intuition_pct INTEGER,
    mode_expression_pct INTEGER,
    mode_word_pct INTEGER,
    active INTEGER NOT NULL DEFAULT 1,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

CREATE TABLE parent_auth (
    profile_id INTEGER PRIMARY KEY,
    pin_hash TEXT NOT NULL,
    pin_salt TEXT NOT NULL,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

CREATE TABLE quiz_attempt_progress (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    question_index INTEGER NOT NULL DEFAULT 0,
    state_json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

CREATE TABLE daily_goal_history (
    profile_id INTEGER NOT NULL,
    day_utc TEXT NOT NULL,
    completions INTEGER NOT NULL DEFAULT 0,
    last_completed_at TEXT NOT NULL,
    PRIMARY KEY (profile_id, day_utc),
    FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

CREATE TABLE historical_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    exam_type TEXT NOT NULL,
    year INTEGER,
    pdf_path TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'historical_pdf',
    created_at TEXT NOT NULL
);

CREATE TABLE historical_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER NOT NULL,
    question_number INTEGER NOT NULL,
    section TEXT NOT NULL DEFAULT 'General',
    category TEXT NOT NULL DEFAULT 'unknown',
    prompt TEXT NOT NULL,
    choice_a TEXT,
    choice_b TEXT,
    choice_c TEXT,
    choice_d TEXT,
    choice_e TEXT,
    correct_answer TEXT,
    explanation TEXT NOT NULL DEFAULT '',
    source_page INTEGER,
    FOREIGN KEY(test_id) REFERENCES historical_tests(id) ON DELETE CASCADE
);

CREATE TABLE schema_version (
    id INTEGER PRIMARY KEY CHECK(id = 1),
    version INTEGER NOT NULL
);

INSERT INTO schema_version (id, version) VALUES (1, 11);
INSERT INTO profiles (id, name, role, created_at) VALUES
    (1, 'Legacy Parent', 'parent', '2026-03-01T08:00:00+00:00'),
    (2, 'Legacy Child', 'child', '2026-03-01T08:05:00+00:00');
INSERT INTO quiz_sets
    (id, name, skill, question_type, num_questions, level,
     mode_intuition_pct, mode_expression_pct, mode_word_pct, created_at)
VALUES
    (10, 'Legacy Addition', 'add_subtract', 'typed', 1, 1,
     20, 50, 30, '2026-03-01T08:10:00+00:00');
INSERT INTO quiz_attempts
    (id, profile_id, quiz_set_id, skill, question_type, num_questions,
     level, score, elapsed_seconds, created_at)
VALUES
    (20, 2, 10, 'add_subtract', 'typed', 1,
     1, 1, 9.5, '2026-03-01T08:20:00+00:00');
INSERT INTO quiz_questions
    (id, attempt_id, skill, subskill, question_label, mode, prompt,
     correct_answer, user_answer, is_correct, explanation)
VALUES
    (30, 20, 'add_subtract', 'Sums within 20', 'Core', 'expression',
     '7 + 5', '12', '12', 1, 'Seven plus five is twelve.');
INSERT INTO assignments
    (id, profile_id, skill, subskill, target_type, target_value, level,
     num_questions, question_type, mode_intuition_pct, mode_expression_pct,
     mode_word_pct, active, notes, created_at, completed_at)
VALUES
    (60, 2, 'add_subtract', 'Sums within 20', 'quiz_score_pct', 100, 1,
     1, 'typed', 20, 50, 30, 1, 'Legacy assignment',
     '2026-03-01T08:15:00+00:00', NULL);

-- Local-only records must survive without entering the Family Sync outbox.
INSERT INTO worksheets
    (id, profile_id, quiz_set_id, skill, question_type, num_questions,
     level, file_path, created_at)
VALUES
    (40, 2, 10, 'add_subtract', 'typed', 1,
     1, '/legacy/worksheet.pdf', '2026-03-01T08:12:00+00:00');
INSERT INTO skill_subskill_progress
    (profile_id, skill, subskill, current_streak, best_streak, mastered, updated_at)
VALUES
    (2, 'add_subtract', 'Sums within 20', 1, 1, 0,
     '2026-03-01T08:20:00+00:00');
INSERT INTO parent_auth
    (profile_id, pin_hash, pin_salt, failed_attempts, locked_until, updated_at)
VALUES
    (1, 'legacy-pin-hash', 'legacy-pin-salt', 0, NULL,
     '2026-03-01T08:00:00+00:00');
INSERT INTO quiz_attempt_progress
    (attempt_id, profile_id, question_index, state_json, updated_at)
VALUES
    (50, 2, 1, '{"version":1,"pending":true}',
     '2026-03-01T08:25:00+00:00');
