from __future__ import annotations

from .arithmetic_draw import (
    draw_count,
    draw_groups,
    draw_icon_grid,
    draw_icon_groups,
    draw_icon_split,
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


def render_arithmetic(panel) -> None:
    canvas = panel.canvas
    canvas.delete("all")
    w = max(10, canvas.winfo_width())
    h = max(10, canvas.winfo_height())
    style = panel.object_style_var.get()
    skill = panel.skill_var.get()

    if skill == "counting":
        count = panel.count_var.get()
        panel.expression_var.set(f"Count = {count}")
        bounds = (10, 10, w - 20, h - 20)
        icon = panel._openmoji_for(style, count, bounds)
        if icon is None:
            draw_count(canvas, count, style, bounds, "#5b8def")
        else:
            draw_icon_grid(canvas, count, icon, bounds)
        return
    if skill == "add_subtract":
        a = panel.a_var.get()
        b = panel.b_var.get()
        if panel.op_var.get() == "add":
            panel.expression_var.set(f"{a} + {b} = {a + b}")
            bounds = (10, 10, w - 20, h - 20)
            icon = panel._openmoji_for(style, max(a, b), (10, 10, (w - 20) // 2, h - 20))
            if icon is None:
                draw_split(canvas, a, b, style, bounds, "#67b26f", "#5b8def")
            else:
                draw_icon_split(canvas, a, b, icon, bounds)
        else:
            a = max(a, b)
            panel.expression_var.set(f"{a} - {b} = {a - b}")
            bounds = (10, 10, w - 20, h - 20)
            icon = panel._openmoji_for(style, max(a, b), (10, 10, (w - 20) // 2, h - 20))
            if icon is None:
                draw_split(canvas, a - b, b, style, bounds, "#67b26f", "#d0d7dd")
            else:
                draw_icon_split(canvas, a - b, b, icon, bounds)
        return
    if skill == "multiply":
        groups = panel.rows_var.get()
        per_group = panel.cols_var.get()
        panel.expression_var.set(f"{groups} x {per_group} = {groups * per_group}")
        bounds = (10, 10, w - 20, h - 20)
        cell_w, cell_h = group_cell_size(groups, bounds)
        icon = panel._openmoji_for(style, per_group, (0, 0, cell_w - 20, cell_h - 20))
        if icon is None:
            draw_groups(canvas, groups, per_group, style, bounds, "#5b8def")
        else:
            draw_icon_groups(canvas, groups, per_group, icon, bounds)
        return
    if skill == "divide":
        total = panel.total_var.get()
        groups = max(1, panel.groups_var.get())
        per_group = total // groups
        remainder = total % groups
        if remainder:
            panel.expression_var.set(f"{total} / {groups} = {per_group} R {remainder}")
        else:
            panel.expression_var.set(f"{total} / {groups} = {per_group}")
        bounds = (10, 10, w - 20, h - 60)
        cell_w, cell_h = group_cell_size(groups, bounds)
        icon = panel._openmoji_for(style, per_group, (0, 0, cell_w - 20, cell_h - 20))
        if icon is None:
            draw_groups(canvas, groups, per_group, style, bounds, "#67b26f")
        else:
            draw_icon_groups(canvas, groups, per_group, icon, bounds)
        if remainder > 0:
            tail_bounds = (10, h - 50, w - 20, 40)
            icon_tail = panel._openmoji_for(style, remainder, tail_bounds)
            if icon_tail is None:
                draw_count(canvas, remainder, style, tail_bounds, "#d0d7dd")
            else:
                draw_icon_grid(canvas, remainder, icon_tail, tail_bounds)
            canvas.create_text(10, h - 58, text=f"Remainder: {remainder}", anchor="w", fill="#666")
        return
    if skill == "ratios":
        a = panel.ratio_a_var.get()
        b = panel.ratio_b_var.get()
        panel.expression_var.set(f"{a} : {b}")
        bounds = (10, 10, w - 20, h - 20)
        if style in panel._openmoji_images:
            icon = panel._openmoji_for(style, max(a, b), (10, 10, (w - 20) // 2, h - 20))
            if icon is None:
                draw_ratio_bars(canvas, a, b, bounds, "#5b8def", "#f2b05e")
            else:
                draw_icon_split(canvas, a, b, icon, bounds)
        else:
            draw_ratio_bars(canvas, a, b, bounds, "#5b8def", "#f2b05e")
        return
    if skill == "fractions":
        numerator = max(0, min(panel.frac_num_var.get(), 36))
        denominator = max(1, min(panel.frac_den_var.get(), 12))
        if numerator != panel.frac_num_var.get():
            panel.frac_num_var.set(numerator)
        if denominator != panel.frac_den_var.get():
            panel.frac_den_var.set(denominator)
        panel.expression_var.set(_fraction_label(numerator, denominator))
        draw_fraction_circle(canvas, numerator, denominator, (10, 10, w - 20, h - 20))
        return


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
    if skill == "long_addition":
        a = panel.long_a_var.get()
        b = panel.long_b_var.get()
        panel.expression_var.set(f"Long addition: {a} + {b} = {a + b}")
        draw_long_addition(canvas, a, b, (10, 10, w - 20, h - 20))
        return
    if skill == "long_subtraction":
        a = panel.long_a_var.get()
        b = panel.long_b_var.get()
        big = max(a, b)
        small = min(a, b)
        panel.expression_var.set(f"Long subtraction: {big} - {small} = {big - small}")
        draw_long_subtraction(canvas, big, small, (10, 10, w - 20, h - 20))
        return
    if skill == "long_multiplication":
        a = panel.long_a_var.get()
        b = panel.long_b_var.get()
        panel.expression_var.set(f"Long multiplication: {a} x {b} = {a * b}")
        draw_long_multiplication(canvas, a, b, (10, 10, w - 20, h - 20))
        return
    if skill == "long_division":
        dividend = panel.long_a_var.get()
        divisor = max(1, panel.long_b_var.get())
        quotient = dividend // divisor
        remainder = dividend % divisor
        if remainder:
            panel.expression_var.set(f"Long division: {dividend} / {divisor} = {quotient} R {remainder}")
        else:
            panel.expression_var.set(f"Long division: {dividend} / {divisor} = {quotient}")
        draw_long_division(canvas, dividend, divisor, (10, 10, w - 20, h - 20))
        return
    if skill == "money":
        dollars = panel.money_dollars_var.get()
        cents = panel.money_cents_var.get()
        panel.expression_var.set(f"Money: ${dollars}.{cents:02d}")
        draw_money_breakdown(canvas, dollars, cents, (10, 10, w - 20, h - 20))
        return
