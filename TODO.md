# TODO

- Add optional server sync so profiles, quizzes, and progress can persist across devices.
- Build story-problem “wrappers” on top of the template bank (word problems).

## Status (Implemented)
- Skill tracks + prerequisite-based recommendations.
- Student dashboard with progress bars + mastery labels.
- Subskill mastery via consecutive-correct streaks (with a simple badge/streak UI).
- Curriculum PDF linking per skill (local PDFs).
- Parameterized question template bank (SQLite) with constraints + safe eval.
- PDF ingestion helper (`pdftotext`) to extract exercise candidates.

## Roadmap: Foundations to Pre-Algebra
- [x] Number sense: counting (in-app); place value (next).
- [x] Addition/subtraction practice (in-app); strategies (next).
- [x] Multiplication/division (in-app); long division (in-app).
- [x] Fractions (in-app).
- [x] Decimals + money (money mode in-app).
- [ ] Measurement: length, area, volume, time, temperature, unit conversion.
- [x] Geometry basics: area of shapes (in-app); symmetry/angles (next).
- [x] Data & graphs: mean + basic probability + percent (in-app); graphs (next).
- [x] Ratios & percents (in-app).
- [x] Integers & coordinates: integers (in-app); coordinate plane (next).
- [x] Order of operations + simple variables: order of ops + linear equations (in-app); variables intro (next).

## Roadmap: Pre-Algebra -> High School Calculus + Statistics
### Pre-Algebra
- [ ] Expressions, variables, integer operations, and order of operations.
- [ ] One- and two-step equations/inequalities; coordinate plane.
- [ ] Proportional relationships, ratios, rates, percent problems.
- [ ] Exponents, roots, scientific notation, and basic function tables.

### Algebra 1
- [ ] Linear equations/inequalities; slope and y=mx+b intuition.
- [ ] Systems of equations (graphing + substitution/elimination).
- [ ] Polynomials: add/subtract/multiply; factoring basics.
- [ ] Quadratics: factoring, completing the square, quadratic formula.
- [ ] Radicals, rational exponents, and basic function transformations.

### Geometry
- [ ] Proofs: congruence/similarity, triangle criteria, angle theorems.
- [ ] Polygons, circles, area/volume, coordinate geometry.
- [ ] Right-triangle trigonometry and basic trig ratios.

### Algebra 2
- [ ] Functions: domain/range, inverse, composition.
- [ ] Exponentials/logarithms and growth/decay models.
- [ ] Rational expressions, complex numbers, sequences/series.

### Precalculus / Trig
- [ ] Unit circle, trig functions/graphs, identities, inverse trig.
- [ ] Vectors, matrices (intro), polar coordinates.

### Calculus
- [ ] Limits and continuity.
- [ ] Derivatives: rules + geometric meaning (slope/velocity).
- [ ] Integrals: area/accumulation + basic techniques.
- [ ] Applications: optimization, motion, area between curves.

### Statistics & Probability
- [ ] Data collection, distributions, center/spread, standard deviation.
- [ ] Probability rules, combinatorics, expected value.
- [ ] Sampling, confidence intervals, hypothesis tests.
- [ ] Correlation/regression; interpreting results.

## Roadmap: Student Dashboard (Progress + Recommendations)
- [ ] Define mastery model per skill (attempts, accuracy, streaks, time, recent trend).
- [x] Choose visual design (progress bars + tiles).
- [ ] Build progress data pipeline (quiz attempts + worksheet completions).
- [x] Add per-skill mastery levels (Needs work/Developing/Proficient/Mastered).
- [x] Recommendation engine: prerequisites + mastery gaps (basic).
- [x] Student profile view: strengths/weak spots + next practice suggestion (basic).

## Roadmap: Prerequisite Logic (Soft Graph)
- [ ] Convert prerequisite graph to soft edges with weights (`required_for_readiness` vs `helpful_background`).
- [ ] Keep all skills unlocked; recommendations are score-based only (no hard locks).
- [ ] Add recommendation scoring using prereq mastery + subskill coverage + recent performance.
- [ ] Add monthly graph tuning workflow from real learner performance data.

## Roadmap: Blended Practice (Prereq Spacing)
- [ ] Add blended quiz composition policy:
  current target + weak prerequisites + spaced-review maintenance.
- [ ] Start with configurable defaults (`60/25/15`) and tune by outcome.
- [ ] Adaptive ratio tuning:
  increase prereq share when target accuracy is low; taper when stable.
- [ ] Enforce a maintenance floor so mastered prerequisites still reappear periodically.

## Roadmap: Free Mode (Guided Random)
- [ ] Add "Free Mode" quiz path in UI (alongside focused skill mode).
- [ ] Guided-random sampling across:
  current level, next-level preview, weak prerequisites, and maintenance review.
- [ ] Add per-question labels (`Core`, `Preview`, `Prereq`, `Review`) for learner clarity.
- [ ] Connect Free Mode outcomes back into mastery and recommendation scoring.

## Roadmap: Exercise Modes (Intuition vs Expression vs Word)
- [ ] Add template `mode` taxonomy for each exercise:
  `intuition`, `expression`, `word`.
- [ ] Keep subskill tags consistent across all modes so mastery is shared.
- [ ] Add stage-based default mix:
  early (`45/40/15`), developing (`30/45/25`), near-mastery (`20/40/40`).
- [ ] Add mode-balancing logic:
  if word-problem accuracy lags expression accuracy, increase `word` share.
- [ ] Add parent controls to override mode mix per assignment or quiz set.

## Roadmap: Daily Review (Spaced Practice)
- [x] Show a “Daily review” target on the Dashboard.
- [x] One-click start daily review quiz.
- [ ] Tune spaced review thresholds and selection logic.
- [ ] Add “daily goal” history (track completion streak per day).

## Roadmap: Template Bank QA
- [x] Template dry-run tool (generate N variants per template; report failures).
- [ ] External IDs for templates everywhere (manifest + UI tooling).
- [x] Subskill-targeted quiz presets for parent assignments.

## Roadmap: Parent Assignments
- [x] Add assignment model/table (skill/subskill target + quiz preset fields).
- [x] Parent UI to create, list, and complete assignments.
- [x] Student dashboard card for next active assignment + one-click start.
- [x] Auto-complete assignments after quiz attempts (score or subskill mastery targets).
- [ ] Add assignment history filters and richer completion analytics.
