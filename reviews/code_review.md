# Code Review: MandelQuest

Comprehensive review of the MandelQuest codebase covering **fractal rendering**, **math sequencing**, and **UI aesthetics**.

---

## 1. Fractal Rendering

### Fortran Engine — [mandelbrot.f90](file:///home/user/projects/mandelbrot_fortran/src/mandelbrot.f90)

**Strengths**
- Clean `render_frame` / `color_pixel` separation
- OpenMP parallelization with `schedule(dynamic)` — good for uneven workloads
- Multiple fractal types (7 variants) and 5 color palettes
- Proper `implicit none`, `real64` precision, and safe path checking

**Suggestions**

| # | Issue | Suggestion | Severity |
|---|-------|------------|----------|
| F1 | **Escape radius of 2.0 is tight for smooth coloring** | Smooth coloring formula `1 − log(log(|z|))/log(2)` converges poorly when `|z|` barely exceeds 2. Raise bailout to **256.0** (or at least **4.0**) for visibly smoother gradients. | Medium |
| F2 | **`z*z` computed twice in Celtic branch** | Lines 282: `z = cmplx(abs(real(z*z)), aimag(z*z), …) + c` — `z*z` is evaluated twice per iteration. Store `z_sq = z*z` and reuse. At deep zooms with 1000+ iterations this matters. | Low |
| F3 | **No SIMD / loop unrolling hints** | The inner pixel loop (lines 259–293) could benefit from `!$omp simd` on the width loop or Fortran `do concurrent`. Profile before acting, but this is the tightest hot loop. | Low |
| F4 | **Palette `color_pixel` is called per-pixel; could be a lookup table** | For non-cyclic coloring, pre-compute a 1D palette array of size `max_iter` and index into it, avoiding the string comparison and trig math per pixel. | Medium |
| F5 | **PPM output is uncompressed** | PPM files for 1920×1080 are ~6 MB. Consider supporting PNG output (via a small C wrapper to `libpng` or `stb_image_write.h`). This would also let `save_high_res` skip the PPM-to-PhotoImage round-trip. | Medium |
| F6 | **Help text doesn't mention `celtic` or `perpendicular`** | [cli.f90](file:///home/user/projects/mandelbrot_fortran/src/cli.f90) line 88 lists `mandelbrot|julia|ship|tricorn|multibrot` but the code also supports `celtic` and `perpendicular`. | Low |

---

### Python Bridge — [fractal_renderer.py](file:///home/user/projects/mandelbrot_fortran/app/fractal_renderer.py)

| # | Issue | Suggestion | Severity |
|---|-------|------------|----------|
| F7 | **Busy-wait polling with `sleep(0.05)`** | `_run_with_cancel` polls in a tight loop with 50 ms sleeps. Consider using `proc.communicate()` in a secondary thread or `selectors` for I/O-driven waiting. The current approach wastes CPU and adds up to 50 ms latency. | Medium |
| F8 | **`waited` drift** | `waited += interval` accumulates floating-point drift over long renders. Use `time.monotonic()` for accurate timeout enforcement. | Low |
| F9 | **No caching of unchanged renders** | When the user merely re-focuses the window, `render()` re-invokes the Fortran binary even if nothing changed. A simple hash of the `FractalConfig` could skip redundant work. | Medium |

---

### Fractal UI — [ui_fractals.py](file:///home/user/projects/mandelbrot_fortran/app/ui_fractals.py)

| # | Issue | Suggestion | Severity |
|---|-------|------------|----------|
| F10 | **No palette selector in the UI** | The Fortran engine supports 5 palettes (`rgb`, `gray`, `sunset`, `ice`, `fire`) but the Python UI hard-codes `self.palette = "rgb"` (line 26). Add a Combobox so users can choose palettes. | **High** |
| F11 | **No Julia parameter sliders** | `julia_cx` and `julia_cy` are fixed at -0.8 / 0.156. When `fractal_type == "julia"`, expose these as sliders so users can explore the Julia family. | **High** |
| F12 | **PhotoImage from raw PPM bytes** | `tk.PhotoImage(data=data)` works for PPM but is fragile — it silently fails if the data is malformed. Wrapping this in a `PIL.Image.open(BytesIO(data))` → `ImageTk.PhotoImage` would be more robust and let you support PNG natively. | Medium |
| F13 | **Save always writes to `saved_fractal.ppm`** | No file dialog — overwrites the same file every time. Use `tkinter.filedialog.asksaveasfilename()` and let the user pick the path and format. | Medium |
| F14 | **Canvas not resized on window resize** | No `<Configure>` binding to re-render when the view panel resizes. After a resize the image sits at the old resolution with black borders. | Medium |

---

## 2. Math Sequencing

### Arithmetic Render Pipeline — [arithmetic_render.py](file:///home/user/projects/mandelbrot_fortran/app/arithmetic_render.py)

**Strengths**
- Covers a wide skill curriculum (counting through calculus slope)
- Clean delegation to specialized drawing functions
- Order-of-operations evaluator handles grouping correctly

**Suggestions**

| # | Issue | Suggestion | Severity |
|---|-------|------------|----------|
| M1 | **Single monolithic dispatcher function (363 lines)** | `render_arithmetic()` is one giant if/elif chain. Refactor to a dispatch dict mapping `skill → render_function`, e.g. `SKILL_RENDERERS = {"counting": _render_counting, …}`. This improves readability and testability. | **High** |
| M2 | **`_safe_eval_order` only supports `+`, `-`, `*`** | Division is conspicuously absent for order-of-operations practice. Add `/` (integer division) to round out the curriculum. | Medium |
| M3 | **Algebra visualization is minimal** | `algebra_linear` draws only a horizontal line labeled "Balance point intuition" and some text. This doesn't teach the balance/scale metaphor effectively. Consider a proper visual balance (two pans, blocks representing terms) or at minimum a step-by-step solve animation. | **High** |
| M4 | **No animation / step-by-step reveal** | Long addition, multiplication, and division show the final result immediately. A step-by-step animation (revealing carries/borrows one at a time) would dramatically improve the learning experience. | Medium |
| M5 | **Trig expression formatting is convoluted** | Line 305 builds a complex f-string with nested ternaries. Extract to a helper function `_trig_label(ratio, a, b, c)`. | Low |

---

### Drawing Primitives — [arithmetic_draw.py](file:///home/user/projects/mandelbrot_fortran/app/arithmetic_draw.py)

| # | Issue | Suggestion | Severity |
|---|-------|------------|----------|
| M6 | **Ratio bars have hard-coded Y offsets** | `draw_ratio_bars` uses `y + 20` and `y + 60` magic numbers. These break when the bounds are small. Derive positions from `bounds` proportionally. | Medium |
| M7 | **No label/legend on ratio bars** | The bars show numbers but not which color corresponds to A vs. B. Add a small legend or inline label. | Low |
| M8 | **`draw_right_triangle` doesn't enforce triangle inequality** | If the user enters sides `(1, 1, 100)`, the visual still draws a triangle. Add validation or at least a warning label. | Low |
| M9 | **Bar chart doesn't handle negative values** | `draw_bar_chart` clamps fractions to `max(0.0, ...)`, which silently hides negative bars. For integer operations that produce negative results, this swallows data. | Medium |

---

### Long Arithmetic — [arithmetic_long.py](file:///home/user/projects/mandelbrot_fortran/app/arithmetic_long.py)

| # | Issue | Suggestion | Severity |
|---|-------|------------|----------|
| M10 | **Font objects created on every render** | `_fonts()` creates `tkfont.Font()` objects each call. Tkinter `Font` objects register with Tcl and should be cached or reused. | Medium |
| M11 | **Multiplication partials aren't right-justified with place-value offset** | `_multiplication_partials` returns raw strings like `["120", "400"]` but doesn't shift them by place value visually (e.g., `120` should appear shifted one column left). The visual therefore doesn't match pencil-and-paper layout. | **High** |
| M12 | **Division doesn't show work steps** | `draw_long_division` shows `divisor)dividend` and the quotient, but omits the standard subtraction steps (bring down, subtract partial products). This is the core pedagogical value of long division. | **High** |

---

### Fractions — [arithmetic_fractions.py](file:///home/user/projects/mandelbrot_fortran/app/arithmetic_fractions.py)

| # | Issue | Suggestion | Severity |
|---|-------|------------|----------|
| M13 | **Arc slices can overlap visually at small radii** | When denominator is large (e.g., 12) and the circle is small, the outline strokes between arcs overlap. Use `outline=""` on interior arcs and draw separating lines explicitly. | Low |

---

### Quiz & Learning Engine (sequencing)

| # | Issue | Suggestion | Severity |
|---|-------|------------|----------|
| M14 | **`ui_quiz.py` is 1009 lines** | This file does question generation, UI rendering, quiz flow, scoring, history, PDF ingestion, and more. Break into `quiz_flow.py` (state machine), `quiz_history.py` (PDF/test ingestion), and keep `ui_quiz.py` as the thin view layer. | **High** |
| M15 | **`start_quiz()` is ~230 lines of branching** | Each strategy (`focused`, `learning_blend`, `free_mode`, `sat_psat_unit`, `historical_practice`) is inline in one method. Extract each into a `_build_<strategy>_questions()` helper. | **High** |
| M16 | **No progress persistence between sessions for quiz position** | If the user closes mid-quiz, all progress is lost. Consider auto-saving partial attempts to the DB. | Medium |

---

## 3. UI Aesthetics

### Overall App Shell — [ui_root.py](file:///home/user/projects/mandelbrot_fortran/app/ui_root.py)

| # | Issue | Suggestion | Severity |
|---|-------|------------|----------|
| U1 | **No custom theme** | The app uses the default Tkinter/Ttk theme which looks dated. Apply a modern theme like `clam`, `alt`, or a custom SVG theme. Even just `ttk.Style().theme_use('clam')` + a handful of style overrides would significantly modernize the look. | **High** |
| U2 | **No app icon or branding** | `self.root.title("MandelQuest")` — no window icon, no splash, no logo. Add `self.root.iconphoto()` with a small fractal icon. | Medium |
| U3 | **Fixed geometry `1200x720`** | No responsive behavior. On small screens the UI clips; on large screens it wastes space. Consider minimum size constraints + proportional layouts. | Medium |
| U4 | **No keyboard shortcuts** | Tab switching, quiz submission, and fractal zooming rely entirely on mouse. Add accelerators (e.g., `Ctrl+1`–`Ctrl+6` for tabs, `Enter` to submit quiz answers). | Medium |

---

### Dashboard — [ui_dashboard.py](file:///home/user/projects/mandelbrot_fortran/app/ui_dashboard.py)

| # | Issue | Suggestion | Severity |
|---|-------|------------|----------|
| U5 | **Tile colors are hard-coded in both code and inline styles** | `"#dfe3e8"`, `"#f3d4d4"`, etc. are scattered as literals. Define a `THEME` dict or dataclass to centralize colors, making re-theming and dark-mode feasible. | **High** |
| U6 | **Progress bars lack color coding** | All progress bars are the same default Ttk blue regardless of mastery level. Style them green for mastered, yellow for developing, red for needs-work. | Medium |
| U7 | **Streak emoji rendering** | `_streak_graph` uses 🔥 and ⬜ emojis — these render inconsistently across platforms and can appear as □ on some Linux setups. Consider using Unicode block characters or small canvas drawings instead. | Low |

---

### Skill Map — [ui_skill_map.py](file:///home/user/projects/mandelbrot_fortran/app/ui_skill_map.py)

| # | Issue | Suggestion | Severity |
|---|-------|------------|----------|
| U8 | **Full re-render on every click** | `_on_canvas_click` calls `self.render()` which deletes and redraws the entire canvas. For a map with 20+ nodes and edges, this causes flicker. Instead, update only the fill/outline of changed nodes and highlighted edges. | Medium |
| U9 | **Node labels overflow at 8pt** | Long skill labels like "Order of Operations" get truncated in the 104px-wide rectangles (line 237 `width=96`). Either abbreviate labels or auto-size boxes. | Low |
| U10 | **No zoom/pan** | The skill map only supports vertical scrolling via mousewheel. A zoom level control or drag-to-pan would help with large skill trees. | Low |

---

### Arithmetic Panel — [ui_arithmetic.py](file:///home/user/projects/mandelbrot_fortran/app/ui_arithmetic.py)

| # | Issue | Suggestion | Severity |
|---|-------|------------|----------|
| U11 | **Canvas background is `#f7f7f7` — nearly white** | This is indistinguishable from the surrounding frame. Use a subtle border or a slightly contrasting background to delineate the drawing area. | Low |
| U12 | **All shapes use the same blue `#5b8def`** | The counting, multiply, and other views all use the same single color. Using per-skill accent colors or gentle color cycling would make each activity feel distinct. | Medium |
| U13 | **Socket check blocks UI thread** | `_can_reach_khan()` opens a TCP socket with 1.2s timeout on the main thread. This can freeze the UI for over a second. Move to a background thread and show a "Checking…" indicator. | **High** |

---

### Quiz UI — [ui_quiz.py](file:///home/user/projects/mandelbrot_fortran/app/ui_quiz.py)

| # | Issue | Suggestion | Severity |
|---|-------|------------|----------|
| U14 | **Controls panel is extremely dense** | The left panel packs ~15 widgets vertically with no grouping or collapsible sections. Group related controls into `LabelFrame` widgets (e.g., "Question Settings", "Historical Tests", "Curriculum"). | **High** |
| U15 | **No visual feedback on correct/incorrect** | Only a text label changes. Add color flash on the answer widget (green/red border) and consider a brief celebratory animation for correct answers — this matters hugely for child engagement. | **High** |
| U16 | **`subprocess.run` for PDF ingestion blocks the UI** | `_ingest_historical_pdfs()` runs `subprocess.run` synchronously. For large PDF sets this freezes the app. Use `ThreadPoolExecutor` similar to the fractal renderer. | Medium |

---

## Summary: Top Priority Items

| Priority | ID | Area | Description |
|----------|----|------|-------------|
| 🔴 High | F10 | Fractal | Expose palette selector in UI |
| 🔴 High | F11 | Fractal | Add Julia parameter sliders |
| 🔴 High | M1 | Math | Refactor `render_arithmetic()` dispatch |
| 🔴 High | M3 | Math | Improve algebra linear visualization |
| 🔴 High | M11 | Math | Fix multiplication partial alignment |
| 🔴 High | M12 | Math | Add long division work steps |
| 🔴 High | M14 | Math | Split `ui_quiz.py` into modules |
| 🔴 High | M15 | Math | Extract quiz strategy builders |
| 🔴 High | U1 | UI | Apply a modern Ttk theme |
| 🔴 High | U5 | UI | Centralize color/theme constants |
| 🔴 High | U13 | UI | Move Khan socket check off main thread |
| 🔴 High | U14 | UI | Group quiz controls into sections |
| 🔴 High | U15 | UI | Add visual correct/incorrect feedback |
