from __future__ import annotations

import math
import tkinter as tk


def draw_fraction_circle(
    canvas: tk.Canvas,
    numerator: int,
    denominator: int,
    bounds: tuple[int, int, int, int],
    fill_color: str = "#5b8def",
    outline: str = "#c7cfd6",
) -> None:
    numerator = max(0, numerator)
    denominator = max(1, denominator)
    x, y, width, height = bounds
    circle_count = _circle_count(numerator, denominator)
    cols, rows = _grid(circle_count)
    cell_w = width / cols
    cell_h = height / rows
    full = numerator // denominator
    rem = numerator % denominator
    for idx in range(circle_count):
        row = idx // cols
        col = idx % cols
        cx = x + col * cell_w + cell_w / 2
        cy = y + row * cell_h + cell_h / 2
        size = min(cell_w, cell_h) * 0.75
        r = size / 2
        bbox = (cx - r, cy - r, cx + r, cy + r)
        canvas.create_oval(*bbox, outline=outline, width=2, fill="white")
        if numerator == 0:
            continue
        if idx < full:
            filled = denominator
        elif idx == full:
            filled = rem
        else:
            filled = 0
        if filled <= 0:
            continue
        step = 360.0 / denominator
        start = -90.0
        for i in range(filled):
            canvas.create_arc(
                *bbox,
                start=start + i * step,
                extent=step,
                fill=fill_color,
                outline=outline,
            )


def _circle_count(numerator: int, denominator: int) -> int:
    if numerator <= 0:
        return 1
    return max(1, math.ceil(numerator / denominator))


def _grid(count: int) -> tuple[int, int]:
    cols = max(1, int(math.ceil(math.sqrt(count))))
    rows = max(1, int(math.ceil(count / cols)))
    return cols, rows
