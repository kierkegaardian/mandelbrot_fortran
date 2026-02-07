from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    path = repo_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def worksheets_dir() -> Path:
    path = repo_root() / "worksheets"
    path.mkdir(parents=True, exist_ok=True)
    return path


def assets_dir() -> Path:
    path = repo_root() / "assets"
    path.mkdir(parents=True, exist_ok=True)
    return path


def mandelbrot_binary() -> Path:
    return repo_root() / "mandelbrot_gen"
