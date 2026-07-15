-- Frozen populated MandelQuest schema-v9 database before persistence v10-v17.
PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;
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
INSERT INTO "assignments" VALUES(1,2,'fractions','Add unlike denominators','quiz_score_pct',100.0,2,2,'typed',20,50,30,1,'Legacy assignment','2026-02-01T08:15:00+00:00',NULL);
CREATE TABLE books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                pdf_filename TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
INSERT INTO "books" VALUES(1,'Legacy Workbook','local','legacy-workbook.pdf','2026-02-01T07:00:00+00:00');
CREATE TABLE daily_goal_history (
                profile_id INTEGER NOT NULL,
                day_utc TEXT NOT NULL,
                completions INTEGER NOT NULL DEFAULT 0,
                last_completed_at TEXT NOT NULL,
                PRIMARY KEY (profile_id, day_utc),
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );
INSERT INTO "daily_goal_history" VALUES(2,'2026-02-01',1,'2026-02-01T08:25:00+00:00');
CREATE TABLE exercise_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                location TEXT NOT NULL,
                text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT NOT NULL,
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
            );
INSERT INTO "exercise_candidates" VALUES(1,1,'p. 3','Find one half plus one fourth.','new','2026-02-01T07:05:00+00:00');
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
INSERT INTO "historical_questions" VALUES(1,1,1,'Math','fractions','What is 1/2 + 1/4?','1/4','1/2','3/4','1',NULL,'C','Use fourths.',1);
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
INSERT INTO "historical_tests" VALUES(1,'LEGACY-TEST-1','Legacy Test','SAT',2025,'/legacy/test.pdf','fixture','2026-02-01T07:20:00+00:00');
CREATE TABLE profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
INSERT INTO "profiles" VALUES(1,'Legacy Parent','parent','2026-02-01T08:00:00+00:00');
INSERT INTO "profiles" VALUES(2,'Legacy Child','child','2026-02-01T08:05:00+00:00');
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
INSERT INTO "question_templates" VALUES(1,1,'legacy-fractions-1','fractions','Add unlike denominators','Core','expression','{a}/{b} + {c}/{d}','3/4','','Use a common denominator.',1,3,4.0,1,'2026-02-01T07:10:00+00:00');
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
INSERT INTO "quiz_attempts" VALUES(1,2,1,'fractions','typed',2,2,1,14.5,'2026-02-01T08:20:00+00:00');
CREATE TABLE quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                skill TEXT NOT NULL,
                question_label TEXT NOT NULL DEFAULT 'Core',
                mode TEXT NOT NULL DEFAULT 'expression',
                prompt TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                user_answer TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                explanation TEXT NOT NULL,
                FOREIGN KEY(attempt_id) REFERENCES quiz_attempts(id) ON DELETE CASCADE
            );
INSERT INTO "quiz_questions" VALUES(1,1,'fractions','Core','expression','1/2 + 1/4','3/4','3/4',1,'Use a common denominator.');
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
INSERT INTO "quiz_sets" VALUES(1,'Legacy Fractions','fractions','typed',2,2,20,50,30,'2026-02-01T08:10:00+00:00');
CREATE TABLE schema_version (
            id INTEGER PRIMARY KEY CHECK(id = 1),
            version INTEGER NOT NULL
        );
INSERT INTO "schema_version" VALUES(1,9);
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
INSERT INTO "skill_subskill_progress" VALUES(2,'fractions','Add unlike denominators',1,1,0,'2026-02-01T08:20:00+00:00');
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
INSERT INTO "template_vars" VALUES(1,'a','int',1.0,9.0,1.0);
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
INSERT INTO "worksheets" VALUES(1,2,1,'fractions','typed',2,2,'/legacy/fractions-worksheet.pdf','2026-02-01T08:12:00+00:00');
CREATE UNIQUE INDEX idx_question_templates_external_id
        ON question_templates(external_id)
        WHERE external_id IS NOT NULL;
CREATE INDEX idx_historical_questions_test_qnum
        ON historical_questions(test_id, question_number);
CREATE INDEX idx_historical_questions_category
        ON historical_questions(category);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('profiles',2);
INSERT INTO "sqlite_sequence" VALUES('quiz_sets',1);
INSERT INTO "sqlite_sequence" VALUES('quiz_attempts',1);
INSERT INTO "sqlite_sequence" VALUES('quiz_questions',1);
INSERT INTO "sqlite_sequence" VALUES('worksheets',1);
INSERT INTO "sqlite_sequence" VALUES('assignments',1);
INSERT INTO "sqlite_sequence" VALUES('books',1);
INSERT INTO "sqlite_sequence" VALUES('exercise_candidates',1);
INSERT INTO "sqlite_sequence" VALUES('question_templates',1);
INSERT INTO "sqlite_sequence" VALUES('historical_tests',1);
INSERT INTO "sqlite_sequence" VALUES('historical_questions',1);
COMMIT;
PRAGMA foreign_keys = ON;
