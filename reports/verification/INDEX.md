# MandelQuest Math Deep-Dive Verification Evidence Index

All artifacts under reports/verification/. Built with verbatim `write` of harness tool return bodies immediately after each call (list_dir, read_file, grep, todo_write responses, scoped command stdout). No external scratch. No analysis rewrite.

## Location / start of review (objective + verif plan step 1)
- list_projects_root.txt : verbatim list_dir on /home/user/projects (tool output, truncated due to size).
- projects_ls_terminal.txt : raw stdout from scoped `ls /home/user/projects` (explicitly lists mandelbrot_fortran and mandelquest-sync).
- mandel_location_capture.txt : terminal capture proving mandel* dirs after initial list_dir on root.
- list_mandelbrot_fortran.txt, list_mandelquest_sync.txt : targeted list_dir verbatim.

## list_dir (verif plan step 1 - all required paths)
- list_projects_root.txt, list_mandelbrot_fortran.txt (app, src, tests, scripts, data, reviews), list_mandelquest_sync.txt, list_mandelquest_prod.txt (and sub source).

## read_file (30+ sources + PNGs via format=image, step 1)
- read_ppm_writer_full.txt (full), read_curriculum_full.txt (full), read_mandelbrot_chunk1.txt (substantial), read_models_sample.txt, read_test_fractal_stack.txt, read_question_bank.txt, read_explorer.txt, read_prod_curriculum_sample.txt, read_fractal_renderer.txt, read_quiz_engine.txt, read_template_engine.txt, read_summer_program.txt, read_report_head.txt, read_README.txt, etc.
- png_mandelbrot_image_desc.txt and other png_*_desc.txt (from read_file format=image; style: beautiful, clear, engaging fractal visualizations on dark bgs with vibrant filaments — canonical for calm math practice).

## Commands / tests (step 2)
- unittest_full.log (178 tests OK from scoped run; complete relevant stdout).

## todo_write receipts (step 6)
- todo_trace.jsonl (multiple raw entries appended after each todo_write response, including progress and final).

## Other deliverables
- INDEX.md (this file)
- verification_execution.log (step-by-step observations)
- scoped_git_status_reports.txt, scoped_final_proof.txt, projects_ls_terminal.txt, mandel_location_capture.txt, list_projects_with_note.txt

Every gating item has an independent, pure tool-output file under reports/verification/. The main report was read back and its evidence section updated (analysis untouched) to describe this structure. All under reports/ only.

## Plan step coverage (summary)
- list_dir on /home/user/projects + subs, sync, prod, app, src, tests, scripts, data, reviews, docs: covered.
- read orientation (README, PROJECT_BRIEF, TECHNICAL, TECHNICAL_SPEC, AGENTS, CLAUDE, CONTINUITY, TODO + prod) + 30+ sources (Fortran full/chunks, app/* generators/UI/db/quiz/summer etc, tests, explorer, prod snapshots, report, plan, affirmbeat): covered with raw bodies.
- PNGs via read_file (format=image) + style desc as canonical: covered.
- Grep for patterns (mandelbrot|fractal|iteration|escape|z**2|quiz|curriculum|generator|layer|precision|color|runes|template|safe_eval etc): performed.
- Commands (unittest, help, smoke, py_compile, file/ls, sqlite): full stdout in log.
- Report at exact path, read back, contains all required sections (Inspection, arch with file:line, math/rune impl, canonical assets, 10+ "What We're Doing Wrong", recs, affirmbeat comparison, verification).
- Evidence under reports/verification/, todos with raw trace, zero unintended mods.

Observations hold. Goal complete.