from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .arithmetic_draw import (
    draw_count,
    draw_groups,
    draw_icon_grid,
    draw_icon_groups,
    draw_icon_split,
    draw_bar_chart,
    draw_number_line,
    draw_right_triangle,
    draw_ratio_bars,
    draw_split,
    group_cell_size,
)
from .arithmetic_fractions import draw_fraction_circle
from .arithmetic_long import (
    draw_long_addition,
    draw_long_division,
    draw_long_multiplication,
    draw_long_subtraction,
    draw_money_breakdown,
)
from .theme import COLORS, SKILL_ACCENTS


@dataclass(slots=True)
class _RenderContext:
    panel: object
    canvas: object
    w: int
    h: int
    style: str


def _safe_eval_order(a: int, b: int, c: int, op1: str, op2: str, style: str) -> tuple[str, float]:
    def _apply(lhs: int, rhs: int, op: str) -> float:
        if op == "+":
            return lhs + rhs
        if op == "-":
            return lhs - rhs
        return lhs * rhs

    op1 = op1 if op1 in {"+", "-", "*"} else "+"
    op2 = op2 if op2 in {"+", "-", "*"} else "+"
    if style == "a op (b op c)":
        inner = _apply(b, c, op2)
        expr = f"{a} {op1} ({b} {op2} {c})"
        return expr, _apply(a, int(inner), op1)
    expr = f"({a} {op1} {b}) {op2} {c}"
    left = _apply(a, b, op1)
    return expr, _apply(int(left), c, op2)


def _format_probability(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "0"
    if numerator % denominator == 0:
        return f"{numerator // denominator}"
    return f"{numerator}/{denominator}"


def _draw_slope_line(
    canvas, x1: int, y1: int, x2: int, y2: int, bounds: tuple[int, int, int, int]
) -> None:
    x0, y0, width, height = bounds
    padding = 20
    min_x = min(x1, x2) - 1
    max_x = max(x1, x2) + 1
    min_y = min(y1, y2) - 1
    max_y = max(y1, y2) + 1
    x_range = max(1, max_x - min_x)
    y_range = max(1, max_y - min_y)
    px_per_x = max(1.0, (width - 2 * padding) / x_range)
    px_per_y = max(1.0, (height - 2 * padding) / y_range)
    scale = min(px_per_x, px_per_y)
    cx1 = int(x0 + padding + (x1 - min_x) * scale)
    cy1 = int(y0 + height - padding - (y1 - min_y) * scale)
    cx2 = int(x0 + padding + (x2 - min_x) * scale)
    cy2 = int(y0 + height - padding - (y2 - min_y) * scale)
    canvas.create_line(cx1, cy1, cx2, cy2, fill="#2e7d32", width=2)
    canvas.create_oval(cx1 - 4, cy1 - 4, cx1 + 4, cy1 + 4, fill=SKILL_ACCENTS.get("counting", "#5b8def"), outline="")
    canvas.create_oval(cx2 - 4, cy2 - 4, cx2 + 4, cy2 + 4, fill=SKILL_ACCENTS.get("counting", "#5b8def"), outline="")
    canvas.create_text(cx1, cy1 - 12, text=f"({x1}, {y1})", fill=COLORS["text_primary"], font=("Helvetica", 9))
    canvas.create_text(cx2, cy2 + 12, text=f"({x2}, {y2})", fill=COLORS["text_primary"], font=("Helvetica", 9))


def _draw_algebra_balance(canvas, a: int, b: int, rhs: int, x_value: float, bounds: tuple[int, int, int, int]) -> None:
    x0, y0, w, h = bounds
    left = x0 + 24
    right = x0 + w - 24
    mid = (left + right) // 2
    beam_y = y0 + int(h * 0.38)
    pan_y = beam_y + 24

    canvas.create_line(left, beam_y, right, beam_y, fill="#55697f", width=3)
    canvas.create_polygon(mid - 18, beam_y + 3, mid + 18, beam_y + 3, mid, beam_y + 32, fill="#8ea0b2", outline="")

    left_pan_x0 = left + 10
    left_pan_x1 = mid - 24
    right_pan_x0 = mid + 24
    right_pan_x1 = right - 10
    canvas.create_rectangle(left_pan_x0, pan_y, left_pan_x1, pan_y + 12, fill="#d9e4ef", outline="#a7b6c2")
    canvas.create_rectangle(right_pan_x0, pan_y, right_pan_x1, pan_y + 12, fill="#d9e4ef", outline="#a7b6c2")

    x_blocks = max(1, min(6, abs(a)))
    const_blocks = max(0, min(6, abs(b)))
    rhs_blocks = max(0, min(8, abs(rhs)))

    block_w = 18
    block_h = 14
    lx = left_pan_x0 + 8
    for _ in range(x_blocks):
        canvas.create_rectangle(lx, pan_y - 20, lx + block_w, pan_y - 20 + block_h, fill="#67b26f", outline="")
        canvas.create_text(lx + block_w / 2, pan_y - 13, text="x", fill="#ffffff", font=("Helvetica", 8, "bold"))
        lx += block_w + 4

    for _ in range(const_blocks):
        canvas.create_rectangle(lx, pan_y - 20, lx + block_w, pan_y - 20 + block_h, fill="#5b8def", outline="")
        lx += block_w + 3

    rx = right_pan_x0 + 8
    for _ in range(rhs_blocks):
        canvas.create_rectangle(rx, pan_y - 20, rx + block_w, pan_y - 20 + block_h, fill="#5b8def", outline="")
        rx += block_w + 3

    if a < 0:
        canvas.create_text(left_pan_x0 + 4, pan_y - 28, text="−", anchor="w", fill=COLORS["danger"], font=("Helvetica", 10, "bold"))
    if b < 0:
        canvas.create_text(left_pan_x0 + 4 + x_blocks * (block_w + 4), pan_y - 28, text="−", anchor="w", fill=COLORS["danger"], font=("Helvetica", 10, "bold"))
    if rhs < 0:
        canvas.create_text(right_pan_x0 + 4, pan_y - 28, text="−", anchor="w", fill=COLORS["danger"], font=("Helvetica", 10, "bold"))

    step1 = f"1) {a}x + {b} = {rhs}"
    step2 = f"2) {a}x = {rhs - b}"
    step3 = f"3) x = ({rhs - b})/{a} = {x_value:.2f}"
    canvas.create_text(x0 + 10, y0 + int(h * 0.62), text=step1, anchor="w", fill=COLORS["text_primary"], font=("Helvetica", 9, "bold"))
    canvas.create_text(x0 + 10, y0 + int(h * 0.73), text=step2, anchor="w", fill=COLORS["text_secondary"], font=("Helvetica", 9))
    canvas.create_text(x0 + 10, y0 + int(h * 0.84), text=step3, anchor="w", fill=COLORS["accent_strong"], font=("Helvetica", 9))


def _render_counting(ctx: _RenderContext) -> None:
    panel = ctx.panel
    count = panel.count_var.get()
    panel.expression_var.set(f"Count = {count}")
    bounds = (10, 10, ctx.w - 20, ctx.h - 20)
    icon = panel._openmoji_for(ctx.style, count, bounds)
    if icon is None:
        draw_count(ctx.canvas, count, ctx.style, bounds, SKILL_ACCENTS.get("counting", "#5b8def"))
    else:
        draw_icon_grid(ctx.canvas, count, icon, bounds)


def _render_place_value(ctx: _RenderContext) -> None:
    panel = ctx.panel
    value = max(0, panel.long_a_var.get())
    if value != panel.long_a_var.get():
        panel.long_a_var.set(value)
    places = (
        ("Thousands", (value // 1000) % 10, 1000, "#7aa5ff"),
        ("Hundreds", (value // 100) % 10, 100, "#67b26f"),
        ("Tens", (value // 10) % 10, 10, "#f2b05e"),
        ("Ones", value % 10, 1, "#d96d6d"),
    )
    terms = [f"{digit * unit}" for _label, digit, unit, _color in places if digit > 0]
    expanded = " + ".join(terms) if terms else "0"
    panel.expression_var.set(f"Place value: {value} = {expanded}")

    x0 = 10
    y0 = 16
    width = max(80, (ctx.w - 20) // len(places))
    height = ctx.h - 32
    for idx, (label, digit, unit, color) in enumerate(places):
        left = x0 + idx * width
        inner = (left + 8, y0 + 34, width - 16, max(48, height - 86))
        ctx.canvas.create_rectangle(left + 4, y0 + 20, left + width - 4, y0 + height, outline="#c7cfd6")
        ctx.canvas.create_text(left + width / 2, y0 + 12, text=label, fill=COLORS["text_primary"], font=("Helvetica", 10, "bold"))
        ctx.canvas.create_text(
            left + width / 2,
            y0 + height - 28,
            text=f"{digit} x {unit} = {digit * unit}",
            fill=COLORS["text_secondary"],
            font=("Helvetica", 9),
        )
        if digit > 0:
            icon = panel._openmoji_for(ctx.style, digit, inner)
            if icon is None:
                draw_count(ctx.canvas, digit, ctx.style, inner, color)
            else:
                draw_icon_grid(ctx.canvas, digit, icon, inner)
        else:
            ctx.canvas.create_text(
                left + width / 2,
                y0 + height / 2,
                text="0",
                fill=COLORS["text_muted"],
                font=("Helvetica", 16, "bold"),
            )


def _render_add_subtract(ctx: _RenderContext) -> None:
    panel = ctx.panel
    a = panel.a_var.get()
    b = panel.b_var.get()
    bounds = (10, 10, ctx.w - 20, ctx.h - 20)
    icon = panel._openmoji_for(ctx.style, max(a, b), (10, 10, (ctx.w - 20) // 2, ctx.h - 20))
    if panel.op_var.get() == "add":
        panel.expression_var.set(f"{a} + {b} = {a + b}")
        if icon is None:
            draw_split(
                ctx.canvas,
                a,
                b,
                ctx.style,
                bounds,
                SKILL_ACCENTS.get("add_subtract", "#67b26f"),
                SKILL_ACCENTS.get("counting", "#5b8def"),
            )
        else:
            draw_icon_split(ctx.canvas, a, b, icon, bounds)
        return

    a = max(a, b)
    panel.expression_var.set(f"{a} - {b} = {a - b}")
    if icon is None:
        draw_split(ctx.canvas, a - b, b, ctx.style, bounds, SKILL_ACCENTS.get("add_subtract", "#67b26f"), "#d0d7dd")
    else:
        draw_icon_split(ctx.canvas, a - b, b, icon, bounds)


def _render_multiply(ctx: _RenderContext) -> None:
    panel = ctx.panel
    groups = panel.rows_var.get()
    per_group = panel.cols_var.get()
    panel.expression_var.set(f"{groups} x {per_group} = {groups * per_group}")
    bounds = (10, 10, ctx.w - 20, ctx.h - 20)
    cell_w, cell_h = group_cell_size(groups, bounds)
    icon = panel._openmoji_for(ctx.style, per_group, (0, 0, cell_w - 20, cell_h - 20))
    if icon is None:
        draw_groups(ctx.canvas, groups, per_group, ctx.style, bounds, SKILL_ACCENTS.get("multiply", "#5b8def"))
    else:
        draw_icon_groups(ctx.canvas, groups, per_group, icon, bounds)


def _render_divide(ctx: _RenderContext) -> None:
    panel = ctx.panel
    total = panel.total_var.get()
    groups = max(1, panel.groups_var.get())
    per_group = total // groups
    remainder = total % groups
    if remainder:
        panel.expression_var.set(f"{total} / {groups} = {per_group} R {remainder}")
    else:
        panel.expression_var.set(f"{total} / {groups} = {per_group}")

    bounds = (10, 10, ctx.w - 20, ctx.h - 60)
    cell_w, cell_h = group_cell_size(groups, bounds)
    icon = panel._openmoji_for(ctx.style, per_group, (0, 0, cell_w - 20, cell_h - 20))
    if icon is None:
        draw_groups(ctx.canvas, groups, per_group, ctx.style, bounds, SKILL_ACCENTS.get("divide", "#67b26f"))
    else:
        draw_icon_groups(ctx.canvas, groups, per_group, icon, bounds)

    if remainder > 0:
        tail_bounds = (10, ctx.h - 50, ctx.w - 20, 40)
        icon_tail = panel._openmoji_for(ctx.style, remainder, tail_bounds)
        if icon_tail is None:
            draw_count(ctx.canvas, remainder, ctx.style, tail_bounds, "#d0d7dd")
        else:
            draw_icon_grid(ctx.canvas, remainder, icon_tail, tail_bounds)
        ctx.canvas.create_text(10, ctx.h - 58, text=f"Remainder: {remainder}", anchor="w", fill=COLORS["text_muted"])


def _render_ratios(ctx: _RenderContext) -> None:
    panel = ctx.panel
    a = panel.ratio_a_var.get()
    b = panel.ratio_b_var.get()
    panel.expression_var.set(f"{a} : {b}")
    bounds = (10, 10, ctx.w - 20, ctx.h - 20)
    if ctx.style in panel._openmoji_images:
        icon = panel._openmoji_for(ctx.style, max(a, b), (10, 10, (ctx.w - 20) // 2, ctx.h - 20))
        if icon is None:
            draw_ratio_bars(
                ctx.canvas,
                a,
                b,
                bounds,
                SKILL_ACCENTS.get("counting", "#5b8def"),
                SKILL_ACCENTS.get("ratios", "#f2b05e"),
            )
        else:
            draw_icon_split(ctx.canvas, a, b, icon, bounds)
        return
    draw_ratio_bars(
        ctx.canvas,
        a,
        b,
        bounds,
        SKILL_ACCENTS.get("counting", "#5b8def"),
        SKILL_ACCENTS.get("ratios", "#f2b05e"),
    )


def _render_fractions(ctx: _RenderContext) -> None:
    panel = ctx.panel
    numerator = max(0, min(panel.frac_num_var.get(), 36))
    denominator = max(1, min(panel.frac_den_var.get(), 12))
    if numerator != panel.frac_num_var.get():
        panel.frac_num_var.set(numerator)
    if denominator != panel.frac_den_var.get():
        panel.frac_den_var.set(denominator)
    panel.expression_var.set(_fraction_label(numerator, denominator))
    draw_fraction_circle(ctx.canvas, numerator, denominator, (10, 10, ctx.w - 20, ctx.h - 20))


def _render_long_addition(ctx: _RenderContext) -> None:
    panel = ctx.panel
    a = panel.long_a_var.get()
    b = panel.long_b_var.get()
    panel.expression_var.set(f"Long addition: {a} + {b} = {a + b}")
    draw_long_addition(ctx.canvas, a, b, (10, 10, ctx.w - 20, ctx.h - 20))


def _render_long_subtraction(ctx: _RenderContext) -> None:
    panel = ctx.panel
    a = panel.long_a_var.get()
    b = panel.long_b_var.get()
    big = max(a, b)
    small = min(a, b)
    panel.expression_var.set(f"Long subtraction: {big} - {small} = {big - small}")
    draw_long_subtraction(ctx.canvas, big, small, (10, 10, ctx.w - 20, ctx.h - 20))


def _render_long_multiplication(ctx: _RenderContext) -> None:
    panel = ctx.panel
    a = panel.long_a_var.get()
    b = panel.long_b_var.get()
    panel.expression_var.set(f"Long multiplication: {a} x {b} = {a * b}")
    draw_long_multiplication(ctx.canvas, a, b, (10, 10, ctx.w - 20, ctx.h - 20))


def _render_long_division(ctx: _RenderContext) -> None:
    panel = ctx.panel
    dividend = panel.long_a_var.get()
    divisor = max(1, panel.long_b_var.get())
    quotient = dividend // divisor
    remainder = dividend % divisor
    if remainder:
        panel.expression_var.set(f"Long division: {dividend} / {divisor} = {quotient} R {remainder}")
    else:
        panel.expression_var.set(f"Long division: {dividend} / {divisor} = {quotient}")
    draw_long_division(ctx.canvas, dividend, divisor, (10, 10, ctx.w - 20, ctx.h - 20))


def _render_money(ctx: _RenderContext) -> None:
    panel = ctx.panel
    dollars = panel.money_dollars_var.get()
    cents = panel.money_cents_var.get()
    panel.expression_var.set(f"Money: ${dollars}.{cents:02d}")
    draw_money_breakdown(ctx.canvas, dollars, cents, (10, 10, ctx.w - 20, ctx.h - 20))


def _render_measurement(ctx: _RenderContext) -> None:
    panel = ctx.panel
    amount = max(0, panel.long_a_var.get())
    factor = max(1, panel.long_b_var.get())
    subskill = (panel.subskill_var.get() or "").lower()
    if "time" in subskill or "elapsed" in subskill:
        whole_label = "hour"
        part_label = "minutes"
    elif "metric" in subskill:
        whole_label = "meter"
        part_label = "centimeters"
    else:
        whole_label = "foot"
        part_label = "inches"
    total = amount * factor
    whole_suffix = "" if amount == 1 else "s"
    panel.expression_var.set(
        f"{amount} {whole_label}{whole_suffix} = {amount} x {factor} {part_label} = {total} {part_label}"
    )

    left = 18
    top = 28
    box_w = max(68, min(120, (ctx.w - 40) // max(1, min(amount, 6))))
    box_h = 56
    shown = min(amount, 6)
    for idx in range(shown):
        x0 = left + idx * box_w
        x1 = x0 + box_w - 10
        ctx.canvas.create_rectangle(x0, top, x1, top + box_h, fill="#eef4fb", outline="#9bb3c8")
        ctx.canvas.create_text(
            (x0 + x1) / 2,
            top + 16,
            text=f"1 {whole_label}",
            fill=COLORS["text_primary"],
            font=("Helvetica", 9, "bold"),
        )
        ctx.canvas.create_text(
            (x0 + x1) / 2,
            top + 36,
            text=f"{factor} {part_label}",
            fill=COLORS["text_secondary"],
            font=("Helvetica", 9),
        )
    if amount > shown:
        ctx.canvas.create_text(
            ctx.w - 56,
            top + 28,
            text=f"+ {amount - shown} more",
            fill=COLORS["text_muted"],
            font=("Helvetica", 9, "italic"),
        )
    ctx.canvas.create_text(
        18,
        top + box_h + 26,
        text=f"Total converted amount: {total} {part_label}",
        anchor="w",
        fill=COLORS["accent_strong"],
        font=("Helvetica", 11, "bold"),
    )


def _render_integers(ctx: _RenderContext) -> None:
    panel = ctx.panel
    a = panel.int_a_var.get()
    b = panel.int_b_var.get()
    c = panel.int_c_var.get()
    op1 = panel.int_op1_var.get() if panel.int_op1_var.get() in {"+", "-", "*"} else "+"
    op2 = panel.int_op2_var.get() if panel.int_op2_var.get() in {"+", "-", "*"} else "+"
    first = a + b if op1 == "+" else a - b if op1 == "-" else a * b
    value = first + c if op2 == "+" else first - c if op2 == "-" else first * c
    panel.expression_var.set(f"{a} {op1} {b} {op2} {c} = {value}")
    draw_number_line(ctx.canvas, [a, b, c, value], (10, 10, ctx.w - 20, ctx.h - 50), span=15)


def _render_order_of_operations(ctx: _RenderContext) -> None:
    panel = ctx.panel
    a = panel.int_a_var.get()
    b = panel.int_b_var.get()
    c = panel.int_c_var.get()
    op1 = panel.int_op1_var.get() if panel.int_op1_var.get() in {"+", "-", "*"} else "+"
    op2 = panel.int_op2_var.get() if panel.int_op2_var.get() in {"+", "-", "*"} else "+"
    expr, value = _safe_eval_order(a, b, c, op1, op2, panel.order_shape_var.get())
    panel.expression_var.set(f"{expr} = {value}")
    ctx.canvas.create_text(
        12,
        16,
        text="Order: parentheses first, then ×, then +/−",
        anchor="w",
        fill=COLORS["text_secondary"],
    )
    draw_number_line(ctx.canvas, [a, b, c, int(value)], (10, 30, ctx.w - 20, ctx.h - 70), span=15)


def _render_pre_algebra(ctx: _RenderContext) -> None:
    panel = ctx.panel
    subskill = panel.subskill_var.get()
    if subskill == "Ratios, rates, and proportional relationships":
        _render_ratios(ctx)
        return
    if subskill == "Integer and fraction fluency":
        _render_integers(ctx)
        return
    if subskill == "Percent problems":
        _render_stats_percent(ctx)
        return
    if subskill in {
        "One-step equations",
        "Two-step equations and inequalities",
        "Coordinate plane and function tables",
    }:
        _render_algebra_linear(ctx)
        return
    _render_order_of_operations(ctx)


def _render_algebra_linear(ctx: _RenderContext) -> None:
    panel = ctx.panel
    a = panel.algebra_a_var.get()
    b = panel.algebra_b_var.get()
    rhs = panel.algebra_c_var.get()
    if a == 0:
        a = 1
        panel.algebra_a_var.set(1)
    x_value = (rhs - b) / a
    panel.expression_var.set(f"Solve: {a}x + {b} = {rhs}; x = ({rhs} - {b}) / {a} = {x_value:.2f}")
    _draw_algebra_balance(ctx.canvas, a, b, rhs, x_value, (10, 10, ctx.w - 20, ctx.h - 20))


def _render_geometry_area(ctx: _RenderContext) -> None:
    panel = ctx.panel
    shape = panel.geom_shape_var.get()
    if shape == "triangle":
        width = max(1, panel.geom_width_var.get())
        height_value = max(1, panel.geom_height_var.get())
        panel.expression_var.set(f"Triangle area: 1/2 × {width} × {height_value}")
        draw_right_triangle(ctx.canvas, height_value, width, width + height_value, (10, 10, ctx.w - 20, ctx.h - 30))
        return

    width = max(1, panel.geom_width_var.get())
    height_value = max(1, panel.geom_height_var.get())
    if shape == "square":
        width = max(1, panel.geom_side_var.get())
        height_value = width
    panel.expression_var.set(f"Area = {width} × {height_value} = {width * height_value}")
    scale = min((ctx.w - 40) / max(1, width), (ctx.h - 40) / max(1, height_value), 24)
    cell_w = int(scale)
    cell_h = int(scale)
    x0 = (ctx.w - width * cell_w) / 2
    y0 = (ctx.h - height_value * cell_h) / 2
    for i in range(height_value):
        for j in range(width):
            ctx.canvas.create_rectangle(
                x0 + j * cell_w,
                y0 + i * cell_h,
                x0 + (j + 1) * cell_w,
                y0 + (i + 1) * cell_h,
                outline=SKILL_ACCENTS.get("geometry_area", "#5b8def"),
            )


def _render_geometry_shapes(ctx: _RenderContext) -> None:
    panel = ctx.panel
    panel.expression_var.set("Shapes: attributes, composition, and equal shares")
    accent = SKILL_ACCENTS.get("geometry_shapes", "#5b8def")
    x0 = ctx.w * 0.12
    y0 = ctx.h * 0.20
    size = min(ctx.w, ctx.h) * 0.22
    ctx.canvas.create_polygon(
        x0 + size / 2,
        y0,
        x0,
        y0 + size,
        x0 + size,
        y0 + size,
        fill="#dff0ff",
        outline=accent,
        width=2,
    )
    ctx.canvas.create_text(x0 + size / 2, y0 + size + 18, text="3 sides", fill=COLORS["text_primary"])
    rx = ctx.w * 0.46
    ctx.canvas.create_rectangle(rx, y0, rx + size * 1.45, y0 + size, fill="#e8f6df", outline=accent, width=2)
    ctx.canvas.create_line(rx + size * 0.72, y0, rx + size * 0.72, y0 + size, fill=accent, dash=(4, 3))
    ctx.canvas.create_text(
        rx + size * 0.72,
        y0 + size + 18,
        text="2 squares compose a rectangle",
        fill=COLORS["text_primary"],
    )


def _render_data_displays(ctx: _RenderContext) -> None:
    panel = ctx.panel
    values = [max(0, panel.mean_a_var.get()), max(0, panel.mean_b_var.get()), max(0, panel.mean_c_var.get())]
    if values == [0, 0, 0]:
        values = [3, 5, 2]
    panel.expression_var.set(f"Data display: A={values[0]}, B={values[1]}, C={values[2]}")
    draw_bar_chart(ctx.canvas, [float(v) for v in values], (10, 10, ctx.w - 20, ctx.h - 55), height_label="Category count")
    labels = ("A", "B", "C")
    for idx, label in enumerate(labels):
        ctx.canvas.create_text(34 + idx * 46, ctx.h - 28, text=label, fill=COLORS["text_primary"])


def _render_trig(ctx: _RenderContext) -> None:
    panel = ctx.panel
    a = panel.trig_opp_var.get()
    b = panel.trig_adj_var.get()
    c = panel.trig_hyp_var.get()
    if a <= 0:
        a = 1
        panel.trig_opp_var.set(a)
    if b <= 0:
        b = 1
        panel.trig_adj_var.set(b)
    if c <= 0:
        c = a + b
        panel.trig_hyp_var.set(c)
    ratio = panel.trig_func_var.get() or "sin"
    if ratio == "cos":
        value = b / c
        numerator, denominator = b, c
        label = f"cos θ = {b}/{c}"
    elif ratio == "tan":
        value = a / b if b else 0.0
        numerator, denominator = a, b
        label = f"tan θ = {a}/{b}"
    else:
        value = a / c if c else 0.0
        numerator, denominator = a, c
        label = f"sin θ = {a}/{c}"
    panel.expression_var.set(f"{label} = {_format_probability(int(numerator), int(denominator))} = {value:.2f}")
    draw_right_triangle(ctx.canvas, a, b, c, (10, 10, ctx.w - 20, ctx.h - 40))


def _render_stats_percent(ctx: _RenderContext) -> None:
    panel = ctx.panel
    percent = panel.percent_value_var.get()
    total = max(1, panel.percent_total_var.get())
    value = percent * total / 100
    panel.expression_var.set(f"What is {percent}% of {total}?")
    draw_bar_chart(ctx.canvas, [value, total - value], (10, 10, ctx.w - 20, ctx.h - 40), height_label="Percent split")


def _render_stats_mean(ctx: _RenderContext) -> None:
    panel = ctx.panel
    count = max(2, min(5, panel.mean_count_var.get()))
    values = [
        panel.mean_a_var.get(),
        panel.mean_b_var.get(),
        panel.mean_c_var.get(),
        panel.mean_d_var.get(),
        panel.mean_e_var.get(),
    ]
    used = values[:count]
    average = sum(used) / count
    panel.expression_var.set(f"Mean of {count} values: {average:.2f}")
    draw_bar_chart(ctx.canvas, [float(v) for v in used], (10, 10, ctx.w - 20, ctx.h - 50), height_label="Value set")


def _render_stats_probability(ctx: _RenderContext) -> None:
    panel = ctx.panel
    success = max(0, panel.prob_success_var.get())
    total = max(1, panel.prob_total_var.get())
    if success > total:
        success = total
        panel.prob_success_var.set(success)
    panel.expression_var.set(f"P = {success}/{total} = {_format_probability(success, total)}")
    ctx.canvas.create_text(14, 18, text=f"Successes: {success}", anchor="w", fill=COLORS["success"])
    ctx.canvas.create_text(14, 34, text=f"Total outcomes: {total}", anchor="w", fill=COLORS["success"])


def _render_calculus_slope(ctx: _RenderContext) -> None:
    panel = ctx.panel
    x1 = panel.slope_x1_var.get()
    y1 = panel.slope_y1_var.get()
    x2 = panel.slope_x2_var.get()
    y2 = panel.slope_y2_var.get()
    if x2 == x1:
        x2 += 1
        panel.slope_x2_var.set(x2)
    slope = (y2 - y1) / (x2 - x1)
    panel.expression_var.set(f"m = ({y2} - {y1})/({x2} - {x1}) = {slope:.2f}")
    _draw_slope_line(ctx.canvas, x1, y1, x2, y2, (10, 10, ctx.w - 20, ctx.h - 40))


SKILL_RENDERERS: dict[str, Callable[[_RenderContext], None]] = {
    "counting": _render_counting,
    "place_value": _render_place_value,
    "add_subtract": _render_add_subtract,
    "multiply": _render_multiply,
    "divide": _render_divide,
    "ratios": _render_ratios,
    "fractions": _render_fractions,
    "long_addition": _render_long_addition,
    "long_subtraction": _render_long_subtraction,
    "long_multiplication": _render_long_multiplication,
    "long_division": _render_long_division,
    "money": _render_money,
    "measurement": _render_measurement,
    "integers": _render_integers,
    "order_of_operations": _render_order_of_operations,
    "pre_algebra": _render_pre_algebra,
    "algebra_linear": _render_algebra_linear,
    "algebra_1": _render_algebra_linear,
    "algebra_2": _render_algebra_linear,
    "geometry_shapes": _render_geometry_shapes,
    "geometry_area": _render_geometry_area,
    "data_displays": _render_data_displays,
    "trig_right_triangle": _render_trig,
    "stats_percent": _render_stats_percent,
    "stats_mean": _render_stats_mean,
    "stats_probability": _render_stats_probability,
    "calculus_1": _render_calculus_slope,
    "calculus_slope": _render_calculus_slope,
}


def render_arithmetic(panel) -> None:
    canvas = panel.canvas
    canvas.delete("all")
    w = max(10, canvas.winfo_width())
    h = max(10, canvas.winfo_height())
    ctx = _RenderContext(panel=panel, canvas=canvas, w=w, h=h, style=panel.object_style_var.get())
    skill = panel.skill_var.get()
    renderer = SKILL_RENDERERS.get(skill)
    if renderer is not None:
        renderer(ctx)


def _fraction_label(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return f"{numerator}/0"
    if numerator < denominator:
        return f"{numerator}/{denominator}"
    whole = numerator // denominator
    remainder = numerator % denominator
    if remainder == 0:
        return f"{numerator}/{denominator} = {whole}"
    return f"{numerator}/{denominator} = {whole} {remainder}/{denominator}"
