# MandelQuest God-File Split Plan

**Date:** 2026-07-08
**Repo:** `/home/user/projects/mandelbrot_fortran`
**Status:** PR1 complete on 2026-07-13; PR2-PR5 remain planned — **revised after Codex review**
**Trigger:** Maintainability debt from oversized modules vs AGENTS file-size rule (`<= 300` LOC target; pause before committing `> 400` LOC without rationale)
**Codex review:** `reviews/codex/god-file-split-plan-review-2026-07-08.md` (also `reviews/codex/latest.md`) — **verdict: approve-with-changes** (P1 blockers for PR1 as originally written)

Browser-friendly twin: `docs/god-file-split-plan-2026-07-08.html`

---

## Implementation receipt (2026-07-13)

PR1 is complete. `app/db.py` is replaced by an explicit `app/db/` package with a static 88-symbol facade,
one shared config provider, and 19 bounded implementation modules. Every package file is `<=290` lines.

Behavior-preservation checks passed:

- all 82 public DB function signatures match the checkpoint source;
- all 153 SQL literals are preserved with none added or removed;
- the 68-test broad DB-consumer set passes;
- all three DB-facing scripts pass import/`--help` smoke;
- app smoke reports `[smoke-test] OK` and full discovery passes 347 tests.

---

## 0. Codex revisions incorporated (2026-07-08)

Blocking plan updates from Codex **P1** and required **P2** items:

1. **DB config override contract (P1):** Tests assign `db.db_config = _tmp_config` in many modules (`test_db_*`, `test_sync_*`, summer/school-year/content-audit/mastery). A package facade that re-exports `connection.db_config` **breaks** this unless `connect()` always reads a shared provider.
   **Decision for PR1:** Introduce an explicit override API in `connection.py`, e.g. `get_db_config()` / `set_db_config(DbConfig | Callable[[], DbConfig])` (or keep a module-level `_config_provider` that both `db_config()` and tests use). Prefer keeping `db.db_config` as a **function** that always calls the provider, and migrate tests to `set_db_config(...)` **or** support assignment via a thin descriptor/property on the package object documented as test-only. Minimum: one shared provider; smoke test that `db.connect()` honors the override after package split.
2. **Public export inventory (P1/P2):** Before moving code, freeze explicit `__all__` lists from current imports (see §3.0). No star-import facade.
3. **Migrations size (P2):** Do **not** put `_run_migrations` + all `_ensure_*` in one file. Split into `migrations.py` (ordering) + `migration_helpers.py` / `indexes.py` / `sync_schema.py` as needed so each stays `<=300` (or document a single exception if a pure DDL block must sit near 300).
4. **Broader PR1 verification (P2):** Include summer, school-year, content-audit, fall-readiness, sync tests + script import smoke—not only the two `test_db_*` files.
5. **Quiz facade (P1):** Re-export `ContentUnavailableError` from `quiz_engine` facade (already re-exported today via import in `quiz_engine.py` and used by `content_audit.py`).
6. **PR2 (P2):** Add seeded `random.seed(...)` generation regression smoke before moving skill branches.
7. **PR4 (P3):** Extend existing `quiz_flow.py` / `quiz_history.py` / `quiz_strategies.py` instead of inventing parallel `ui_quiz_view.py` seams.
8. **Worktree hygiene:** Preserve unrelated dirty files; report touched paths per PR; no drive-by cleanups.

**PR1 readiness after these revisions:** proceed only once §3.0 inventory + config-provider design are in the PR description.

---

## 1. Problem statement

Several core modules far exceed the project modular-first rule:

| File | ~LOC | Shape | Why it hurts |
| --- | ---: | --- | --- |
| `app/db.py` | 2868 | ~99 free functions + huge `init_db` / migrations | Every feature touches SQLite here; high merge/regression risk |
| `app/ui_parent.py` | 1988 | One `ParentPanel` class (~72 methods) | Parent tabs are independent products jammed into one class |
| `app/ui_quiz.py` | 1592 | One `QuizPanel` class (~80 methods) | Launch strategies, session state, UI, progress, historical tests mixed |
| `app/quiz_engine.py` | 1396 | Helpers + giant `generate_question` if-chain | Skill generators hard to navigate; already partially extracted elsewhere |
| `app/summer_program.py` | 1182 | Domain logic | Secondary target after db/quiz/parent |
| `app/explanations.py` | 974 | Large dict/catalog | Split later if editing friction remains |

This plan prioritizes **behavior-preserving mechanical splits** with a **stable import facade**, not redesign of pedagogy, schema, or UI copy.

---

## 2. Goals and non-goals

### Goals
1. Bring actively edited modules toward `<= 300` LOC (exceptions only with handoff rationale if a pure schema blob must stay slightly larger).
2. Keep public call sites working: `from app import db`, `db.init_db()`, `from app.quiz_engine import generate_question, Question, SKILLS`, `ParentPanel`, `QuizPanel`.
3. Make each module own one bounded concern so tests and agents can change one area safely.
4. Ship as a sequenced PR stack with verification after each PR (full or focused tests + import smoke).

### Non-goals
- No schema redesign, no new tables, no data migration for end users (file moves only).
- No UI redesign, no pedagogy/policy changes in `learning_engine`.
- No finishing multi-device sync.
- No mass rewrite of generators’ math content.
- No moving Fortran renderer or packaging story.

### Invariants (must not break)
- Offline-first local SQLite under `data/` / `MANDELQUEST_DATA_DIR`.
- Parent PIN hashing/lockout behavior.
- Attempt/question history as the learning ledger (sync docs already treat this as canonical).
- Template vs procedural generation precedence in `generate_question`.
- Child vs parent tab gating and offline/external-link settings.
- Pedagogical integrity and mastery-truthfulness tests remain green.

---

## 3. Compatibility strategy (required in PR1)

### 3.0 Pre-PR1 export inventory (required)

Generate and check into the PR notes (or a short `docs/` appendix) the **actual** public symbols:

```bash
# Approximate inventory from call sites (refine manually)
rg -n 'db\.[A-Za-z_][A-Za-z0-9_]*' app tests scripts --type py -o | sort -u
rg -n 'from app\.quiz_engine import|from \.quiz_engine import' app tests scripts --type py
```

**Known `quiz_engine` exports that must remain importable from `app.quiz_engine`:**
- `Question`, `SKILLS`, `QUESTION_TYPES`, `generate_question`
- `ContentUnavailableError` (imported by `content_audit.py` from `quiz_engine` today; defined in `quiz_content.py`)
- Any subskill constants tests import (`GEOMETRY_AREA_SUBSKILLS`, `TRIG_PRECALCULUS_SUBSKILLS`, etc.)

**Known `db` test contract:**
- Many tests do `db.db_config = _tmp_config` then `db.init_db()`. PR1 must preserve effective override semantics (see §0).

### 3.1 Database package facade
Convert `app/db.py` → package `app/db/`:

```text
app/db/
  __init__.py          # explicit re-exports only (static imports + __all__)
  connection.py        # DbConfig, get/set config provider, connect, managed_connection, db_config()
  schema.py            # init_db DDL only (CREATE TABLE IF NOT EXISTS...)
  migrations.py        # _run_migrations ordering only
  migration_helpers.py # _ensure_column and small shared helpers
  indexes.py           # _ensure_*_indexes helpers
  sync_schema.py       # _ensure_sync_schema / _ensure_sync_columns (if size warrants)
  profiles.py
  parent_auth.py
  quiz_sets.py
  attempts.py          # create_attempt, add_question_result, list_attempts
  progress.py          # quiz resume + subskill progress + daily goals + skill_progress_pipeline
  templates.py
  worksheets.py
  assignments.py
  historical.py
  books.py             # books + exercise candidates
  summer.py
  school_year.py
  _rows.py             # private row mappers + pin hash + time helpers if shared
```

**`app/db/__init__.py` rules:**
- Re-export every currently imported symbol so `from app import db` / `db.foo` keeps working.
- **Explicit static imports + explicit `__all__` from PR1 day one** (no star-import facade; Codex P2).
- Private helpers stay module-local with leading underscore; do not expand public surface.
- `connect()` / `managed_connection()` / all domain modules must share one config provider so test overrides cannot hit production `data/app.db` by accident.

**Import rule during/after split:**
- New code may `from app.db.attempts import create_attempt` optionally.
- Existing call sites need not change in the first stack.
- Avoid circular imports: connection/schema at bottom; domain modules import `managed_connection` only.

### 3.2 Quiz engine facade
Keep `app/quiz_engine.py` as a thin facade **or** convert to `app/quiz_engine/` package with the same exported names:

```text
app/quiz_engine/
  __init__.py          # Question, SKILLS, QUESTION_TYPES, generate_question, re-exports
  types.py             # Question dataclass, constants, LEGACY_SKILL_ALIASES
  choices.py           # _choice_set family, formatting helpers
  dispatch.py          # generate_question orchestration + template precedence
  foundation.py        # counting through money / long ops / integers / OoO
  algebra_geometry.py  # place_value deep, measurement deep, algebra_linear, geometry_area, pre_algebra bridge
  # Prefer reusing existing: algebra_1_generators, algebra_2_generators, elementary_generators, etc.
```

Do **not** duplicate modules that already exist (`algebra_1_generators.py`, `pre_algebra_generators.py`, …). Move only the remaining procedural bodies still living inside `quiz_engine.py`.

### 3.3 UI composition (not one mega-class forever)
Keep public classes:
- `from app.ui_parent import ParentPanel`
- `from app.ui_quiz import QuizPanel`

Internally compose section objects / mixins / helper modules rather than one 2k-line class body.

---

## 4. Target module map (detail)

### 4.1 `db` buckets → modules (from current symbol inventory)

| Module | Approx current symbols / blocks | Notes |
| --- | --- | --- |
| `connection.py` | `DbConfig`, `db_config`, `connect`, `managed_connection` | Tiny; foundation |
| `schema.py` | `init_db` (~279 LOC DDL) | May land ~280–320; OK if pure DDL and documented exception |
| `migrations.py` | `_run_migrations` (~295) + `_ensure_*` | Keep migration ordering single-threaded and explicit |
| `profiles.py` | list/create/delete profile | |
| `parent_auth.py` | PIN set/verify/lock/hash | Security-sensitive; keep tests in `test_db_parent_auth_and_progress.py` |
| `quiz_sets.py` | CRUD quiz sets | |
| `attempts.py` | create_attempt, add_question_result, list_attempts | Ledger core |
| `progress.py` | quiz_progress + subskill + daily goals + mode_accuracy + rebuild | |
| `templates.py` | template CRUD + mode listing | Heavy list/query helpers |
| `worksheets.py` | create/list/archive | |
| `assignments.py` | create/list/complete evaluation | Keep assignment semantics tests green |
| `historical.py` | historical tests/questions/answer keys | |
| `books.py` | books + exercise candidates | |
| `summer.py` | programs/tasks/assessments | Largest domain after schema |
| `school_year.py` | grade targets | Small |
| `_rows.py` / `_util.py` | row mappers, ISO helpers, sync_now_text | Shared private |

**Estimated end state:** most modules `80–250` LOC; `schema.py` / `migrations.py` may each be near 300.

### 4.2 `quiz_engine` split detail

Current shape:
- L67–80: `Question`
- L82–330: shared choice/format helpers
- L337–745: large skill helpers (`_algebra_linear_problem`, `_geometry_area_problem`, `_place_value_problem`, `_measurement_problem`)
- L808–end: `generate_question` skill if-chain + stats/trig/calc branches

Recommended order:
1. Extract `types.py` + `choices.py` (no behavior change).
2. Extract large helpers to `problems_algebra_geometry.py` (or reuse names aligned with existing generator files).
3. Extract foundation skill branches from `generate_question` into `problems_foundation.py`.
4. Leave `dispatch.py` as the only place that implements template precedence and skill routing.

**Public API freeze:** `Question`, `SKILLS`, `QUESTION_TYPES`, `LEGACY_SKILL_ALIASES` (if imported), `generate_question`, `ContentUnavailableError`, plus any subskill constants currently imported by tests (`GEOMETRY_AREA_SUBSKILLS`, `TRIG_PRECALCULUS_SUBSKILLS`, etc.—re-export from facade).

**PR2 pre-step:** add a small seeded generation regression (fixed `random.seed`, representative skills/modes) so mechanical moves cannot silently change outputs.

### 4.3 `ui_parent` split detail

Current tabs in `_build_controls`:
Profiles, Quiz Sets, Grades, Assignments, Summer Program, School Year, Worksheets

Proposed structure:

```text
app/ui_parent.py                 # ParentPanel shell: notebook + wiring only (<=300)
app/ui_parent_profiles.py        # profiles + PIN + offline/external/summer mode toggles + accessibility
app/ui_parent_quiz_sets.py
app/ui_parent_grades.py
app/ui_parent_assignments.py
app/ui_parent_summer.py          # summer tab + resource review export hooks
app/ui_parent_school_year.py
# worksheets already partially via WorksheetSection in parent_worksheets — keep that path
app/ui_parent_sync.py            # family sync controls if still in profiles tab
```

**Composition pattern (recommended):**
- Each section is a small class or builder that owns its tab frame and refresh methods.
- `ParentPanel` holds section instances and implements thin methods for keyboard shortcuts / `on_module_activated` / tab selection.
- Avoid deep inheritance of one giant `ParentPanel` mixin stack if composition is clearer.

### 4.4 `ui_quiz` split detail

**Codex correction:** Do not invent parallel modules that compete with existing seams. Extend:

```text
app/ui_quiz.py                   # QuizPanel shell + public launch entrypoints + thin Tk wiring
app/quiz_flow.py                 # EXISTING — grow show/build/submit/next/finish/render helpers here
app/quiz_history.py              # EXISTING — historical/SAT paths as already factored
app/quiz_strategies.py           # EXISTING — free/blend/focused plan builders
app/ui_quiz_controls.py          # optional: skill/track/subskill control construction only if still oversized
app/quiz_progress_ui.py          # optional: persist/resume/clear progress helpers if not already clean in panel
```

**Important:** Prefer extracting **pure** helpers into existing `quiz_*.py` modules first (easier unit tests) before slicing Tk widget trees.

### 4.5 Secondary (post-stack)
- `summer_program.py` (1182): schedule vs seed vs status already partly split—continue extraction only if parent/db splits land cleanly.
- `explanations.py` (974): dict-per-skill modules or generate from catalogs.
- `ui_dashboard.py` / `ui_arithmetic.py` / `arithmetic_render.py`: only if actively edited.

---

## 5. PR / implementation sequence

### PR0 — Guardrails (docs + smoke only)
- Add this plan under `docs/`.
- Optional: short note in `TECHNICAL.md` pointing at the package layout target (no mass rewrite of TECHNICAL yet).
- Capture baseline: `python -m unittest discover -s tests -q` (or project’s usual test command) and note failures that are pre-existing.

### PR1 — `app/db` package + facade (highest value)
0. Inventory exports (§3.0). Design/shared **config provider** so test overrides cannot hit real DB (Codex P1).
1. Move `db.py` → `db/` modules without changing SQL text or public function signatures (except intentional `set_db_config` helper if chosen).
2. `__init__.py` **explicit** re-exports full public API (`__all__`, no star imports).
3. Split migrations vs helpers vs indexes so no new logic file casually exceeds 400 LOC.
4. Verify import smoke + broad consumer tests:
   - `tests/test_db_parent_auth_and_progress.py`
   - `tests/test_db_assignment_semantics.py`
   - `tests/test_sync_store.py`, `tests/test_sync_service.py`
   - `tests/test_summer_program.py`, `tests/test_summer_program_templates.py`
   - `tests/test_school_year.py`, `tests/test_fall_readiness_audit.py`
   - `tests/test_content_audit.py`
   - `tests/test_mastery_truthfulness.py` (uses `db.db_config` override)
   - Script import smoke: at least one of `scripts/template_catalog.py` / `import_template_manifest.py` / `ingest_textbook.py` imports `app.db` successfully
5. Config override smoke: set temp config → `init_db` → write profile → confirm path is temp, not `data/app.db`.
6. No unrelated call-site churn; preserve dirty worktree files outside the PR.
7. Packaging: if facade is package-only, note whether `mandelquest.spec` needs `hiddenimports` for `app.db.*` (verify with import smoke first; full PyInstaller optional unless packaging is in scope).

**Done when:** no `app/db.py` file (only package); line counts per module mostly `<=300`; config override safe; listed tests green.

### PR2 — `quiz_engine` extract helpers + dispatch
1. Extract types/choices/helpers first.
2. Move skill bodies; keep `generate_question` behavior identical (including template short-circuit and `ContentUnavailableError`).
3. Verify generation spot-checks +:
   - `tests/test_pedagogical_integrity.py`
   - `tests/test_quiz_engine_*.py`
   - scope tests (`test_algebra_1_scope`, early math, etc.)

**Done when:** facade imports stable; no intentional content changes.

### PR3 — `ParentPanel` composition
1. Define a small typed **section context** (profile getter, quiz launcher, settings-changed callback, summer launcher, shared refresh hooks) before extracting tabs (Codex P3).
2. Extract one tab at a time starting with **Profiles/auth** and **Assignments** (high test coverage / high churn).
3. Keep `ParentPanel` public constructor signature stable for `ui_root.py`.
4. Manual smoke: open Parent tabs, set PIN, create quiz set, create assignment, summer refresh, school year packet list.

**Done when:** `ui_parent.py` shell `<=300` or clearly shrunken with remaining extract backlog listed; no UX change.

### PR4 — `QuizPanel` / existing quiz_* split
1. Prefer moving logic into **existing** `quiz_flow.py`, `quiz_history.py`, `quiz_strategies.py`.
2. Only add new `ui_quiz_*.py` files if existing modules would exceed size limits.
3. Verify:
   - `tests/test_mastery_truthfulness.py`
   - `tests/test_ui_quiz_subskill.py`
   - `tests/test_quiz_recovery.py`
   - summer mode UI flow tests if they drive QuizPanel

### PR5 — Optional cleanup
- `summer_program.py` further split
- Remove temporary star-exports if any
- Update `TECHNICAL.md` architecture section to match reality
- Only then consider `explanations.py` / dashboard

---

## 6. Risk register

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Circular imports in `db` package | High | One-way deps: connection → domain; no domain→domain cycles; shared mappers in `_rows` |
| Broken `from app import db` after package rename | High | Facade `__init__` + import smoke in each PR |
| Hidden relative imports / PyInstaller path assumptions | Medium | Run packaged smoke if packaging path imports `app.db`; check `mandelquest.spec` datas/hiddenimports only if needed |
| Behavioral drift in `generate_question` order | High | No logic edits while moving; keep template precedence block intact in `dispatch` |
| Tk widget parent/lifecycle bugs when splitting UI | High | One tab per PR; manual smoke; avoid changing bind/shortcut strings |
| Test isolation / shared `data/app.db` | Medium | Prefer temp dirs already used in mastery tests; don’t point unit tests at developer DB |
| Oversized pure DDL module still >300 | Low | Document exception: schema DDL is declarative data, not logic |
| Scope creep into sync/product features | Medium | Explicit non-goals; reject feature work in split PRs |

---

## 7. Verification plan (per PR)

1. **Static:** `python -m compileall app`
2. **Import smoke:**
   ```bash
   python -c "from app import db; from app.quiz_engine import generate_question, Question, SKILLS; from app.ui_parent import ParentPanel; from app.ui_quiz import QuizPanel; print('ok', len(SKILLS))"
   ```
3. **Focused tests** for the PR’s surface (listed above).
4. **Broader:** `python -m unittest discover -s tests -q` (pytest may be absent on this host; prefer unittest).
5. **Line-count gate:** report LOC for new/changed modules; flag any new file `>300` or heavily modified `>400` with rationale.
6. **No product behavior change:** same PIN rules, same generation for fixed seeds where tests pin seeds, same assignment completion semantics.
7. **Manual** (PR3/PR4): child dashboard → quiz → complete; parent PIN; worksheet list; summer tab open.

Do **not** require network. Do **not** change remotes or push without user confirmation.

---

## 8. Alignment with AGENTS.md / project policy

| Policy | How this plan complies |
| --- | --- |
| Modular first `<=300` LOC | Primary goal of the stack |
| Propose split plan before large edits | This document is that plan |
| Typesafety / type hints | Preserve existing annotations; no untyped rewrites |
| Offline-first / local data | No storage location changes |
| Skill UX intuition standard | No explanation content removal; `explanations.py` deferred |
| Second-agent review Tier B | Multi-file refactor → request Codex (and optional AGY) review of plan before implement |
| No remote/push without confirm | Implementation PRs stay local until user asks |
| Continuity | After implementation starts, update `CONTINUITY.md` / project continuity with PR status |

---

## 9. Explicit “do not do” list during implementation

- Do not “fix” SQL, PIN iterations, or mastery thresholds while moving code.
- Do not rename public functions in the same PR as the move (rename later if desired).
- Do not merge UI redesign with structural split.
- Do not expand sync MVP in these PRs.
- Do not delete Fortran/fractal code paths.
- Do not rewrite template manifests or reseed production DBs.

---

## 10. Success criteria

1. God-file targets reduced: `db` as package of small modules; `quiz_engine` facade + submodules; `ParentPanel`/`QuizPanel` shells under control.
2. Zero intentional user-facing behavior change.
3. Full unit test suite green on the implementation host.
4. Import paths used by `app/`, `tests/`, and `scripts/` remain valid.
5. Future feature work (Texas packets, summer, sync) has an obvious home module.

---

## 11. Completed first implementation slice

**PR1 complete:** `app/db.py` → `app/db/` package with full re-export facade and DB-focused tests. Stop and reassess LOC/test health before PR2.

---

## 12. Open questions (residual after Codex)

1. Prefer migrating tests to `set_db_config(...)` vs preserving assignable `db.db_config` via a package-level descriptor? (Recommendation: explicit `set_db_config` + update tests in the same PR1—clearer and typesafe.)
2. Prefer real package `app/db/` (recommended) vs keep `db.py` as a shim forever for monkeypatch familiarity?
3. Should PR1 include full PyInstaller smoke, or import smoke only until a packaging-focused PR?
4. Should `SKILLS` stay owned by `quiz_engine`, or move to `skill_graph` in a later non-mechanical cleanup? (Out of scope for split stack.)
5. Should `schema.py` be allowed a documented ~300 LOC exception for pure DDL? (Yes, if needed.)

---

## 13. Review receipt

| Item | Path |
| --- | --- |
| Plan (md) | `docs/god-file-split-plan-2026-07-08.md` |
| Plan (html) | `docs/god-file-split-plan-2026-07-08.html` |
| Codex review | `reviews/codex/god-file-split-plan-review-2026-07-08.md` |
| Codex latest pointer | `reviews/codex/latest.md` |
| Codex model | `gpt-5.5` via `codex -a never exec --sandbox read-only` |
| Verdict | **approve-with-changes** (P1: config override + export inventory before PR1) |
