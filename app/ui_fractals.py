"""Backwards-compatible re-export of the split fractal viewer modules.

``FractalPanel`` is the public API consumed by :mod:`ui_root`.
"""

from __future__ import annotations

# Re-export the assembled panel so existing imports keep working.
from .ui_fractal_controls import FractalPanel  # noqa: F401

__all__: list[str] = ["FractalPanel"]
