# MandelQuest — Code Review TODO

Actionable checklist derived from the [code review](file:///home/user/.gemini/antigravity/brain/ad6fa51d-0ca3-43f6-8e52-a4ad6444f55a/code_review.md). Items are grouped by review area and ordered by priority within each section.

---

## 1. Fractal Rendering

### 🔴 High Priority
- [ ] **F10 — Palette selector in UI** — Add a `ttk.Combobox` to [ui_fractals.py](file:///home/user/projects/mandelbrot_fortran/app/ui_fractals.py) bound to `self.palette` with values `["rgb", "gray", "sunset", "ice", "fire"]`. Wire to `self.render()` on change.
- [ ] **F11 — Julia parameter sliders** — Add `julia_cx` / `julia_cy` `ttk.Scale` widgets (range −2.0 to 2.0). Show/hide them when `fractal_type == "julia"`. Wire to `self.render()`.

### 🟡 Medium Priority
- [ ] **F1 — Raise escape radius** — In [mandelbrot.f90](file:///home/user/projects/mandelbrot_fortran/src/mandelbrot.f90) `render_frame`, change `abs(z) <= 2.0` to `abs(z) <= 256.0` for smoother gradients with smooth coloring enabled.
- [ ] **F4 — Pre-compute palette LUT** — In `color_pixel`, build a `rgb_lut(0:max_iter)` array once before the render loop. Index into it per-pixel instead of computing trig per pixel.
- [ ] **F5 — Support PNG output** — Add a C helper using `stb_image_write.h` or `libpng` to write PNG. Update `save_high_res` to default to PNG and add a file dialog for path selection.
- [ ] **F7 — Replace busy-wait polling** — In [fractal_renderer.py](file:///home/user/projects/mandelbrot_fortran/app/fractal_renderer.py) `_run_with_cancel`, replace `sleep(0.05)` loop with `proc.communicate()` on a secondary thread + cancel-event check.
- [ ] **F9 — Cache unchanged renders** — Hash `FractalConfig` fields. Skip `render_ppm` call if the hash matches the last completed render.
- [ ] **F12 — Use Pillow for image loading** — Replace `tk.PhotoImage(data=data)` with `PIL.Image.open(BytesIO(data))` → `ImageTk.PhotoImage` for robustness and PNG support.
- [ ] **F13 — File save dialog** — Replace hardcoded `"saved_fractal.ppm"` with `tkinter.filedialog.asksaveasfilename()`.
- [ ] **F14 — Re-render on resize** — Bind `<Configure>` on the canvas and debounce a re-render when the view panel size changes.

### 🟢 Low Priority
- [ ] **F2 — Cache `z*z` in Celtic branch** — Store `z_sq = z*z` before the `cmplx(abs(real(z_sq)), aimag(z_sq), …)` call.
- [ ] **F3 — Add SIMD hints** — Experiment with `!$omp simd` on the inner width loop. Benchmark before/after.
- [ ] **F6 — Fix help text** — Update `print_help` in [cli.f90](file:///home/user/projects/mandelbrot_fortran/src/cli.f90) to list `celtic` and `perpendicular` as valid `--type` values.
- [ ] **F8 — Fix timeout drift** — Replace `waited += interval` with `time.monotonic()` start/current delta.

---

## 2. Math Sequencing

### 🔴 High Priority
- [ ] **M1 — Refactor `render_arithmetic()` dispatch** — In [arithmetic_render.py](file:///home/user/projects/mandelbrot_fortran/app/arithmetic_render.py), replace the 363-line if/elif chain with a `SKILL_RENDERERS: dict[str, Callable]` dispatch table mapping each skill to a dedicated `_render_<skill>(panel)` function.
- [ ] **M3 — Improve algebra linear visualization** — Replace the single horizontal line with a proper balance-scale visual: two pans with blocks representing terms, animated transfer showing the solve steps (`ax + b = c` → `ax = c − b` → `x = (c − b)/a`).
- [ ] **M11 — Fix multiplication partial alignment** — In [arithmetic_long.py](file:///home/user/projects/mandelbrot_fortran/app/arithmetic_long.py) `_multiplication_partials`, each partial product should be right-justified with trailing zeros matching its place value (e.g., `120` not `12` for tens digit). Align partials visually like pencil-and-paper long multiplication.
- [ ] **M12 — Add long division work steps** — Extend `draw_long_division` to show iterative bring-down / multiply / subtract steps. Each step should show: (a) top quotient digit, (b) partial product below dividend segment, (c) subtraction line, (d) remainder carried to next digit.
- [ ] **M14 — Split `ui_quiz.py` into modules** — Extract from [ui_quiz.py](file:///home/user/projects/mandelbrot_fortran/app/ui_quiz.py):
  - [ ] `quiz_flow.py` — state machine (start, show question, submit, next, finish)
  - [ ] `quiz_history.py` — historical test PDF ingestion and browsing
  - [ ] `quiz_strategies.py` — question generation per strategy
  - [ ] Keep `ui_quiz.py` as thin view layer importing from the above
- [ ] **M15 — Extract quiz strategy builders** — From `start_quiz()`, extract each strategy branch into its own function:
  - [ ] `_build_focused_questions()`
  - [ ] `_build_learning_blend_questions()`
  - [ ] `_build_free_mode_questions()`
  - [ ] `_build_sat_psat_questions()`
  - [ ] `_build_historical_questions()`

### 🟡 Medium Priority
- [ ] **M2 — Add division to order-of-operations** — Update `_safe_eval_order` to support `/` (integer division with `//`). Add it to the operation dropdowns in `_build_integer_like`.
- [ ] **M4 — Step-by-step animation for long arithmetic** — Add a "Show Steps" button that reveals carries/borrows/partial products one at a time using `canvas.after()` delays. Start with long addition as the simplest case.
- [ ] **M6 — Fix ratio bar positioning** — In [arithmetic_draw.py](file:///home/user/projects/mandelbrot_fortran/app/arithmetic_draw.py) `draw_ratio_bars`, derive bar Y positions from `bounds` proportionally instead of hardcoded `y + 20` / `y + 60`.
- [ ] **M9 — Handle negative bar chart values** — In `draw_bar_chart`, draw negative bars below the baseline with a different color. Add a zero-line marker.
- [ ] **M10 — Cache `tkfont.Font` objects** — In [arithmetic_long.py](file:///home/user/projects/mandelbrot_fortran/app/arithmetic_long.py) `_fonts`, cache created `Font` objects in a module-level dict keyed by `(family, size)`.
- [ ] **M16 — Auto-save partial quiz attempts** — On each answer submission, persist intermediate progress to the DB. Allow resuming incomplete quizzes from the dashboard.

### 🟢 Low Priority
- [ ] **M5 — Clean up trig label formatting** — Extract line 305's f-string logic into a `_trig_label(ratio, a, b, c) -> str` helper function.
- [ ] **M7 — Add ratio bar legend** — Add inline color-coded labels ("A" / "B") next to each ratio bar.
- [ ] **M8 — Triangle inequality validation** — In `draw_right_triangle`, check `a + b > c` and show a warning label if violated.
- [ ] **M13 — Fix fraction arc overlaps** — Use `outline=""` on interior arcs and draw separator lines explicitly.

---

## 3. UI Aesthetics

### 🔴 High Priority
- [ ] **U1 — Apply modern Ttk theme** — In [ui_root.py](file:///home/user/projects/mandelbrot_fortran/app/ui_root.py) `__init__`, add:
  ```python
  style = ttk.Style()
  style.theme_use('clam')
  # Override key styles: TButton, TNotebook.Tab, TProgressbar, etc.
  ```
  Define accent colors, fonts, and padding overrides for a polished look.
- [ ] **U5 — Centralize color/theme constants** — Create a new file `app/theme.py` with:
  - [ ] `COLORS` dict (background, accent, mastery levels, skill-specific accents)
  - [ ] `FONTS` dict (heading, body, mono, small)
  - [ ] Replace all hardcoded hex colors across `ui_dashboard.py`, `ui_skill_map.py`, `arithmetic_draw.py`, etc.
- [ ] **U13 — Move Khan socket check off main thread** — In [ui_arithmetic.py](file:///home/user/projects/mandelbrot_fortran/app/ui_arithmetic.py), run `_can_reach_khan()` via `ThreadPoolExecutor`. Show "Checking…" text while pending. Update button state on completion via `widget.after()`.
- [ ] **U14 — Group quiz controls into sections** — In [ui_quiz.py](file:///home/user/projects/mandelbrot_fortran/app/ui_quiz.py) `_build_controls`, wrap related widgets in `ttk.LabelFrame`:
  - [ ] "Skill Selection" (track, skill, subskill, curriculum)
  - [ ] "Historical Tests" (combo, ingest buttons, filters)
  - [ ] "Quiz Settings" (question type, strategy, num questions, level)
- [ ] **U15 — Visual correct/incorrect feedback** — On answer submission:
  - [ ] Flash the answer widget border green (correct) or red (incorrect)
  - [ ] Add a brief celebratory animation for correct answers (e.g., bouncing ✓ or confetti dots on canvas)
  - [ ] Consider a streak counter with visual flair for consecutive correct answers

### 🟡 Medium Priority
- [ ] **U2 — App icon and branding** — Generate a small fractal icon. Set via `root.iconphoto()`. Consider a brief splash screen or animated title.
- [ ] **U3 — Responsive geometry** — Replace fixed `1200x720` with `root.minsize(960, 600)` + let geometry expand naturally. Test on 1080p and 1440p.
- [ ] **U4 — Keyboard shortcuts** — Bind:
  - [ ] `Ctrl+1` through `Ctrl+6` for tab switching
  - [ ] `Return` to submit quiz answer
  - [ ] `+` / `-` for fractal zoom (when fractal tab active)
  - [ ] `Escape` to cancel in-progress render
- [ ] **U6 — Color-coded progress bars** — Style `TProgressbar` per mastery level (green=mastered, amber=developing, red=needs-work) in the dashboard.
- [ ] **U8 — Incremental skill map updates** — In [ui_skill_map.py](file:///home/user/projects/mandelbrot_fortran/app/ui_skill_map.py), on click, update node fill/outline via `canvas.itemconfigure()` instead of full `self.render()`.
- [ ] **U12 — Per-skill accent colors** — Define a color map in `theme.py` (e.g., `counting=#5b8def`, `multiply=#67b26f`, `divide=#f2b05e`). Apply in arithmetic drawing functions.
- [ ] **U16 — Async PDF ingestion** — In `ui_quiz.py`, run `subprocess.run` for PDF ingestion via `ThreadPoolExecutor`. Show a progress indicator and re-enable buttons on completion.

### 🟢 Low Priority
- [ ] **U7 — Replace emoji streaks** — Replace 🔥/⬜ in `_streak_graph` with Unicode block chars (`▓`/`░`) or small canvas-drawn progress pips for cross-platform consistency.
- [ ] **U9 — Auto-size skill map labels** — Abbreviate long skill labels or auto-expand node rectangles to fit text width.
- [ ] **U10 — Skill map zoom/pan** — Add a zoom slider and drag-to-pan (translate canvas scroll region).
- [ ] **U11 — Canvas border differentiation** — Add a 1px `#e0e0e0` border or use `bg="#f0f0f0"` on arithmetic canvas to distinguish from surrounding frame.

---

## Implementation Order (Suggested)

> [!TIP]
> Start with the theme/color centralization (U5, U1) since it touches every UI file and should be done before other visual changes to avoid rework.

1. **Foundation** — `app/theme.py` (U5) → apply theme (U1) → responsive geometry (U3)
2. **Fractal UX** — palette selector (F10) → Julia sliders (F11) → file dialog (F13) → resize handler (F14)
3. **Math pedagogy** — long division steps (M12) → multiplication alignment (M11) → algebra balance (M3) → step-by-step animation (M4)
4. **Code structure** — `render_arithmetic` dispatch (M1) → split `ui_quiz.py` (M14, M15) → quiz control grouping (U14)
5. **Engagement** — visual feedback (U15) → per-skill colors (U12) → progress bar styling (U6)
6. **Threading fixes** — Khan check (U13) → PDF ingestion (U16) → render polling (F7)
7. **Performance** — palette LUT (F4) → escape radius (F1) → font caching (M10) → render caching (F9)
8. **Polish** — keyboard shortcuts (U4) → app icon (U2) → ratio bars (M6, M7) → fraction arcs (M13) → skill map UX (U8–U10)
