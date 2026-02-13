from __future__ import annotations

import tkinter as tk

from .arithmetic_draw import draw_count, draw_groups, draw_ratio_bars, draw_split
from .arithmetic_fractions import draw_fraction_circle
from .arithmetic_long import (
    draw_long_addition,
    draw_long_division,
    draw_long_multiplication,
    draw_long_subtraction,
    draw_money_breakdown,
)


def render_quiz_visual(canvas: tk.Canvas, visual: dict) -> None:
    canvas.delete("all")
    w = max(10, canvas.winfo_width())
    h = max(10, canvas.winfo_height())
    kind = visual.get("kind")
    if kind == "counting":
        draw_count(canvas, visual["count"], "Circles", (10, 10, w - 20, h - 20), "#5b8def")
    if kind == "add":
        draw_split(canvas, visual["a"], visual["b"], "Squares", (10, 10, w - 20, h - 20), "#67b26f", "#5b8def")
    if kind == "subtract":
        draw_split(
            canvas,
            visual["a"] - visual["b"],
            visual["b"],
            "Squares",
            (10, 10, w - 20, h - 20),
            "#67b26f",
            "#d0d7dd",
        )
    if kind == "multiply":
        draw_groups(canvas, visual["a"], visual["b"], "Circles", (10, 10, w - 20, h - 20), "#5b8def")
    if kind == "divide":
        per_group = visual["total"] // max(1, visual["groups"])
        draw_groups(canvas, visual["groups"], per_group, "Circles", (10, 10, w - 20, h - 20), "#67b26f")
    if kind == "ratio":
        draw_ratio_bars(canvas, visual["a"], visual["b"], (10, 10, w - 20, h - 20), "#5b8def", "#f2b05e")
    if kind == "fraction":
        draw_fraction_circle(canvas, visual["numerator"], visual["denominator"], (10, 10, w - 20, h - 20))
    if kind == "long_addition":
        draw_long_addition(canvas, visual["a"], visual["b"], (10, 10, w - 20, h - 20))
    if kind == "long_subtraction":
        draw_long_subtraction(canvas, visual["a"], visual["b"], (10, 10, w - 20, h - 20))
    if kind == "long_multiplication":
        draw_long_multiplication(canvas, visual["a"], visual["b"], (10, 10, w - 20, h - 20))
    if kind == "long_division":
        draw_long_division(canvas, visual["dividend"], visual["divisor"], (10, 10, w - 20, h - 20))
    if kind == "money":
        draw_money_breakdown(canvas, visual["dollars"], visual["cents"], (10, 10, w - 20, h - 20))
    if kind == "slope":
        _draw_slope_line(
            canvas,
            visual["x1"],
            visual["y1"],
            visual["x2"],
            visual["y2"],
            (10, 10, w - 20, h - 20),
        )


def _draw_slope_line(
    canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, bounds: tuple[int, int, int, int]
) -> None:
    x0, y0, width, height = bounds
    padding = 10
    min_x = min(0, x1, x2) - 1
    max_x = max(0, x1, x2) + 1
    min_y = min(0, y1, y2) - 2
    max_y = max(0, y1, y2) + 2

    x_range = max(1, max_x - min_x)
    y_range = max(1, max_y - min_y)
    scale_x = max(1.0, (width - 2 * padding) / x_range)
    scale_y = max(1.0, (height - 2 * padding) / y_range)
    scale = min(scale_x, scale_y)
    cx1 = int(x0 + padding + (x1 - min_x) * scale)
    cy1 = int(y0 + height - padding - (y1 - min_y) * scale)
    cx2 = int(x0 + padding + (x2 - min_x) * scale)
    cy2 = int(y0 + height - padding - (y2 - min_y) * scale)

    canvas.create_line(cx1, cy1, cx2, cy2, fill="#2e7d32", width=2)
    canvas.create_oval(cx1 - 4, cy1 - 4, cx1 + 4, cy1 + 4, fill="#5b8def", outline="")
    canvas.create_oval(cx2 - 4, cy2 - 4, cx2 + 4, cy2 + 4, fill="#5b8def", outline="")
    canvas.create_text(cx1, cy1 - 8, text=f"({x1}, {y1})", fill="#2a2a2a", font=("Helvetica", 9))
    canvas.create_text(cx2, cy2 + 10, text=f"({x2}, {y2})", fill="#2a2a2a", font=("Helvetica", 9))

    axis_y = y0 + height - padding - (0 - min_y) * scale
    axis_x = x0 + padding + (0 - min_x) * scale
    axis_y = min(max(axis_y, y0 + padding), y0 + height - padding)
    axis_x = min(max(axis_x, x0 + padding), x0 + width - padding)
    canvas.create_line(x0 + padding, axis_y, x0 + width - padding, axis_y, fill="#b0bec5")
    canvas.create_line(axis_x, y0 + padding, axis_x, y0 + height - padding, fill="#b0bec5")
