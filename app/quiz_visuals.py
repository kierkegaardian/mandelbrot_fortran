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
