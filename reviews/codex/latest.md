# Codex review: God-file split plan (2026-07-08)

**Reviewer:** Codex CLI (`gpt-5.5`), read-only sandbox  
**Plan reviewed:** `docs/god-file-split-plan-2026-07-08.md`  
**Session:** `019f43ae-2291-7093-838c-3877c5d8b6bb`  
**Note:** Reviewer could not write files under read-only sandbox; this artifact was captured from Codex stdout by the orchestrating agent.

## Verdict (approve / approve-with-changes / reject)

**approve-with-changes**

## Summary (5-10 lines)

- The plan targets the right oversized modules and is feasible overall.
- PR1 is not ready as written because `db.db_config` is currently monkeypatched by tests; a simple package facade will break that contract.
- The quiz-engine facade inventory is incomplete: `ContentUnavailableError` is imported from `app.quiz_engine` today.
- The migration bucket is underestimated; `_run_migrations` plus `_ensure_*` helpers likely exceeds the AGENTS 400 LOC pause threshold.
- `ui_parent.py` matches the proposed tab seams.
- `ui_quiz.py` is already partly split into `quiz_flow.py`, `quiz_history.py`, and `quiz_strategies.py`; PR4 should extend those seams.
- PR1 verification needs broader DB consumer coverage: sync, scripts, summer, school-year, content audit.
- No network, remote, schema redesign, or UI redesign is required.

## Alignment with AGENTS.md

The plan aligns with the repo’s modular-first rule and correctly proposes a split before large edits. It preserves offline-first behavior and avoids remote/push changes. It needs stronger typesafety discipline around explicit `__all__` exports and should avoid star/dynamic facade imports. Any migration file expected to exceed 400 LOC needs an explicit exception rationale before implementation.

## Plan vs actual codebase (what matches / mismatches)

Matches:

- `app/db.py` is 2868 LOC, with `init_db` at 277 LOC and `_run_migrations` at 293 LOC.
- `app/quiz_engine.py` is 1396 LOC, with a 589 LOC `generate_question`.
- `app/ui_parent.py` is one large `ParentPanel` class with clear tab seams.
- `app/ui_quiz.py` is one large `QuizPanel` class, but already delegates to `quiz_flow.py`, `quiz_history.py`, and `quiz_strategies.py`.
- Existing generator modules are real and mostly under 300 LOC.

Mismatches:

- The DB facade plan misses direct `db.db_config = _tmp_config` assignment in tests.
- The quiz-engine public API list omits `ContentUnavailableError`.
- The proposed `migrations.py` bucket is too large if it includes `_run_migrations` plus all `_ensure_*` helpers.
- PR1 test coverage is too narrow for real DB call sites.
- Proposed `ui_quiz_view.py` duplicates existing `quiz_flow.py` responsibilities.

## Strengths

- Keeps stable user-facing imports.
- Prioritizes behavior-preserving mechanical moves.
- Correctly protects template precedence in `generate_question`.
- Correctly avoids duplicating existing generator modules.
- Treats Tk UI extraction as higher risk than DB/engine extraction.
- Includes useful per-PR verification and line-count gates.

## Findings

### P1: DB config override contract will break under a simple package facade

Severity: **P1**

Evidence: `app/db.py:46` defines `db_config`; `app/db.py:51` uses it from `connect`. Tests assign `db.db_config = _tmp_config` before `db.init_db()` in `tests/test_db_parent_auth_and_progress.py`, `tests/test_sync_service.py`, and `tests/test_db_assignment_semantics.py`.

Why it matters: A package facade re-exporting `connection.db_config` will not make `db.db_config = ...` affect `connection.connect()`. Tests could silently hit the real app DB.

Concrete plan change recommended: Add and document a typed config override mechanism before PR1, such as `set_db_config_provider` or `override_db_config`, update tests to use it, and add a smoke test proving all split DB modules use the same provider.

### P1: Quiz-engine facade inventory is incomplete

Severity: **P1**

Evidence: `app/content_audit.py:8` imports `ContentUnavailableError` from `.quiz_engine`, but the plan’s public API freeze omits it.

Why it matters: The split can break an existing app import while core question generation still passes.

Concrete plan change recommended: Add an explicit current-export inventory for `app.quiz_engine` and include `ContentUnavailableError`, `GEOMETRY_AREA_SUBSKILLS`, `TRIG_PRECALCULUS_SUBSKILLS`, `QUESTION_TYPES`, `SKILLS`, `Question`, and `generate_question` in facade smoke tests.

### P2: Migration module estimate is too low

Severity: **P2**

Evidence: `_run_migrations` spans roughly `app/db.py:351`–`643`; `_ensure_*` helpers span roughly `app/db.py:646`–`827`.

Why it matters: Putting all of that into one `migrations.py` likely exceeds 400 LOC, triggering the AGENTS pause/exception rule.

Concrete plan change recommended: Split migration ordering from helpers, for example `migrations.py`, `migration_helpers.py`, `sync_schema.py`, or `indexes.py`, or record an explicit exception rationale before PR1.

### P2: PR1 verification misses major DB consumers

Severity: **P2**

Evidence: DB consumers include scripts using `db.connect()`, sync modules using `db.managed_connection()`, and major callers in `app/summer_program.py`, `app/school_year.py`, `app/content_audit.py`, `app/ui_dashboard.py`, and `app/ui_skill_map.py`.

Why it matters: `db.init_db()` plus a few DB tests can pass while scripts, sync payloads, summer tasks, or school-year paths fail.

Concrete plan change recommended: Add PR1 checks for summer/school-year/content-audit tests, sync import smoke, and DB script `--help` or dry-run import smoke.

### P2: Facades should not rely on temporary star/dynamic imports

Severity: **P2**

Evidence: `mandelquest.spec` has `hiddenimports=[]`; the plan allows star-import as a temporary bridge.

Why it matters: Dynamic/broad facade imports can hide missing exports and make PyInstaller analysis less reliable.

Concrete plan change recommended: Require explicit static imports and explicit `__all__` from the first split PR. Add packaging smoke if dynamic imports are used.

### P2: PR2 needs deterministic generation regression coverage

Severity: **P2**

Evidence: `generate_question` uses global `random` heavily; current tests do not seed `random`.

Why it matters: Mechanical moves can change generation order or fallback behavior without property tests catching it.

Concrete plan change recommended: Add a small seeded regression smoke for representative skills and modes before moving quiz-engine branches.

### P3: `ui_quiz` module map duplicates existing seams

Severity: **P3**

Evidence: `ui_quiz.py` already delegates show/build/submit/next/finish/render behavior to `quiz_flow.py`; `quiz_strategies.py` already owns launch strategy builders.

Why it matters: Adding parallel `ui_quiz_view.py` or strategy modules creates competing structures.

Concrete plan change recommended: Revise PR4 to extend or rename existing `quiz_flow.py`, `quiz_history.py`, and `quiz_strategies.py`.

### P3: ParentPanel composition needs an explicit section contract

Severity: **P3**

Evidence: `_refresh_profiles` fans out across tabs; profile settings also own sync/offline/external-link state.

Why it matters: Tab objects can become tightly coupled to parent internals without a small shared context.

Concrete plan change recommended: Add a PR3 note defining a typed section context: profile getter, launch callbacks, settings-changed callback, and shared refresh hooks.

## Risks the plan underweights

- Silent real-DB use if config override semantics are not fixed.
- `migrations.py` exceeding 400 LOC.
- Missing exports hidden by star imports.
- Dirty-worktree risk during a broad mechanical move.
- Quiz behavior drift not caught by unseeded tests.
- PyInstaller behavior with dynamic package facades.

## Recommended plan revisions (ordered)

1. Add a PR1 pre-step to inventory exact public exports for `app.db` and `app.quiz_engine`.
2. Resolve `db.db_config` override semantics before moving DB functions.
3. Split migration helpers or record an explicit exception rationale.
4. Expand PR1 verification across scripts, sync, summer, school-year, content-audit, dashboard, and skill-map paths.
5. Add `ContentUnavailableError` to the quiz-engine facade contract.
6. Add seeded representative quiz-generation regression checks before PR2.
7. Revise PR4 to build on existing `quiz_flow.py`, `quiz_history.py`, and `quiz_strategies.py`.
8. Add an implementation note to preserve unrelated dirty-worktree changes and report touched files per PR.

## PR1 readiness checklist (pass/fail items)

- **PASS:** `app/db.py` is the highest-value split target.
- **PASS:** No remote, push, network, schema redesign, or product behavior change is required.
- **PASS:** Current import smoke works for `db`, `quiz_engine`, `ParentPanel`, and `QuizPanel`.
- **FAIL:** DB config override behavior is not specified.
- **FAIL:** Explicit DB facade export inventory is missing.
- **FAIL:** Planned migration bucket likely violates the file-size rule.
- **FAIL:** PR1 test list is too narrow.
- **FAIL:** PyInstaller/static facade strategy is not strict enough.
- **FAIL:** Dirty-worktree implementation strategy is missing.

## Residual questions

- Is direct `db.db_config = ...` a supported internal test contract, or may PR1 replace it with an explicit override helper?
- Should `app/db/` still be preferred over a `db.py` shim after accounting for monkeypatch semantics?
- Which migration helper grouping is acceptable if `_run_migrations` remains near 300 LOC?
- Should PR1 include packaging smoke, or is import smoke enough until later PRs?
- Should `SKILLS` remain owned by `quiz_engine`, or move to `skill_graph` in a later non-mechanical cleanup?
