from __future__ import annotations

import ast
import math
import random
from dataclasses import dataclass

from .models import QuestionTemplate, TemplateVar


@dataclass(frozen=True)
class InstantiatedTemplate:
    prompt: str
    answer: str
    explanation: str
    numeric_answer: float | None


def instantiate_template(
    template: QuestionTemplate, vars_spec: list[TemplateVar], *, rng: random.Random
) -> InstantiatedTemplate:
    values = _sample_with_constraints(template.constraint_expr, vars_spec, rng=rng)

    numeric = _safe_eval_numeric(template.answer_expr, values)
    answer = _format_numeric(numeric)
    prompt = template.prompt_template.format_map(_format_map(values))
    explanation = template.explanation_template.format_map(_format_map(values))
    return InstantiatedTemplate(prompt=prompt, answer=answer, explanation=explanation, numeric_answer=float(numeric))


def mc_choices(numeric_answer: float, *, spread: float, rng: random.Random) -> list[str]:
    # Numeric-only baseline. We can add domain-specific distractors later.
    correct = float(numeric_answer)
    if abs(correct - round(correct)) < 1e-9:
        correct_int = int(round(correct))
        return _int_choice_set(correct_int, spread=max(2, int(round(spread))), rng=rng)
    return _float_choice_set(correct, spread=max(0.5, float(spread)), rng=rng)


def _format_map(values: dict[str, float]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in values.items():
        out[k] = _format_numeric(v)
    return out


def _sample_var(var: TemplateVar, *, rng: random.Random) -> float:
    lo = float(var.min_value)
    hi = float(var.max_value)
    step = float(var.step) if float(var.step) > 0 else 1.0
    if hi < lo:
        lo, hi = hi, lo

    if var.kind == "int":
        ilo = int(math.ceil(lo))
        ihi = int(math.floor(hi))
        if ihi < ilo:
            ihi = ilo
        candidates = list(range(ilo, ihi + 1, max(1, int(round(step)))))
        return float(rng.choice(candidates))

    # float kind
    if abs(step - round(step)) < 1e-9:
        step = float(int(round(step)))
    steps = int(max(0, math.floor((hi - lo) / step)))
    return lo + rng.randint(0, max(0, steps)) * step


def _format_numeric(value: float) -> str:
    rounded = round(float(value), 6)
    if abs(rounded - round(rounded)) < 1e-9:
        return str(int(round(rounded)))
    text = f"{rounded:.6f}".rstrip("0").rstrip(".")
    return text


def _int_choice_set(correct: int, *, spread: int, rng: random.Random) -> list[str]:
    choices = {int(correct)}
    while len(choices) < 4:
        delta = rng.randint(-spread, spread)
        if delta == 0:
            continue
        choices.add(int(correct) + int(delta))
    ordered = list(choices)
    rng.shuffle(ordered)
    return [str(c) for c in ordered]


def _float_choice_set(correct: float, *, spread: float, rng: random.Random) -> list[str]:
    choices = {float(correct)}
    while len(choices) < 4:
        delta = rng.uniform(-spread, spread)
        if abs(delta) < 1e-12:
            continue
        choices.add(round(correct + delta, 3))
    ordered = list(choices)
    rng.shuffle(ordered)
    return [_format_numeric(c) for c in ordered]


def _safe_eval_numeric(expr: str, variables: dict[str, float]) -> float:
    node = ast.parse(expr, mode="eval")
    return float(_eval_node(node.body, variables))


def _sample_with_constraints(constraint_expr: str, vars_spec: list[TemplateVar], *, rng: random.Random) -> dict[str, float]:
    constraint_expr = (constraint_expr or "").strip()
    for _attempt in range(200):
        values: dict[str, float] = {}
        for var in vars_spec:
            values[var.name] = _sample_var(var, rng=rng)
        if not constraint_expr:
            return values
        if _safe_eval_bool(constraint_expr, values):
            return values
    raise ValueError("Could not satisfy template constraints after many attempts")


def _safe_eval_bool(expr: str, variables: dict[str, float]) -> bool:
    node = ast.parse(expr, mode="eval")
    return bool(_eval_bool_node(node.body, variables))


def _eval_bool_node(node: ast.AST, variables: dict[str, float]) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return bool(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not _eval_bool_node(node.operand, variables)
    if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
        values = [_eval_bool_node(v, variables) for v in node.values]
        return all(values) if isinstance(node.op, ast.And) else any(values)
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, variables)
        for op, comp in zip(node.ops, node.comparators):
            right = _eval_node(comp, variables)
            ok = _compare(op, left, right)
            if not ok:
                return False
            left = right
        return True
    # Allow numeric expression truthiness (non-zero) as a convenience.
    return bool(_eval_node(node, variables))


def _compare(op: ast.cmpop, left: float, right: float) -> bool:
    if isinstance(op, ast.Eq):
        return left == right
    if isinstance(op, ast.NotEq):
        return left != right
    if isinstance(op, ast.Lt):
        return left < right
    if isinstance(op, ast.LtE):
        return left <= right
    if isinstance(op, ast.Gt):
        return left > right
    if isinstance(op, ast.GtE):
        return left >= right
    raise ValueError("Unsupported comparison operator")


def _eval_node(node: ast.AST, variables: dict[str, float]) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id not in variables:
            raise ValueError(f"Unknown variable: {node.id}")
        return float(variables[node.id])
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        val = _eval_node(node.operand, variables)
        return val if isinstance(node.op, ast.UAdd) else -val
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)):
        left = _eval_node(node.left, variables)
        right = _eval_node(node.right, variables)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.FloorDiv):
            return float(math.floor(left / right))
        if isinstance(node.op, ast.Mod):
            return left % right
        return left**right
    raise ValueError("Unsupported expression node")
