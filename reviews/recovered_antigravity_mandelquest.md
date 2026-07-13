# Recovered Antigravity MandelQuest Note

This note preserves the latest MandelQuest planning artifacts recovered from
Antigravity after the workspace sidebar stopped showing the related chat.

Recovered on: 2026-03-20

Source artifacts:
- `/home/user/.gemini/antigravity/brain/3296cd7a-8850-4932-a3e5-e2fbd3153dbb/task.md`
- `/home/user/.gemini/antigravity/brain/3296cd7a-8850-4932-a3e5-e2fbd3153dbb/implementation_plan.md`

Related older review artifacts already mirrored in this repo:
- `reviews/code_review.md`
- `reviews/todo.md`

Why this file exists:
- The recovered MandelQuest artifacts still exist on disk.
- Antigravity's local saved-chat index no longer contains the corresponding
  sidebar/chat entry, so the `mandelbrot_fortran` workspace shows `No chats yet`.
- This note keeps the latest recoverable planning content inside the repo.

## Recovered task checklist

### Review Phase
- [x] Explore codebase: skills, topics, templates, Khan links, intuitions
- [x] Map implemented topics against K-9th Grade Geometry curriculum
- [x] Assess exercise variety per topic
- [x] Assess Khan Academy link coverage
- [x] Assess built-in intuition content quality
- [x] Test core features: profiles, quizzes, parent tools, worksheets, dashboard
- [x] Find bugs and functional gaps

### Delivery Plan Phase
- [x] Compile findings into a gap analysis
- [x] Create prioritized execution plan for Monday delivery
- [ ] Get user approval on plan

### Execution (Pending Approval)
- [ ] Fix test infrastructure (G1)
- [ ] Add Place Value skill (G2)
- [ ] Add Measurement skill (G3)
- [ ] Add grade-level filter (G6)
- [ ] Add K-9 scope toggle (G7)
- [ ] Add Khan entries for new skills
- [ ] Verify all changes

## Recovered implementation plan

### Executive summary

MandelQuest was assessed as much more complete than the TODO implied for a
K-9 Geometry handoff. The recovered plan says the app already has broad
curriculum coverage, enriched intuition content, Khan links, profiles, quizzes,
worksheets, and parent tools. The main blockers identified were:
- missing standalone `place_value`
- missing standalone `measurement`
- broken test discovery
- lack of grade-level navigation and K-9 scoping polish

Target deadline in the recovered plan:
- Monday, 2026-03-23

### Current state the recovered plan says already works

Covered skills and tracks:
- Counting
- Add/Subtract
- Multiply
- Divide
- Fractions
- Long Addition
- Long Subtraction
- Long Multiplication
- Long Division
- Money
- Ratios
- Integers
- Order of Operations
- Percent
- Mean
- Probability
- Pre-Algebra
- Linear Equations
- Algebra 1
- Geometry

Recovered note on geometry scope:
- Geometry was described as having 12 working subskills and being the main
  9th-grade target scope.

Recovered geometry subskills:
1. Area of rectangles and squares
2. Area of triangles and parallelograms
3. Area of trapezoids and composite figures
4. Perimeter and missing sides
5. Circumference and area of circles
6. Surface area and volume
7. Pythagorean theorem
8. Coordinate geometry distance and midpoint
9. Angles in lines and triangles
10. Transformations and congruence
11. Similarity and scale factor
12. Analytic geometry and coordinate proofs

Recovered feature summary:
- multiple choice and typed answers
- three exercise modes: intuition, expression, word problems
- adaptive mode blending by mastery stage
- word-problem gap boost
- template-based exercises and story-wrapper exercises
- Khan unit links across the skill registry
- enriched explanations with `mental_model`, `common_mistake`, and `try_this`
- profile picker and parent PIN gate
- quiz engine, dashboard, skill map, worksheets, assignments
- keyboard shortcuts
- offline-first local SQLite storage

### Gaps found in the recovered plan

#### P0

G1: Test suite infrastructure bug
- `pytest` and `unittest discover` were reported as producing empty output.
- Tests were said to exist but not collect.
- Suspected causes were missing `tests/__init__.py` or import path issues.

G2: Missing curriculum topic: Place Value
- No standalone place-value skill.
- It was described as partially implied by other arithmetic work but not
  directly quizzable.

G3: Missing curriculum topic: Measurement
- The recovered plan explicitly called out missing measurement support:
  length, area, volume, time, temperature, and unit conversion.

#### P1

G4: Pre-Algebra is thin
- Only three subskills were considered present.
- Missing areas included expressions, equations/inequalities, coordinate
  basics, exponents/roots/scientific notation, and function tables.

G5: Geometry skill mislabeled as `geometry_area`
- The internal id was flagged as too narrow for the actual geometry scope.
- The plan recommended deferring a rename because of data compatibility risk.

G6: No grade-level navigation for homeschool use
- Skills were grouped by track, not by grade.
- The plan said `curriculum_index.json` already had `grade_band` data but the
  UI did not expose it.

G7: Advanced tracks exceed K-9 scope
- Algebra 2, Trig, Calculus, and Test Prep were considered out of scope for
  the immediate homeschool-mom handoff.

#### P2

G8: No visual geometry diagrams in quizzes
- Geometry questions were described as text-only.

G9: Khan URLs are generic
- Most links were said to point to unit pages rather than direct exercises.

G10: Template coverage is thinner for upper skills
- Pre-Algebra and higher skills were described as relying more on hardcoded
  generators than on template banks.

### Proposed Monday delivery plan from the recovered artifact

Component 1: Fix test infrastructure
- Repair collection in `tests/`
- Verify tests collect and run under `python -m pytest tests/ -v`

Component 2: Add `place_value`
- Update `app/quiz_engine.py`
- Update `app/skill_graph.py`
- Update `app/explanations.py`
- Update `data/curriculum_index.json`

Planned `place_value` subskills:
- ones/tens/hundreds identification
- expanded form
- compare numbers by place value

Component 3: Add `measurement`
- Update `app/quiz_engine.py`
- Update `app/skill_graph.py`
- Update `app/explanations.py`
- Update `data/curriculum_index.json`

Planned `measurement` subskills:
- length unit conversion
- time reading and arithmetic
- temperature basics

Component 4: Add grade-level filter
- Target file: `app/ui_skill_map.py`
- Use `grade_band` from `curriculum_index.json`

Component 5: Add K-9 scope boundary toggle
- Target file: `app/ui_skill_map.py` or `app/ui_quiz.py`
- Hide Algebra 2, Trig, Calculus, and Test Prep by default

Component 6: Add Khan registry entries for new skills
- Target file: `data/khan_subskill_registry.json`

Deferred after Monday:
- expand Pre-Algebra depth
- rename `geometry_area`
- add visual geometry diagrams
- add more direct Khan assignable URLs
- expand template-bank coverage for upper skills

### Verification plan from the recovered artifact

Automated verification:
- fix test discovery first
- run `python -m pytest tests/ -v --tb=short`
- add tests for the new `place_value` and `measurement` skills
- verify explanation coverage and Khan links for those skills

Manual verification:
- launch `python explorer.py`
- create test student and parent profiles
- verify quiz generation and scoring
- verify geometry subskill generation
- verify the new skills appear in the UI once implemented

## Recovery note

This file is a repo-local preservation of the latest recovered MandelQuest plan.
It is not proof that the original Antigravity sidebar chat can be restored.
The recovered evidence supports that the content survived as artifact files but
was lost from Antigravity's saved chat/sidebar registration state.
