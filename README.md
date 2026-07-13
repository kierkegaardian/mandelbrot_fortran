# MandelQuest

Project brief: see `PROJECT_BRIEF.md`  
Technical notes: see `TECHNICAL.md`

MandelQuest is an offline-first desktop math practice app for homeschool families, built with a Python Tkinter UI and a Modern Fortran rendering engine. It combines visual math practice, printable worksheets, parent-managed assignments, and an exploratory fractal lab in one local-first app.

## Public Launch Surface
- Landing page: `docs/index.html`
- Topic coverage and curriculum honesty: `docs/coverage.html`
- Privacy and local-data policy: `docs/privacy.html`
- Support and backup guide: `docs/support.html`
- Homeschool beta program: `docs/homeschool-beta.html`
- First 15 minutes guide: `docs/first-15-minutes.html`
- Sample worksheet + answer key: `docs/sample-worksheet.html`
- College/adult review note: `docs/college-review.html`

## Product Highlights
- **Offline-first math practice:** Core learning flows run locally with no required internet connection.
- **Parent-managed learning:** Multiple profiles, parent PIN protection, quiz sets, assignments, grades, and printable worksheets.
- **Intuition-first practice:** Visual explanations, intuition prompts, expression practice, and word-problem practice.
- **Cross-platform packaging path:** Windows, macOS, and Linux packaging workflows are included.
- **Fractal exploration bonus:** The original Mandelbrot and Julia visualizer remains available as a separate learning/exploration mode.

## Build & Run

Prereq: `gfortran` (Arch: `sudo pacman -S gcc-fortran`).
Optional: ImageMagick for PNG conversion (`sudo pacman -S imagemagick`).

- Build: `make`
- Run default: `./mandelbrot_gen`
- See options: `./mandelbrot_gen --help`
- OpenMP: `make OPENMP=1` then `./mandelbrot_gen --threads 8`
- Smooth coloring: `./mandelbrot_gen --smooth`
- Julia: `./mandelbrot_gen --julia --julia-cx -0.4 --julia-cy 0.6 --iter 2000`
- Extra palettes: `--palette sunset|ice|fire`
- PNG output: `make png` (uses ImageMagick)

### Desktop Learning App (Tkinter UI)

- Run the multi‑panel desktop app: `python explorer.py`
- The app includes Fractals, Arithmetic visuals, Quizzes, and Parent tools.
- Parent tools are PIN-gated once a parent sets a PIN in `Parent -> Profiles -> Set / Change Parent PIN`.
- Offline mode can be enforced in `Parent -> Profiles` to disable all external lesson launches.
- Keyboard-first shortcuts:
  - Global tabs: `Ctrl+1..6`, `Ctrl+Tab`, `Ctrl+Shift+Tab`
  - Global refresh/focus: `F5` or `Ctrl+R`, `Ctrl+L`
  - Quiz: `Alt+S` start, `Ctrl+Enter` or `Alt+N` submit/next, `Alt+I` intuition hint
  - Parent: `Alt+1..5` sub-tabs, `Ctrl+R` refresh tab, `Ctrl+N` primary create action
  - Dashboard: `Ctrl+R` refresh, `Alt+D` daily review, `Alt+A` assignment

### Offline-First Setup

- Default behavior is local-first: all profiles, attempts, assignments, and worksheets are stored in local SQLite.
- External lesson links are optional and disabled by default.
- **Family Sync (Beta)** is experimental, opt-in, and intended for operator-managed testing with a separately deployed compatible sync API.
- Local-only is the default: public builds ship with sync disabled and no server configured. A parent cannot enable the beta until `MANDELQUEST_SYNC_CONFIG=/path/to/sync-config.json` points to a machine-local config.
- The beta sends profiles, quiz sets, assignments, completed quiz attempts, and question history (including prompts and answers) to the configured server. Parent PIN data, UI/offline settings, local PDFs, worksheet files and records, Summer Program state, school-year targets, and in-progress quiz resume state stay on the device.
- Machine-local sync config files should stay outside Git. Back up the local data directory before beta testing.
- To disable external lesson launches, enable `Enforce offline mode` in Parent settings. Family Sync beta has its own separate opt-in control.

### Local Data and Backup

- Local data directory (dev run): `data/`
- Local data directory (packaged app):
  - Windows: `%APPDATA%/MandelQuest`
  - macOS: `~/Library/Application Support/MandelQuest`
  - Linux: `${XDG_DATA_HOME:-~/.local/share}/MandelQuest`
- Override data location for testing or managed installs: `MANDELQUEST_DATA_DIR=/path/to/data`
- Main database: `data/app.db`
- Worksheets output: `data/worksheets/`
- Recommended backup: close the app, then copy `data/app.db` and `data/worksheets/` to a safe location.

### Homeschool Positioning

- Best current fit: homeschool families who want local-first math review, parent oversight, printable practice, and calm desktop workflows.
- Honest limits today:
  - Full geometry-proof coverage is not complete.
  - Algebra 2 and post-Algebra-1 tracks are selective rather than course-complete.
  - The app is not yet positioned as a web/mobile college-placement product.
- Planned launch pricing: closed beta free, then `$59` per household with a 14-day refund window.

### Optional Dependency Fallbacks

- If `pdftotext` is missing, historical-PDF ingestion and story-wrapper extraction are skipped with a friendly error, but core quiz/worksheet learning flows continue to work.
- If ImageMagick is missing, `make png` is unavailable; use default PPM outputs or install `imagemagick`.

### Content Pipeline (Khan + Open Textbooks)

- Build Khan subskill registry for all local skills/subskills:
  - `python scripts/build_khan_subskill_registry.py`
  - Output: `scripts/catalogs/khan_subskill_registry.json`
- Ingest word-problem candidates from curated free/open textbooks:
  - `python scripts/ingest_open_textbook_wordproblems.py --source-id ray_new_practical_arithmetic_1897 --max-candidates 120`
  - Catalog: `scripts/source_catalog.json`
- Dry-run ingestion without DB writes:
  - `python scripts/ingest_open_textbook_wordproblems.py --dry-run --source-id ray_new_practical_arithmetic_1897`

## Packaging (Windows/macOS/Linux)

This repo includes a PyInstaller spec and GitHub Actions workflow for cross-platform app bundles.

- Spec file: `mandelquest.spec`
- CI workflow: `.github/workflows/package.yml`
- Trigger packaging:
  - Manually via **Actions -> Package MandelQuest -> Run workflow**
  - Or by pushing a version tag like `v0.1.0`

Artifacts produced by CI:
- Linux: `MandelQuest-linux.tar.gz`
- macOS: `MandelQuest-macos.tar.gz`
- Windows: `MandelQuest-windows.zip`

## GitHub Releases (Tagged Builds)

- Release workflow: `.github/workflows/release.yml`
- Trigger: push a version tag (`v*`, e.g. `v0.1.0`)
- Behavior:
  - Builds all three OS packages
  - Runs tests
  - Publishes archives directly to the GitHub Release for that tag

Local packaging (same machine):
1. Build Fortran renderer first (`make OPENMP=0`).
2. Install PyInstaller (`python -m pip install pyinstaller`).
3. Build app bundle (`pyinstaller --noconfirm --clean mandelquest.spec`).
4. Output is under `dist/MandelQuest/`.
5. Run packaged smoke test (headless): `MANDELQUEST_DATA_DIR=/tmp/mandelquest-smoke ./dist/MandelQuest/MandelQuest --smoke-test`

## Release Readiness

- v1 checklist: `docs/V1_RELEASE_CHECKLIST.md`
- Go-to-market checklist: `docs/GO_TO_MARKET_CHECKLIST.md`
- Demo video script: `docs/DEMO_VIDEO_SCRIPT.md`
- Screenshot shot list: `docs/MEDIA_SHOTLIST.md`
- Recommended final gate before `v1.0.0`: run full tests, validate packaging artifacts, and complete manual cross-platform smoke checks.

### Known Limitations (v1.0)

- No hosted cloud/LAN sync service ships with v1. The operator-configured Family Sync beta remains disabled unless a compatible server config is supplied and a parent explicitly opts in.
- Curriculum depth beyond Foundations through Algebra 1 is intentionally deferred.
- Historical-PDF ingestion and some conversion helpers rely on optional system tools (`pdftotext`, ImageMagick).

## Fractal Engine

The project still includes the original high-performance command-line fractal renderer written in Modern Fortran (2008+).

### CLI Features
- **High Performance:** Utilizes Fortran's native complex number support and efficient array operations.
- **Zero Dependencies:** Generates standard PPM (Portable Pixel Map) image files that can be opened by most image viewers (or converted easily).
- **Configurable:** CLI options for resolution, bounds, center/zoom, palette, and output file.
- **Optional OpenMP:** Multi-core rendering with `make OPENMP=1`.
- **Smooth Coloring:** Continuous iteration-based gradients for cleaner bands.
- **Julia Sets:** Render Julia sets with configurable constants.

### Assets & Licensing

See `assets/ASSETS_LICENSE.md` for attribution and licensing details (including OpenMoji, CC BY-SA 4.0).

### Docker (no host Fortran compiler)

If you don’t want to install `gfortran` locally, you can build/run via Docker:

- Build: `make docker-build`
- Run default: `make docker-run`
- Run OpenMP render: `make docker-run-omp`

## Product Roadmap

### Phase 1: Core Engine (Current)
- [x] Basic Escape Time Algorithm implementation.
- [x] Native `complex` type usage.
- [x] PPM Image Writer module.
- [x] Single-threaded rendering.

### Phase 2: Optimization & UX
- [x] OpenMP Parallelization for multi-core rendering (optional build flag).
- [x] CLI for specifying coordinates, bounds, and zoom level.
- [x] Progress indicator during rendering (auto-disabled under multi-threading).

### Phase 3: Advanced Features
- [x] Smooth coloring algorithms (continuous potential).
- [x] Support for Julia Sets.
- [ ] BMP or PNG output support (via simple libraries).
