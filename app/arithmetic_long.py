from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont


def draw_long_addition(canvas: tk.Canvas, a: int, b: int, bounds: tuple[int, int, int, int]) -> None:
    result = a + b
    _draw_long_add_sub(canvas, a, b, "+", result, bounds, show_carry=True)


def draw_long_subtraction(canvas: tk.Canvas, a: int, b: int, bounds: tuple[int, int, int, int]) -> None:
    big = max(a, b)
    small = min(a, b)
    result = big - small
    _draw_long_add_sub(canvas, big, small, "-", result, bounds, show_borrow=True)


def draw_long_multiplication(canvas: tk.Canvas, a: int, b: int, bounds: tuple[int, int, int, int]) -> None:
    partial_rows = _multiplication_partials(a, b)
    result = a * b

    width = max(
        len(str(a)),
        len(str(b)) + 1,
        len(str(result)),
        max(len(str(value)) for value, _shift in partial_rows),
    )
    width += 1
    font, small_font, char_w, line_h = _fonts(bounds, width)
    text_width = width * char_w
    x0, y0, w, h = bounds
    start_x = x0 + max(0, int((w - text_width) / 2))

    lines = [str(a).rjust(width), f"x{b}".rjust(width)]
    separator_after_inputs = 1
    if len(partial_rows) == 1:
        lines += [str(result).rjust(width)]
        separator_before_result = None
    else:
        lines += [str(value).rjust(width) for value, _shift in partial_rows]
        separator_before_result = len(lines) - 1
        lines += [str(result).rjust(width)]

    total_lines = len(lines) + 2
    start_y = y0 + max(0, int((h - total_lines * line_h) / 2))

    for idx, line in enumerate(lines):
        y = start_y + idx * line_h
        canvas.create_text(start_x, y, text=line, font=font, anchor=tk.NW, fill="#2a2a2a")

    y_line = start_y + separator_after_inputs * line_h + int(line_h * 0.82)
    canvas.create_line(start_x, y_line, start_x + text_width, y_line, fill="#2a2a2a", width=2)
    if separator_before_result is not None:
        y_line = start_y + separator_before_result * line_h + int(line_h * 0.82)
        canvas.create_line(start_x, y_line, start_x + text_width, y_line, fill="#2a2a2a", width=2)

    _draw_note(canvas, bounds, f"{a} x {b} = {result}")


def draw_long_division(canvas: tk.Canvas, dividend: int, divisor: int, bounds: tuple[int, int, int, int]) -> None:
    divisor = max(1, divisor)
    quotient = dividend // divisor
    remainder = dividend % divisor
    dividend_digits = str(max(0, dividend))
    line = f"{divisor}){dividend_digits}"
    width = max(len(line), len(str(quotient)) + len(str(divisor)) + 1) + 2
    font, small_font, char_w, line_h = _fonts(bounds, width)
    text_width = width * char_w
    x0, y0, w, h = bounds
    start_x = x0 + max(0, int((w - text_width) / 2))
    base_y = y0 + 16

    canvas.create_text(start_x, base_y, text=line.rjust(width - 1), font=font, anchor=tk.NW, fill="#2a2a2a")
    dividend_x = start_x + (width - len(dividend_digits)) * char_w
    quotient_x = dividend_x + (len(dividend_digits) - len(str(quotient))) * char_w
    canvas.create_text(quotient_x, base_y - line_h, text=str(quotient), font=font, anchor=tk.NW, fill="#2a2a2a")
    top_line_y = base_y + int(line_h * 0.82)
    canvas.create_line(
        dividend_x,
        top_line_y,
        dividend_x + len(dividend_digits) * char_w,
        top_line_y,
        fill="#2a2a2a",
        width=2,
    )

    steps = _division_steps(dividend, divisor)
    y_cursor = base_y + line_h + 2
    for step in steps:
        right_x = dividend_x + (step.end_index + 1) * char_w
        segment_text = str(step.segment)
        subtract_text = str(step.subtract)
        segment_x = right_x - len(segment_text) * char_w
        subtract_x = right_x - len(subtract_text) * char_w

        canvas.create_text(segment_x, y_cursor, text=segment_text, font=font, anchor=tk.NW, fill="#2a2a2a")
        y_cursor += line_h
        canvas.create_text(subtract_x - char_w, y_cursor, text=f"-{subtract_text}", font=font, anchor=tk.NW, fill="#2a2a2a")
        y_sub_line = y_cursor + int(line_h * 0.8)
        canvas.create_line(subtract_x - char_w, y_sub_line, right_x, y_sub_line, fill="#2a2a2a", width=1)
        y_cursor += line_h

        remainder_x = right_x - len(str(step.remainder)) * char_w
        canvas.create_text(remainder_x, y_cursor, text=str(step.remainder), font=font, anchor=tk.NW, fill="#2a2a2a")
        if step.bring_down is not None:
            canvas.create_text(
                right_x + 8,
                y_cursor + 1,
                text=f"bring down {step.bring_down}",
                font=small_font,
                anchor=tk.NW,
                fill="#6b6b6b",
            )
        y_cursor += line_h

    if not steps:
        canvas.create_text(
            dividend_x,
            y_cursor,
            text=f"{dividend_digits} is smaller than {divisor}",
            font=small_font,
            anchor=tk.NW,
            fill="#6b6b6b",
        )
        y_cursor += line_h

    if remainder:
        canvas.create_text(
            dividend_x,
            y_cursor,
            text=f"Remainder {remainder}",
            font=small_font,
            anchor=tk.NW,
            fill="#6b6b6b",
        )

    _draw_note(canvas, bounds, f"{dividend} / {divisor} = {quotient} R {remainder}")


def draw_money_breakdown(
    canvas: tk.Canvas, dollars: int, cents: int, bounds: tuple[int, int, int, int]
) -> None:
    dollars = max(0, dollars)
    cents = max(0, min(99, cents))
    bills = _breakdown(dollars, [(10, "$10"), (5, "$5"), (1, "$1")])
    coins = _breakdown(cents, [(25, "25c"), (10, "10c"), (5, "5c"), (1, "1c")])
    rows = [(label, count, "bill") for denom, label, count in bills] + [
        (label, count, "coin") for denom, label, count in coins
    ]

    x0, y0, w, h = bounds
    if not rows:
        return
    row_h = max(32, int(h / len(rows)))
    label_x = x0 + 10
    shapes_x = x0 + 90
    max_shapes = max(4, int((w - 120) / 26))

    for idx, (label, count, kind) in enumerate(rows):
        y = y0 + idx * row_h + 4
        canvas.create_text(label_x, y + 8, text=label, anchor=tk.NW, fill="#2a2a2a", font=("Helvetica", 11, "bold"))
        shape_size = min(20, row_h - 12)
        gap = shape_size + 6
        shown = min(count, max_shapes)
        for i in range(shown):
            sx = shapes_x + i * gap
            sy = y + 4
            if kind == "bill":
                canvas.create_rectangle(sx, sy, sx + shape_size + 8, sy + shape_size, fill="#8ccf9b", outline="")
            else:
                canvas.create_oval(sx, sy, sx + shape_size, sy + shape_size, fill="#d9c38f", outline="#b89b5e")
        if count > shown:
            canvas.create_text(
                shapes_x + shown * gap + 6,
                y + 8,
                text=f"x{count}",
                anchor=tk.NW,
                fill="#6b6b6b",
                font=("Helvetica", 10),
            )


def _breakdown(total: int, denoms: list[tuple[int, str]]) -> list[tuple[int, str, int]]:
    remaining = total
    rows: list[tuple[int, str, int]] = []
    for denom, label in denoms:
        count = remaining // denom
        remaining = remaining % denom
        rows.append((denom, label, count))
    return rows


def _multiplication_partials(a: int, b: int) -> list[tuple[int, int]]:
    digits = list(reversed(str(max(0, b))))
    partials: list[tuple[int, int]] = []
    for idx, digit_char in enumerate(digits):
        digit = int(digit_char)
        partial_value = a * digit * (10**idx)
        partials.append((partial_value, idx))
    return partials


class _DivisionStep:
    def __init__(self, end_index: int, segment: int, subtract: int, remainder: int, bring_down: int | None) -> None:
        self.end_index = end_index
        self.segment = segment
        self.subtract = subtract
        self.remainder = remainder
        self.bring_down = bring_down


def _division_steps(dividend: int, divisor: int) -> list[_DivisionStep]:
    digits = [int(ch) for ch in str(max(0, dividend))]
    steps: list[_DivisionStep] = []
    current = 0
    started = False
    for idx, digit in enumerate(digits):
        current = (current * 10) + digit
        if not started and current < divisor:
            continue
        started = True
        q_digit = current // divisor
        subtract = q_digit * divisor
        remainder = current - subtract
        bring_down = digits[idx + 1] if idx + 1 < len(digits) else None
        steps.append(_DivisionStep(idx, current, subtract, remainder, bring_down))
        current = remainder
    return steps


def _draw_long_add_sub(
    canvas: tk.Canvas,
    a: int,
    b: int,
    op: str,
    result: int,
    bounds: tuple[int, int, int, int],
    show_carry: bool = False,
    show_borrow: bool = False,
) -> None:
    width = max(len(str(a)), len(str(b)), len(str(result))) + 1
    font, small_font, char_w, line_h = _fonts(bounds, width)
    line1 = str(a).rjust(width)
    line2 = f"{op}{b}".rjust(width)
    line3 = str(result).rjust(width)

    text_width = width * char_w
    x0, y0, w, h = bounds
    extra_lines = 1 if (show_carry or show_borrow) else 0
    total_lines = 4 + extra_lines
    start_x = x0 + max(0, int((w - text_width) / 2))
    start_y = y0 + max(0, int((h - total_lines * line_h) / 2))

    offset = 0
    if show_carry:
        carries = _compute_carries(a, b, width)
        _draw_marks(canvas, carries, start_x, start_y, char_w, small_font)
        offset = 1
    if show_borrow:
        borrows = _compute_borrows(a, b, width)
        _draw_marks(canvas, borrows, start_x, start_y, char_w, small_font)
        offset = 1

    canvas.create_text(start_x, start_y + offset * line_h, text=line1, font=font, anchor=tk.NW, fill="#2a2a2a")
    canvas.create_text(
        start_x, start_y + (offset + 1) * line_h, text=line2, font=font, anchor=tk.NW, fill="#2a2a2a"
    )
    y_line = start_y + (offset + 2) * line_h - 4
    canvas.create_line(start_x, y_line, start_x + text_width, y_line, fill="#2a2a2a", width=2)
    canvas.create_text(
        start_x, start_y + (offset + 2) * line_h, text=line3, font=font, anchor=tk.NW, fill="#2a2a2a"
    )

    _draw_note(canvas, bounds, f"{a} {op} {b} = {result}")


def _compute_carries(a: int, b: int, width: int) -> list[int]:
    digits_a = list(str(a).rjust(width, "0"))
    digits_b = list(str(b).rjust(width, "0"))
    carry = 0
    carries = [0 for _ in range(width)]
    for idx in range(width - 1, -1, -1):
        da = int(digits_a[idx])
        db = int(digits_b[idx])
        total = da + db + carry
        carry = 1 if total >= 10 else 0
        if carry and idx > 0:
            carries[idx - 1] = carry
    return carries


def _compute_borrows(a: int, b: int, width: int) -> list[int]:
    digits_a = list(str(a).rjust(width, "0"))
    digits_b = list(str(b).rjust(width, "0"))
    borrow = 0
    borrows = [0 for _ in range(width)]
    for idx in range(width - 1, -1, -1):
        da = int(digits_a[idx]) - borrow
        db = int(digits_b[idx])
        if da < db:
            borrow = 1
            if idx > 0:
                borrows[idx - 1] = 1
            da += 10
        else:
            borrow = 0
    return borrows


def _draw_marks(
    canvas: tk.Canvas,
    marks: list[int],
    start_x: int,
    start_y: int,
    char_w: int,
    font: tkfont.Font,
) -> None:
    for idx, mark in enumerate(marks):
        if mark:
            canvas.create_text(start_x + idx * char_w, start_y, text=str(mark), font=font, anchor=tk.NW, fill="#6b6b6b")


def _draw_note(canvas: tk.Canvas, bounds: tuple[int, int, int, int], text: str) -> None:
    x0, y0, w, h = bounds
    canvas.create_text(x0 + 10, y0 + h - 24, text=text, anchor=tk.W, fill="#6b6b6b", font=("Helvetica", 10))


def _fonts(bounds: tuple[int, int, int, int], min_chars: int | None = None) -> tuple[tkfont.Font, tkfont.Font, int, int]:
    _, _, w, h = bounds
    max_size = max(12, min(22, int(h / 7)))
    min_size = 8
    size = max_size
    if min_chars:
        available = max(20, w - 20)
        for test_size in range(max_size, min_size - 1, -1):
            test_font = tkfont.Font(family="Courier", size=test_size)
            if test_font.measure("0") * min_chars <= available:
                size = test_size
                break
        else:
            size = min_size
    font = tkfont.Font(family="Courier", size=size)
    small_font = tkfont.Font(family="Courier", size=max(7, size - 6))
    char_w = font.measure("0")
    line_h = font.metrics("linespace") + 4
    return font, small_font, char_w, line_h
