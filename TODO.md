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

## Roadmap: Daily Review (Spaced Practice)
- [x] Show a “Daily review” target on the Dashboard.
- [x] One-click start daily review quiz.
- [ ] Tune spaced review thresholds and selection logic.
- [ ] Add “daily goal” history (track completion streak per day).

## Roadmap: Template Bank QA
- [ ] Template dry-run tool (generate N variants per template; report failures).
- [ ] External IDs for templates everywhere (manifest + UI tooling).
- [ ] Subskill-targeted quiz presets for parent assignments.
