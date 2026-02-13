from __future__ import annotations

import math
from typing import Callable

import tkinter as tk


def _grid(count: int, width: int, height: int) -> tuple[int, int]:
    if count <= 0:
        return (1, 1)
    cols = max(1, int(math.sqrt(count)))
    rows = max(1, int(math.ceil(count / cols)))
    if cols * rows < count:
        rows += 1
    return cols, rows


def _cell_positions(
    count: int, x: int, y: int, width: int, height: int, padding: int = 8
) -> list[tuple[float, float, float]]:
    cols, rows = _grid(count, width, height)
    cell_w = max(1.0, (width - padding * 2) / cols)
    cell_h = max(1.0, (height - padding * 2) / rows)
    size = min(cell_w, cell_h) * 0.7
    positions: list[tuple[float, float, float]] = []
    for idx in range(count):
        col = idx % cols
        row = idx // cols
        cx = x + padding + col * cell_w + cell_w / 2.0
        cy = y + padding + row * cell_h + cell_h / 2.0
        positions.append((cx, cy, size))
    return positions


def cell_positions(count: int, bounds: tuple[int, int, int, int]) -> list[tuple[float, float, float]]:
    x, y, width, height = bounds
    return _cell_positions(count, x, y, width, height)


def group_cell_size(groups: int, bounds: tuple[int, int, int, int]) -> tuple[int, int]:
    x, y, width, height = bounds
    cols, rows = _grid(groups, width, height)
    return int(width / cols), int(height / rows)


def draw_circle(canvas: tk.Canvas, cx: float, cy: float, size: float, color: str) -> None:
    r = size / 2.0
    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")


def draw_square(canvas: tk.Canvas, cx: float, cy: float, size: float, color: str) -> None:
    r = size / 2.0
    canvas.create_rectangle(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")


def draw_triangle(canvas: tk.Canvas, cx: float, cy: float, size: float, color: str) -> None:
    r = size / 2.0
    points = [
        (cx, cy - r),
        (cx - r, cy + r),
        (cx + r, cy + r),
    ]
    canvas.create_polygon(points, fill=color, outline="")


def draw_star(canvas: tk.Canvas, cx: float, cy: float, size: float, color: str) -> None:
    r_outer = size / 2.0
    r_inner = r_outer * 0.45
    points = []
    for i in range(10):
        angle = i * (math.pi / 5.0) - math.pi / 2.0
        radius = r_outer if i % 2 == 0 else r_inner
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    canvas.create_polygon(points, fill=color, outline="")


def draw_heart(canvas: tk.Canvas, cx: float, cy: float, size: float, color: str) -> None:
    r = size * 0.25
    canvas.create_oval(cx - r * 2, cy - r * 1.5, cx, cy + r * 0.5, fill=color, outline="")
    canvas.create_oval(cx, cy - r * 1.5, cx + r * 2, cy + r * 0.5, fill=color, outline="")
    points = [
        (cx - r * 2.1, cy - r * 0.2),
        (cx + r * 2.1, cy - r * 0.2),
        (cx, cy + r * 2.4),
    ]
    canvas.create_polygon(points, fill=color, outline="")


def draw_apple(canvas: tk.Canvas, cx: float, cy: float, size: float, color: str) -> None:
    r = size / 2.0
    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")
    canvas.create_rectangle(cx - r * 0.1, cy - r * 1.1, cx + r * 0.1, cy - r * 0.6, fill="#6b4a1e", outline="")
    canvas.create_polygon(
        (cx + r * 0.2, cy - r * 0.9),
        (cx + r * 0.8, cy - r * 0.7),
        (cx + r * 0.3, cy - r * 0.4),
        fill="#6bbf59",
        outline="",
    )


def draw_fish(canvas: tk.Canvas, cx: float, cy: float, size: float, color: str) -> None:
    r = size / 2.0
    canvas.create_oval(cx - r, cy - r * 0.7, cx + r, cy + r * 0.7, fill=color, outline="")
    tail = [(cx + r, cy), (cx + r * 1.6, cy - r * 0.6), (cx + r * 1.6, cy + r * 0.6)]
    canvas.create_polygon(tail, fill=color, outline="")
    canvas.create_oval(cx - r * 0.4, cy - r * 0.2, cx - r * 0.2, cy + r * 0.0, fill="#222", outline="")


def draw_black_dog(canvas: tk.Canvas, cx: float, cy: float, size: float, color: str) -> None:
    tone = "#1f1f1f"
    r = size / 2.0
    body_w = size * 0.9
    body_h = size * 0.45
    x0 = cx - body_w / 2.0
    y0 = cy - body_h / 2.0
    canvas.create_rectangle(x0, y0, x0 + body_w, y0 + body_h, fill=tone, outline="")
    canvas.create_oval(cx - r * 0.9, cy - r * 0.7, cx - r * 0.2, cy + r * 0.1, fill=tone, outline="")
    canvas.create_oval(cx - r * 0.1, cy - r * 0.6, cx + r * 0.1, cy - r * 0.4, fill=tone, outline="")
    canvas.create_rectangle(x0 + body_w * 0.1, y0 + body_h * 0.7, x0 + body_w * 0.25, y0 + body_h * 1.3, fill=tone, outline="")
    canvas.create_rectangle(x0 + body_w * 0.6, y0 + body_h * 0.7, x0 + body_w * 0.75, y0 + body_h * 1.3, fill=tone, outline="")
    tail = [(x0 + body_w, y0 + body_h * 0.2), (x0 + body_w + r * 0.4, y0), (x0 + body_w + r * 0.3, y0 + body_h * 0.5)]
    canvas.create_polygon(tail, fill=tone, outline="")


def draw_avocado(canvas: tk.Canvas, cx: float, cy: float, size: float, color: str) -> None:
    r = size / 2.0
    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")
    canvas.create_oval(cx - r * 0.3, cy - r * 0.2, cx + r * 0.3, cy + r * 0.4, fill="#6b4a1e", outline="")


def draw_truck(canvas: tk.Canvas, cx: float, cy: float, size: float, color: str) -> None:
    w = size
    h = size * 0.6
    x0 = cx - w / 2.0
    y0 = cy - h / 2.0
    canvas.create_rectangle(x0, y0, x0 + w * 0.7, y0 + h, fill=color, outline="")
    canvas.create_rectangle(x0 + w * 0.7, y0 + h * 0.35, x0 + w, y0 + h, fill="#9aa4ad", outline="")
    wheel_r = size * 0.18
    canvas.create_oval(x0 + w * 0.15 - wheel_r, y0 + h - wheel_r / 2, x0 + w * 0.15 + wheel_r, y0 + h + wheel_r, fill="#333", outline="")
    canvas.create_oval(x0 + w * 0.55 - wheel_r, y0 + h - wheel_r / 2, x0 + w * 0.55 + wheel_r, y0 + h + wheel_r, fill="#333", outline="")


def draw_icon_grid(
    canvas: tk.Canvas,
    count: int,
    image: tk.PhotoImage,
    bounds: tuple[int, int, int, int],
) -> None:
    for cx, cy, _size in cell_positions(count, bounds):
        canvas.create_image(cx, cy, image=image)


def draw_icon_split(
    canvas: tk.Canvas,
    left_count: int,
    right_count: int,
    image: tk.PhotoImage,
    bounds: tuple[int, int, int, int],
) -> None:
    x, y, width, height = bounds
    mid = x + width // 2
    draw_icon_grid(canvas, left_count, image, (x, y, width // 2, height))
    draw_icon_grid(canvas, right_count, image, (mid, y, width // 2, height))


def draw_icon_groups(
    canvas: tk.Canvas,
    groups: int,
    per_group: int,
    image: tk.PhotoImage,
    bounds: tuple[int, int, int, int],
) -> None:
    x, y, width, height = bounds
    cols, rows = _grid(groups, width, height)
    cell_w = width / cols
    cell_h = height / rows
    for idx in range(groups):
        col = idx % cols
        row = idx // cols
        gx = int(x + col * cell_w)
        gy = int(y + row * cell_h)
        canvas.create_rectangle(gx + 6, gy + 6, gx + cell_w - 6, gy + cell_h - 6, outline="#c7cfd6")
        draw_icon_grid(
            canvas,
            per_group,
            image,
            (gx + 10, gy + 10, int(cell_w - 20), int(cell_h - 20)),
        )


def _drawer(style: str) -> Callable[[tk.Canvas, float, float, float, str], None]:
    mapping = {
        "Circles": draw_circle,
        "Squares": draw_square,
        "Triangles": draw_triangle,
        "Stars": draw_star,
        "Hearts": draw_heart,
        "Apples": draw_apple,
        "Fish": draw_fish,
        "Black Dog": draw_black_dog,
        "Avocados": draw_avocado,
        "Trucks": draw_truck,
    }
    if style not in mapping:
        raise ValueError("Unknown object style")
    return mapping[style]


def draw_count(
    canvas: tk.Canvas,
    count: int,
    style: str,
    bounds: tuple[int, int, int, int],
    color: str,
) -> None:
    x, y, width, height = bounds
    drawer = _drawer(style)
    for cx, cy, size in _cell_positions(count, x, y, width, height):
        drawer(canvas, cx, cy, size, color)


def draw_split(
    canvas: tk.Canvas,
    left_count: int,
    right_count: int,
    style: str,
    bounds: tuple[int, int, int, int],
    left_color: str,
    right_color: str,
) -> None:
    x, y, width, height = bounds
    mid = x + width // 2
    draw_count(canvas, left_count, style, (x, y, width // 2, height), left_color)
    draw_count(canvas, right_count, style, (mid, y, width // 2, height), right_color)


def draw_groups(
    canvas: tk.Canvas,
    groups: int,
    per_group: int,
    style: str,
    bounds: tuple[int, int, int, int],
    color: str,
) -> None:
    x, y, width, height = bounds
    cols, rows = _grid(groups, width, height)
    cell_w = width / cols
    cell_h = height / rows
    for idx in range(groups):
        col = idx % cols
        row = idx // cols
        gx = int(x + col * cell_w)
        gy = int(y + row * cell_h)
        canvas.create_rectangle(gx + 6, gy + 6, gx + cell_w - 6, gy + cell_h - 6, outline="#c7cfd6")
        draw_count(canvas, per_group, style, (gx + 10, gy + 10, int(cell_w - 20), int(cell_h - 20)), color)


def draw_ratio_bars(
    canvas: tk.Canvas,
    a: int,
    b: int,
    bounds: tuple[int, int, int, int],
    color_a: str,
    color_b: str,
) -> None:
    x, y, width, height = bounds
    total = max(1, a + b)
    bar_height = height // 3
    bar_width_a = int(width * (a / total))
    bar_width_b = int(width * (b / total))
    canvas.create_rectangle(x, y + 20, x + bar_width_a, y + 20 + bar_height, fill=color_a, outline="")
    canvas.create_rectangle(x, y + 60, x + bar_width_b, y + 60 + bar_height, fill=color_b, outline="")
    canvas.create_text(x + bar_width_a + 10, y + 20 + bar_height / 2, text=str(a), anchor=tk.W, fill="#333")
    canvas.create_text(x + bar_width_b + 10, y + 60 + bar_height / 2, text=str(b), anchor=tk.W, fill="#333")


def draw_number_line(
    canvas: tk.Canvas,
    values: list[int],
    bounds: tuple[int, int, int, int],
    *,
    span: int = 10,
) -> None:
    x, y, width, height = bounds
    width = max(1, width)
    height = max(1, height)
    left_x = x + 24
    right_x = x + max(1, width - 24)
    mid_y = y + height // 2
    zero_x = left_x + (width - 48) // 2
    canvas.create_line(left_x, mid_y, right_x, mid_y, width=2)
    if span > 0:
        step = (right_x - left_x) / (2 * span)
        for tick in range(-span, span + 1):
            tx = zero_x + tick * step
            canvas.create_line(tx, mid_y - 5, tx, mid_y + 5)
            if tick % 2 == 0:
                canvas.create_text(tx, mid_y + 12, text=str(tick), anchor=tk.N, font=("Helvetica", 8))
    for value in values:
        if span == 0:
            t = 0.5
        else:
            t = (value / span + 1) / 2
        t = max(0.0, min(1.0, t))
        cx = left_x + (right_x - left_x) * t
        color = "#2e7d32" if value >= 0 else "#c62828"
        canvas.create_oval(cx - 5, mid_y - 5, cx + 5, mid_y + 5, fill=color, outline="#333")
        canvas.create_text(cx, mid_y - 12, text=str(value), anchor=tk.S, font=("Helvetica", 9), fill="#222")


def draw_right_triangle(
    canvas: tk.Canvas,
    opposite: int,
    adjacent: int,
    hypotenuse: int,
    bounds: tuple[int, int, int, int],
) -> None:
    x, y, width, height = bounds
    width = max(1, width)
    height = max(1, height)
    pad = 14
    p1 = (x + pad, y + height - pad)
    p2 = (x + width - pad, y + height - pad)
    p3 = (x + pad, y + height - pad - (height - 2 * pad) * 0.72)
    canvas.create_polygon(p1, p2, p3, outline="#4a4a4a", width=2, fill="")
    for x0, y0, label in [( (p1[0] + p2[0]) / 2, p1[1] + 10, str(adjacent)),
                           (p3[0] - 12, (p1[1] + p3[1]) / 2, str(opposite)),
                           (((p1[0] + p2[0]) / 2), ((p1[1] + p3[1]) / 2 + 8), f"h = {hypotenuse}")]:
        canvas.create_text(x0, y0, text=label, fill="#333", font=("Helvetica", 9))
    right_angle_x = p3[0] + 12
    right_angle_y = p1[1] - 12
    canvas.create_arc(p3[0], p3[1], p3[0] + 24, p1[1], start=90, extent=90, style=tk.ARC, width=1)


def draw_bar_chart(
    canvas: tk.Canvas,
    values: list[float],
    bounds: tuple[int, int, int, int],
    *,
    height_label: str,
) -> None:
    x, y, width, height = bounds
    width = max(1, width)
    height = max(1, height)
    if not values:
        return
    max_value = max(values) if max(values) > 0 else 1.0
    bottom = y + height - 16
    left = x + 10
    right = x + width - 10
    bars = len(values)
    gap = 10
    bar_area = max(1, right - left - gap * max(0, bars - 1))
    bar_width = max(12, bar_area // max(1, bars))
    origin = left
    canvas.create_line(left, bottom, right, bottom, width=2)
    for idx, value in enumerate(values):
        fraction = max(0.0, value / max_value)
        bar_h = fraction * (height - 40)
        bx0 = origin + idx * (bar_width + gap)
        bx1 = bx0 + bar_width
        by0 = bottom
        by1 = by0 - bar_h
        canvas.create_rectangle(bx0, by1, bx1, by0, fill="#5b8def", outline="#365f9c")
        canvas.create_text((bx0 + bx1) / 2, by1 - 12, text=f"{value:.2g}", font=("Helvetica", 8), fill="#333")
        canvas.create_text((bx0 + bx1) / 2, bottom + 4, text=str(idx + 1), anchor=tk.N, font=("Helvetica", 8), fill="#555")
    canvas.create_text(x + 8, y + 8, text=height_label, anchor=tk.NW, font=("Helvetica", 9), fill="#333")
