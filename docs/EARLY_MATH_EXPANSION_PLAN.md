# Early Math Expansion Plan

## Goal

Make MandelQuest course-complete for arithmetic through pre-algebra by:

- backing every exposed subskill with reusable Khan-grounded problem families
- upgrading intuition content from broad skill-level blurbs to subskill-level teaching assets
- mapping external lesson links at the subskill level, still controlled by the parent external-links setting
- keeping current learner history and skill IDs stable unless a split is clearly worth the migration cost

## Baseline

- Exposed early-math subskills in the current app: 60
- Early-math subskills with active templates today: 15
- Active early-math templates today: 75
- Active early-math intuition templates today: 0

The current gaps are concentrated in:

- counting
- place value
- multiplication and division
- long arithmetic algorithms
- money and measurement
- subskill-specific intuition
- subskill-specific Khan links

## Completion Criteria

The expansion is complete only when all of the following are true:

1. Every arithmetic and pre-algebra subskill exposed in the UI has at least one Khan mapping.
2. Every exposed subskill has a subskill-level intuition pack:
   - Mental model
   - Common mistake
   - Try this
3. Every exposed subskill has active expression coverage.
4. Every word-friendly subskill has active word coverage.
5. Every intuition-friendly subskill has active intuition coverage.
6. The arithmetic panel and quiz flow can open the mapped Khan lesson or exercise for the selected subskill when external links are enabled.
7. Tests fail if a new exposed subskill is missing coverage.

## Scope Freeze

Keep the current early skill IDs for now:

- counting
- place_value
- add_subtract
- multiply
- divide
- ratios
- fractions
- long_addition
- long_subtraction
- long_multiplication
- long_division
- money
- measurement
- integers
- order_of_operations
- pre_algebra

Do not introduce new top-level IDs in the first wave unless one of these becomes unmaintainable:

- `measurement`
- `pre_algebra`
- `add_subtract`

The safer first move is to expand subskills and template coverage under the existing IDs.

## Curriculum Backlog

### Band A: Counting and Place Value

Target subskills:

- number recognition
- count-to-number matching
- skip counting by 2, 5, 10, and 100
- ones/tens/hundreds identification
- standard, word, and expanded form
- compare and order whole numbers
- decimal place value and regrouping

Khan anchors:

- Skip-counting by 100s: https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-place-value/cc-2nd-skip-counting/e/skip-counting-by-100s
- Write numbers in different forms: https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-place-value/x3184e0ec:numbers-in-standard-word-and-expanded-form/e/writing-numbers-to-1000
- Decimal place value with regrouping: https://www.khanacademy.org/math/cc-fourth-grade-math/imp-decimals/imp-decimals-greater-than-one/e/decimals-greater-than-one-intuition

### Band B: Addition and Subtraction

Target subskills:

- add within 20
- subtract within 20
- missing-addend thinking
- regrouping with base-ten structure
- compare totals and differences
- multi-digit word problems

Khan anchors:

- Add within 20: https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:add-and-subtract-within-20/x3184e0ec:add-within-20/e/addition_2
- Add and subtract within 1000 word problems: https://www.khanacademy.org/math/cc-third-grade-math/imp-addition-and-subtraction/addition-and-subtraction-word-problems/e/add-and-subtract-within-1000-word-problems

### Band C: Multiplication and Division

Target subskills:

- equal groups
- repeated addition and skip counting
- arrays and area models
- fact fluency
- multiplicative comparison
- quotient as fair sharing
- quotient as repeated subtraction
- remainders
- long division placement
- multi-digit multiplication and estimation

Khan anchors:

- Understand equal groups as multiplication: https://www.khanacademy.org/math/cc-third-grade-math/intro-to-multiplication/imp-multiplication-intro/e/understand-equal-groups-as-multiplication
- Equal groups: https://www.khanacademy.org/math/cc-third-grade-math/intro-to-multiplication/imp-multiplication-intro/e/equal-groups
- Multiplication and division word problems: https://www.khanacademy.org/math/cc-fourth-grade-math/division/mult-division-word-problems/e/arithmetic_word_problems
- Estimate multi-digit multiplication: https://www.khanacademy.org/math/cc-fifth-grade-math/multi-digit-multiplication-and-division/multi-digit-multiplication-estimation/e/estimate-multi-digit-multiplication-problems

### Band D: Fractions and Decimals

Target subskills:

- unit fractions
- equivalent fractions
- compare fractions
- improper fractions and mixed numbers
- fraction to decimal
- decimal place value
- decimal comparison

Khan anchors:

- Equivalent fractions: https://www.khanacademy.org/math/cc-fourth-grade-math/comparing-fractions-and-equivalent-fractions/imp-equivalent-fractions-2/e/visualizing-equivalent-fractions
- Compare fractions with models: https://www.khanacademy.org/math/cc-third-grade-math/equivalent-fractions-and-comparing-fractions/imp-comparing-fractions/e/comparing-fractions-with-the-same-numerator-or-denominator

### Band E: Money, Time, and Measurement

Target subskills:

- coin and bill value
- making change
- dollars vs cents
- metric conversion
- customary conversion
- elapsed time
- temperature and comparison language

Khan anchors:

- Convert money word problems: https://www.khanacademy.org/math/cc-fourth-grade-math/imp-measurement-and-data-2/imp-money-word-problems/e/measuring-and-converting-money-word-problems
- Metric conversions word problems: https://www.khanacademy.org/math/cc-fourth-grade-math/imp-measurement-and-data-2/imp-conversion-word-problems/e/metric-conversions-word-problems
- Time word problems with number line: https://www.khanacademy.org/math/cc-third-grade-math/time/tell-time-on-number-line/e/telling-time-word-problems-with-the-number-line

### Band F: Integers and Order of Operations

Target subskills:

- signed numbers
- negative arithmetic
- absolute value
- operation order
- parentheses
- exponents inside expressions

Khan anchors:

- Compare and order absolute values: https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-negative-number-topic/x0267d782:cc-6th-comparing-absolute-values/e/comparing_absolute_values
- Order of operations: https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:cc-6th-exponents-and-order-of-operations/x0267d782:more-on-order-of-operations/e/order_of_operations_2

### Band G: Ratios, Rates, and Percent

Target subskills:

- ratio language
- equivalent ratios
- unit rates
- rates with fractions
- proportional relationships
- percent of a quantity
- percent as a part-whole comparison
- percent change

Khan anchors:

- Equivalent ratios: https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-ratios-prop-topic/cc-6th-equivalent-ratios/e/equivalent-ratios
- Rates with fractions: https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-fractions-decimals/cc-7th-rates/e/rate_problems_1
- Percent word problems: https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:cc-6th-rates-and-percentages/cc-6th-percent-word-problems/e/percentage_word_problems_1

### Band H: Expressions, Equations, and Pre-Algebra Structure

Target subskills:

- evaluate expressions
- combine like terms where appropriate
- one-step equations
- two-step equations
- inequalities
- exponents and roots
- scientific notation
- coordinate plane and function tables

Khan anchors:

- Evaluate expressions: https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:foundation-algebra/x2f8bb11595b61c86:substitute-evaluate-expression/e/evaluating_expressions_2
- Two-step equations: https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-variables-expressions/cc-7th-2-step-equations-intro/e/linear_equations_2
- Scientific notation: https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-numbers-operations/cc-8th-scientific-notation/e/scientific_notation
- Coordinate plane word problems: https://www.khanacademy.org/math/geometry/hs-geo-analytic-geometry/hs-geo-dist-problems/e/coordinate-plane-word-problems-with-polygons

### Band I: Summer Algebra And Geometry Preview

Scope: optional post-core enrichment after the official `prealgebra_finish` path. This band should provide as much algebra and geometry exposure as practical for summer, but it must not change the official pre-algebra completion definition.

Preview units:

- `linear_relationships_preview`
- `functions_patterns_preview`
- `geometry_measurement_preview`
- `coordinate_geometry_preview`

Targets:

- [ ] Slope from tables, coordinate pairs, and graphs.
- [ ] Linear relationships and slope-intercept form.
- [ ] Function tables, function rules, and input/output notation.
- [ ] Arithmetic sequences and simple pattern generalization.
- [ ] Triangle area, parallelogram/rectangle area, composite area, and circle basics.
- [ ] Pythagorean theorem as a visual/coordinate bridge.
- [ ] Coordinate geometry distance and midpoint.
- [ ] Transformations, similarity, and scale factor.

Khan anchors to map into Resource Review:

- https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:slope/e/slope-table
- https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:functions/x2f8bb11595b61c86:function-inputs-and-outputs/e/inputs-and-outputs-of-a-function
- https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:sequences/x2f8bb11595b61c86:constructing-arithmetic-sequences/e/sequences_1
- https://www.khanacademy.org/math/basic-geo/basic-geo-area-and-perimeter/area-triangle/e/area_of_triangles_1
- https://www.khanacademy.org/math/basic-geo/basic-geo-pythagorean-topic/basic-geometry-pythagorean-theorem/e/pythagorean_theorem_1
- https://www.khanacademy.org/math/geometry/hs-geo-similarity/hs-geo-similarity-definitions/e/exploring-angle-preserving-transformations-and-similarity

Acceptance criteria:

- [ ] Preview units stay optional and never block official `prealgebra_finish` completion, pace, catch-up, or exit status.
- [ ] Each preview unit has active expression templates, word problems where relevant, scaffolded lesson/checkpoint items, and a mapped help resource.
- [x] Parent Resource Review reports coverage status for each preview unit as `ready`, `thin`, or `missing`.
- [x] Child dashboard labels this material as `Bonus preview`.

## File-by-File Backlog

### /home/user/projects/mandelbrot_fortran/app/skill_graph.py

- audit all arithmetic and pre-algebra subskills for naming consistency
- normalize duplicate or vague labels
- add any missing exposed subskills needed for the Khan matrix
- keep labels stable where quiz history or assignments may already rely on them

### /home/user/projects/mandelbrot_fortran/app/explanations.py

- introduce subskill-level intuition content
- keep skill-level summaries for the panel header, but stop using them as the only pedagogy layer
- add a helper lookup so quizzes and the arithmetic panel can request intuition by `skill + subskill`

### /home/user/projects/mandelbrot_fortran/app/ui_arithmetic.py

- replace skill-level lesson links with subskill-aware lookup
- preserve parent gating through `show_external_links` and `enforce_offline_mode`
- update button copy so it is clear whether the link opens a lesson or a practice exercise

### /home/user/projects/mandelbrot_fortran/app/ui_quiz.py

- surface intuition mode for early-math subskills when templates exist
- ensure subskill-targeted assignments can force the intended mode mix

### /home/user/projects/mandelbrot_fortran/app/quiz_engine.py

- keep native generators only as fallback or for visual-first practice
- route expression, word, and intuition requests to templates whenever the matrix says the subskill is template-backed
- reduce giant conditional growth by delegating to smaller skill-specific helpers where needed

### /home/user/projects/mandelbrot_fortran/app/pre_algebra_generators.py

- narrow this file to true native fallback content
- move comprehensive pre-algebra depth into imported template manifests

### /home/user/projects/mandelbrot_fortran/scripts/build_khan_subskill_registry.py

- expand `KHAN_ASSIGNABLE_URL_OVERRIDES` so every early-math subskill has a mapped assignment URL
- add metadata for recommended modes per subskill if needed

### /home/user/projects/mandelbrot_fortran/scripts/template_manifests/

Add new manifests by wave:

- `arith_number_sense_wave1.json`
- `arith_operations_wave1.json`
- `arith_fractions_decimals_wave1.json`
- `arith_money_measurement_wave2.json`
- `prealg_integers_order_wave2.json`
- `prealg_ratios_percent_wave3.json`
- `prealg_expressions_equations_wave3.json`

### /home/user/projects/mandelbrot_fortran/tests/test_pedagogical_integrity.py

- extend assertions to arithmetic and pre-algebra, not only selected template-backed areas
- fail if an exposed subskill lacks required modes or Khan mapping

### /home/user/projects/mandelbrot_fortran/tests/

Add focused regression files:

- `test_early_math_coverage.py`
- `test_early_math_intuition.py`
- `test_khan_subskill_links.py`

## Delivery Waves

### Wave 1

- counting and place value
- addition and subtraction
- multiplication and division
- fractions and decimals

Exit criteria:

- all Band A through Band D subskills mapped
- at least 6 active templates per subskill family
- at least 2 intuition templates for each intuition-friendly family

### Wave 2

- money
- time
- measurement
- integers
- order of operations

Exit criteria:

- no zero-template subskills remain in arithmetic
- arithmetic panel opens subskill-aware Khan links

### Wave 3

- ratios
- rates
- percent
- expressions
- equations
- scientific notation
- coordinate plane and function tables

Exit criteria:

- `pre_algebra` is no longer a shallow umbrella
- all pre-algebra subskills have expression coverage
- word and intuition coverage exist wherever Khan exercises justify them

## Immediate Next PRs

### PR 1: Coverage Matrix and Link Plumbing

- update registry for full early-math mappings
- add subskill-aware link lookup
- add failing coverage tests

### PR 2: Wave 1 Template Import

- create and import manifests for Band A through Band D
- add subskill-level intuition for the same bands

### PR 3: Wave 2 Template Import

- create and import manifests for Band E and Band F
- clean up native fallback overlap

### PR 4: Wave 3 Template Import

- create and import manifests for Band G and Band H
- tighten quiz mode routing and assignment support

## Non-Goals for This Expansion

- algebra 1 and above
- state-by-state standards alignment
- changing the parent gating model for external links
- replacing every native visual with a template-driven one
