# TODO

## Immediate Next: Fall School Year Texas Alignment

### P0 - Standards-aligned planning spine
- [x] Add a Texas Grade Goals catalog for grades 1-7 with TEKS references, focal areas, quiz-ready mappings, stretch goals, and honest content-gap rows.
- [x] Add a parent-facing `School Year` tab to browse Texas grade goals and seed grade-level quiz sets.
- [x] Add per-child default grade/target path settings instead of relying only on the global grade-band setting.
- [x] Add a school-year dashboard card that shows the child's current Texas grade goal, next quiz-ready goal, and stretch path.
- [x] Add grade-goal parent assignment seeding with subskill-mastery targets.
- [x] Convert grade goals into parent-generated tests/assessment packets with subskill specificity.
- [x] Add a formal fall-readiness audit tying Texas goals, two-child targets, kid-first navigation, assessments, intuition, blended practice, graph tuning, and stretch paths together.

### P1 - Texas content gaps to fill next
- [x] Add Grade 1 shape composition/attribute lessons, questions, and intuition packs.
- [x] Add elementary data-display lessons/questions for picture graphs, bar graphs, and dot plots.
- [x] Add Grade 2-5 measurement/data coverage checks against the Texas Grade Goals catalog.
- [x] Add Grade 6-7 measurement/data/probability coverage checks against the Texas Grade Goals catalog.
- [x] Add Grade 1-7 personal financial literacy goals, native questions, intuition, and parent-controlled Khan links.
- [x] Add exact Grade 6-7 data-analysis depth for histograms, box plots, center/spread/shape, median/IQR, variability, comparative displays, sample inference, and part-to-whole comparisons.
- [x] Audit any remaining Grade 1-7 Texas coverage gaps after the exact data-analysis and financial-literacy slices.
- [x] Start the child-first UI pass with math-first tabs, hidden child Parent tab, and Mandelbrot under Bonus Explore after practice.
- [x] Continue the child-first UI pass by simplifying quiz/test launch choices for kids while keeping parent assessment controls complete.
- [x] Add kid-facing quiz-completion screens with what-happened and next-step copy while keeping parent mastery retake controls.
- [x] Add a child-only dashboard next-step card with practice/assignment launch, Texas goal progress, and Bonus Explore lock/unlock status.
- [x] Add child dashboard intuition copy for the next Texas goal with a concrete next subskill to practice.
- [x] Add child quiz question intuition previews so practice starts with a mental model before the child asks for help.
- [x] Add direct child dashboard launch for the next saved Texas goal practice.
- [x] Add child-facing Texas goal step clarity by showing partial goal progress and launching the first unfinished subskill.
- [x] Add child-specific next-goal review assignments from a saved Texas grade target.
- [x] Add parent-facing test/quiz-builder polish for selecting individual Texas goals and browsing saved assessment packets.
- [x] Add a parent-friendly saved-packet management pass that archives old Texas packets without deleting generated files.
- [x] Add printable grade-level assessment packets generated from Texas Grade Goals.
- [x] Keep all external links parent-controlled through the existing external-links/offline settings.

## Immediate Next: Summer Content Audit and Resource Review

### P0 - Build the audit spine
- [x] Add `app/content_audit.py` to summarize Summer Program coverage by lane, unit, and subskill.
- [x] Include active template count, word-template count, scaffold count, intuition/help content status, Khan Academy URL, open-resource URL, and readiness label.
- [x] Use readiness labels: `ready`, `thin`, `missing`.
- [x] Add a parent-facing `Resource Review` section in Parent tools, preferably adjacent to the Summer Program controls.
- [x] Highlight weakest core and preview units first instead of rendering the audit as an undifferentiated table.
- [x] Add tests for `prealgebra_finish`, `foundation_bridge`, and optional preview-unit audit output.

### P1 - Map algebra/geometry resources
- [x] Add Khan mappings for slope tables, linear relationships, functions, sequences, triangle/area, circles, Pythagorean theorem, coordinate geometry distance/midpoint, transformations, and similarity.
- [x] Add open-resource links where stable, parent-appropriate resources exist.
- [x] Add content integrity tests that fail if optional preview units have no active questions or no mapped help resource.

### P2 - Expand preview content from the audit
- [x] Use Resource Review output to drive template manifests for `linear_relationships_preview`.
- [x] Use Resource Review output to drive template manifests for `functions_patterns_preview`.
- [x] Use Resource Review output to drive template manifests for `geometry_measurement_preview`.
- [x] Use Resource Review output to drive template manifests for `coordinate_geometry_preview`.
- [x] Use Resource Review output to drive the optional `algebra_1_preview_capstone` mixed-readiness unit.
- [x] Use Resource Review output to drive the optional `geometry_preview_capstone` mixed-readiness unit.
- [x] Expand scaffolded question families beyond the current starter set for slope, functions, sequences, area, coordinate midpoint, and similarity.
- [x] Add a parent export/print action for the Resource Review summary after the audit is stable.

## Status: Summer Program Preview Units
- [x] Append optional algebra/geometry preview units after the official `prealgebra_finish` exit path.
- [x] Keep optional preview units out of official completion, pace, catch-up, and blocked-state rules.
- [x] Route preview units to algebra/geometry generators and scaffolded lesson/checkpoint items.
- [x] Label post-core preview work as `Bonus preview` in the child dashboard.
- [x] Add Resource Review coverage UI for core and preview units.

## Roadmap: Family Sync Beta (Operator-Configured Client + Future Hosted Service)

Goal: let a family opt into shared profiles and progress across devices without making accounts, cloud access, or internet connectivity required for core use.

Current boundary: the client is an explicitly labeled beta behind a machine-local server config and parent opt-in. Public v1 builds provide no hosted server, so local-only remains the normal supported path.

### P0 — Sync Boundary and Safety
- [x] Keep local-only mode as the default; the app must stay fully usable with no account and no network.
- [x] Add a parent-controlled “Enable family sync” flow in Parent tools with plain-language privacy copy and a manual `Sync now` action.
- [x] Define MVP sync scope: parent/child profiles, quiz sets, assignments, completed quiz attempts, and question history.
- [x] Define MVP local-only scope: parent PIN, offline-mode toggle, UI preferences, local PDFs, worksheet files, and other machine-specific paths/settings.
- [x] Treat completed quiz attempts/question rows as the canonical synced ledger; rebuild derived progress tables from synced history instead of merging rollups directly.
- [x] Keep in-progress quiz resume state local-only in the first sync release to avoid cross-device resume/conflict bugs.

### P1 — Local DB and Client Sync Foundation
- [x] Add stable UUIDs, `updated_at`, and soft-delete/tombstone metadata to synced tables (`profiles`, `quiz_sets`, `assignments`, `quiz_attempts`, `quiz_questions`).
- [x] Add local device identity and sync state storage (`device_id`, `family_id`, `last_sync_at`, `last_error`, `sync_enabled`).
- [x] Add a sync outbox/change-log table so every local mutation can be queued, retried, and replayed safely.
- [x] Route synced writes through one sync-aware service layer instead of letting UI code write synced tables ad hoc.
- [x] Add migrations and regression tests so existing `app.db` files upgrade cleanly before sync is enabled.

### P2 — Central Server MVP
- [ ] Stand up a small Python API service for family accounts, device registration, pairing, push/pull sync, and auth tokens.
- [ ] Use a real multi-user server database (recommended: PostgreSQL) with per-family isolation and auditable timestamps.
- [ ] Require TLS and hashed server-side credentials; do not reuse or upload the local parent PIN hash as the server credential.
- [ ] Support bootstrap from one trusted device, then link additional devices with a short-lived pairing code.
- [ ] Add idempotent upsert endpoints plus incremental pull-by-cursor endpoints so retries do not duplicate data.

### P3 — Merge Rules and Data Integrity
- [ ] Use latest-write-wins for profile names and quiz-set metadata.
- [ ] Use append-only merge semantics for completed quiz attempts and question history.
- [ ] Make assignment completion monotonic: once completed, it stays completed unless a parent explicitly reopens it.
- [ ] Recompute mastery, streaks, recommendations, and daily-goal rollups after sync instead of trying to three-way-merge derived tables.
- [ ] Define delete semantics for synced entities and cover them with tombstone tests.

### P4 — Parent UX and Operations
- [x] Add a parent-only Sync settings panel with status, last sync time, last error, device identity, and `Sync now`.
- [x] Keep first-run wording explicit that sync is beta/optional and local-only use remains supported.
- [ ] Add pause, disconnect, export, and backup actions so a family can stop syncing without losing local access.
- [x] Surface server/offline errors as non-blocking warnings; quizzes, worksheets, and profile selection must continue working when sync fails.

### P5 — Testing, Privacy, and Rollout
- [ ] Add two-device integration tests: create a child on device A -> sync -> take a quiz on device B -> sync -> review on device A.
- [ ] Add conflict tests for simultaneous profile edits, assignment edits, duplicate retries, and delete/recreate cases.
- [x] Add migration tests from pre-sync `app.db` snapshots with sync disabled and then enabled later.
- [x] Update README, privacy page, and support docs to explain exactly what sync sends and what stays local.
- [x] Ship behind an operator-supplied config gate and explicit beta toggle before exposing it as a normal parent setting.

## High-Priority v1.0 Ship Backlog (Offline Homeschool MVP)

### P0 — Must Complete Before Release
- [x] Fix SQLite resource warnings and connection lifecycle in `app/db.py` (no unclosed-handle warnings in test runs).
- [x] Add Parent PIN gate and lockout for Parent tab access (`ui_root.py`, `ui_parent.py`, `db.py`).
- [x] Add persistent quiz resume state (`quiz_attempt_progress`) so in-progress sessions survive app restarts.
- [x] Guarantee offline-first behavior for all core learning flows (no required internet).

### P1 — Required for Product Quality
- [x] Complete Pre-Algebra scope in roadmap with tests.
- [x] Complete Algebra 1 core scope in roadmap with tests.
- [x] Add graceful fallback when optional binaries (`pdftotext`, ImageMagick) are missing.
- [x] Add keyboard-first navigation pass for Profile, Quiz, Parent, Dashboard core flows.
- [x] Add readability/accessibility settings baseline in UI settings.

### P2 — Distribution and Launch Hardening
- [x] Harden packaging/release workflows for compatibility-first artifacts.
- [x] Validate packaged app smoke tests on Windows 10+, macOS 11+, Ubuntu LTS baseline.
- [x] Update `README.md` with offline setup, parent controls, backup/recovery, and troubleshooting.
- [x] Publish v1.0 release checklist and known limitations.

## Status (Implemented)
- Skill tracks + prerequisite-based recommendations.
- Student dashboard with progress bars + mastery labels.
- Subskill mastery via consecutive-correct streaks (with a simple badge/streak UI).
- Curriculum PDF linking per skill (local PDFs).
- Parameterized question template bank (SQLite) with constraints + safe eval.
- PDF ingestion helper (`pdftotext`) to extract exercise candidates.
- Story-problem wrappers sourced from curriculum PDFs (word mode, arithmetic/pre-algebra).

## Roadmap: Foundations to Pre-Algebra
- [x] Number sense: counting (in-app); place value (next).
- [x] Addition/subtraction practice (in-app); strategies (next).
- [x] Multiplication/division (in-app); long division (in-app).
- [x] Fractions (in-app).
- [x] Decimals + money (money mode in-app).
- [x] Measurement: length, area, volume, time, temperature, unit conversion.
- [x] Geometry basics: area of shapes (in-app); symmetry/angles (next).
- [x] Data & graphs: mean + basic probability + percent (in-app); graphs (next).
- [x] Ratios & percents (in-app).
- [x] Integers & coordinates: integers (in-app); coordinate plane (next).
- [x] Order of operations + simple variables: order of ops + linear equations (in-app); variables intro (next).

## Roadmap: Pre-Algebra -> High School Calculus + Statistics
### Pre-Algebra
- [x] Expressions, variables, integer operations, and order of operations.
- [x] One- and two-step equations/inequalities; coordinate plane.
- [x] Proportional relationships, ratios, rates, percent problems.
- [x] Exponents, roots, scientific notation, and basic function tables.

### Algebra 1
- [x] Linear equations/inequalities; slope and y=mx+b intuition.
  - [x] Slope from points native questions, intuition, and parent-controlled Khan lesson link.
  - [x] Slope-intercept form native questions, intuition, and parent-controlled Khan lesson link.
  - [x] Graphing linear inequalities native questions, intuition, and parent-controlled Khan lesson link.
- [x] Summer preview layer: deepen slope, linear relationships, functions, and sequence content after the Resource Review audit.
  - [x] Add optional Algebra 1 mixed-readiness capstone with slope, functions, sequences, graphing inequalities, and solving equations.
- [x] Systems of equations (graphing + substitution/elimination).
  - [x] Systems by substitution native questions, intuition, and parent-controlled Khan lesson link.
  - [x] Systems by elimination native questions, intuition, and parent-controlled Khan lesson link.
  - [x] Graphing systems/intersection intuition with native questions and parent-controlled Khan lesson link.
- [x] Polynomials: add/subtract/multiply; factoring basics.
  - [x] Polynomial arithmetic native questions, intuition, and parent-controlled Khan lesson link.
  - [x] Factoring basics native questions, intuition, and parent-controlled Khan lesson link.
  - [x] Binomial multiplying cross-product intuition and parent-controlled Khan unit link.
- [x] Quadratics: factoring, completing the square, quadratic formula.
  - [x] Quadratic factoring by grouping native questions, intuition, and parent-controlled Khan lesson link.
  - [x] Difference-of-squares native questions, intuition, and parent-controlled Khan lesson link.
  - [x] Quadratic formula native questions, intuition, and parent-controlled Khan lesson link.
  - [x] Completing-the-square native questions, intuition, and parent-controlled Khan lesson link.
- [x] Function transformations: shifted parent-function evaluation with child-facing intuition.
- [x] Radicals and rational exponents beyond square-root basics.

### Geometry
- [x] Proofs: congruence/similarity, triangle criteria, angle theorems.
- [x] Polygons, circles, area/volume, coordinate geometry.
- [x] Summer preview layer: deepen circles, Pythagorean theorem, coordinate geometry, transformations, and similarity after the Resource Review audit.
  - [x] Add optional Geometry mixed-readiness capstone with circles, Pythagorean theorem, coordinate geometry, transformations, and similarity.
- [x] Right-triangle trigonometry and basic trig ratios.

### Algebra 2
- [x] Functions: domain/range, inverse, composition.
- [x] Exponentials/logarithms and growth/decay models.
- [x] Rational expressions, complex numbers, sequences/series.

### Precalculus / Trig
- [x] Unit circle, trig functions/graphs, identities, inverse trig.
- [x] Vectors, matrices (intro), polar coordinates.

### Calculus
- [x] Limits and continuity.
- [x] Derivatives: rules + geometric meaning (slope/velocity).
- [x] Integrals: area/accumulation + basic techniques.
- [x] Applications: optimization, motion, area between curves.

### Statistics & Probability
- [x] Data collection, distributions, center/spread, standard deviation.
- [x] Probability rules, combinatorics, expected value.
- [x] Sampling, confidence intervals, hypothesis tests.
- [x] Correlation/regression; interpreting results.

## Roadmap: Student Dashboard (Progress + Recommendations)
- [x] Define mastery model per skill (attempts, accuracy, streaks, time, recent trend).
- [x] Choose visual design (progress bars + tiles).
- [x] Build progress data pipeline (quiz attempts + worksheet completions).
- [x] Add per-skill mastery levels (Needs work/Developing/Proficient/Mastered).
- [x] Recommendation engine: prerequisites + mastery gaps (basic).
- [x] Student profile view: strengths/weak spots + next practice suggestion (basic).

## Roadmap: Prerequisite Logic (Soft Graph)
- [x] Convert prerequisite graph to soft edges with weights (`required_for_readiness` vs `helpful_background`).
- [x] Keep all skills unlocked; recommendations are score-based only (no hard locks).
- [x] Add recommendation scoring using prereq mastery + subskill coverage + recent performance.
- [x] Add monthly graph tuning workflow from real learner performance data.

## Roadmap: Blended Practice (Prereq Spacing)
- [x] Add blended quiz composition policy:
  current target + weak prerequisites + spaced-review maintenance.
- [x] Start with configurable defaults (`60/25/15`) and tune by outcome.
- [x] Adaptive ratio tuning:
  increase prereq share when target accuracy is low; taper when stable.
- [x] Enforce a maintenance floor so mastered prerequisites still reappear periodically.

## Roadmap: Free Mode (Guided Random)
- [x] Add "Free Mode" quiz path in UI (alongside focused skill mode).
- [x] Guided-random sampling across:
  current level, next-level preview, weak prerequisites, and maintenance review.
- [x] Add per-question labels (`Core`, `Preview`, `Prereq`, `Review`) for learner clarity.
- [x] Connect Free Mode outcomes back into mastery and recommendation scoring.

## Roadmap: Exercise Modes (Intuition vs Expression vs Word)
- [x] Add template `mode` taxonomy for each exercise:
  `intuition`, `expression`, `word`.
- [x] Keep subskill tags consistent across all modes so mastery is shared.
- [x] Add stage-based default mix:
  early (`45/40/15`), developing (`30/45/25`), near-mastery (`20/40/40`).
- [x] Add mode-balancing logic:
  if word-problem accuracy lags expression accuracy, increase `word` share.
- [x] Add parent controls to override mode mix per assignment or quiz set.

## Roadmap: Daily Review (Spaced Practice)
- [x] Show a “Daily review” target on the Dashboard.
- [x] One-click start daily review quiz.
- [x] Tune spaced review thresholds and selection logic.
- [x] Add “daily goal” history (track completion streak per day).

## Roadmap: Template Bank QA
- [x] Template dry-run tool (generate N variants per template; report failures).
- [x] Optional Fortran verifier mode for arithmetic/algebra templates (Python cross-check).
- [x] External IDs for templates everywhere (manifest + UI tooling).
- [x] Subskill-targeted quiz presets for parent assignments.

## Roadmap: Historical SAT/GRE Archive
- [x] Historical test/question ingestion into local DB.
- [x] Dedicated answer-key ingestion pipeline.
- [x] Coverage report script for SAT/GRE by year (1980s->current) with missing-year gaps.
- [ ] Expand SAT/GRE corpus to include 1980s/1990s year-by-year coverage.

## Roadmap: Parent Assignments
- [x] Add assignment model/table (skill/subskill target + quiz preset fields).
- [x] Parent UI to create, list, and complete assignments.
- [x] Student dashboard card for next active assignment + one-click start.
- [x] Auto-complete assignments after quiz attempts (score or subskill mastery targets).
- [x] Add assignment history filters and richer completion analytics.

## Roadmap: Code Review Backlog (from `reviews/todo.md`)
- [x] F10 — Fractal UI palette selector (`rgb/gray/sunset/ice/fire`) with live re-render.
- [x] F11 — Julia parameter sliders (`julia_cx`, `julia_cy`) with live re-render.
- [x] M1 — Refactor `render_arithmetic()` into dispatch-table based skill renderers.
- [x] M3 — Replace minimal algebra view with balance-scale step visualization.
- [x] M11 — Fix long-multiplication partial alignment/place-value shifting.
- [x] M12 — Add full long-division work-step rendering.
- [x] M14 — Split `ui_quiz.py` into focused modules (`quiz_flow`, `quiz_history`, `quiz_strategies`).
- [x] M15 — Extract strategy-specific question builders from `start_quiz()`.
- [x] U1 — Apply modern Ttk theme baseline and style overrides.
- [x] U5 — Centralize UI color/font constants in `app/theme.py`.
- [x] U13 — Move Khan reachability check off main UI thread.
- [x] U14 — Group quiz controls into labeled sections.
- [x] U15 — Add visual answer feedback (correct/incorrect animation cues).
