# Agent Collaboration Log

<!-- GOVERNANCE_BASELINE_START -->
## Governance Baseline (Canonical)
- Project ID (portable): `mandelbrot_fortran`
- Path (current environment): `/home/user/projects/mandelbrot_fortran`
- Canonical origin (current): `git@github.com:kierkegaardian/mandelbrot_fortran.git`
- Default branch (current): `master`
- Stack / language (canonical): Fortran engine + Python Tkinter UI.
- File-size rule (enforced target): keep new files and heavily modified files (`>100` non-comment LOC changed or `>25%` of file touched) at `<= 300` LOC where practical; split into modules when larger. Exceptions are allowed for generated files, lockfiles, or legacy files when splitting would reduce clarity.
- Heavily-modified response (enforced): if modular splitting clearly improves maintainability, propose a split plan first; otherwise pause for user acknowledgement before committing any file that would exceed `400` LOC, and record the exception rationale in the handoff.
- Typesafety rule (enforced): apply stack-appropriate strict typing in every change (strict TypeScript for TS, Python type hints + pyright/mypy where configured, ShellCheck/input validation for shell, explicit declarations for Fortran/C# where applicable).
- Remote/push rule (enforced): do not change remotes or push destinations without explicit user confirmation; treat `origin` as canonical by default. This applies to human-in-the-loop agent actions and does not override already-approved CI automation.
- Workspace fast-path rule (enforced): for trivial, self-contained requests that do not touch files, secrets, infrastructure, active project state, or prior context, answer directly and skip continuity-ledger reads/updates, broad repo scans, discovery docs, and second-agent review; for non-trivial workspace/repo/infra/follow-up work, read the relevant context first and update continuity only when state materially changes.
<!-- GOVERNANCE_BASELINE_END -->

This project was co-developed with an AI Agent specialized in software engineering.

## Roles
- **User:** Product Owner, System Administrator (Arch Linux).
- **Agent:** Lead Developer, Architect.

## Context
- **Language:** Modern Fortran.
- **Goal:** Demonstrate Fortran's capabilities in math and array processing through a visual application.
- **Environment:** Arch Linux.

## Quality
- **Typesafety (Request):** Enforce robust, stack-appropriate typesafety in all changes (keep `implicit none` and explicit declarations).
- **Skill UX Standard:** For every new math skill, include (1) enriched intuition content (`Mental model`, `Common mistake`, `Try this`) and (2) an optional mapped external lesson link (Khan Academy) controlled by the parent external-links setting.
