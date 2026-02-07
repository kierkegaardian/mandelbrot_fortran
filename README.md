# Fortran Mandelbrot Generator

Project brief: see `PROJECT_BRIEF.md`  
Technical notes: see `TECHNICAL.md`

A high-performance command-line tool written in Modern Fortran (2008+) to generate high-resolution renderings of the Mandelbrot set.

## Features
- **High Performance:** Utilizes Fortran's native complex number support and efficient array operations.
- **Zero Dependencies:** Generates standard PPM (Portable Pixel Map) image files that can be opened by most image viewers (or converted easily).
- **Configurable:** CLI options for resolution, bounds, center/zoom, palette, and output file.
- **Optional OpenMP:** Multi-core rendering with `make OPENMP=1`.
- **Smooth Coloring:** Continuous iteration-based gradients for cleaner bands.
- **Julia Sets:** Render Julia sets with configurable constants.

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
