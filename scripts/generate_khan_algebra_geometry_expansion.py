from __future__ import annotations

import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.skill_graph import SKILL_SUBSKILLS


def _var(name: str, lo: int, hi: int, step: int = 1) -> dict[str, object]:
    return {"name": name, "kind": "int", "min": lo, "max": hi, "step": step}


def _tpl(
    *,
    external_id: str,
    skill: str,
    subskill: str,
    label: str,
    mode: str,
    prompt_template: str,
    answer_expr: str,
    explanation_template: str,
    vars: list[dict[str, object]],
    constraint_expr: str = "",
    min_level: int = 1,
    max_level: int = 3,
    choice_spread: float = 8.0,
) -> dict[str, object]:
    return {
        "external_id": external_id,
        "skill": skill,
        "subskill": subskill,
        "label": label,
        "mode": mode,
        "prompt_template": prompt_template,
        "answer_expr": answer_expr,
        "constraint_expr": constraint_expr,
        "explanation_template": explanation_template,
        "min_level": min_level,
        "max_level": max_level,
        "choice_spread": choice_spread,
        "active": True,
        "vars": vars,
    }


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _algebra_variants(skill: str, subskill: str, key: str) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    s = subskill.lower()

    if "sequence" in s:
        out.append(
            _tpl(
                external_id=f"khan.v3.{skill}.{key}.arith_term",
                skill=skill,
                subskill=subskill,
                label="Arithmetic sequence term",
                mode="expression",
                prompt_template="An arithmetic sequence starts at {a1} with common difference {d}. Find term {n}.",
                answer_expr="a1 + (n-1)*d",
                explanation_template="Use a_n = a_1 + (n-1)d.",
                vars=[_var("a1", -20, 30), _var("d", -8, 12), _var("n", 4, 18)],
            )
        )
        out.append(
            _tpl(
                external_id=f"khan.v3.{skill}.{key}.arith_word",
                skill=skill,
                subskill=subskill,
                label="Step pattern",
                mode="word",
                prompt_template="A pattern starts at {a1} and increases by {d} each step. What is value at step {n}?",
                answer_expr="a1 + (n-1)*d",
                explanation_template="Repeated addition creates an arithmetic sequence.",
                vars=[_var("a1", 5, 40), _var("d", 2, 15), _var("n", 3, 15)],
            )
        )
        return out

    if "logarithm" in s:
        out.append(
            _tpl(
                external_id=f"khan.v3.{skill}.{key}.log_power",
                skill=skill,
                subskill=subskill,
                label="Log from exponent form",
                mode="expression",
                prompt_template="Compute log base {b} of {b}^{p}.",
                answer_expr="p",
                explanation_template="log_b(b^p) = p.",
                vars=[_var("b", 2, 10), _var("p", 1, 6)],
            )
        )
        out.append(
            _tpl(
                external_id=f"khan.v3.{skill}.{key}.log_word",
                skill=skill,
                subskill=subskill,
                label="Exponent from logarithm",
                mode="word",
                prompt_template="If log base {b} of N is {p}, and N = {b}^{p}, what is N?",
                answer_expr="b**p",
                explanation_template="Convert log form to exponent form.",
                vars=[_var("b", 2, 9), _var("p", 1, 5)],
                choice_spread=20.0,
            )
        )
        return out

    if "complex" in s:
        out.append(
            _tpl(
                external_id=f"khan.v3.{skill}.{key}.i_even",
                skill=skill,
                subskill=subskill,
                label="Even power of i",
                mode="expression",
                prompt_template="Evaluate i^(2*{n}).",
                answer_expr="(-1)**n",
                explanation_template="i^2=-1 and powers repeat in cycles.",
                vars=[_var("n", 1, 12)],
            )
        )
        out.append(
            _tpl(
                external_id=f"khan.v3.{skill}.{key}.i_cycle",
                skill=skill,
                subskill=subskill,
                label="Power cycle",
                mode="expression",
                prompt_template="Evaluate i^(4*{k} + 2).",
                answer_expr="-1",
                explanation_template="Every power 4k+2 equals -1.",
                vars=[_var("k", 0, 9)],
                choice_spread=3.0,
            )
        )
        return out

    if "trigonometry" in s:
        out.append(
            _tpl(
                external_id=f"khan.v3.{skill}.{key}.tan_ratio",
                skill=skill,
                subskill=subskill,
                label="Tangent ratio",
                mode="expression",
                prompt_template="In a right triangle, opposite={o}, adjacent={a}. Compute 100*tan(theta).",
                answer_expr="(100*o)/a",
                explanation_template="tan(theta)=opposite/adjacent.",
                vars=[_var("o", 2, 20), _var("a", 2, 20)],
                constraint_expr="(100*o)%a==0",
            )
        )
        out.append(
            _tpl(
                external_id=f"khan.v3.{skill}.{key}.similar_tri",
                skill=skill,
                subskill=subskill,
                label="Right-triangle scaling",
                mode="word",
                prompt_template="A similar right triangle has adjacent side {a2} when the reference adjacent side is {a1} with opposite {o1}. Find new opposite.",
                answer_expr="(o1*a2)/a1",
                explanation_template="Similar triangles preserve side ratios.",
                vars=[_var("a1", 2, 20), _var("o1", 2, 20), _var("a2", 2, 40)],
                constraint_expr="(o1*a2)%a1==0",
            )
        )
        return out

    if "geometry" in skill:
        return []

    # Default algebra pair
    out.append(
        _tpl(
            external_id=f"khan.v3.{skill}.{key}.linear_solve",
            skill=skill,
            subskill=subskill,
            label="Linear equation solve",
            mode="expression",
            prompt_template="Solve for x: {m}x + {b} = {c}",
            answer_expr="(c-b)/m",
            explanation_template="Subtract b, then divide by m.",
            vars=[_var("m", 1, 20), _var("b", -40, 40), _var("c", -180, 180)],
            constraint_expr="(c-b)%m==0",
        )
    )
    out.append(
        _tpl(
            external_id=f"khan.v3.{skill}.{key}.model_word",
            skill=skill,
            subskill=subskill,
            label="Linear model word problem",
            mode="word",
            prompt_template="A plan charges ${f} fee plus ${r} per unit. What is total for {n} units?",
            answer_expr="f + r*n",
            explanation_template="Use total = fixed fee + rate*units.",
            vars=[_var("f", 5, 140), _var("r", 2, 30), _var("n", 2, 35)],
            choice_spread=12.0,
        )
    )
    return out


def _geometry_variants(skill: str, subskill: str, key: str) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    s = subskill.lower()

    if "rectangle" in s or "square" in s:
        out.extend(
            [
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.rect_area",
                    skill=skill,
                    subskill=subskill,
                    label="Rectangle area",
                    mode="expression",
                    prompt_template="Find area of rectangle with length {l} and width {w}.",
                    answer_expr="l*w",
                    explanation_template="Area = length*width.",
                    vars=[_var("l", 3, 40), _var("w", 2, 35)],
                ),
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.square_area",
                    skill=skill,
                    subskill=subskill,
                    label="Square area",
                    mode="expression",
                    prompt_template="Find area of square with side {s}.",
                    answer_expr="s*s",
                    explanation_template="Area = side^2.",
                    vars=[_var("s", 2, 30)],
                ),
            ]
        )
        return out

    if "triangle" in s or "parallelogram" in s or "trapezoid" in s or "composite" in s:
        out.extend(
            [
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.tri_area",
                    skill=skill,
                    subskill=subskill,
                    label="Triangle area",
                    mode="expression",
                    prompt_template="Find area of triangle with base {b} and height {h}.",
                    answer_expr="(b*h)/2",
                    explanation_template="Area = 1/2*base*height.",
                    vars=[_var("b", 4, 36), _var("h", 2, 30)],
                    constraint_expr="(b*h)%2==0",
                ),
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.trap_area",
                    skill=skill,
                    subskill=subskill,
                    label="Trapezoid area",
                    mode="expression",
                    prompt_template="Find area of trapezoid with bases {b1},{b2} and height {h}.",
                    answer_expr="((b1+b2)*h)/2",
                    explanation_template="Area = (b1+b2)*h/2.",
                    vars=[_var("b1", 4, 30), _var("b2", 4, 30), _var("h", 2, 24)],
                    constraint_expr="((b1+b2)*h)%2==0",
                ),
            ]
        )
        return out

    if "perimeter" in s or "missing" in s:
        out.extend(
            [
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.perimeter",
                    skill=skill,
                    subskill=subskill,
                    label="Rectangle perimeter",
                    mode="expression",
                    prompt_template="Find perimeter of rectangle with length {l} and width {w}.",
                    answer_expr="2*(l+w)",
                    explanation_template="Perimeter adds all sides.",
                    vars=[_var("l", 4, 30), _var("w", 3, 24)],
                ),
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.missing_side",
                    skill=skill,
                    subskill=subskill,
                    label="Missing width from perimeter",
                    mode="word",
                    prompt_template="A rectangle has perimeter {p} and length {l}. Find width.",
                    answer_expr="(p/2)-l",
                    explanation_template="From p=2(l+w), solve w=p/2-l.",
                    vars=[_var("p", 20, 200, 2), _var("l", 4, 80)],
                    constraint_expr="(p/2)>l",
                ),
            ]
        )
        return out

    if "circle" in s:
        out.extend(
            [
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.circumference",
                    skill=skill,
                    subskill=subskill,
                    label="Circumference (pi≈3.14)",
                    mode="expression",
                    prompt_template="Using pi≈3.14, find circumference for radius {r}.",
                    answer_expr="(628*r)/100",
                    explanation_template="C=2*pi*r.",
                    vars=[_var("r", 2, 25)],
                ),
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.circle_area",
                    skill=skill,
                    subskill=subskill,
                    label="Circle area (pi≈3.14)",
                    mode="expression",
                    prompt_template="Using pi≈3.14, find area for radius {r}.",
                    answer_expr="(314*(r**2))/100",
                    explanation_template="A=pi*r^2.",
                    vars=[_var("r", 2, 20)],
                    choice_spread=20.0,
                ),
            ]
        )
        return out

    if "surface area" in s or "volume" in s:
        out.extend(
            [
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.prism_volume",
                    skill=skill,
                    subskill=subskill,
                    label="Prism volume",
                    mode="expression",
                    prompt_template="Find volume of rectangular prism l={l}, w={w}, h={h}.",
                    answer_expr="l*w*h",
                    explanation_template="Volume=l*w*h.",
                    vars=[_var("l", 2, 20), _var("w", 2, 16), _var("h", 2, 14)],
                ),
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.prism_surface",
                    skill=skill,
                    subskill=subskill,
                    label="Prism surface area",
                    mode="expression",
                    prompt_template="Find surface area of rectangular prism l={l}, w={w}, h={h}.",
                    answer_expr="2*(l*w + l*h + w*h)",
                    explanation_template="Add all face pairs.",
                    vars=[_var("l", 2, 18), _var("w", 2, 14), _var("h", 2, 12)],
                ),
            ]
        )
        return out

    if "pythagorean" in s:
        out.extend(
            [
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.pyth_hyp",
                    skill=skill,
                    subskill=subskill,
                    label="Find hypotenuse",
                    mode="expression",
                    prompt_template="Right triangle legs are {a} and {b} where ({a},{b},{c}) is a Pythagorean triple. Find hypotenuse.",
                    answer_expr="c",
                    explanation_template="Use known triple / a^2+b^2=c^2.",
                    vars=[_var("a", 3, 9), _var("b", 4, 12), _var("c", 5, 15)],
                    constraint_expr="(a*a + b*b) == (c*c)",
                ),
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.pyth_leg",
                    skill=skill,
                    subskill=subskill,
                    label="Find missing leg",
                    mode="expression",
                    prompt_template="Right triangle has hypotenuse {c} and one leg {a}. In this triple, find other leg.",
                    answer_expr="b",
                    explanation_template="Use triple relation.",
                    vars=[_var("a", 3, 9), _var("b", 4, 12), _var("c", 5, 15)],
                    constraint_expr="(a*a + b*b) == (c*c)",
                ),
            ]
        )
        return out

    if "coordinate" in s or "analytic" in s:
        out.extend(
            [
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.midpoint_x",
                    skill=skill,
                    subskill=subskill,
                    label="Midpoint x-coordinate",
                    mode="expression",
                    prompt_template="Find x-coordinate of midpoint of ({x1},{y1}) and ({x2},{y2}).",
                    answer_expr="(x1+x2)/2",
                    explanation_template="Average x-values.",
                    vars=[_var("x1", -20, 20), _var("y1", -20, 20), _var("x2", -20, 20), _var("y2", -20, 20)],
                    constraint_expr="(x1+x2)%2==0",
                ),
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.slope",
                    skill=skill,
                    subskill=subskill,
                    label="Slope from coordinates",
                    mode="expression",
                    prompt_template="Find slope through ({x1},{y1}) and ({x2},{y2}).",
                    answer_expr="(y2-y1)/(x2-x1)",
                    explanation_template="Slope is rise over run.",
                    vars=[_var("x1", -12, 8), _var("y1", -20, 20), _var("x2", -8, 12), _var("y2", -20, 20)],
                    constraint_expr="x2!=x1",
                ),
            ]
        )
        return out

    if "angle" in s:
        out.extend(
            [
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.triangle_angle",
                    skill=skill,
                    subskill=subskill,
                    label="Third triangle angle",
                    mode="expression",
                    prompt_template="Triangle angles are {a} and {b}. Find the third angle.",
                    answer_expr="180-a-b",
                    explanation_template="Triangle sum is 180 degrees.",
                    vars=[_var("a", 20, 110), _var("b", 20, 110)],
                    constraint_expr="a+b<180",
                ),
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.straight_line",
                    skill=skill,
                    subskill=subskill,
                    label="Supplementary angle",
                    mode="expression",
                    prompt_template="Angles on a line are {a} and x. Find x.",
                    answer_expr="180-a",
                    explanation_template="Supplementary angles total 180.",
                    vars=[_var("a", 10, 170)],
                ),
            ]
        )
        return out

    if "transform" in s or "congruence" in s:
        out.extend(
            [
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.reflect_y",
                    skill=skill,
                    subskill=subskill,
                    label="Reflection over y-axis",
                    mode="expression",
                    prompt_template="Point ({x},{y}) is reflected across y-axis. What is new x-coordinate?",
                    answer_expr="-x",
                    explanation_template="Reflection over y-axis flips x sign.",
                    vars=[_var("x", -20, 20), _var("y", -20, 20)],
                ),
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.translate_x",
                    skill=skill,
                    subskill=subskill,
                    label="Horizontal translation",
                    mode="expression",
                    prompt_template="Point ({x},{y}) translated right by {k}. Find new x-coordinate.",
                    answer_expr="x+k",
                    explanation_template="Translation adds shift to x.",
                    vars=[_var("x", -20, 20), _var("y", -20, 20), _var("k", 1, 20)],
                ),
            ]
        )
        return out

    if "similar" in s or "scale" in s:
        out.extend(
            [
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.scale_side",
                    skill=skill,
                    subskill=subskill,
                    label="Scale factor side length",
                    mode="expression",
                    prompt_template="A similar figure has scale factor {k}. If original side is {s}, find scaled side.",
                    answer_expr="k*s",
                    explanation_template="Multiply corresponding lengths by scale factor.",
                    vars=[_var("k", 2, 8), _var("s", 2, 40)],
                ),
                _tpl(
                    external_id=f"khan.v3.{skill}.{key}.scale_back",
                    skill=skill,
                    subskill=subskill,
                    label="Reverse scale",
                    mode="expression",
                    prompt_template="Scaled side is {s2} with scale factor {k}. Find original side.",
                    answer_expr="s2/k",
                    explanation_template="Divide by scale factor to reverse scaling.",
                    vars=[_var("s2", 4, 160), _var("k", 2, 8)],
                    constraint_expr="s2%k==0",
                ),
            ]
        )
        return out

    # fallback geometry templates
    out.extend(
        [
            _tpl(
                external_id=f"khan.v3.{skill}.{key}.rect_area_fallback",
                skill=skill,
                subskill=subskill,
                label="Geometry area fallback",
                mode="expression",
                prompt_template="Find rectangle area for length {l} and width {w}.",
                answer_expr="l*w",
                explanation_template="Area = length*width.",
                vars=[_var("l", 2, 30), _var("w", 2, 25)],
            ),
            _tpl(
                external_id=f"khan.v3.{skill}.{key}.word_fallback",
                skill=skill,
                subskill=subskill,
                label="Geometry word fallback",
                mode="word",
                prompt_template="A rectangular floor is {l} by {w}. Tiles cover 1 sq unit each. How many tiles are needed?",
                answer_expr="l*w",
                explanation_template="Tile count equals area.",
                vars=[_var("l", 3, 40), _var("w", 3, 30)],
            ),
        ]
    )
    return out


def build_manifest() -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for skill in ("algebra_1", "algebra_2"):
        for subskill in SKILL_SUBSKILLS.get(skill, ()):
            key = _slug(subskill)
            items.extend(_algebra_variants(skill, subskill, key))

    for subskill in SKILL_SUBSKILLS.get("geometry_area", ()):
        key = _slug(subskill)
        items.extend(_geometry_variants("geometry_area", subskill, key))

    return items


def main() -> int:
    out_path = Path("scripts/template_manifests/khan_algebra_geometry_expansion_v1.json")
    manifest = build_manifest()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {out_path} templates={len(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
