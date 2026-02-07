from __future__ import annotations

import subprocess
from dataclasses import dataclass

from .paths import mandelbrot_binary


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


def render_ppm(config: FractalConfig) -> bytes:
    binary = mandelbrot_binary()
    if not binary.exists():
        raise FileNotFoundError("Fractal renderer not found. Please run 'make' in the project folder.")

    args = [
        str(binary),
        "--width",
        str(config.width),
        "--height",
        str(config.height),
        "--output",
        "/dev/stdout",
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
        "--progress-every",
        "0",
    ]

    if config.smooth:
        args.append("--smooth")
    if config.cyclic:
        args.append("--cyclic")

    result = subprocess.run(args, capture_output=True, check=True)
    return result.stdout


def save_high_res(config: FractalConfig, output_path: str) -> None:
    binary = mandelbrot_binary()
    if not binary.exists():
        raise FileNotFoundError("Fractal renderer not found. Please run 'make' in the project folder.")

    args = [
        str(binary),
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
        "--freq",
        str(config.freq),
        "--power",
        str(config.power),
    ]
    if config.smooth:
        args.append("--smooth")
    if config.cyclic:
        args.append("--cyclic")

    subprocess.run(args, check=True)
