# UI Foundation Module Boundaries

This slice keeps the public constructors for `AppShell`, `ParentPanel`, and
`QuizPanel` unchanged while separating the shell, dashboard, arithmetic, and
fractal implementation into bounded modules.

The files materially rewritten in this slice are at or below the 300-line
target. The public facades remain:

- `app/ui_root.py` for `AppShell`;
- `app/ui_arithmetic.py` for `ArithmeticPanel`;
- `app/ui_dashboard.py` for `DashboardPanel`; and
- `app/ui_fractals.py` for `FractalPanel`.

Two legacy files remain above 400 lines:

- `app/ui_parent.py` receives only small keyboard/focus hooks here. Its
  workflow decomposition belongs with the later parent-authentication,
  Family Sync, and Summer Program slices so this foundation does not expose
  unfinished behavior.
- `app/ui_quiz.py` receives only small keyboard/focus hooks here. Its state
  machine decomposition belongs with the later transactional quiz-continuity
  slice, where resume and completion behavior can be reviewed together.

`app/ui_skill_map.py` is also legacy-sized but is not materially modified in
this slice. The Fortran renderer remains on its existing public CLI path; this
slice adds only the two palettes used by the split fractal controls.
