from __future__ import annotations

import html
from datetime import datetime
from typing import Iterable, Optional, Tuple

from .paths import worksheets_dir
from .quiz_engine import Question, generate_question
from .worksheet_fractions import fraction_svg


def generate_worksheet(
    skill: str, question_type: str, num_questions: int, level: int, title: str
) -> tuple[str, list[Question]]:
    questions: list[Question] = []
    for idx in range(num_questions):
        q_type = question_type
        if q_type == "both":
            q_type = "mc" if idx % 2 == 0 else "typed"
        questions.append(generate_question(skill, level, q_type))

    filename = f"worksheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    path = worksheets_dir() / filename
    path.write_text(_render_html(title, questions), encoding="utf-8")
    return str(path), questions


def generate_custom_worksheet(
    topics: list[dict],
    title: str,
) -> tuple[str, list[Question]]:
    questions: list[Question] = []
    force_visual_skills = {
        "counting",
        "fractions",
        "money",
        "long_addition",
        "long_subtraction",
        "long_multiplication",
        "long_division",
        "calculus_1",
        "calculus_slope",
    }
    for spec in topics:
        skill = spec["skill"]
        count = int(spec["count"])
        level = int(spec["level"])
        graphical = int(spec["graphical"])
        if count <= 0:
            continue
        if skill in force_visual_skills and graphical < count:
            graphical = count
        graphical = max(0, min(graphical, count))

        for idx in range(count):
            q = generate_question(skill, level, "typed")
            essential = q.skill in force_visual_skills
            if idx >= graphical and not essential:
                q.visual = None
            questions.append(q)

    filename = f"worksheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    path = worksheets_dir() / filename
    path.write_text(_render_html(title, questions), encoding="utf-8")
    return str(path), questions


def _render_html(title: str, questions: Iterable[Question]) -> str:
    q_list = list(questions)
    body = [
        "<html><head><meta charset='utf-8'>",
        "<style>",
        "body{font-family:Arial, sans-serif; margin:40px; color:#222}",
        "h1{color:#2d5d7c}",
        ".question{margin:14px 0; padding:10px; border:1px solid #dfe6ec; border-radius:6px; break-inside:avoid}",
        ".dot-grid{display:grid; gap:6px; margin-top:8px; break-inside:avoid}",
        ".dot{width:14px; height:14px; background:#5b8def; border-radius:50%}",
        ".long-arith{margin-top:8px; font-family:'Courier New', monospace; font-size:18px}",
        ".long-arith pre{margin:0}",
        ".money-grid{border-collapse:collapse; margin-top:8px}",
        ".money-grid th,.money-grid td{border:1px solid #dfe6ec; padding:4px 8px; font-size:13px}",
        ".money-blank{min-width:80px}",
        ".fraction-circle{margin-top:8px}",
        ".choices{margin:8px 0 0 0; padding-left:18px}",
        ".choices li{margin:2px 0}",
        "@media print{*{print-color-adjust:exact;-webkit-print-color-adjust:exact}}",
        "</style></head><body>",
        f"<h1>{html.escape(title)}</h1>",
        "<h2>Questions</h2>",
    ]
    answer_overrides: list[Optional[str]] = []
    for idx, q in enumerate(q_list, start=1):
        prompt, visual, answer_override = _worksheet_prompt(q)
        body.append("<div class='question'>")
        body.append(f"<strong>{idx}.</strong> {html.escape(prompt)}")
        if visual:
            body.append(visual)
        if q.choices:
            body.append("<div style='margin-top:8px'>Choose one:</div>")
            body.append("<ul class='choices'>")
            for choice in q.choices:
                body.append(f"<li>{html.escape(str(choice))}</li>")
            body.append("</ul>")
        body.append("<div style='margin-top:8px'>Answer: _____________________</div>")
        body.append("</div>")
        answer_overrides.append(answer_override)

    body.append("<h2>Answer Key</h2>")
    for idx, q in enumerate(q_list, start=1):
        override = answer_overrides[idx - 1]
        answer = override if override is not None else q.correct_answer
        body.append(f"<div>{idx}. {html.escape(str(answer))}</div>")

    body.append("</body></html>")
    return "\n".join(body)


def _worksheet_prompt(question: Question) -> Tuple[str, Optional[str], Optional[str]]:
    visual = question.visual or {}
    kind = visual.get("kind")
    if kind == "counting":
        count = int(visual.get("count", 0))
        return "Count the dots.", _dot_grid(count, 8), None
    if kind == "multiply":
        rows = int(visual.get("a", 1))
        cols = int(visual.get("b", 1))
        prompt = "Write a multiplication expression for this array (rows x columns)."
        answer = f"{rows} x {cols}"
        return prompt, _array_grid(rows, cols), answer
    if kind == "ratio":
        a = int(visual.get("a", 1))
        b = int(visual.get("b", 1))
        return f"{a} : {b} = ?", None, None
    if kind == "add":
        a = int(visual.get("a", 0))
        b = int(visual.get("b", 0))
        return f"{a} + {b} = ?", None, None
    if kind == "subtract":
        a = int(visual.get("a", 0))
        b = int(visual.get("b", 0))
        return f"{a} - {b} = ?", None, None
    if kind == "divide":
        total = int(visual.get("total", 0))
        groups = int(visual.get("groups", 1))
        return f"{total} / {groups} = ?", None, None
    if kind == "long_addition":
        a = int(visual.get("a", 0))
        b = int(visual.get("b", 0))
        return f"Long addition: {a} + {b} = ?", _long_arith_block("+", a, b), None
    if kind == "long_subtraction":
        a = int(visual.get("a", 0))
        b = int(visual.get("b", 0))
        big = max(a, b)
        small = min(a, b)
        return f"Long subtraction: {big} - {small} = ?", _long_arith_block("-", big, small), None
    if kind == "long_multiplication":
        a = int(visual.get("a", 0))
        b = int(visual.get("b", 0))
        return f"Long multiplication: {a} x {b} = ?", _long_arith_block("x", a, b), None
    if kind == "long_division":
        dividend = int(visual.get("dividend", 0))
        divisor = int(visual.get("divisor", 1))
        safe_divisor = max(1, divisor)
        return (
            f"Long division: {dividend} / {safe_divisor} = ? (use R for remainder)",
            _long_division_block(dividend, safe_divisor),
            None,
        )
    if kind == "money":
        dollars = int(visual.get("dollars", 0))
        cents = int(visual.get("cents", 0))
        prompt = f"Make ${dollars}.{cents:02d} using $10, $5, $1, 25c, 10c, 5c, 1c."
        return prompt, _money_grid(), _money_answer(dollars, cents)
    if kind == "fraction":
        numerator = int(visual.get("numerator", 0))
        denominator = max(1, int(visual.get("denominator", 1)))
        prompt = "What fraction is shaded? (fraction, decimal, or repeating like 0.(3) or 0.1(6))"
        return prompt, fraction_svg(numerator, denominator), f"{numerator}/{denominator}"
    if kind == "slope":
        x1 = int(visual.get("x1", 0))
        y1 = int(visual.get("y1", 0))
        x2 = int(visual.get("x2", 0))
        y2 = int(visual.get("y2", 0))
        return f"Find the slope of the line through ({x1}, {y1}) and ({x2}, {y2}).", None, None
    return question.prompt, None, None


def _grid_dimensions(count: int, cols: int) -> tuple[int, int]:
    cols = max(1, cols)
    rows = max(1, (count + cols - 1) // cols)
    return rows, cols


def _dot_grid(count: int, cols: int) -> str:
    rows, cols = _grid_dimensions(count, cols)
    style = f"grid-template-columns: repeat({cols}, 16px);"
    dots = ["<div class='dot'></div>" for _ in range(count)]
    return f"<div class='dot-grid' style='{style}'>{''.join(dots)}</div>"


def _array_grid(rows: int, cols: int) -> str:
    rows = max(1, rows)
    cols = max(1, cols)
    style = f"grid-template-columns: repeat({cols}, 16px);"
    dots = ["<div class='dot'></div>" for _ in range(rows * cols)]
    return f"<div class='dot-grid' style='{style}'>{''.join(dots)}</div>"


def _long_arith_block(op: str, top: int, bottom: int) -> str:
    width = max(len(str(top)), len(str(bottom))) + 1
    line1 = str(top).rjust(width)
    line2 = f"{op}{bottom}".rjust(width)
    line3 = "-" * width
    line4 = "_" * width
    text = "\n".join([line1, line2, line3, line4])
    return f"<div class='long-arith'><pre>{text}</pre></div>"


def _long_division_block(dividend: int, divisor: int) -> str:
    dividend_str = str(dividend)
    divisor_str = str(max(1, divisor))
    placeholder = " " * (len(divisor_str) + 2) + "_" * len(dividend_str)
    bracket = f"{divisor_str}){dividend_str}"
    bar = " " * (len(divisor_str) + 1) + "-" * len(dividend_str)
    text = "\n".join([placeholder, bracket, bar])
    return f"<div class='long-arith'><pre>{text}</pre></div>"


def _money_grid() -> str:
    rows = ["$10", "$5", "$1", "25c", "10c", "5c", "1c"]
    body = ["<table class='money-grid'>", "<tr><th>Denomination</th><th>Count</th></tr>"]
    for label in rows:
        body.append(f"<tr><td>{label}</td><td class='money-blank'></td></tr>")
    body.append("</table>")
    return "".join(body)


def _money_answer(dollars: int, cents: int) -> str:
    remaining = max(0, dollars)
    parts: list[str] = []
    for denom in [10, 5, 1]:
        count = remaining // denom
        remaining = remaining % denom
        if count:
            parts.append(f"${denom}x{count}")
    remaining = max(0, cents)
    for denom in [25, 10, 5, 1]:
        count = remaining // denom
        remaining = remaining % denom
        if count:
            parts.append(f"{denom}cx{count}")
    if not parts:
        return "$0x0"
    return " ".join(parts)
