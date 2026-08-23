#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
BUILD_LOG="$PROJECT_ROOT/data/launcher-build.log"
cd "$PROJECT_ROOT"

notify() {
  if command -v notify-send >/dev/null 2>&1; then
    notify-send "MandelQuest" "$1"
  fi
}

find_latest_build() {
  if [[ ! -d "$PROJECT_ROOT/dist" ]]; then
    return 1
  fi

  find "$PROJECT_ROOT/dist" -type f -executable \
    \( -name "MandelQuest" -o -name "MandelQuest.AppImage" -o -name "MandelQuest.bin" \) \
    -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n1 | cut -d" " -f2-
}

wants_smoke_test() {
  local arg
  for arg in "$@"; do
    if [[ "$arg" == "--smoke-test" ]]; then
      return 0
    fi
  done
  return 1
}

renderer_needs_build() {
  local binary="$PROJECT_ROOT/mandelbrot_gen"
  if [[ ! -x "$binary" ]]; then
    return 0
  fi
  if [[ "$PROJECT_ROOT/Makefile" -nt "$binary" ]]; then
    return 0
  fi
  if find "$PROJECT_ROOT/src" -type f -name "*.f90" -newer "$binary" -print -quit | grep -q .; then
    return 0
  fi
  return 1
}

run_build() {
  local description="$1"
  shift

  mkdir -p "$(dirname "$BUILD_LOG")"
  {
    printf "[%s] %s\n" "$(date --iso-8601=seconds)" "$description"
    printf "[%s] Command:" "$(date --iso-8601=seconds)"
    printf " %q" "$@"
    printf "\n"
  } >"$BUILD_LOG"

  if "$@" >>"$BUILD_LOG" 2>&1; then
    return 0
  fi
  return 1
}

ensure_renderer() {
  if ! renderer_needs_build; then
    return 0
  fi

  notify "Preparing fractal renderer. First launch may take a minute."

  if command -v gfortran >/dev/null 2>&1 && command -v make >/dev/null 2>&1; then
    if run_build "Building renderer with gfortran" make -C "$PROJECT_ROOT" OPENMP="${OPENMP:-1}"; then
      return 0
    fi
  fi

  if command -v docker >/dev/null 2>&1 && command -v make >/dev/null 2>&1; then
    if run_build "Building renderer with Docker" make -C "$PROJECT_ROOT" docker-build; then
      return 0
    fi
  fi

  notify "Renderer build failed. Fractals tab may be unavailable. See $BUILD_LOG."
  return 1
}

launch_from_source() {
  if ! wants_smoke_test "$@"; then
    ensure_renderer || true
  fi

  if command -v python3 >/dev/null 2>&1; then
    exec python3 "$PROJECT_ROOT/explorer.py" "$@"
  fi

  exec python "$PROJECT_ROOT/explorer.py" "$@"
}

main() {
  local latest_build=""
  latest_build="$(find_latest_build || true)"

  if [[ -n "$latest_build" && -x "$latest_build" ]]; then
    exec "$latest_build" "$@"
  fi

  launch_from_source "$@"
}

main "$@"
