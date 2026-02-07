from __future__ import annotations

import math


def fraction_svg(numerator: int, denominator: int) -> str:
    numerator = max(0, numerator)
    denominator = max(1, denominator)
    circle_count = _circle_count(numerator, denominator)
    cols, rows = _grid(circle_count)
    cell = 120
    gap = 12
    width = cols * cell + (cols - 1) * gap
    height = rows * cell + (rows - 1) * gap
    full = numerator // denominator
    rem = numerator % denominator
    parts: list[str] = [
        f"<svg class='fraction-circle' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>"
    ]
    for idx in range(circle_count):
        row = idx // cols
        col = idx % cols
        cx = col * (cell + gap) + cell / 2
        cy = row * (cell + gap) + cell / 2
        r = cell / 2 - 2
        parts.append(f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='white' stroke='#c7cfd6' stroke-width='2' />")
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
            path = _arc_path(cx, cy, r, start + i * step, start + (i + 1) * step)
            parts.append(f"<path d='{path}' fill='#5b8def' stroke='#c7cfd6' stroke-width='1' />")
    parts.append("</svg>")
    return "".join(parts)


def _circle_count(numerator: int, denominator: int) -> int:
    if numerator <= 0:
        return 1
    return max(1, math.ceil(numerator / denominator))


def _grid(count: int) -> tuple[int, int]:
    cols = max(1, int(math.ceil(math.sqrt(count))))
    rows = max(1, int(math.ceil(count / cols)))
    return cols, rows


def _arc_path(cx: float, cy: float, r: float, start_deg: float, end_deg: float) -> str:
    start_rad = math.radians(start_deg)
    end_rad = math.radians(end_deg)
    x1 = cx + r * math.cos(start_rad)
    y1 = cy + r * math.sin(start_rad)
    x2 = cx + r * math.cos(end_rad)
    y2 = cy + r * math.sin(end_rad)
    large = 1 if (end_deg - start_deg) > 180 else 0
    return f"M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large} 1 {x2} {y2} Z"
