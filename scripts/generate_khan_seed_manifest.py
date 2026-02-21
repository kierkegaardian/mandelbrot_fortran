from __future__ import annotations

import json
from pathlib import Path


def _item(
    *,
    external_id: str,
    skill: str,
    subskill: str,
    label: str,
    prompt: str,
    answer: str,
    explanation: str,
    level: int,
    spread: float,
) -> dict[str, object]:
    return {
        "external_id": external_id,
        "skill": skill,
        "subskill": subskill,
        "label": label,
        "mode": "expression",
        "prompt_template": prompt,
        "answer_expr": answer,
        "constraint_expr": "",
        "explanation_template": explanation,
        "min_level": int(level),
        "max_level": int(level),
        "choice_spread": float(spread),
        "active": True,
        "vars": [],
    }


def build_seed_items() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []

    # Arithmetic: equivalent fractions (Khan pull pages 1-2).
    out.extend(
        [
            _item(
                external_id="khan.fractions.equivalent.p1.i1.v1",
                skill="fractions",
                subskill="Equivalent fractions",
                label="Equivalent fraction value",
                prompt="What value of t makes 1/3 = t/6?",
                answer="2",
                explanation="Scale 1/3 by 2/2 to get 2/6.",
                level=1,
                spread=3.0,
            ),
            _item(
                external_id="khan.fractions.equivalent.p1.i2.v1",
                skill="fractions",
                subskill="Equivalent fractions",
                label="Equivalent fraction value",
                prompt="What value of m makes m/8 = 1/2?",
                answer="4",
                explanation="Half of 8 is 4, so m = 4.",
                level=1,
                spread=3.0,
            ),
            _item(
                external_id="khan.fractions.equivalent.p1.i3.v1",
                skill="fractions",
                subskill="Equivalent fractions",
                label="Equivalent fraction value",
                prompt="What value of p makes p/4 = 6/8?",
                answer="3",
                explanation="6/8 simplifies to 3/4, so p = 3.",
                level=1,
                spread=3.0,
            ),
            _item(
                external_id="khan.fractions.equivalent.p1.i4.v1",
                skill="fractions",
                subskill="Equivalent fractions",
                label="Equivalent fraction denominator",
                prompt="What value of k makes 4/k = 2/3?",
                answer="6",
                explanation="Cross-multiply: 4*3 = 2*k, so k = 6.",
                level=1,
                spread=3.0,
            ),
            _item(
                external_id="khan.fractions.equivalent.p1.i5.v1",
                skill="fractions",
                subskill="Equivalent fractions",
                label="Equivalent fraction denominator",
                prompt="What value of w makes 1/4 = 2/w?",
                answer="8",
                explanation="Cross-multiply: w = 8.",
                level=1,
                spread=3.0,
            ),
            _item(
                external_id="khan.fractions.equivalent.p2.i1.v1",
                skill="fractions",
                subskill="Equivalent fractions",
                label="Equivalent fraction denominator",
                prompt="What value of c makes 3/6 = 4/c?",
                answer="8",
                explanation="3/6 is 1/2, so 4/c must be 1/2. Then c = 8.",
                level=1,
                spread=3.0,
            ),
        ]
    )

    # Pre-Algebra: two-step equations (Khan pull pages 1-2).
    out.extend(
        [
            _item(
                external_id="khan.algebra_linear.two_step.p1.i1.v1",
                skill="algebra_linear",
                subskill="Two-step equations",
                label="Solve two-step equation",
                prompt="Solve for b: -11b + 7 = 40",
                answer="-3",
                explanation="Subtract 7, then divide by -11.",
                level=2,
                spread=8.0,
            ),
            _item(
                external_id="khan.algebra_linear.two_step.p1.i2.v1",
                skill="algebra_linear",
                subskill="Two-step equations",
                label="Solve two-step equation",
                prompt="Solve for g: 3 = g/(-4) - 5",
                answer="-32",
                explanation="Add 5, then multiply both sides by -4.",
                level=2,
                spread=8.0,
            ),
            _item(
                external_id="khan.algebra_linear.two_step.p1.i3.v1",
                skill="algebra_linear",
                subskill="Two-step equations",
                label="Solve two-step equation",
                prompt="Solve for h: h/6 - 1 = -3",
                answer="-12",
                explanation="Add 1, then multiply by 6.",
                level=2,
                spread=8.0,
            ),
            _item(
                external_id="khan.algebra_linear.two_step.p1.i4.v1",
                skill="algebra_linear",
                subskill="Two-step equations",
                label="Solve two-step equation",
                prompt="Solve for j: j/(-2) + 7 = -12",
                answer="38",
                explanation="Subtract 7, then multiply by -2.",
                level=2,
                spread=8.0,
            ),
            _item(
                external_id="khan.algebra_linear.two_step.p1.i5.v1",
                skill="algebra_linear",
                subskill="Two-step equations",
                label="Solve two-step equation",
                prompt="Solve for r: -13 = r/9 + 8",
                answer="-189",
                explanation="Subtract 8, then multiply by 9.",
                level=2,
                spread=10.0,
            ),
            _item(
                external_id="khan.algebra_linear.two_step.p2.i1.v1",
                skill="algebra_linear",
                subskill="Two-step equations",
                label="Solve two-step equation",
                prompt="Solve for m: 13 = 2m + 5",
                answer="4",
                explanation="Subtract 5, then divide by 2.",
                level=2,
                spread=8.0,
            ),
            _item(
                external_id="khan.algebra_linear.two_step.p2.i2.v1",
                skill="algebra_linear",
                subskill="Two-step equations",
                label="Solve two-step equation",
                prompt="Solve for d: 41 = 12d - 7",
                answer="4",
                explanation="Add 7, then divide by 12.",
                level=2,
                spread=8.0,
            ),
            _item(
                external_id="khan.algebra_linear.two_step.p2.i3.v1",
                skill="algebra_linear",
                subskill="Two-step equations",
                label="Solve two-step equation",
                prompt="Solve for n: 7n - 4 = 31",
                answer="5",
                explanation="Add 4, then divide by 7.",
                level=2,
                spread=8.0,
            ),
            _item(
                external_id="khan.algebra_linear.two_step.p2.i4.v1",
                skill="algebra_linear",
                subskill="Two-step equations",
                label="Solve two-step equation",
                prompt="Solve for m: 2 = m/2 - 7",
                answer="18",
                explanation="Add 7, then multiply by 2.",
                level=2,
                spread=8.0,
            ),
            _item(
                external_id="khan.algebra_linear.two_step.p2.i5.v1",
                skill="algebra_linear",
                subskill="Two-step equations",
                label="Solve two-step equation",
                prompt="Solve for k: k/4 + 3 = 14",
                answer="44",
                explanation="Subtract 3, then multiply by 4.",
                level=2,
                spread=8.0,
            ),
        ]
    )

    # Basic geometry: rectangle area (Khan pull pages 1-2).
    out.extend(
        [
            _item(
                external_id="khan.geometry_area.rectangle.p1.i1.v1",
                skill="geometry_area",
                subskill="Rectangle area",
                label="Rectangle area",
                prompt="Find area: rectangle with width 3 meters and height 4 meters.",
                answer="12",
                explanation="Area = width * height = 3 * 4 = 12 square meters.",
                level=1,
                spread=8.0,
            ),
            _item(
                external_id="khan.geometry_area.rectangle.p1.i2.v1",
                skill="geometry_area",
                subskill="Rectangle area",
                label="Rectangle area",
                prompt="Find area: rectangle with width 6 meters and height 3 meters.",
                answer="18",
                explanation="Area = 6 * 3 = 18 square meters.",
                level=1,
                spread=8.0,
            ),
            _item(
                external_id="khan.geometry_area.rectangle.p1.i3.v1",
                skill="geometry_area",
                subskill="Rectangle area",
                label="Rectangle area",
                prompt="Find area: rectangle with width 11 units and height 2 units.",
                answer="22",
                explanation="Area = 11 * 2 = 22 square units.",
                level=1,
                spread=8.0,
            ),
            _item(
                external_id="khan.geometry_area.rectangle.p1.i4.v1",
                skill="geometry_area",
                subskill="Rectangle area",
                label="Rectangle area",
                prompt="Find area: rectangle with width 7 units and height 4 units.",
                answer="28",
                explanation="Area = 7 * 4 = 28 square units.",
                level=1,
                spread=8.0,
            ),
            _item(
                external_id="khan.geometry_area.rectangle.p1.i5.v1",
                skill="geometry_area",
                subskill="Rectangle area",
                label="Rectangle area",
                prompt="Find area: rectangle with width 7 centimeters and height 5 centimeters.",
                answer="35",
                explanation="Area = 7 * 5 = 35 square centimeters.",
                level=1,
                spread=8.0,
            ),
            _item(
                external_id="khan.geometry_area.rectangle.p2.i1.v1",
                skill="geometry_area",
                subskill="Rectangle area",
                label="Rectangle area",
                prompt="Find area: rectangle with width 5 centimeters and height 6 centimeters.",
                answer="30",
                explanation="Area = 5 * 6 = 30 square centimeters.",
                level=1,
                spread=8.0,
            ),
            _item(
                external_id="khan.geometry_area.rectangle.p2.i2.v1",
                skill="geometry_area",
                subskill="Rectangle area",
                label="Rectangle area",
                prompt="Find area: rectangle with width 7 meters and height 6 meters.",
                answer="42",
                explanation="Area = 7 * 6 = 42 square meters.",
                level=1,
                spread=8.0,
            ),
            _item(
                external_id="khan.geometry_area.rectangle.p2.i3.v1",
                skill="geometry_area",
                subskill="Rectangle area",
                label="Rectangle area",
                prompt="Find area: rectangle with width 11 meters and height 4 meters.",
                answer="44",
                explanation="Area = 11 * 4 = 44 square meters.",
                level=1,
                spread=8.0,
            ),
            _item(
                external_id="khan.geometry_area.rectangle.p2.i4.v1",
                skill="geometry_area",
                subskill="Rectangle area",
                label="Rectangle area",
                prompt="Find area: rectangle with width 8 centimeters and height 6 centimeters.",
                answer="48",
                explanation="Area = 8 * 6 = 48 square centimeters.",
                level=1,
                spread=8.0,
            ),
            _item(
                external_id="khan.geometry_area.rectangle.p2.i5.v1",
                skill="geometry_area",
                subskill="Rectangle area",
                label="Rectangle area",
                prompt="Find area: rectangle with width 10 centimeters and height 5 centimeters.",
                answer="50",
                explanation="Area = 10 * 5 = 50 square centimeters.",
                level=1,
                spread=8.0,
            ),
        ]
    )

    return out


def main() -> None:
    out_path = Path("scripts/template_manifests/khan_seed_arith_prealg_geometry_v1.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    items = build_seed_items()
    out_path.write_text(json.dumps(items, indent=2), encoding="utf-8")
    print(f"wrote {len(items)} templates to {out_path}")


if __name__ == "__main__":
    main()
