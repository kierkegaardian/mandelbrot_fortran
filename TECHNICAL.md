# Technical Record: MandelQuest

## System Overview
A desktop learning app that combines a Fortran fractal renderer with a Python (Tkinter) multi‑panel GUI. The app adds arithmetic visualizations, quiz creation, grading, and printable worksheets, while keeping the existing fractal explorer.

## Architecture (High Level)
- **UI Shell (Python + Tkinter):** Multi‑panel desktop app with tabs for Fractals, Arithmetic, Quizzes, and Parent tools.
- **Fractal Engine (Fortran):** Existing `mandelbrot_gen` binary renders PPM via CLI; Python feeds parameters and displays results.
- **Arithmetic Visualizer (Python):** Canvas‑based shapes and icon sprites for counting, add/subtract, multiply, divide, ratios.
- **Quiz Engine (Python):** Generates questions, records responses, scores attempts, and produces printable worksheets + answer key.
- **Local Storage (SQLite):** Profiles, settings, quiz attempts, and worksheet history stored locally for offline use.

## Repository Layout (Proposed)
- `src/`
  - `app.py` (main entry)
  - `ui/` (panels, tabs, widgets)
  - `modules/fractal/` (Fortran bridge + rendering)
  - `modules/arithmetic/` (visualizers + explanations)
  - `modules/quiz/` (question bank + grading)
  - `modules/print/` (worksheet + answer key)
  - `data/` (schema + data access)
- `assets/` (open‑source icons, shape presets, palettes)
- `PROJECT_BRIEF.md`, `TECHNICAL.md`

Note: Keep all code files under 300 lines by splitting into modules.

## Data Model (Local)
- **Profile**: id, name, role (child/parent), created_at
- **QuizAttempt**: id, profile_id, quiz_type, created_at, score
- **QuizQuestion**: id, attempt_id, skill, prompt, correct_answer, user_answer, is_correct
- **Worksheet**: id, profile_id, created_at, quiz_type, file_path

## Quiz & Worksheet Behavior
- Supports **multiple choice** and **typed answers**.
- Quizzes can be **per‑skill** or **mixed**.
- Results show **score + explanations** for mistakes.
- Printable worksheets render a clean layout with light color accents and a separate answer key.

### Exercise Mode Strategy
- Every question template should be tagged with a `mode`:
  `intuition`, `expression`, or `word`.
- Mastery should remain subskill-centric, independent of mode.
  Example: `add_subtract / regrouping` can be practiced through visuals, symbols, or stories, but contributes to one mastery record.
- Quiz composition should use weighted mode blending by mastery stage:
  early (`45/40/15` intuition/expression/word),
  developing (`30/45/25`),
  near-mastery (`20/40/40`).
- If transfer lags (word-problem accuracy lower than expression accuracy), automatically increase word-problem share until gap narrows.
- Free Mode should preserve mode labels per question (`Core`, `Preview`, `Prereq`, `Review`) plus mode (`intuition`/`expression`/`word`) for analytics.

## UI Flow
1. **Profile Picker** on launch.
2. **Main Tabs**: Fractals, Arithmetic, Quizzes, Parent.
3. **Parent Area**: manage profiles, create/edit quizzes, view grades, print worksheets.

## Open‑Source Visual Assets
- Use open‑source icons stored locally in `assets/` (no runtime downloads).
- Candidate sets: OpenMoji (CC BY‑SA 4.0) or similar.
- Keep a local `LICENSES/` folder with attributions.

## Type Safety & Validation
- Use Python type hints across modules.
- Runtime validation for quiz generation and scoring.
- Fortran code keeps `implicit none` and explicit declarations.

## Testing Strategy
- Unit tests for quiz generation, grading, and ratio logic.
- Integration test for profile creation + quiz attempt flow.
- Visual smoke tests (render arithmetic scenes + fractal preview).

## Deployment / Run
- Local desktop only.
- Build Fortran binary with `make`.
- Run the Tkinter app via Python (no server required).

## Security & Privacy
- Local‑only storage; no cloud sync in v1.
- No external network calls.

## Known Tradeoffs
- Python UI for speed of delivery; pure Fortran GUI can be revisited later.
- Local‑only accounts (multi‑device sync deferred).

## Future Work
- Add algebra/geometry/trig/calculus modules.
- Expand printable worksheet styles.
- Optional cloud backup for families with multiple devices.
- Optional server-hosted profiles to sync progress across devices.
