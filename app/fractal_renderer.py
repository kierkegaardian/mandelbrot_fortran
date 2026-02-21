from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
import os
from pathlib import Path
from threading import Event
from time import sleep

from .paths import mandelbrot_binary

PREVIEW_TIMEOUT_SECONDS = 45.0
EXPORT_TIMEOUT_SECONDS = 300.0


@dataclass(frozen=True)
class FractalConfig:
    width: int
    height: int
    max_iter: int
    center_x: float
    center_y: float
    zoom: float
    fractal_type: str
    palette: str
    freq: float
    power: float
    julia_cx: float
    julia_cy: float
    smooth: bool
    cyclic: bool
    threads: int


class RenderCancelled(RuntimeError):
    """Raised when a render is cancelled by the UI."""


def _base_args(config: FractalConfig, output_path: str) -> list[str]:
    return [
        "--width",
        str(config.width),
        "--height",
        str(config.height),
        "--output",
        output_path,
        "--iter",
        str(int(config.max_iter)),
        "--center-x",
        str(config.center_x),
        "--center-y",
        str(config.center_y),
        "--zoom",
        str(config.zoom),
        "--type",
        config.fractal_type,
        "--palette",
        config.palette,
        "--freq",
        str(config.freq),
        "--power",
        str(config.power),
        "--julia-cx",
        str(config.julia_cx),
        "--julia-cy",
        str(config.julia_cy),
        "--threads",
        str(int(config.threads)),
        "--progress-every",
        "0",
    ]


def _run_with_cancel(args: list[str], cancel_event: Event | None, timeout_seconds: float) -> subprocess.CompletedProcess[bytes]:
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        if cancel_event is None:
            out, err = proc.communicate(timeout=timeout_seconds)
            ret = proc.returncode
        else:
            waited = 0.0
            interval = 0.05
            while True:
                if cancel_event.is_set():
                    proc.kill()
                    proc.wait(timeout=2.0)
                    raise RenderCancelled("Render cancelled")
                ret = proc.poll()
                if ret is not None:
                    out = proc.stdout.read() if proc.stdout is not None else b""
                    err = proc.stderr.read() if proc.stderr is not None else b""
                    break
                sleep(interval)
                waited += interval
                if waited >= timeout_seconds:
                    proc.kill()
                    proc.wait(timeout=2.0)
                    raise TimeoutError(f"Render timed out after {int(timeout_seconds)}s")
    except subprocess.TimeoutExpired as exc:
        proc.kill()
        proc.wait(timeout=2.0)
        raise TimeoutError(f"Render timed out after {int(timeout_seconds)}s") from exc

    if ret != 0:
        raise subprocess.CalledProcessError(ret, args, output=out, stderr=err)
    return subprocess.CompletedProcess(args=args, returncode=ret, stdout=out, stderr=err)


def render_ppm(config: FractalConfig, cancel_event: Event | None = None) -> bytes:
    binary = mandelbrot_binary()
    if not binary.exists():
        raise FileNotFoundError("Fractal renderer not found. Please run 'make' in the project folder.")

    fd, tmp_path_str = tempfile.mkstemp(suffix=".ppm")
    tmp_path = Path(tmp_path_str)
    os.close(fd)
    try:
        args = [str(binary), *_base_args(config, str(tmp_path))]
        if config.smooth:
            args.append("--smooth")
        if config.cyclic:
            args.append("--cyclic")
        _run_with_cancel(args, cancel_event=cancel_event, timeout_seconds=PREVIEW_TIMEOUT_SECONDS)
        return tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)


def save_high_res(config: FractalConfig, output_path: str, cancel_event: Event | None = None) -> None:
    binary = mandelbrot_binary()
    if not binary.exists():
        raise FileNotFoundError("Fractal renderer not found. Please run 'make' in the project folder.")

    args = [str(binary), *_base_args(config, output_path)]
    if config.smooth:
        args.append("--smooth")
    if config.cyclic:
        args.append("--cyclic")
    _run_with_cancel(args, cancel_event=cancel_event, timeout_seconds=EXPORT_TIMEOUT_SECONDS)
