from __future__ import annotations

import json
from pathlib import Path


def _entry(
    *,
    external_id: str,
    skill: str,
    subskill: str,
    label: str,
    prompt: str,
    answer_expr: str,
    explanation: str,
    vars_spec: list[dict[str, float | str]],
    mode: str = "expression",
    constraint: str = "",
    min_level: int = 1,
    max_level: int = 4,
    spread: float = 6.0,
) -> dict[str, object]:
    return {
        "external_id": external_id,
        "skill": skill,
        "subskill": subskill,
        "label": label,
        "mode": mode,
        "prompt_template": prompt,
        "answer_expr": answer_expr,
        "constraint_expr": constraint,
        "explanation_template": explanation,
        "min_level": min_level,
        "max_level": max_level,
        "choice_spread": spread,
        "vars": vars_spec,
        "active": True,
    }


def build_manifest() -> list[dict[str, object]]:
    items: list[dict[str, object]] = []

    for i in range(1, 9):
        items.append(
            _entry(
                external_id=f"khan.pull.v1.percent.previous_height.v{i}",
                skill="stats_percent",
                subskill="Reverse percent change",
                label="Reverse percent change",
                prompt=(
                    "A student's current score is {current} and that is {pct}% higher than the previous score. "
                    "What was the previous score?"
                ),
                answer_expr="current / (1 + pct/100)",
                constraint="(100 + pct) != 0",
                explanation=(
                    "Current is (100% + increase) of previous, so previous = current / (1 + pct/100)."
                ),
                vars_spec=[
                    {"name": "current", "kind": "int", "min": 120, "max": 400, "step": 2},
                    {"name": "pct", "kind": "int", "min": 5, "max": 80, "step": 5},
                ],
                spread=8.0,
            )
        )
        items.append(
            _entry(
                external_id=f"khan.pull.v1.percent.more_less.v{i}",
                skill="stats_percent",
                subskill="Percent change",
                label="Percent change amount",
                prompt=(
                    "A bottle has {base} mL. The smaller bottle has {pct}% less. "
                    "How many fewer mL does the smaller bottle have?"
                ),
                answer_expr="base * pct / 100",
                explanation="Percent difference is base * pct/100.",
                vars_spec=[
                    {"name": "base", "kind": "int", "min": 20, "max": 250, "step": 5},
                    {"name": "pct", "kind": "int", "min": 5, "max": 90, "step": 5},
                ],
                spread=7.0,
            )
        )
        items.append(
            _entry(
                external_id=f"khan.pull.v1.percent.previous_height.intuition.v{i}",
                skill="stats_percent",
                subskill="Reverse percent change",
                label="Reverse percent multiplier",
                mode="intuition",
                prompt="If a current score is {pct}% higher than the previous score, what multiplier turns the previous score into the current score?",
                answer_expr="1 + pct/100",
                explanation="Reverse percent problems start by identifying the growth multiplier before undoing it.",
                vars_spec=[{"name": "pct", "kind": "int", "min": 5, "max": 80, "step": 5}],
                spread=0.6,
            )
        )
        items.append(
            _entry(
                external_id=f"khan.pull.v1.percent.more_less.intuition.v{i}",
                skill="stats_percent",
                subskill="Percent change",
                label="Percent change setup",
                mode="intuition",
                prompt=(
                    "A bottle has {base} mL. The smaller bottle has {pct}% less. "
                    "Before converting anything to a percent, how many mL is the change?"
                ),
                answer_expr="base * pct / 100",
                explanation="Percent change begins with the raw change amount before comparing it to the original.",
                vars_spec=[
                    {"name": "base", "kind": "int", "min": 20, "max": 250, "step": 5},
                    {"name": "pct", "kind": "int", "min": 5, "max": 90, "step": 5},
                ],
                spread=7.0,
            )
        )

    for i in range(1, 7):
        items.append(
            _entry(
                external_id=f"khan.pull.v1.slope.two_points.v{i}",
                skill="calculus_slope",
                subskill="Average rate of change between two points",
                label="Slope from two points",
                prompt="Find the slope of the line through ({x1}, {y1}) and ({x2}, {y2}).",
                answer_expr="(y2 - y1) / (x2 - x1)",
                constraint="x2 != x1",
                explanation="Use slope = (y2 - y1)/(x2 - x1).",
                vars_spec=[
                    {"name": "x1", "kind": "int", "min": -8, "max": 5, "step": 1},
                    {"name": "y1", "kind": "int", "min": -10, "max": 10, "step": 1},
                    {"name": "x2", "kind": "int", "min": -4, "max": 10, "step": 1},
                    {"name": "y2", "kind": "int", "min": -10, "max": 12, "step": 1},
                ],
                spread=5.0,
            )
        )

    for i in range(1, 7):
        items.append(
            _entry(
                external_id=f"khan.pull.v1.area.rectangle.v{i}",
                skill="geometry_area",
                subskill="Khan rectangles",
                label="Area of rectangle",
                prompt="What is the area of a rectangle with side lengths {w} and {h}?",
                answer_expr="w * h",
                explanation="Area of a rectangle is width * height.",
                vars_spec=[
                    {"name": "w", "kind": "int", "min": 2, "max": 24, "step": 1},
                    {"name": "h", "kind": "int", "min": 2, "max": 18, "step": 1},
                ],
                spread=12.0,
            )
        )

    for i in range(1, 9):
        items.append(
            _entry(
                external_id=f"khan.pull.v1.algebra.two_step.v{i}",
                skill="algebra_linear",
                subskill="Khan two-step equations",
                label="Solve two-step equation",
                prompt="Solve for x: {a}x + {b} = {c}",
                answer_expr="(c - b) / a",
                constraint="a != 0 and (c - b) % a == 0",
                explanation="Subtract b from both sides, then divide by a.",
                vars_spec=[
                    {"name": "a", "kind": "int", "min": 2, "max": 12, "step": 1},
                    {"name": "b", "kind": "int", "min": -30, "max": 30, "step": 1},
                    {"name": "c", "kind": "int", "min": -50, "max": 50, "step": 1},
                ],
                spread=8.0,
            )
        )

    for i in range(1, 5):
        items.append(
            _entry(
                external_id=f"khan.pull.v1.mean.five_values.v{i}",
                skill="stats_mean",
                subskill="Mean from display",
                label="Mean from display",
                prompt="A display lists five values: {a}, {b}, {c}, {d}, and {e}. What is the mean?",
                answer_expr="(a + b + c + d + e) / 5",
                constraint="(a + b + c + d + e) % 5 == 0",
                explanation="Add all values and divide by 5.",
                vars_spec=[
                    {"name": "a", "kind": "int", "min": 1, "max": 30, "step": 1},
                    {"name": "b", "kind": "int", "min": 1, "max": 30, "step": 1},
                    {"name": "c", "kind": "int", "min": 1, "max": 30, "step": 1},
                    {"name": "d", "kind": "int", "min": 1, "max": 30, "step": 1},
                    {"name": "e", "kind": "int", "min": 1, "max": 30, "step": 1},
                ],
                spread=6.0,
            )
        )
        items.append(
            _entry(
                external_id=f"khan.pull.v1.mean.five_values.intuition.v{i}",
                skill="stats_mean",
                subskill="Mean from display",
                label="Sum before mean",
                mode="intuition",
                prompt="A display lists five values: {a}, {b}, {c}, {d}, and {e}. What total sum will you divide by 5 to find the mean?",
                answer_expr="a + b + c + d + e",
                explanation="For a mean, first combine the full total shown by the display, then divide by the count.",
                vars_spec=[
                    {"name": "a", "kind": "int", "min": 1, "max": 30, "step": 1},
                    {"name": "b", "kind": "int", "min": 1, "max": 30, "step": 1},
                    {"name": "c", "kind": "int", "min": 1, "max": 30, "step": 1},
                    {"name": "d", "kind": "int", "min": 1, "max": 30, "step": 1},
                    {"name": "e", "kind": "int", "min": 1, "max": 30, "step": 1},
                ],
                spread=12.0,
            )
        )

    for i in range(1, 5):
        items.append(
            _entry(
                external_id=f"khan.pull.v1.sat.linear_fee.v{i}",
                skill="sat_math",
                subskill="SAT algebra modeling",
                label="SAT fee model",
                prompt=(
                    "An event charges a fixed fee of ${f} plus ${r} per guest. "
                    "If the total bill is ${t}, how many guests attended?"
                ),
                answer_expr="(t - f) / r",
                constraint="r != 0 and (t - f) % r == 0 and t > f",
                explanation="Set up t = f + r*g and solve for g.",
                vars_spec=[
                    {"name": "f", "kind": "int", "min": 10, "max": 120, "step": 1},
                    {"name": "r", "kind": "int", "min": 2, "max": 25, "step": 1},
                    {"name": "t", "kind": "int", "min": 100, "max": 900, "step": 1},
                ],
                spread=10.0,
            )
        )
        items.append(
            _entry(
                external_id=f"khan.pull.v1.sat.linear_fee.intuition.v{i}",
                skill="sat_math",
                subskill="SAT algebra modeling",
                label="SAT fee model setup",
                mode="intuition",
                prompt=(
                    "An event charges a fixed fee of ${f} plus ${r} per guest. "
                    "If {g} guests attend, what part of the bill comes from the guest charges before the fixed fee is added?"
                ),
                answer_expr="r * g",
                explanation="Separate the repeated guest cost from the fixed fee before building the full model.",
                vars_spec=[
                    {"name": "f", "kind": "int", "min": 10, "max": 120, "step": 1},
                    {"name": "r", "kind": "int", "min": 2, "max": 25, "step": 1},
                    {"name": "g", "kind": "int", "min": 3, "max": 24, "step": 1},
                ],
                spread=10.0,
            )
        )

    for i in range(1, 5):
        items.append(
            _entry(
                external_id=f"khan.pull.v1.gre.percent_change.v{i}",
                skill="gre_quant",
                subskill="GRE percent reasoning",
                label="GRE percent change",
                prompt=(
                    "A quantity increases from {old} to {new}. What is the percent increase?"
                ),
                answer_expr="(new - old) * 100 / old",
                constraint="old > 0 and new > old",
                explanation="Percent increase = (new - old)/old * 100.",
                vars_spec=[
                    {"name": "old", "kind": "int", "min": 20, "max": 300, "step": 1},
                    {"name": "new", "kind": "int", "min": 25, "max": 500, "step": 1},
                ],
                spread=9.0,
            )
        )
        items.append(
            _entry(
                external_id=f"khan.pull.v1.gre.percent_change.intuition.v{i}",
                skill="gre_quant",
                subskill="GRE percent reasoning",
                label="GRE percent setup",
                mode="intuition",
                prompt=(
                    "A quantity increases from {old} to {new}. "
                    "Before turning the change into a percent, how much did the quantity increase by?"
                ),
                answer_expr="new - old",
                constraint="new > old",
                explanation="Percent reasoning starts with the raw change before comparing it to the original amount.",
                vars_spec=[
                    {"name": "old", "kind": "int", "min": 20, "max": 300, "step": 1},
                    {"name": "new", "kind": "int", "min": 25, "max": 500, "step": 1},
                ],
                spread=9.0,
            )
        )

    return items


def main() -> int:
    manifest = build_manifest()
    out_path = Path("scripts/template_manifests/khan_pulled_test_prep_v1.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {out_path} templates={len(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
