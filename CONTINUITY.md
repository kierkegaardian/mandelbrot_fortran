# MandelQuest Continuity

Last updated: 2026-06-26

## Current Product Direction

MandelQuest is now primarily a math learning app with a calmer child-first flow. The Mandelbrot/fractal viewer should remain a bonus exploration feature, not the opening screen or the core progress model.

Child profiles now open into a math-first shell. In normal mode they see `Today`, `Practice`, `Quizzes`, and `Skill Map`; the Parent tab is hidden from child navigation, and Mandelbrot appears only through the dashboard's `Bonus Explore` flow after a practice session has been recorded. Parent profiles still retain Parent tools and direct `Bonus Explore` access, but the tab label no longer presents fractals as a primary workflow.

Child profiles now also get a simplified quiz launcher. The child `Quizzes` tab keeps skill/subskill choice plus one `Start Practice` action, hides historical-test ingestion/printing and advanced quiz settings, defaults manual launches to learning-blend practice with both question types, and leaves full test/history/strategy controls available for parent profiles.

Child quiz completion now uses kid-facing summary copy. Child profiles see `Practice Complete` / `Perfect Practice`, a `What happened` line, a concrete `Next step`, `Practice This Again`, and friendly no-mistake copy. Parent profiles keep the existing mastery/retake wording and full review behavior.

Child dashboards now include a child-only `Today's Next Step` card. It surfaces the current program step, daily practice, or assignment launch; shows visible-skill mastery progress; includes the selected Texas grade goal progress and next goal; and tells the child whether `Bonus Explore` is locked or unlocked. Parent dashboards do not render this child-only card.

Child dashboards now also translate the next Texas grade goal into intuition copy. When a child has a saved Texas target, the card shows why the next goal matters using the goal's mental model and names one concrete subskill to try next; without a saved target it asks the child to get a parent to choose the grade goal.

Child quiz practice now surfaces a short mental-model cue as soon as each child question appears. The cue uses the same skill/subskill explanation catalog as the expanded `Show intuition` help, so the default practice flow starts with `Think:` guidance while the stuck/help button still expands to subskill, mental model, common mistake, and try-this details. Parent quiz starts remain unchanged and do not auto-fill the child-facing cue.

Child dashboards can now launch the next saved Texas goal directly. When there is no program task or parent assignment waiting, the child `Today's Next Step` card shows `Next Texas Goal`, names the next unfinished subskill inside that goal, and starts a focused quiz using that goal's skill, subskill, and quiz level. Parent-seeded assignments still take priority over this direct goal practice.

Child dashboards now also show a compact goal-step checklist for the next Texas goal. If one subskill inside the goal is already mastered, the card reports partial progress and routes `Practice Next Goal` to the first unfinished subskill instead of repeating the completed one.

The active fall-school-year goal is Texas-aligned math readiness for grades 1-7, with both kids able to work at their own pace and keep moving into stretch material when ready. Parent tools now include a Texas Grade Goals surface backed by `app/texas_grade_goals.py`; it shows quiz-ready goals, honest content gaps, TEKS references, and one-click quiz-set seeding for the selected grade.

Each child can now have a local Texas school-year target with a selected grade and stretch-goal toggle. The dashboard derives the child's next Texas goal from saved subskill mastery and shows grade progress, next goal, stretch state, and content-gap count.

Parent tools can also seed active assignments from a selected Texas grade target. Assignment seeding creates one `subskill_mastered` assignment per quiz-ready goal subskill, respects the stretch toggle, and dedupes against existing active assignments.

Parent tools can generate printable Texas grade assessment packets from the selected child/grade target. Packets are HTML worksheets with TEKS metadata, goal/subskill sections, an answer key, coverage notes for content gaps or skipped stretch goals, and a worksheet-history row.

Parent tools can now add a focused next-goal review set for a selected child. The School Year tab uses the child's saved Texas target and mastery state, finds the next unmet quiz-ready Texas goal, and creates active subskill-mastery assignments only for that goal without duplicating existing active review work.

Parent tools can also add review assignments for any selected Texas goal in the visible grade list, independent of the child's saved target. The same School Year tab now shows recent saved Texas assessment packets for the selected child and can reopen the packet HTML from the recorded worksheet path.

The School Year tab can now archive saved Texas assessment packets from the active packet list. Archiving marks the worksheet row with `archived_at`, leaves the generated HTML file on disk, hides the row from the default saved-packets list, and keeps worksheet progress counts intact for the child dashboard.

Grade 1 shape composition/attributes and elementary data displays are now first-class quiz-ready content. The new `geometry_shapes` and `data_displays` skills include native generators, guided lesson steps, subskill intuition packs, template-manifest coverage, parent-controlled Khan links, curriculum-index rows, and simple child-practice visuals.

Grades 2-5 now have explicit Texas measurement/data coverage checks. The grade-goal catalog splits geometry, measurement, coordinate, and data rows into quiz-ready targets instead of hiding data inside broad geometry goals.

Grades 6-7 now have explicit Texas measurement/data/probability coverage checks. Grade 6 splits geometry measurement, coordinate plane work, data displays, data summaries, and categorical percent summaries. Grade 7 splits similarity/circle work, volume/surface area, probability, and sample-based data comparisons.

Grades 6-7 data analysis is now exact enough for the middle-school TEKS display expectations. The new `data_analysis` skill covers histograms, box plots, center/spread/shape, median/range/IQR, variability, comparative dot/box plots, sample inferences, and part-to-whole display comparisons with native questions, enriched intuition, assessment-packet routing, and parent-controlled Khan links.

Grades 1-7 now have explicit quiz-ready Texas personal financial literacy rows. The new `financial_literacy` skill is native-generated and covers income/gifts/wants/needs, saving/spending/giving/borrowing/lending, scarcity and credit choices, expenses/profit/institutions, taxes/payments/records/budgets, accounts/credit/education-income, and budget/net-worth/interest/incentive reasoning.

The Grade 1-7 Texas standards spine has been audited against the current TEA elementary and middle-school math PDFs. Every non-process core TEKS root from Grade 1 through Grade 7 now has a non-stretch quiz-ready goal, including the previously missing Grade 2 fractional-units root `2.3` and Grade 3 place-value root `3.2`; the catalog currently has zero content-gap rows.

The active summer goal is honest pre-algebra completion for the 9-year-old, a foundation bridge lane for the 6-year-old, and optional algebra/geometry enrichment after the official pre-algebra finish. Optional preview work should be abundant, but it must not blur the completion definition for pre-algebra.

## Recently Landed

- Texas Grade Goals catalog for grades 1-7 exists with TEKS section references, focal areas, quiz-ready mappings, stretch goals, and content-gap rows.
- Parent tools now have a `School Year` tab for browsing Texas grade goals and adding grade-level quiz sets from quiz-ready goals.
- Parent tools can save per-child Texas grade targets and stretch settings.
- Student dashboards show the active school-year target and next quiz-ready Texas goal.
- Parent tools can add Texas grade-goal assignments for the selected child.
- Parent tools can add child-specific next-goal review assignments from the child's saved Texas target.
- Parent tools can add selected Texas goal review assignments and reopen recent saved Texas assessment packets.
- Parent tools can archive saved Texas assessment packets from the active list without deleting the generated HTML file or removing worksheet progress credit.
- Parent tools can generate printable Texas grade assessment packets from Texas Grade Goals.
- Texas Grade 1 shape, data-display, and personal-finance goals are quiz-ready; Grade 1 now has 6 quiz-ready goals and 0 content gaps.
- Texas Grades 2-5 now have explicit quiz-ready measurement/data coverage rows, including Grade 5 data displays and measurement conversion goals.
- Texas Grades 6-7 now have explicit quiz-ready measurement/data/probability rows instead of broad geometry/statistics bundles.
- Texas Grades 6-7 data displays now include exact middle-school data-analysis coverage: histograms, box plots, center/spread/shape, median/range/IQR, variability, comparative displays, sample inference, and part-to-whole comparisons.
- Texas Grades 1-7 now have explicit quiz-ready personal financial literacy rows instead of treating money arithmetic as a substitute for the full TEKS strand.
- Texas Grades 1-7 now pass a standards-spine audit: every non-process core TEKS root is covered by a non-stretch quiz-ready goal, Grade 2 `2.3` fractional units and Grade 3 `3.2` place value are explicit rows, and no content-gap rows remain.
- Child navigation is now math-first: child profiles do not show the Parent tab, and Mandelbrot is labeled `Bonus Explore` and unlocked from the dashboard after practice.
- Child quiz launch is simplified: children see `Start Practice` and no historical-test/advanced settings surface, while parent profiles keep complete assessment controls.
- Child quiz completion now gives a clear result and next step, while parent profiles still see mastery retake controls when needed.
- Child dashboards now show a `Today's Next Step` card with launch action, skill progress, Texas goal progress, and Bonus Explore lock/unlock status.
- Child dashboards now show next-Texas-goal intuition copy and one concrete next subskill to practice.
- Child quiz questions now show a short `Think:` mental-model preview during child practice, while parent quiz starts stay free of child-only guidance.
- Child dashboards can launch the next saved Texas goal as focused practice when no program task or assignment is waiting.
- Algebra 1 stretch content now includes slope from points, slope-intercept form, graphing linear inequalities, function transformations, systems by substitution/elimination, graph intersections, polynomial arithmetic/factoring basics, quadratic factoring by grouping, difference of squares, radicals/rational exponents, completing the square, and quadratic formula work, with native questions and subskill-specific intuition.
- Summer Program core architecture exists with lanes, generated tasks, placement, checkpoints, midpoint/exit assessment flow, pace status, and local-only persistence.
- Parent override and reporting flow exists with explicit placement review states, blocked-task summaries, retry guidance, and dashboard gating.
- The child dashboard prioritizes launchable Summer Program work over generic review, while keeping manual assignments secondary.
- The app now treats the fractal viewer as an optional learning bonus instead of the core home experience.
- Optional post-core `prealgebra_finish` preview units were added:
  - `linear_relationships_preview`
  - `functions_patterns_preview`
  - `algebra_1_preview_capstone`
  - `geometry_measurement_preview`
  - `coordinate_geometry_preview`
  - `geometry_preview_capstone`
- These preview units are marked optional and do not block official `prealgebra_finish` completion, pace status, catch-up generation, or exit requirements.
- Preview quiz generation routes into algebra/geometry families including linear relationships, functions, sequences, circles, Pythagorean theorem, coordinate midpoint, transformations, and similarity-style scaffolds.
- Dashboard copy labels post-core optional preview work as `Bonus preview`.
- Resource cleanup was hardened for the fractal renderer. The earlier `ResourceWarning` path came from `subprocess.Popen(... stdout/stderr=PIPE)` handles and is fixed by closing process pipes and cleaning Tk callbacks.
- The full `prealgebra_finish` Resource Review now has no thin or missing rows: 43 ready, 0 thin, 0 missing across 43 rows.
- Parent tools can export a printable Resource Review HTML report for the active Summer Program lane without creating worksheet-progress credit for the child.

## Verification Receipts

These checks passed after the recent Summer Program and resource-cleanup work:

- `python -m unittest discover -s tests` passed 174 tests.
- `python -m app.main --smoke-test` completed successfully.
- Warning-enabled Summer Program/UI checks passed without `ResourceWarning`.
- Focused Summer Program checks passed for optional preview generation, completion exclusion, dashboard labeling, catch-up exclusion, and assessment gating.

Latest verification after the Texas Grade Goals slice:

- `python -m py_compile app/texas_grade_goals.py app/ui_parent.py app/ui_root.py tests/test_texas_grade_goals.py`
- `python -W error::ResourceWarning -m unittest tests.test_texas_grade_goals tests.test_summer_mode_ui_flow tests.test_summer_mode tests.test_ui_settings tests.test_content_audit`
- `python -m unittest tests.test_texas_grade_goals tests.test_summer_mode_ui_flow tests.test_summer_mode tests.test_ui_settings tests.test_content_audit`
- `python -m app.main --smoke-test`
- `python -m unittest discover -s tests` passed 184 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the per-child school-year target slice:

- `python -m py_compile app/models.py app/db.py app/school_year.py app/ui_parent.py app/ui_dashboard.py tests/test_school_year.py`
- `python -m unittest tests.test_school_year tests.test_texas_grade_goals`
- `python -m unittest tests.test_summer_mode_ui_flow tests.test_ui_settings tests.test_content_audit`
- `python -W error::ResourceWarning -m unittest tests.test_school_year tests.test_texas_grade_goals tests.test_summer_mode_ui_flow tests.test_ui_settings tests.test_content_audit`
- `python -m app.main --smoke-test`
- `python -m unittest discover -s tests` passed 189 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Texas assessment-packet slice:

- `python -m py_compile app/school_year_assessment.py app/ui_parent.py tests/test_school_year.py tests/test_summer_mode_ui_flow.py`
- `python -W error::ResourceWarning -m unittest tests.test_school_year tests.test_texas_grade_goals tests.test_summer_mode_ui_flow tests.test_ui_settings tests.test_content_audit` passed 27 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 191 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Grade 1 shapes/data content slice:

- `python -m py_compile app/elementary_generators.py app/quiz_engine.py app/early_math_catalog.py app/early_math_intuition.py app/skill_graph.py app/explanations.py app/ui_arithmetic.py app/arithmetic_render.py app/arithmetic_summer_lessons.py app/texas_grade_goals.py tests/test_elementary_shapes_data.py tests/test_school_year.py tests/test_summer_mode_ui_flow.py tests/early_math_test_utils.py scripts/generate_early_math_manifests.py`
- `python -W error::ResourceWarning -m unittest tests.test_elementary_shapes_data tests.test_school_year tests.test_texas_grade_goals tests.test_summer_mode_ui_flow tests.test_ui_settings tests.test_content_audit tests.test_khan_subskill_links tests.test_arithmetic_summer_lessons` passed 41 tests.
- `python -m unittest tests.test_pedagogical_integrity tests.test_elementary_shapes_data tests.test_early_math_coverage tests.test_new_skills tests.test_skill_graph_tracks tests.test_explanations` passed 49 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 196 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Grade 2-5 measurement/data coverage slice:

- `python -m py_compile app/elementary_generators.py app/quiz_engine.py app/early_math_catalog.py app/early_math_intuition.py app/texas_grade_goals.py tests/test_elementary_shapes_data.py tests/test_new_skills.py tests/test_school_year.py tests/test_texas_measurement_data_coverage.py scripts/generate_early_math_manifests.py`
- `python -m json.tool scripts/template_manifests/early_math_money_measurement_time_v1.json`
- `python -m json.tool scripts/template_manifests/early_math_shapes_data_v1.json`
- `python -c "from scripts.generate_early_math_manifests import _band_map, _validate; _validate(_band_map())"`
- `python -W error::ResourceWarning -m unittest tests.test_elementary_shapes_data tests.test_new_skills tests.test_texas_grade_goals tests.test_texas_measurement_data_coverage tests.test_school_year tests.test_summer_mode_ui_flow tests.test_ui_settings tests.test_content_audit tests.test_khan_subskill_links tests.test_arithmetic_summer_lessons` passed 61 tests.
- `python -m unittest tests.test_pedagogical_integrity tests.test_elementary_shapes_data tests.test_early_math_coverage tests.test_new_skills tests.test_skill_graph_tracks tests.test_explanations tests.test_texas_measurement_data_coverage` passed 53 tests. The suite still prints existing SQLite `ResourceWarning` noise.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 200 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Grade 6-7 measurement/data/probability coverage slice:

- `python -m py_compile app/quiz_engine.py app/texas_grade_goals.py tests/test_texas_measurement_data_coverage.py`
- `python -W error::ResourceWarning -m unittest tests.test_texas_measurement_data_coverage tests.test_texas_grade_goals tests.test_school_year` passed 18 tests.
- `python -W error::ResourceWarning -m unittest tests.test_texas_measurement_data_coverage tests.test_texas_grade_goals tests.test_school_year tests.test_summer_mode_ui_flow tests.test_ui_settings tests.test_content_audit tests.test_khan_subskill_links tests.test_arithmetic_summer_lessons tests.test_skill_graph_tracks` passed 56 tests.
- `python -m unittest tests.test_pedagogical_integrity tests.test_texas_measurement_data_coverage tests.test_early_math_coverage tests.test_new_skills tests.test_skill_graph_tracks tests.test_explanations` passed 51 tests. The suite still prints existing SQLite `ResourceWarning` noise.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 203 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Grade 1-7 personal financial literacy slice:

- `python -m py_compile app/financial_literacy.py app/quiz_engine.py app/skill_graph.py app/explanations.py app/ui_arithmetic.py app/texas_grade_goals.py tests/test_texas_financial_literacy.py tests/test_texas_measurement_data_coverage.py`
- `python -m json.tool data/curriculum_index.json`
- `python -W error::ResourceWarning -m unittest tests.test_texas_financial_literacy tests.test_texas_measurement_data_coverage tests.test_texas_grade_goals tests.test_school_year tests.test_explanations tests.test_khan_subskill_links tests.test_summer_mode_ui_flow tests.test_ui_settings` passed 40 tests.
- `python -m unittest tests.test_pedagogical_integrity tests.test_texas_financial_literacy tests.test_texas_measurement_data_coverage tests.test_early_math_coverage tests.test_explanations tests.test_skill_graph_tracks` passed 39 tests. The suite still prints existing SQLite `ResourceWarning` noise.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 207 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Grade 6-7 data-analysis depth slice:

- `python -m py_compile app/data_analysis.py app/quiz_engine.py app/skill_graph.py app/explanations.py app/ui_arithmetic.py app/texas_grade_goals.py tests/test_data_analysis.py tests/test_texas_measurement_data_coverage.py tests/test_skill_graph_tracks.py`
- `python -m json.tool data/curriculum_index.json`
- `python -W error::ResourceWarning -m unittest tests.test_data_analysis tests.test_texas_measurement_data_coverage tests.test_texas_grade_goals tests.test_school_year tests.test_explanations tests.test_khan_subskill_links tests.test_skill_graph_tracks` passed 41 tests.
- `python -m unittest tests.test_pedagogical_integrity tests.test_data_analysis tests.test_texas_measurement_data_coverage tests.test_early_math_coverage tests.test_explanations tests.test_skill_graph_tracks tests.test_texas_financial_literacy` passed 43 tests. The suite still prints existing SQLite `ResourceWarning` noise.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 211 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the child-first navigation slice:

- `python -m py_compile app/ui_root.py app/ui_dashboard.py tests/test_summer_mode_ui_flow.py`
- `python -m unittest tests.test_summer_mode_ui_flow` passed 11 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 212 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the child quiz-launch simplification slice:

- `python -m py_compile app/ui_quiz.py tests/test_summer_mode_ui_flow.py`
- `python -m unittest tests.test_summer_mode_ui_flow` passed 13 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 214 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the child quiz-completion polish slice:

- `python -m py_compile app/ui_quiz.py tests/test_summer_mode_ui_flow.py`
- `python -m unittest tests.test_summer_mode_ui_flow` passed 15 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 216 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the child dashboard next-step card slice:

- `python -m py_compile app/ui_dashboard.py tests/test_summer_mode_ui_flow.py`
- `python -m unittest tests.test_summer_mode_ui_flow` passed 15 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 216 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Grade 1-7 Texas standards audit slice:

- `python -m py_compile app/texas_grade_goals.py app/elementary_generators.py tests/test_texas_standards_audit.py`
- `python -m unittest tests.test_texas_standards_audit tests.test_texas_grade_goals tests.test_texas_measurement_data_coverage tests.test_texas_financial_literacy tests.test_school_year` passed 27 tests.
- `python -m app.main --smoke-test` completed successfully.
- `git diff --check -- app/texas_grade_goals.py app/elementary_generators.py tests/test_texas_standards_audit.py TODO.md CONTINUITY.md`
- `python -m unittest discover -s tests` passed 220 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the child-specific next-goal review slice:

- `python -m py_compile app/ui_parent.py tests/test_summer_mode_ui_flow.py`
- `python -m unittest tests.test_summer_mode_ui_flow tests.test_school_year tests.test_texas_grade_goals tests.test_texas_standards_audit` passed 31 tests.
- `python -m app.main --smoke-test` completed successfully.
- `git diff --check -- app/ui_parent.py tests/test_summer_mode_ui_flow.py TODO.md CONTINUITY.md`
- `python -m unittest discover -s tests` passed 221 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the selected-goal and saved-packet parent builder slice:

- `python -m py_compile app/db.py app/ui_parent.py tests/test_db_assignment_semantics.py tests/test_summer_mode_ui_flow.py`
- `python -m unittest tests.test_db_assignment_semantics tests.test_summer_mode_ui_flow tests.test_school_year tests.test_texas_grade_goals tests.test_texas_standards_audit` passed 38 tests.
- `python -m app.main --smoke-test` completed successfully.
- `git diff --check -- app/db.py app/ui_parent.py tests/test_db_assignment_semantics.py tests/test_summer_mode_ui_flow.py TODO.md CONTINUITY.md`
- `python -m unittest discover -s tests` passed 223 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the child Texas-goal intuition dashboard slice:

- `python -m py_compile app/ui_dashboard.py tests/test_summer_mode_ui_flow.py`
- `python -m unittest tests.test_summer_mode_ui_flow tests.test_school_year tests.test_texas_grade_goals tests.test_texas_standards_audit` passed 32 tests.
- `python -m app.main --smoke-test` completed successfully.
- `git diff --check -- app/ui_dashboard.py tests/test_summer_mode_ui_flow.py TODO.md CONTINUITY.md`
- `python -m unittest discover -s tests` passed 223 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the child quiz question intuition preview slice:

- `python -m py_compile app/quiz_flow.py tests/test_early_math_intuition.py tests/test_summer_mode_ui_flow.py`
- `python -m unittest tests.test_early_math_intuition` passed 4 tests.
- `python -m unittest tests.test_summer_mode_ui_flow` passed 17 tests.
- `python -m app.main --smoke-test` completed successfully.
- `git diff --check -- app/quiz_flow.py tests/test_early_math_intuition.py tests/test_summer_mode_ui_flow.py`
- `python -m unittest discover -s tests` passed 225 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the saved Texas packet management slice:

- `python -m py_compile app/models.py app/db.py app/ui_parent.py tests/test_db_assignment_semantics.py tests/test_summer_mode_ui_flow.py`
- `python -m unittest tests.test_db_assignment_semantics` passed 6 tests.
- `python -m unittest tests.test_summer_mode_ui_flow` passed 17 tests.
- `python -m unittest tests.test_db_assignment_semantics tests.test_summer_mode_ui_flow tests.test_school_year tests.test_texas_grade_goals tests.test_texas_standards_audit` passed 38 tests.
- `python -m app.main --smoke-test` completed successfully.
- `git diff --check -- app/models.py app/db.py app/ui_parent.py tests/test_db_assignment_semantics.py tests/test_summer_mode_ui_flow.py TODO.md CONTINUITY.md`
- `python -m unittest discover -s tests` passed 225 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the child next-Texas-goal launch slice:

- `python -m py_compile app/ui_dashboard.py app/ui_root.py tests/test_summer_mode_ui_flow.py`
- `python -m unittest tests.test_summer_mode_ui_flow.SummerModeUiFlowTests.test_child_dashboard_launches_next_texas_goal_practice` passed 1 test.
- `python -m unittest tests.test_summer_mode_ui_flow.SummerModeUiFlowTests.test_parent_school_year_target_and_goal_assignments` passed 1 test.
- `python -m unittest tests.test_summer_mode_ui_flow` passed 18 tests.
- `python -m unittest tests.test_school_year tests.test_texas_grade_goals tests.test_texas_standards_audit` passed 15 tests.
- `python -m app.main --smoke-test` completed successfully.
- `git diff --check -- app/ui_dashboard.py app/ui_root.py tests/test_summer_mode_ui_flow.py TODO.md CONTINUITY.md`
- `python -m unittest discover -s tests` passed 226 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the full Resource Review readiness slice:

- `python -m py_compile app/summer_program_preview_template_seed.py app/summer_program_template_seed.py app/summer_program_quiz.py tests/test_content_audit.py tests/test_summer_program_templates.py`
- `python -m unittest tests.test_content_audit tests.test_summer_program_templates` passed 15 tests.
- `python -m unittest tests.test_summer_program` passed 19 tests.
- `python -m unittest tests.test_quiz_engine_algebra_geometry tests.test_summer_mode_ui_flow tests.test_khan_subskill_links tests.test_quiz_engine_algebra_courses` passed 34 tests.
- `python -m app.main --smoke-test` completed successfully.
- Live and fresh `prealgebra_finish` Resource Review both report 32 ready, 0 thin, 0 missing across 32 rows.
- `git diff --check -- app/summer_program_preview_template_seed.py app/summer_program_template_seed.py app/summer_program_quiz.py scripts/template_manifests/coordinate_geometry_preview_v1.json tests/test_content_audit.py tests/test_summer_program_templates.py TODO.md CONTINUITY.md`
- `python -m unittest discover -s tests` passed 235 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Resource Review export slice:

- `python -m py_compile app/content_audit_report.py app/ui_parent.py tests/test_content_audit.py tests/test_summer_mode_ui_flow.py`
- `python -m unittest tests.test_content_audit` passed 10 tests.
- `python -m unittest tests.test_summer_mode_ui_flow.SummerModeUiFlowTests.test_parent_exports_resource_review_without_student_worksheet_credit` passed 1 test.
- `python -m unittest tests.test_summer_mode_ui_flow` passed 19 tests.
- `python -m unittest tests.test_content_audit tests.test_summer_program tests.test_summer_program_templates` passed 35 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 237 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the child Texas goal-step clarity slice:

- `python -m py_compile app/school_year.py app/ui_dashboard.py tests/test_school_year.py tests/test_summer_mode_ui_flow.py`
- `python -m unittest tests.test_school_year` passed 5 tests.
- `python -m unittest tests.test_summer_mode_ui_flow.SummerModeUiFlowTests.test_child_dashboard_launches_next_texas_goal_practice tests.test_summer_mode_ui_flow.SummerModeUiFlowTests.test_child_dashboard_targets_unfinished_step_inside_next_texas_goal` passed 2 tests.
- `python -m unittest tests.test_summer_mode_ui_flow` passed 20 tests.
- `python -m unittest tests.test_school_year tests.test_texas_grade_goals tests.test_texas_standards_audit tests.test_summer_mode_ui_flow` passed 35 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 238 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Algebra 1 function-transformations slice:

- `python -m py_compile app/algebra_1_generators.py app/skill_graph.py app/explanations.py tests/test_quiz_engine_algebra_courses.py tests/test_skill_graph_tracks.py tests/test_explanations.py`
- `python -m unittest tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations` passed 27 tests.
- `python -m unittest tests.test_pedagogical_integrity tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links` passed 39 tests. The suite still prints existing SQLite `ResourceWarning` noise.
- `python -m unittest tests.test_summer_mode tests.test_summer_program tests.test_summer_program_templates` passed 31 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 240 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Algebra 1 radicals/rational-exponents slice:

- `python -m py_compile app/algebra_1_generators.py app/skill_graph.py app/explanations.py tests/test_quiz_engine_algebra_courses.py tests/test_skill_graph_tracks.py tests/test_explanations.py`
- `python -m unittest tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations` passed 29 tests.
- `python -m unittest tests.test_pedagogical_integrity tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links` passed 41 tests. The suite still prints existing SQLite `ResourceWarning` noise.
- `python -m unittest tests.test_summer_mode tests.test_summer_program tests.test_summer_program_templates` passed 31 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 242 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Algebra 1 quadratic-formula slice:

- `python -m py_compile app/algebra_1_generators.py app/ui_arithmetic.py app/skill_graph.py app/explanations.py scripts/build_khan_subskill_registry.py tests/test_quiz_engine_algebra_courses.py tests/test_skill_graph_tracks.py tests/test_explanations.py tests/test_khan_subskill_links.py tests/test_build_khan_subskill_registry.py`
- `python -m unittest tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 39 tests.
- `python -m unittest tests.test_pedagogical_integrity tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 48 tests. The suite still prints existing SQLite `ResourceWarning` noise.
- `python -m unittest tests.test_summer_mode tests.test_summer_program tests.test_summer_program_templates` passed 31 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 246 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Algebra 1 completing-the-square slice:

- `python -m py_compile app/algebra_1_generators.py app/ui_arithmetic.py app/skill_graph.py app/explanations.py scripts/build_khan_subskill_registry.py tests/test_quiz_engine_algebra_courses.py tests/test_skill_graph_tracks.py tests/test_explanations.py tests/test_khan_subskill_links.py tests/test_build_khan_subskill_registry.py`
- `python -m unittest tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 43 tests.
- `python -m unittest tests.test_pedagogical_integrity tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 52 tests. The suite still prints existing SQLite `ResourceWarning` noise.
- `python -m unittest tests.test_summer_mode tests.test_summer_program tests.test_summer_program_templates` passed 31 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 250 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Algebra 1 systems-by-substitution slice:

- `python -m py_compile app/algebra_1_generators.py app/ui_arithmetic.py app/skill_graph.py app/explanations.py scripts/build_khan_subskill_registry.py tests/test_quiz_engine_algebra_courses.py tests/test_skill_graph_tracks.py tests/test_explanations.py tests/test_khan_subskill_links.py tests/test_build_khan_subskill_registry.py`
- `python -m unittest tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 47 tests.
- `python -m unittest tests.test_pedagogical_integrity tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 56 tests. The suite still prints existing SQLite `ResourceWarning` noise.
- `python -m unittest tests.test_summer_mode tests.test_summer_program tests.test_summer_program_templates` passed 31 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 254 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Algebra 1 systems-by-elimination slice:

- `python -m py_compile app/algebra_1_generators.py app/ui_arithmetic.py app/skill_graph.py app/explanations.py scripts/build_khan_subskill_registry.py tests/test_quiz_engine_algebra_courses.py tests/test_skill_graph_tracks.py tests/test_explanations.py tests/test_khan_subskill_links.py tests/test_build_khan_subskill_registry.py`
- `python -m unittest tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 51 tests.
- `python -m unittest tests.test_pedagogical_integrity tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 60 tests. The suite still prints existing SQLite `ResourceWarning` noise.
- `python -m unittest tests.test_summer_mode tests.test_summer_program tests.test_summer_program_templates` passed 31 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 258 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Algebra 1 graphing-systems/intersections slice:

- `python -m py_compile app/algebra_1_generators.py app/algebra_1_systems.py app/ui_arithmetic.py app/skill_graph.py app/explanations.py scripts/build_khan_subskill_registry.py tests/test_quiz_engine_algebra_courses.py tests/test_skill_graph_tracks.py tests/test_explanations.py tests/test_khan_subskill_links.py tests/test_build_khan_subskill_registry.py`
- `python -m unittest tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 55 tests.
- `python -m unittest tests.test_pedagogical_integrity tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 64 tests. The suite still prints existing SQLite `ResourceWarning` noise.
- `python -m unittest tests.test_summer_mode tests.test_summer_program tests.test_summer_program_templates` passed 31 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 262 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Algebra 1 polynomial-arithmetic/factoring-basics slice:

- `python -m py_compile app/algebra_1_generators.py app/algebra_1_polynomials.py app/algebra_1_systems.py app/ui_arithmetic.py app/skill_graph.py app/explanations.py scripts/build_khan_subskill_registry.py tests/test_quiz_engine_algebra_courses.py tests/test_skill_graph_tracks.py tests/test_explanations.py tests/test_khan_subskill_links.py tests/test_build_khan_subskill_registry.py`
- `python -m unittest tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 65 tests.
- `python -m unittest tests.test_pedagogical_integrity tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 74 tests. The suite still prints existing SQLite `ResourceWarning` noise.
- `python -m unittest tests.test_summer_mode tests.test_summer_program tests.test_summer_program_templates` passed 31 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 272 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Algebra 1 slope/linear-inequalities slice:

- `python -m py_compile app/algebra_1_generators.py app/algebra_1_linear.py app/algebra_1_polynomials.py app/algebra_1_systems.py app/ui_arithmetic.py app/skill_graph.py app/explanations.py scripts/build_khan_subskill_registry.py tests/test_quiz_engine_algebra_courses.py tests/test_skill_graph_tracks.py tests/test_explanations.py tests/test_khan_subskill_links.py tests/test_build_khan_subskill_registry.py`
- `python -m unittest tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 77 tests.
- `python -m unittest tests.test_pedagogical_integrity tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 86 tests. The suite still prints existing SQLite `ResourceWarning` noise.
- `python -m unittest tests.test_summer_mode tests.test_summer_program tests.test_summer_program_templates` passed 31 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 284 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

Latest verification after the Algebra 1 deeper-quadratic-factoring slice:

- `python -m py_compile app/algebra_1_generators.py app/algebra_1_linear.py app/algebra_1_polynomials.py app/algebra_1_systems.py app/ui_arithmetic.py app/skill_graph.py app/explanations.py scripts/build_khan_subskill_registry.py tests/test_quiz_engine_algebra_courses.py tests/test_skill_graph_tracks.py tests/test_explanations.py tests/test_khan_subskill_links.py tests/test_build_khan_subskill_registry.py`
- `python -m unittest tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 85 tests.
- `python -m unittest tests.test_pedagogical_integrity tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_build_khan_subskill_registry` passed 94 tests. The suite still prints existing SQLite `ResourceWarning` noise.
- `python -m unittest tests.test_summer_mode tests.test_summer_program tests.test_summer_program_templates` passed 31 tests.
- `python -m app.main --smoke-test` completed successfully.
- `python -m unittest discover -s tests` passed 292 tests. The broad discovery run still prints existing SQLite `ResourceWarning` noise, but it does not fail the suite.

## Recently Added Resource Review

The parent-facing Resource Review slice is now implemented.

- `app/content_audit.py` produces typed audit rows for each Summer Program lane, unit, and target subskill.
- Audit rows include active expression-template count, word-template count, scaffold-step count, native generator availability, intuition status, Khan link, open-resource link, and a `ready` / `thin` / `missing` label.
- Parent tools now show a `Resource Review` section under Summer Program, with weakest rows first.
- The audit uncovered and fixed a bridge-lane quiz fallback bug: early-math native generators now remain available when Summer Program passes a subskill that does not yet have a template.
- `tests/test_content_audit.py` covers pre-algebra preview rows, foundation-bridge exclusion of algebra/geometry preview work, template-depth reporting, and weak-row ordering.

## Recently Added Linear Preview Depth

The `linear_relationships_preview` audit slice now has real optional enrichment depth.

- `app/summer_program_template_seed.py` seeds expression templates for slope from points, slope-intercept interpretation, direct variation, unit-rate modeling, and linear-model word problems.
- `scripts/template_manifests/linear_relationships_preview_v1.json` records the same importable manifest coverage, including one word-mode linear model item.
- `app/summer_program_quiz.py` now has scaffolded lesson starts for direct variation, rate/unit-rate modeling, and linear model word problems, in addition to the existing slope starts.
- Live Resource Review after `db.init_db()` reports all five `linear_relationships_preview` rows as `ready`: `expr=1`, scaffolded steps present, and `Word problems with linear models` has `word=1`.
- Overall `prealgebra_finish` Resource Review moved to 19 ready, 13 thin, 0 missing across 32 rows.

## Recently Added Functions Preview Depth

The `functions_patterns_preview` audit slice now has durable seeded depth and scaffolded lesson starts.

- `app/summer_program_template_seed.py` seeds expression and word templates for functions, sequences, linear equations/graphs, and solving equations/inequalities.
- `scripts/template_manifests/functions_patterns_preview_v1.json` records the same importable manifest coverage with eight items.
- `app/summer_program_quiz.py` now has scaffolded lesson starts for `Linear equations & graphs` and `Solving equations & inequalities`, alongside the existing functions and sequences starts.
- A fresh test database now reports all four `functions_patterns_preview` rows as `ready`: `expr=1`, `word=1`, scaffolded steps present, and native questions available.
- Live Resource Review after `db.init_db()` reports `functions_patterns_preview` ready and moves the overall `prealgebra_finish` Resource Review to 21 ready, 11 thin, 0 missing across 32 rows.

## Recently Added Geometry Measurement Preview Depth

The `geometry_measurement_preview` audit slice now has durable seeded depth and scaffolded lesson starts.

- Preview template seed definitions were split into `app/summer_program_preview_template_seed.py`, with `app/summer_program_seed_types.py` holding the shared `SeedPattern` dataclass. This keeps the core seed file below the project size target while allowing more preview packs.
- `app/summer_program_preview_template_seed.py` seeds expression and word templates for perimeter/missing sides, triangle/parallelogram area, circle circumference, surface area/volume, and Pythagorean theorem.
- `scripts/template_manifests/geometry_measurement_preview_v1.json` records the same importable manifest coverage with ten items.
- `app/summer_program_quiz.py` now has scaffolded lesson starts for perimeter/missing sides, circle circumference, surface area/volume, and Pythagorean theorem, alongside the existing triangle-area scaffold.
- A fresh test database now reports all five `geometry_measurement_preview` rows as `ready`: `expr=1`, `word=1`, scaffolded steps present, and native questions available.
- Live Resource Review after `db.init_db()` reports `geometry_measurement_preview` ready and moves the overall `prealgebra_finish` Resource Review to 25 ready, 7 thin, 0 missing across 32 rows.

## Recently Added Coordinate Geometry Preview Depth

The `coordinate_geometry_preview` audit slice now has durable seeded depth and scaffolded lesson starts.

- `app/summer_program_preview_template_seed.py` seeds expression and word templates for coordinate midpoint/distance, transformations/congruence, similarity/scale factor, analytic geometry proofs, and slope from points.
- `scripts/template_manifests/coordinate_geometry_preview_v1.json` records the same importable manifest coverage with ten items.
- `app/summer_program_quiz.py` now has scaffolded lesson starts for `Transformations and congruence` and `Analytic geometry and coordinate proofs`, alongside the existing coordinate midpoint, similarity, and slope starts.
- A fresh test database now reports all five `coordinate_geometry_preview` rows as `ready`: `expr=1`, `word=1`, scaffolded steps present, and native questions available.
- Live Resource Review after `db.init_db()` reports all optional preview units ready and moves the overall `prealgebra_finish` Resource Review to 27 ready, 5 thin, 0 missing across 32 rows.
- Remaining thin rows are core pre-algebra scaffold gaps: `Integer and fraction fluency`, `Expressions and variables` twice due two units, `Order of operations`, and `Exponents, roots, and scientific notation`.

## Recently Completed Full Resource Review Readiness

The remaining core `prealgebra_finish` audit gaps are now closed.

- `app/summer_program_quiz.py` has scaffolded lesson starts for integer/fraction fluency, order of operations, expressions and variables, and exponents/roots/scientific notation.
- `app/summer_program_template_seed.py` now seeds durable expression templates for order of operations.
- `tests/test_content_audit.py` asserts that `prealgebra_finish` has no thin or missing Resource Review rows.
- Live and fresh Resource Review runs both report 32 ready, 0 thin, 0 missing across 32 rows.

## Recently Added Resource Review Export

Parent tools can now turn the active Summer Program Resource Review into a printable HTML report.

- `app/content_audit_report.py` renders the full lane review, not just the weakest rows shown in the UI.
- The report includes readiness counts, row count, question-source counts, scaffold/native-generator status, intuition status, Khan links, open-resource links, and notes.
- The parent `Resource Review` panel has an `Export Printable Review` action that writes the report under the worksheets data directory and opens it in the browser for printing.
- Exporting the audit report does not create a `worksheets` row, so it does not inflate a child's worksheet-progress credit.

## Recently Added Child Texas Goal-Step Clarity

The child dashboard now treats multi-subskill Texas goals as visible step lists instead of opaque single labels.

- `app/school_year.py` exposes `next_goal_steps` with each subskill's current streak, target streak, and mastered state.
- The child `Today's Next Step` card reports partial goal progress such as `Goal steps: 1/2 done`.
- `Practice Next Goal` now targets the first unfinished subskill in the current Texas goal, so a child does not repeat a mastered first subskill when the second subskill is still waiting.

## Recently Added Algebra 1 Function Transformations

The stretch path now has a concrete Algebra 1 function-transformation target.

- `algebra_1` includes `Function transformations` in the skill graph.
- Native quiz generation asks students to evaluate shifted parent functions such as `(x - h)^2 + k`.
- `explanation_for("algebra_1", "Function transformations")` now gives specific mental model, common mistake, and try-this copy, so child practice does not fall back to generic Algebra 1 help.
- The broader Algebra 1 roadmap still has open work for summer-preview depth across linear relationships, functions, and sequences.

## Recently Added Algebra 1 Radicals And Rational Exponents

The stretch path now goes beyond principal square-root checks.

- `algebra_1` includes `Radicals and rational exponents` in the skill graph.
- Native quiz generation asks students to evaluate rational exponent forms such as `64^(1/3)`.
- `explanation_for("algebra_1", "Radicals and rational exponents")` now gives a specific root-index mental model, common mistake, and try-this prompt.
- The broader Algebra 1 roadmap still has open work for summer-preview depth across linear relationships, functions, and sequences.

## Recently Added Algebra 1 Quadratic Formula

The stretch path now has a general quadratic-solving target beyond factorable-root recognition.

- `algebra_1` includes `Quadratic formula` in the skill graph.
- Native quiz generation asks students to apply the quadratic formula to standard-form equations and report the larger real root.
- `explanation_for("algebra_1", "Quadratic formula")` now gives a universal-root-finder mental model, common mistake, and try-this prompt.
- `khan_url_for_selection("algebra_1", "Quadratic formula")` maps to a Khan quadratic-formula review and still obeys parent external-link and offline-mode settings.
- The broader Algebra 1 roadmap still has open work for summer-preview depth across linear relationships, functions, and sequences.

## Recently Added Algebra 1 Deeper Quadratic Factoring

The stretch path now moves beyond monic factoring into two core Algebra 1 factoring patterns.

- `algebra_1` includes `Quadratic factoring by grouping` and `Difference of squares` in the skill graph.
- Native quiz generation asks students to factor leading-coefficient quadratics by grouping and recognize `A^2 - B^2` structures.
- `explanation_for("algebra_1", "Quadratic factoring by grouping")` and `Difference of squares` now give specific mental models, common mistakes, and try-this prompts.
- `khan_url_for_selection("algebra_1", "Quadratic factoring by grouping")` and `Difference of squares` map to Khan factoring material and still obey parent external-link and offline-mode settings.
- The broader Algebra 1 roadmap still has open work for summer-preview depth across linear relationships, functions, and sequences.

## Recently Added Algebra 1 Completing The Square

The stretch path now has a second general quadratic-solving method in addition to the quadratic formula.

- `algebra_1` includes `Completing the square` in the skill graph.
- Native quiz generation asks students to solve standard-form quadratics by completing the square and report the larger root.
- `explanation_for("algebra_1", "Completing the square")` now gives a perfect-square mental model, common mistake, and try-this prompt.
- `khan_url_for_selection("algebra_1", "Completing the square")` maps to Khan completing-the-square practice and still obeys parent external-link and offline-mode settings.
- The broader Algebra 1 roadmap still has open work for summer-preview depth across linear relationships, functions, and sequences.

## Recently Added Algebra 1 Systems By Substitution

The stretch path now has a dedicated algebraic systems method beyond the existing one-step elimination check.

- `algebra_1` includes `Systems by substitution` in the skill graph.
- Native quiz generation asks students to set two `y = mx + b` equations equal and report the shared `x` value.
- `explanation_for("algebra_1", "Systems by substitution")` now gives an intersection-as-same-point mental model, common mistake, and try-this prompt.
- `khan_url_for_selection("algebra_1", "Systems by substitution")` maps to Khan Algebra 1 systems-by-substitution material and still obeys parent external-link and offline-mode settings.
- The broader Algebra 1 roadmap still has open work for summer-preview depth across linear relationships, functions, and sequences.

## Recently Added Algebra 1 Systems By Elimination

The stretch path now has both main algebraic systems methods: substitution and elimination.

- `algebra_1` includes `Systems by elimination` in the skill graph.
- Native quiz generation asks students to add equations with opposite x-coefficients, cancel one variable, and report `y`.
- `explanation_for("algebra_1", "Systems by elimination")` now gives a canceling-variable mental model, common mistake, and try-this prompt.
- `khan_url_for_selection("algebra_1", "Systems by elimination")` maps to Khan Algebra 1 systems-by-elimination practice and still obeys parent external-link and offline-mode settings.
- The broader Algebra 1 roadmap still has open work for summer-preview depth across linear relationships, functions, and sequences.

## Recently Added Algebra 1 Graphing Systems And Intersections

The systems path now connects algebraic methods to the graph interpretation: the solution is where both lines meet.

- `algebra_1` includes `Graphing systems and intersections` in the skill graph.
- Native quiz generation asks students to identify the x-coordinate of the intersection point for two slope-intercept lines.
- `explanation_for("algebra_1", "Graphing systems and intersections")` now gives a same-point mental model, common mistake, and try-this prompt.
- `khan_url_for_selection("algebra_1", "Graphing systems and intersections")` maps to Khan graphing systems material and still obeys parent external-link and offline-mode settings.
- The broader Algebra 1 roadmap still has open work for summer-preview depth across linear relationships, functions, and sequences.

## Recently Added Algebra 1 Polynomial Arithmetic And Factoring Basics

The stretch path now covers basic polynomial manipulation before students move deeper into quadratic solving.

- `algebra_1` includes `Polynomial arithmetic` and `Factoring basics` in the skill graph.
- Native quiz generation asks students to combine polynomial like terms, factor monic quadratics by sum/product reasoning, and connect binomial multiplication to the middle x-term.
- `explanation_for("algebra_1", "Polynomial arithmetic")`, `Factoring basics`, and `Quadratics: Multiplying & factoring` now give specific mental models, common mistakes, and try-this prompts.
- `khan_url_for_selection("algebra_1", "Polynomial arithmetic")` and `Factoring basics` map to Khan polynomial/factoring material and still obey parent external-link and offline-mode settings.
- The broader Algebra 1 roadmap still has open work for summer-preview depth across linear relationships, functions, and sequences.

## Recently Added Algebra 1 Slope And Linear Inequalities

The stretch path now has explicit line-interpretation targets before systems and quadratics.

- `algebra_1` includes `Slope from points`, `Slope-intercept form`, and `Graphing linear inequalities` in the skill graph.
- Native quiz generation asks students to compute slope from two points, identify the y-intercept as the output at `x = 0`, and use a boundary line for two-variable linear inequalities.
- `explanation_for("algebra_1", "Slope from points")`, `Slope-intercept form`, and `Graphing linear inequalities` now give specific mental models, common mistakes, and try-this prompts.
- `khan_url_for_selection("algebra_1", "Slope from points")`, `Slope-intercept form`, and `Graphing linear inequalities` map to Khan line/inequality material and still obey parent external-link and offline-mode settings.
- The broader Algebra 1 roadmap still has open work for summer-preview depth across linear relationships, functions, and sequences.

## Immediate Next Feature Slice

Use the Texas Grade Goals catalog to drive fall readiness without losing the existing Summer Program guardrails.

1. Continue child-first UI polish only where it directly improves practice, intuition, or standards progress clarity while preserving complete parent assessment controls.
2. Use the parent School Year tools in real fall planning and keep packet history manageable through the archive workflow.
3. Keep the standards-spine audit green whenever Texas grade goals or skill mappings change.
4. Keep external lesson links controlled by the parent external-links setting.

## Summer Content Status

Resource Review no longer has content gaps for `prealgebra_finish`.

1. `linear_relationships_preview`, `functions_patterns_preview`, `geometry_measurement_preview`, and `coordinate_geometry_preview` all have importable template manifests; `algebra_1_preview_capstone` has its own importable manifest for Algebra 1 linear rows, and `geometry_preview_capstone` reuses ready geometry rows from the existing geometry manifests.
2. Core and preview rows now have the expression templates, word templates, scaffolded starts, native generators, intuition/help content, and parent-controlled links needed to render as `ready`.
3. Official `prealgebra_finish` completion rules remain unchanged while optional enrichment stays outside pace, catch-up, blocked-state, and exit requirements.
4. Parent tools can export/print the full Resource Review without changing student progress.

## Algebra And Geometry Expansion Targets

Add as much algebra and geometry as possible as optional summer enrichment, but keep the official pre-algebra finish definition unchanged.

Priority preview topics:

- Slope from tables, graphs, and coordinate pairs.
- Linear relationships and slope-intercept form.
- Function tables, function rules, and input/output notation.
- Arithmetic sequences and simple pattern generalization.
- Triangle area, parallelogram/rectangle area, and composite area.
- Circles: radius, diameter, circumference, and area.
- Pythagorean theorem as a visual/coordinate bridge.
- Coordinate geometry distance and midpoint.
- Transformations: translations, reflections, rotations, dilations.
- Similarity and scale factor.
- Mixed Algebra 1 and Geometry preview capstones for students who finish the official pre-algebra path and want more.

## Implementation Guardrails

- Keep Summer Program v1 local-only in `app.db`; do not extend sync payloads yet.
- Do not let optional preview units affect `prealgebra_finish` official completion, pace, catch-up, or blocked-state logic.
- Keep `foundation_bridge` conservative for the 6-year-old. Do not surface pre-algebra-only or algebra/geometry preview units there unless a later explicit parent override flow is added.
- Preserve the existing scaffolded question model for lessons and checkpoint starts.
- Every new math skill needs enriched intuition content: `Mental model`, `Common mistake`, and `Try this`.
- External lesson links must remain controlled by the parent external-links setting.
- Follow the project size rule: split heavily modified files when that clearly improves maintainability.

## Current Worktree Caution

The repo currently has a large dirty worktree, including many untracked app/test files from previous work. Do not assume `git diff` captures the full implemented feature state.

Important Summer Program files that may be untracked in this snapshot:

- `app/summer_program.py`
- `app/summer_program_defs.py`
- `app/summer_program_quiz.py`
- `tests/test_summer_program.py`

Tracked files recently touched include dashboard and renderer/resource-cleanup surfaces such as `app/ui_dashboard.py` and renderer-related code.

## Recommended Next Commands

For the next implementation thread, start with:

```bash
python -m unittest tests.test_summer_program tests.test_summer_program_templates tests.test_khan_subskill_links tests.test_summer_mode_ui_flow
python -m unittest discover -s tests
python -m app.main --smoke-test
```

After adding the Resource Review slice, also run:

```bash
python -m py_compile app/content_audit.py app/ui_parent.py tests/test_content_audit.py
python -m unittest tests.test_content_audit
```

Latest verification after Resource Review:

```bash
python -m py_compile app/content_audit.py app/summer_program_quiz.py app/ui_parent.py app/quiz_engine.py tests/test_content_audit.py
python -m unittest tests.test_content_audit
python -m unittest tests.test_summer_program tests.test_summer_program_templates tests.test_khan_subskill_links tests.test_summer_mode_ui_flow tests.test_content_audit
python -m unittest tests.test_quiz_engine_algebra_courses tests.test_quiz_engine_algebra_geometry tests.test_ui_quiz_subskill
python -m unittest discover -s tests
python -m app.main --smoke-test
```

Latest verification after linear relationships preview expansion:

```bash
python -m py_compile app/summer_program_template_seed.py app/summer_program_quiz.py tests/test_content_audit.py tests/test_summer_program_templates.py
python -m json.tool scripts/template_manifests/linear_relationships_preview_v1.json
python -m unittest tests.test_content_audit tests.test_summer_program_templates
python -m unittest tests.test_summer_program
python -m unittest tests.test_content_audit tests.test_summer_program tests.test_summer_program_templates tests.test_khan_subskill_links tests.test_summer_mode_ui_flow
python -m unittest tests.test_quiz_engine_algebra_courses tests.test_quiz_engine_algebra_geometry tests.test_ui_quiz_subskill
python -m app.main --smoke-test
python -m unittest discover -s tests
```

Full discovery passed 228 tests. The broad suite still emits existing SQLite `ResourceWarning` noise, but it exits successfully.

Latest verification after functions patterns preview expansion:

```bash
python -m py_compile app/summer_program_template_seed.py app/summer_program_quiz.py tests/test_content_audit.py tests/test_summer_program_templates.py
python -m json.tool scripts/template_manifests/functions_patterns_preview_v1.json
python -m unittest tests.test_content_audit tests.test_summer_program_templates
python -m unittest tests.test_summer_program
python -m unittest tests.test_quiz_engine_algebra_courses tests.test_summer_mode_ui_flow
python -m app.main --smoke-test
python -m unittest discover -s tests
```

The ad hoc fresh-database evaluator check instantiated all eight functions-pattern template modes and confirmed all four `functions_patterns_preview` Resource Review rows are `ready`. Full discovery passed 230 tests. The broad suite still emits existing SQLite `ResourceWarning` noise, but it exits successfully.

Latest verification after geometry measurement preview expansion:

```bash
python -m py_compile app/summer_program_seed_types.py app/summer_program_preview_template_seed.py app/summer_program_template_seed.py app/summer_program_quiz.py tests/test_content_audit.py tests/test_summer_program_templates.py
python -m json.tool scripts/template_manifests/geometry_measurement_preview_v1.json
python -m unittest tests.test_content_audit tests.test_summer_program_templates
python -m unittest tests.test_summer_program
python -m unittest tests.test_quiz_engine_algebra_geometry tests.test_summer_mode_ui_flow
python -m app.main --smoke-test
python -m unittest discover -s tests
```

The ad hoc fresh-database evaluator check instantiated all ten geometry-measurement template modes and confirmed all five `geometry_measurement_preview` Resource Review rows are `ready`. Full discovery passed 232 tests. The broad suite still emits existing SQLite `ResourceWarning` noise, but it exits successfully.

Latest verification after coordinate geometry preview expansion:

```bash
python -m py_compile app/summer_program_preview_template_seed.py app/summer_program_quiz.py tests/test_content_audit.py tests/test_summer_program_templates.py
python -m json.tool scripts/template_manifests/coordinate_geometry_preview_v1.json
python -m unittest tests.test_content_audit tests.test_summer_program_templates
python -m unittest tests.test_summer_program
python -m unittest tests.test_quiz_engine_algebra_geometry tests.test_summer_mode_ui_flow tests.test_khan_subskill_links
```

The ad hoc fresh-database evaluator check instantiated all ten coordinate-geometry template modes and confirmed all five `coordinate_geometry_preview` Resource Review rows are `ready`.

## Latest Algebra 1 Preview Capstone Slice

The optional `algebra_1_preview_capstone` unit now sits after the official `prealgebra_finish` exit path and remains outside core completion gates.

- Targets: `Slope from points`, `Functions`, `Slope-intercept form`, `Sequences`, `Graphing linear inequalities`, and `Solving equations & inequalities`.
- `scripts/template_manifests/algebra_1_preview_capstone_v1.json` records six importable template entries for the three Algebra 1 linear rows that were previously native-only in this summer-preview path.
- `app/summer_program_preview_template_seed.py` now seeds expression and word templates for those three Algebra 1 linear rows.
- The capstone checkpoint builds a mixed Algebra 1 quiz plan while preserving scaffolded lesson/checkpoint starts.
- Live Resource Review after `db.init_db()` reports `prealgebra_finish` as `38 ready`, `0 thin`, `0 missing` across `38` rows. All six capstone rows are `ready` with expression templates, word templates, native generators, scaffolded steps, intuition, Khan links, and open-resource links.

Latest verification after Algebra 1 preview capstone:

```bash
python -m json.tool scripts/template_manifests/algebra_1_preview_capstone_v1.json
python -m compileall app/summer_program_defs.py app/summer_program_quiz.py app/summer_program_preview_template_seed.py app/content_audit.py
python -m unittest tests.test_content_audit tests.test_summer_program_templates tests.test_summer_program
python -m unittest tests.test_quiz_engine_algebra_courses tests.test_explanations tests.test_khan_subskill_links tests.test_skill_graph_tracks tests.test_summer_mode_ui_flow
python -m unittest discover -s tests
python -m app.main --smoke-test
python -c "from app import db; from app.content_audit import summer_resource_review; from app.summer_program_defs import PREALGEBRA_FINISH_LANE; db.init_db(); r=summer_resource_review(PREALGEBRA_FINISH_LANE); print(r.ready_count, r.thin_count, r.missing_count, len(r.rows)); print([(row.subskill, row.readiness, row.expression_template_count, row.word_template_count, row.scaffold_step_count) for row in r.rows if row.unit_code == 'algebra_1_preview_capstone'])"
```

Full discovery passed 294 tests. The broad suite still emits existing SQLite `ResourceWarning` noise, but it exits successfully.

## Latest Geometry Preview Capstone Slice

The optional `geometry_preview_capstone` unit now sits after the official `prealgebra_finish` exit path and remains outside core completion gates.

- Targets: `Circumference and area of circles`, `Pythagorean theorem`, `Coordinate geometry distance and midpoint`, `Transformations and congruence`, and `Similarity and scale factor`.
- The capstone reuses the ready geometry preview template families from `geometry_measurement_preview_v1.json` and `coordinate_geometry_preview_v1.json` instead of adding duplicate manifest rows.
- The capstone checkpoint builds a mixed Geometry quiz plan while preserving scaffolded lesson/checkpoint starts.
- Live Resource Review after `db.init_db()` reports `prealgebra_finish` as `43 ready`, `0 thin`, `0 missing` across `43` rows. All five Geometry capstone rows are `ready` with expression templates, word templates, native generators, scaffolded steps, intuition, Khan links, and open-resource links.

Latest verification after Geometry preview capstone:

```bash
python -m compileall app/summer_program_defs.py app/summer_program_quiz.py tests/test_content_audit.py tests/test_summer_program.py tests/test_summer_mode_ui_flow.py
python -m unittest tests.test_content_audit tests.test_summer_program tests.test_summer_mode_ui_flow
python -m unittest tests.test_summer_program_templates tests.test_quiz_engine_algebra_geometry tests.test_khan_subskill_links tests.test_explanations tests.test_skill_graph_tracks
python -c "from app import db; from app.content_audit import summer_resource_review; from app.summer_program_defs import PREALGEBRA_FINISH_LANE; db.init_db(); r=summer_resource_review(PREALGEBRA_FINISH_LANE); print(r.ready_count, r.thin_count, r.missing_count, len(r.rows)); print([(row.subskill, row.readiness, row.expression_template_count, row.word_template_count, row.scaffold_step_count) for row in r.rows if row.unit_code == 'geometry_preview_capstone'])"
```

## Latest Foundation Measurement Scope Receipt

The roadmap item `Measurement: length, area, volume, time, temperature, unit conversion` is now closed from current evidence.

- `tests/test_foundation_measurement_scope.py` proves all measurement subskills are visible: length conversion, time arithmetic, capacity/weight, temperature, metric/customary conversion, and elapsed time.
- The same test proves each measurement subskill generates both multiple-choice and typed questions, has enriched intuition (`mental_model`, `common_mistake`, `try_this`), and has a parent-controlled Khan catalog link.
- Area and volume are covered through `geometry_area` with question generation and intuition for `Area of rectangles and squares`, `Area of triangles and parallelograms`, and `Surface area and volume`.

Latest verification after foundation measurement scope closure:

```bash
python -m unittest tests.test_foundation_measurement_scope
```

## Latest Pre-Algebra Scope Receipt

The roadmap item `Complete Pre-Algebra scope in roadmap with tests` is now closed from current evidence.

- `tests/test_pre_algebra_scope.py` groups the roadmap language into explicit subskills for integer/fraction fluency, order of operations, expressions/variables, one-step equations, two-step equations/inequalities, coordinate plane/function tables, ratios/rates/proportionality, percents, exponents/roots/scientific notation, and basic function-table work.
- The same test proves every Pre-Algebra subskill generates multiple-choice and typed questions, has enriched intuition, has a parent-controlled Khan catalog link, and has active seeded expression templates, with word templates required where the catalog says word mode is needed.
- Texas grades 5-7 are checked against the Pre-Algebra scope: Grade 5 coordinate-plane preview, Grade 6 proportionality/percent/expression/equation rows, and Grade 7 rational-operations rows all map into the expected subskills. Grade 5 order-of-operations coverage is verified through its companion `order_of_operations` goal.

Latest verification after Pre-Algebra scope closure:

```bash
python -m unittest tests.test_pre_algebra_scope
```

## Latest Algebra 1 Core Scope Receipt

The release checklist item `Complete Algebra 1 core scope in roadmap with tests` is now closed from current evidence.

- `tests/test_algebra_1_scope.py` maps the Algebra 1 roadmap language into explicit subskills for linear equations/inequalities, slope and y=mx+b intuition, systems, polynomials, quadratics, radicals/rational exponents, functions, sequences, transformations, exponential models, absolute value/piecewise functions, and irrational numbers.
- The same test proves every Algebra 1 subskill is visible in the skill graph, generates multiple-choice and typed questions, has subskill-specific enriched intuition, and exposes a parent-controlled Khan Academy link through the existing external-links/offline settings.
- Texas Grade 7 `g7_algebra1_stretch` is checked against the Algebra 1 scope so students who finish grade-level work can continue into functions, sequences, and linear equations/graphs.
- `app/explanations.py` now has specific Algebra 1 intuition entries for all 29 Algebra 1 subskills instead of falling back to generic Algebra 1 help for the remaining foundation, linear, function, exponential, and irrational-number topics.

Latest verification after Algebra 1 core scope closure:

```bash
python -m unittest tests.test_algebra_1_scope tests.test_quiz_engine_algebra_courses tests.test_explanations tests.test_khan_subskill_links tests.test_texas_grade_goals tests.test_skill_graph_tracks
```

## Latest Geometry Scope Receipt

The Geometry roadmap rows for proofs, polygons/circles/area/volume/coordinate geometry, and right-triangle trigonometry are now closed from current evidence.

- `tests/test_geometry_scope.py` maps the Geometry roadmap language into explicit geometry and trig subskills: area/perimeter families, circles, surface area/volume, Pythagorean theorem, coordinate distance/midpoint, angle facts, triangle congruence criteria, transformations/congruence, similarity, analytic coordinate proofs, and right-triangle trig ratios.
- `Triangle congruence criteria` is now a first-class `geometry_area` subskill in the skill graph and native quiz generator, covering SSS/SAS/ASA/AAS/HL proof-shortcut reasoning.
- The same test proves every Geometry and right-triangle-trig subskill generates multiple-choice and typed questions, has subskill-specific enriched intuition, and exposes a parent-controlled Khan Academy link through the existing external-links/offline settings.
- Texas grades 2-7 geometry goals are checked against the current geometry scope, including Grade 5 volume, Grade 6 trapezoid/composite area, and Grade 7 similarity/circle rows.

Latest verification after Geometry scope closure:

```bash
python -m unittest tests.test_geometry_scope tests.test_quiz_engine_algebra_geometry tests.test_explanations tests.test_khan_subskill_links tests.test_skill_graph_tracks tests.test_texas_measurement_data_coverage tests.test_summer_program_templates tests.test_content_audit
```

## Latest SQLite ResourceWarning Receipt

The release-checklist claim that test runs avoid unclosed SQLite handle warnings is now backed by live verification again.

- The lingering `ResourceWarning: unclosed database` noise came from test helper/readback code using `with sqlite3.connect(...) as conn`, which commits or rolls back but does not close the connection.
- `tests/test_early_math_coverage.py`, `tests/test_pedagogical_integrity.py`, and `tests/test_pre_algebra_scope.py` now wrap direct sqlite connections in `contextlib.closing(...)`.
- Full discovery with ResourceWarning enabled now exits cleanly with no `ResourceWarning` or `unclosed database` output.

Latest verification after SQLite warning cleanup:

```bash
python -W default::ResourceWarning -m unittest tests.test_early_math_coverage tests.test_pedagogical_integrity tests.test_pre_algebra_scope
python -W default::ResourceWarning -m unittest discover -s tests
```

## Latest Algebra 2 Scope Receipt

The Algebra 2 roadmap rows for functions, exponentials/logarithms, rational expressions, complex numbers, and sequences/series are now closed from current evidence.

- `tests/test_algebra_2_scope.py` maps the Algebra 2 roadmap language into explicit subskills for domain/range, inverse/composition, transformations, modeling, rational exponents/radicals, exponential models, logarithms, polynomial work, rational expressions/functions, complex numbers, and sequences/series.
- `app/algebra_2_generators.py` now exposes first-class native branches for `Domain and range`, `Inverse and composition`, `Rational expressions`, and `Sequences and series`, in addition to the existing Algebra 2 topics.
- Every Algebra 2 subskill now generates multiple-choice and typed questions, has subskill-specific enriched intuition, and exposes a parent-controlled Khan Academy link through the existing external-links/offline settings.
- `app/algebra_2_generators.py` remains under the 300-line target after the expansion.

Latest verification after Algebra 2 scope closure:

```bash
python -m unittest tests.test_algebra_2_scope tests.test_quiz_engine_algebra_courses tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links
```

## Latest Precalculus Scope Receipt

The Precalculus / Trig roadmap rows for unit-circle trig, trig graphs, identities, inverse trig, vectors, intro matrices, and polar coordinates are now closed from current evidence.

- `trig_right_triangle` is expanded into a full Precalculus track surface: right-triangle ratios, unit-circle trig values, trig functions/graphs, trig identities, inverse trig, vectors, matrices/linear transformations, and polar coordinates.
- `app/quiz_engine.py` now generates native multiple-choice and typed questions for each Precalculus subskill, while preserving right-triangle trig as the Geometry bridge topic.
- `app/explanations.py` provides subskill-specific Mental model, Common mistake, and Try this intuition for every Precalculus subskill.
- `app/ui_arithmetic.py` maps each Precalculus subskill to a parent-controlled Khan Academy route through the existing external-links/offline settings.
- `tests/test_precalculus_scope.py` pins the two roadmap rows to visible subskills and verifies generation, intuition, and lesson-link controls.

Latest verification after Precalculus scope closure:

```bash
python -m unittest tests.test_precalculus_scope tests.test_skill_graph_tracks tests.test_geometry_scope tests.test_explanations tests.test_khan_subskill_links tests.test_pedagogical_integrity
```

## Latest Calculus Scope Receipt

The Calculus roadmap rows for limits/continuity, derivative rules and slope/velocity intuition, integrals/accumulation/basic techniques, and applications are now closed from current evidence.

- `app/calculus_catalog.py` defines the expanded Calculus I, II, and III subskill surfaces plus parent-controlled Khan Academy routes and subskill-specific intuition text.
- `app/calculus_generators.py` generates native multiple-choice and typed questions for every Calculus subskill while preserving legacy default behavior for callers that do not request a subskill.
- `app/skill_graph.py`, `app/explanations.py`, and `app/ui_arithmetic.py` now consume the Calculus catalog for visible subskills, enriched intuition, and lesson links.
- `tests/test_calculus_scope.py` maps the four Calculus roadmap rows into explicit subskills and verifies generation, intuition, and external-link controls.
- New Calculus files remain under the 300-line target: 129 lines for `app/calculus_catalog.py`, 249 lines for `app/calculus_generators.py`, and 87 lines for `tests/test_calculus_scope.py`.

Latest verification after Calculus scope closure:

```bash
python -m unittest tests.test_calculus_scope tests.test_quiz_engine_calculus tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_pedagogical_integrity
```

## Latest Statistics Scope Receipt

The Statistics & Probability roadmap rows for data collection/distributions/standard deviation, probability/combinatorics/expected value, sampling/confidence intervals/hypothesis tests, and correlation/regression are now closed from current evidence.

- `app/statistics_catalog.py` defines the expanded composite Statistics subskills plus parent-controlled Khan Academy routes and subskill-specific intuition text.
- `app/statistics_generators.py` generates native multiple-choice and typed questions for every composite Statistics subskill while preserving existing template-first behavior when no specific subskill is requested.
- `statistics` is no longer treated as template-only in `app/quiz_content.py`; it is now native-intuition-capable while SAT/PSAT/GRE remain template-only.
- `app/skill_graph.py`, `app/explanations.py`, and `app/ui_arithmetic.py` now consume the Statistics catalog for visible subskills, enriched intuition, and lesson links.
- `tests/test_statistics_scope.py` maps the four Statistics roadmap rows into explicit `statistics`, `data_analysis`, and `stats_probability` subskills and verifies generation, intuition, and external-link controls.
- New Statistics files remain under the 300-line target: 95 lines for `app/statistics_catalog.py`, 191 lines for `app/statistics_generators.py`, and 86 lines for `tests/test_statistics_scope.py`.

Latest verification after Statistics scope closure:

```bash
python -m unittest tests.test_statistics_scope tests.test_data_analysis tests.test_skill_graph_tracks tests.test_explanations tests.test_khan_subskill_links tests.test_pedagogical_integrity
```

## Latest Blended Practice Policy Receipt

The Blended Practice roadmap rows for target/prerequisite/review composition, configurable `60/25/15` defaults, and adaptive prerequisite tuning are now closed from current evidence.

- `app/learning_engine.py` now exposes `BlendPolicyConfig`, defaults to `60/25/15`, normalizes custom policy inputs, and threads the optional config through `build_blended_plan`.
- `pick_blend_policy` now increases prerequisite share when the target skill is weak (`45/40/15` below 60% recent accuracy, `55/30/15` below 75%) and tapers prerequisite share when the target is stable (`70/15/15` above 85%).
- The prior review-floor behavior remains covered: when a review pool exists and the quiz is large enough, maintenance review still appears.
- `tests/test_learning_engine_signals.py` now proves default policy, adaptive bands, custom configurable defaults, and actual blended-plan label counts.

Latest verification after Blended Practice policy closure:

```bash
python -m unittest tests.test_learning_engine tests.test_learning_engine_signals tests.test_skill_graph_tracks tests.test_ui_quiz_subskill
```

## Latest Monthly Graph Tuning Receipt

The prerequisite-logic roadmap row for monthly graph tuning from real learner performance data is now closed from current evidence.

- `app/graph_tuning.py` adds a read-only monthly tuning workflow that consumes real `QuizAttempt` history, filters to a configurable recent window, evaluates target/prerequisite edge performance, and emits evidence-backed suggestions to increase, monitor, or taper prerequisite weights.
- The workflow returns structured `GraphTuningSuggestion` rows and a Markdown report via `render_monthly_graph_tuning_markdown`, so graph changes can be reviewed before any future manual update to `SKILL_PREREQUISITE_WEIGHTS`.
- The first-pass policy deliberately avoids automatic graph mutation; this keeps recommendations auditable and prevents hidden changes to student paths.
- `tests/test_graph_tuning.py` proves monthly-window filtering, weak-evidence increase suggestions, stable-evidence taper suggestions, and parent-reviewable Markdown output.
- New graph-tuning files remain under the 300-line target: 143 lines for `app/graph_tuning.py` and 84 lines for `tests/test_graph_tuning.py`.

Latest verification after monthly graph tuning closure:

```bash
python -m unittest tests.test_graph_tuning tests.test_learning_engine tests.test_learning_engine_signals
```

## Latest Fall Readiness Audit Receipt

The fall school-year objective now has a single app-level audit surface tying the implemented Grade 1-7 readiness work together.

- `app/fall_readiness_audit.py` builds a typed `FallReadinessReport` and Markdown receipt covering Texas Grade 1-7 catalog span, zero content gaps, typed question generation for grade-goal subskills, subskill intuition copy, per-child target APIs, assessment packet generation, stretch paths through advanced math, parent-controlled external lessons, adaptive blended practice, monthly graph tuning, and child-first `Bonus Explore` navigation.
- The audit uses the Texas Grade Goals source URL in `app/texas_grade_goals.py` and treats the official Grade 1-7 TEKS spine as the core fall readiness boundary; optional family sync and broader SAT/GRE historical corpus expansion remain separate roadmap work.
- `tests/test_fall_readiness_audit.py` proves the report is ready, two child profiles can hold independent Texas grade targets and next-goal paths, and both Grade 1 and Grade 7 assessment packets generate questions plus answer keys.
- New files stay under the project file-size target: `app/fall_readiness_audit.py` is 262 lines and `tests/test_fall_readiness_audit.py` is 95 lines.

Latest verification after the fall readiness audit:

```bash
python -m compileall app/fall_readiness_audit.py tests/test_fall_readiness_audit.py
python -m unittest tests.test_fall_readiness_audit
python -m unittest tests.test_fall_readiness_audit tests.test_texas_standards_audit tests.test_texas_grade_goals tests.test_school_year tests.test_summer_mode_ui_flow tests.test_learning_engine_signals tests.test_graph_tuning
python -W default::ResourceWarning -m unittest discover -s tests
python -m app.main --smoke-test
rg -n "[ \t]+$" app/fall_readiness_audit.py tests/test_fall_readiness_audit.py TODO.md CONTINUITY.md
git diff --check -- TODO.md app/fall_readiness_audit.py tests/test_fall_readiness_audit.py
```

Full discovery passed 332 tests with no `ResourceWarning` or `unclosed` output in `/tmp/mandelbrot_full_warn.log`.

## Latest Family Sync Boundary Receipt

Family Sync remains an operator-configured beta, not a normal v1 promise. Local-only is the default: public config has no server URL, sync state defaults off, and Parent tools cannot enable the beta until `MANDELQUEST_SYNC_CONFIG` supplies a compatible endpoint. The UI, README, privacy page, support page, release checklist, and TODO now use that boundary consistently. The client syncs profiles, quiz sets, assignments, completed attempts, and question history; sensitive/device-specific settings, worksheets, Summer Program and school-year state, derived progress, and in-progress resume state stay local. No server ships in this repo, and two-device/conflict/migration testing remains required before broader release.

## Latest Family Sync Settings Flow Receipt

The parent-only Family Sync settings flow is now accessible as its own `Family Sync` tab instead of being
buried below the Profile controls.

- `app/ui_family_sync.py` owns the optional device toggle, family start/join controls, pairing-code display,
  status/error copy, and the manual `Sync now` action while continuing to call the existing `app/sync_*`
  service, state, config, and store boundaries.
- The tab explains in plain language that family profiles, saved quiz sets and assignments, and completed
  quiz questions/answers/results may be shared. Parent PIN, app/offline settings, worksheet/PDF files,
  Summer Program and school-year plans, derived progress summaries, and unfinished quizzes stay local.
- Public builds remain local-only and cannot turn sync on without an operator-supplied config. Child profiles
  cannot manage the controls, and turning sync off preserves the existing family link while preventing manual
  sync actions.
- `tests/test_family_sync_ui_copy.py` covers the public/local-only gate, parent enable -> link -> manual sync ->
  disable flow, saved-link preservation, privacy copy, and the child-profile management guard.
- The extracted UI module is 266 lines, below the project 300-line target; the sync backend contracts were not
  changed in this slice.

Focused verification passed:

```bash
python -m py_compile app/ui_family_sync.py app/ui_parent.py app/ui_root.py tests/test_family_sync_ui_copy.py
python -W default::ResourceWarning -m unittest tests.test_sync_config tests.test_sync_state tests.test_sync_store tests.test_sync_client tests.test_sync_service tests.test_family_sync_ui_copy
python -m unittest tests.test_summer_mode_ui_flow.SummerModeUiFlowTests.test_normal_child_layout_keeps_parent_and_fractal_secondary
python -m app.main --smoke-test
```

The focused sync run passed 23 tests, the child-shell parent-tab boundary passed 1 test, and the smoke test
reported `[smoke-test] OK`.

## Latest Family Sync Database Migration Receipt

Pre-sync `app.db` adoption now has a frozen schema-v11 fixture and an end-to-end regression seam.

- Schema v17 backfills one idempotent outbox upsert for every existing, active canonical sync row that has no
  prior outbox history. The dependency order is profiles, quiz sets, assignments, completed attempts, then
  question history.
- Migration does not enable Family Sync, create a sync-state file, or make a network call. Parent PIN data,
  worksheets, derived progress, and unfinished-quiz state remain local and are preserved by the fixture test.
- If a parent enables and pairs Family Sync later, the normal `sync_service.sync_now()` path uploads the
  migrated canonical rows with their new stable UUID relationships; running database initialization again
  does not duplicate the migration outbox entries.
- `tests/fixtures/pre_sync_app_db_v11.sql` is a small, reviewable legacy snapshot, and
  `tests/test_db_sync_migration.py` covers both the default-off upgrade and later-enabled upload paths.

Verification passed:

```bash
python -m py_compile app/db.py tests/test_db_sync_migration.py
python -W default::ResourceWarning -m unittest -v tests.test_db_sync_migration tests.test_db_parent_auth_and_progress tests.test_db_assignment_semantics tests.test_sync_config tests.test_sync_state tests.test_sync_store tests.test_sync_client tests.test_sync_service tests.test_family_sync_ui_copy
python -W default::ResourceWarning -m unittest discover -s tests
python -m app.main --smoke-test
```

The focused DB/sync/UI run passed 35 tests, full discovery passed 341 tests, and the smoke test reported
`[smoke-test] OK`.

## Latest PR1 Database Split Pre-work Receipt

The behavior-preserving guardrails required before splitting `app/db.py` are now implemented.

- `app.db` owns one typed, provider-backed configuration source exposed through `get_db_config()`,
  `set_db_config()`, `reset_db_config()`, and the nesting-safe `override_db_config()` context manager.
  Existing `db_config()` callers remain supported, while test overrides no longer replace the facade
  function directly.
- All existing temp-database tests now use `override_db_config()`, preserving their isolation contract and
  preparing them for an `app/db/` package facade whose re-exports cannot be safely monkeypatched by assignment.
- `app.db.__all__` freezes 88 public exports and `app.quiz_engine.__all__` freezes 12 public exports, including
  `ContentUnavailableError` and the externally imported subskill constants.
- `tests/test_db_split_contract.py` pins both inventories, imports the broader sync, summer, school-year,
  content-audit, dashboard, skill-map, and script consumer surfaces, and proves schema plus sync-consumer writes
  use the temporary override without changing the default database path.

Verification passed:

```bash
python -m unittest -q tests.test_db_parent_auth_and_progress tests.test_db_assignment_semantics tests.test_db_sync_migration tests.test_sync_store tests.test_sync_service tests.test_summer_program tests.test_summer_program_templates tests.test_school_year tests.test_fall_readiness_audit tests.test_content_audit tests.test_mastery_truthfulness
python -m unittest -q tests.test_db_split_contract tests.test_db_parent_auth_and_progress tests.test_db_assignment_semantics tests.test_db_sync_migration tests.test_sync_store tests.test_sync_service tests.test_summer_program tests.test_summer_program_templates tests.test_school_year tests.test_fall_readiness_audit tests.test_content_audit tests.test_mastery_truthfulness
python -m app.main --smoke-test
python -m unittest discover -s tests -q
```

The untouched baseline consumer run passed 65 tests; the post-change consumer/contract run passed 68 tests;
the app smoke test reported `[smoke-test] OK`; and full discovery passed 347 tests.

## Latest PR1 Database Package Split Receipt

The first god-file split is complete and behavior-preserving.

- The verified pre-split product state is checkpointed on branch
  `codex/worktree-checkpoint-2026-07-13` at commit `9fb3665`.
- The former 3,058-line `app/db.py` monolith is replaced by an explicit `app/db/` package. Its static
  `__init__.py` facade preserves all 88 frozen exports, while 19 implementation modules separate connection,
  schema, migration, profile/auth, quiz, progress, historical/template, worksheet/assignment, and Summer
  Program concerns.
- Every DB package file is at or below 290 lines. `migrations.py` is 290 lines, `schema.py` is 283, and
  `migration_helpers.py` is 262, resolving the migration-size concern without a `>400`-line exception.
- The shared config provider remains owned by `connection.py`; all domain modules import the same
  `managed_connection()` boundary, so scoped test overrides cannot fall through to the default database.
- Static equivalence checks confirm all 82 public function signatures and all 153 SQL literals match the
  checkpoint source exactly. No SQL literal was added or removed.

Verification passed:

```bash
python -m py_compile app/db/*.py
python -m unittest -q tests.test_db_split_contract tests.test_db_parent_auth_and_progress tests.test_db_assignment_semantics tests.test_db_sync_migration tests.test_sync_store tests.test_sync_service tests.test_summer_program tests.test_summer_program_templates tests.test_school_year tests.test_fall_readiness_audit tests.test_content_audit tests.test_mastery_truthfulness
python scripts/template_catalog.py --help
python scripts/import_template_manifest.py --help
python scripts/ingest_textbook.py --help
python -m app.main --smoke-test
python -m unittest discover -s tests -q
```

The broad DB-consumer set passed 68 tests, all three script smokes passed, app smoke reported
`[smoke-test] OK`, and full discovery passed 347 tests.
