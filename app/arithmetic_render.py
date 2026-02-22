from __future__ import annotations

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
        return expr, _apply(a, int(inner), op1) if op1 in {"+", "-"} else _apply(a, int(inner), op1)
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
    canvas.create_oval(cx1 - 4, cy1 - 4, cx1 + 4, cy1 + 4, fill="#5b8def", outline="")
    canvas.create_oval(cx2 - 4, cy2 - 4, cx2 + 4, cy2 + 4, fill="#5b8def", outline="")
    canvas.create_text(cx1, cy1 - 12, text=f"({x1}, {y1})", fill="#2a2a2a", font=("Helvetica", 9))
    canvas.create_text(cx2, cy2 + 12, text=f"({x2}, {y2})", fill="#2a2a2a", font=("Helvetica", 9))


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
    if skill == "integers":
        a = panel.int_a_var.get()
        b = panel.int_b_var.get()
        c = panel.int_c_var.get()
        op1 = panel.int_op1_var.get() if panel.int_op1_var.get() in {"+", "-", "*"} else "+"
        op2 = panel.int_op2_var.get() if panel.int_op2_var.get() in {"+", "-", "*"} else "+"
        first = a + b if op1 == "+" else a - b if op1 == "-" else a * b
        value = first + c if op2 == "+" else first - c if op2 == "-" else first * c
        panel.expression_var.set(f"{a} {op1} {b} {op2} {c} = {value}")
        draw_number_line(canvas, [a, b, c, value], (10, 10, w - 20, h - 50), span=15)
        return
    if skill == "order_of_operations":
        a = panel.int_a_var.get()
        b = panel.int_b_var.get()
        c = panel.int_c_var.get()
        op1 = panel.int_op1_var.get() if panel.int_op1_var.get() in {"+", "-", "*"} else "+"
        op2 = panel.int_op2_var.get() if panel.int_op2_var.get() in {"+", "-", "*"} else "+"
        expr, value = _safe_eval_order(a, b, c, op1, op2, panel.order_shape_var.get())
        panel.expression_var.set(f"{expr} = {value}")
        canvas.create_text(12, 16, text="Order: parentheses first, then ×, then +/−", anchor=tk.W, fill="#4f6b7a")
        draw_number_line(canvas, [a, b, c, int(value)], (10, 30, w - 20, h - 70), span=15)
        return
    if skill == "algebra_linear":
        a = panel.algebra_a_var.get()
        b = panel.algebra_b_var.get()
        rhs = panel.algebra_c_var.get()
        if a == 0:
            a = 1
            panel.algebra_a_var.set(1)
        x = (rhs - b) / a
        panel.expression_var.set(f"Solve: {a}x + {b} = {rhs}; x = ({rhs} - {b}) / {a} = {x:.2f}")
        # Simple balance line graphic
        left = 20
        top = h // 2
        canvas.create_line(left, top, w - 20, top, fill="#666", width=2)
        canvas.create_text(left + 10, top - 20, text="Balance point intuition", fill="#2f6f3e", font=("Helvetica", 9))
        canvas.create_text(w // 2, top + 12, text=f"target height: {rhs}", fill="#333")
        return
    if skill == "geometry_area":
        shape = panel.geom_shape_var.get()
        if shape == "triangle":
            width = max(1, panel.geom_width_var.get())
            height_value = max(1, panel.geom_height_var.get())
            panel.expression_var.set(f"Triangle area: 1/2 × {width} × {height_value}")
            draw_right_triangle(canvas, height_value, width, width + height_value, (10, 10, w - 20, h - 30))
        else:
            width = max(1, panel.geom_width_var.get())
            height_value = max(1, panel.geom_height_var.get())
            if shape == "square":
                width = max(1, panel.geom_side_var.get())
                height_value = width
            panel.expression_var.set(f"Area = {width} × {height_value} = {width * height_value}")
            scale = min((w - 40) / max(1, width), (h - 40) / max(1, height_value), 24)
            cell_w = int(scale)
            cell_h = int(scale)
            x0 = (w - width * cell_w) / 2
            y0 = (h - height_value * cell_h) / 2
            for i in range(height_value):
                for j in range(width):
                    canvas.create_rectangle(
                        x0 + j * cell_w,
                        y0 + i * cell_h,
                        x0 + (j + 1) * cell_w,
                        y0 + (i + 1) * cell_h,
                        outline="#5b8def",
                    )
        return
    if skill == "trig_right_triangle":
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
            label = f"cos θ = {b}/{c}"
        elif ratio == "tan":
            value = a / b if b else 0.0
            label = f"tan θ = {a}/{b}"
        else:
            value = a / c if c else 0.0
            label = f"sin θ = {a}/{c}"
        panel.expression_var.set(f"{label} = {_format_probability(int(a), int(c) if ratio == 'sin' else (int(b) if ratio == 'cos' else int(b)))} = {value:.2f}")
        draw_right_triangle(canvas, a, b, c, (10, 10, w - 20, h - 40))
        return
    if skill == "stats_percent":
        percent = panel.percent_value_var.get()
        total = max(1, panel.percent_total_var.get())
        value = percent * total / 100
        panel.expression_var.set(f"What is {percent}% of {total}?")
        draw_bar_chart(canvas, [value, total - value], (10, 10, w - 20, h - 40), height_label="Percent split")
        return
    if skill == "stats_mean":
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
        draw_bar_chart(canvas, [float(v) for v in used], (10, 10, w - 20, h - 50), height_label="Value set")
        return
    if skill == "stats_probability":
        success = max(0, panel.prob_success_var.get())
        total = max(1, panel.prob_total_var.get())
        if success > total:
            success = total
            panel.prob_success_var.set(success)
        panel.expression_var.set(f"P = {success}/{total} = {_format_probability(success, total)}")
        canvas.create_text(14, 18, text=f"Successes: {success}", anchor=tk.W, fill="#2f6f3e")
        canvas.create_text(14, 34, text=f"Total outcomes: {total}", anchor=tk.W, fill="#2f6f3e")
        return
    if skill in {"calculus_1", "calculus_slope"}:
        x1 = panel.slope_x1_var.get()
        y1 = panel.slope_y1_var.get()
        x2 = panel.slope_x2_var.get()
        y2 = panel.slope_y2_var.get()
        if x2 == x1:
            x2 += 1
            panel.slope_x2_var.set(x2)
        slope = (y2 - y1) / (x2 - x1)
        panel.expression_var.set(f"m = ({y2} - {y1})/({x2} - {x1}) = {slope:.2f}")
        _draw_slope_line(canvas, x1, y1, x2, y2, (10, 10, w - 20, h - 40))
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
