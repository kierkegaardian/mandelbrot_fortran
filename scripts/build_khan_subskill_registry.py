from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.early_math_catalog import EARLY_MATH_SKILLS, early_math_specs, khan_url_for  # noqa: E402
from app.skill_graph import SKILL_LABELS, SKILL_ORDER, SKILL_SUBSKILLS  # noqa: E402
from app.time_utils import now_iso  # noqa: E402


LEGACY_SKILLS = {"calculus_slope"}

KHAN_UNIT_URL_BY_SKILL: dict[str, str] = {
    "counting": "https://www.khanacademy.org/math/cc-kindergarten-math/cc-kindergarten-counting-and-cardinality",
    "add_subtract": "https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-add-subtract-100",
    "multiply": "https://www.khanacademy.org/math/cc-third-grade-math/imp-mult-div",
    "divide": "https://www.khanacademy.org/math/cc-third-grade-math/imp-mult-div",
    "ratios": "https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-ratios-proportional-relationships",
    "fractions": "https://www.khanacademy.org/math/cc-fourth-grade-math/imp-fractions-2",
    "long_addition": "https://www.khanacademy.org/math/arithmetic-home/arith-review-add-subtract",
    "long_subtraction": "https://www.khanacademy.org/math/arithmetic-home/arith-review-add-subtract",
    "long_multiplication": "https://www.khanacademy.org/math/arithmetic-home/arith-review-multiply-divide",
    "long_division": "https://www.khanacademy.org/math/arithmetic-home/arith-review-multiply-divide",
    "money": "https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-money",
    "integers": "https://www.khanacademy.org/math/pre-algebra/pre-algebra-negative-numbers",
    "order_of_operations": "https://www.khanacademy.org/math/pre-algebra/pre-algebra-exponents-radicals",
    "pre_algebra": "https://www.khanacademy.org/math/pre-algebra",
    "algebra_linear": "https://www.khanacademy.org/math/algebra-basics/alg-basics-solving-equations-and-inequalities",
    "algebra_1": "https://www.khanacademy.org/math/algebra",
    "algebra_2": "https://www.khanacademy.org/math/algebra2",
    "geometry_area": "https://www.khanacademy.org/math/geometry",
    "trig_right_triangle": "https://www.khanacademy.org/math/precalculus",
    "stats_percent": "https://www.khanacademy.org/math/pre-algebra/pre-algebra-ratios-rates",
    "stats_mean": "https://www.khanacademy.org/math/statistics-probability/summarizing-quantitative-data",
    "stats_probability": "https://www.khanacademy.org/math/statistics-probability/probability-library",
    "statistics": "https://www.khanacademy.org/math/statistics-probability",
    "calculus_1": "https://www.khanacademy.org/math/ap-calculus-ab",
    "calculus_2": "https://www.khanacademy.org/math/ap-calculus-bc",
    "calculus_3": "https://www.khanacademy.org/math/multivariable-calculus",
    "sat_math": "https://www.khanacademy.org/digital-sat/start",
    "psat_math": "https://www.khanacademy.org/digital-sat/start",
    "gre_quant": "https://www.khanacademy.org/math/algebra2",
}

KHAN_ASSIGNABLE_URL_OVERRIDES: dict[tuple[str, str], str] = {
    (
        "pre_algebra",
        "expressions and variables",
    ): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:foundation-algebra/x2f8bb11595b61c86:substitute-evaluate-expression/e/evaluating_expressions_2",
    (
        "pre_algebra",
        "two-step equations and inequalities",
    ): "https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-variables-expressions/cc-7th-2-step-equations-intro/e/linear_equations_2",
    (
        "pre_algebra",
        "ratios, rates, and proportional relationships",
    ): "https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-ratio-proportion/cc-7th-proportional-rel/e/analyzing-and-identifying-proportional-relationships",
    (
        "pre_algebra",
        "exponents, roots, and scientific notation",
    ): "https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-numbers-operations/cc-8th-scientific-notation/e/scientific_notation",
    (
        "pre_algebra",
        "coordinate plane and function tables",
    ): "https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:coordinate-plane/x0267d782:cc-6th-distance/e/coordinate-plane-word-problems",
    (
        "calculus_1",
        "tangent slope as derivative at a point",
    ): "https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-1-new/ab-2-1/e/derivative-at-a-point-as-slope-of-tangent-line",
    (
        "algebra_1",
        "solving equations & inequalities",
    ): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:inequalities-systems-graphs/x2f8bb11595b61c86:checking-solutions-of-two-variable-inequalities/e/checking-solutions-to-two-var-inequalities",
    (
        "algebra_1",
        "slope from points",
    ): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:slope/e/slope-from-two-points",
    (
        "algebra_1",
        "slope-intercept form",
    ): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:forms-of-linear-equations/x2f8bb11595b61c86:intro-to-slope-intercept-form/e/slope-from-an-equation-in-slope-intercept-form",
    (
        "algebra_1",
        "graphing linear inequalities",
    ): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:inequalities-systems-graphs/x2f8bb11595b61c86:graphing-two-variable-inequalities/e/graphing_inequalities_2",
    (
        "algebra_1",
        "systems by substitution",
    ): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:systems-of-equations/x2f8bb11595b61c86:solving-systems-of-equations-with-substitution",
    (
        "algebra_1",
        "systems by elimination",
    ): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:systems-of-equations/x2f8bb11595b61c86:solving-systems-elimination/e/systems_of_equations_with_elimination_0.5",
    (
        "algebra_1",
        "graphing systems and intersections",
    ): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:systems-of-equations/x2f8bb11595b61c86:introduction-to-systems-of-equations/v/solving-systems-graphically",
    (
        "algebra_1",
        "polynomial arithmetic",
    ): "https://www.khanacademy.org/math/algebra-home/alg-polynomials",
    (
        "algebra_1",
        "factoring basics",
    ): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratics-multiplying-factoring/x2f8bb11595b61c86:factor-quadratics-intro/e/factoring_polynomials_1",
    (
        "algebra_1",
        "quadratics: multiplying & factoring",
    ): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratics-multiplying-factoring",
    (
        "algebra_1",
        "quadratic factoring by grouping",
    ): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratics-multiplying-factoring/x2f8bb11595b61c86:factor-quadratics-grouping/e/factoring_polynomials_by_grouping_1",
    (
        "algebra_1",
        "difference of squares",
    ): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratics-multiplying-factoring/x2f8bb11595b61c86:factor-difference-squares/e/factoring_difference_of_squares_2",
    (
        "algebra_1",
        "completing the square",
    ): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratic-functions-equations/x2f8bb11595b61c86:more-on-completing-square/e/completing_the_square_2",
    (
        "algebra_1",
        "quadratic formula",
    ): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratic-functions-equations/x2f8bb11595b61c86:quadratic-formula-a1/a/quadratic-formula-review",
    (
        "algebra_2",
        "polynomial factorization",
    ): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratics-multiplying-factoring/x2f8bb11595b61c86:factor-quadratics-intro/e/factor-quadratics-common-factor",
    (
        "algebra_2",
        "equations",
    ): "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:complex/x2ec2f6f830c9fb89:complex-eq/e/quadratic-formula-with-complex-solutions",
    (
        "algebra_2",
        "logarithms",
    ): "https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:transformations/x2ec2f6f830c9fb89:log-graphs/e/graphs-of-exponentials-and-logarithms",
    (
        "geometry_area",
        "transformations and congruence",
    ): "https://www.khanacademy.org/math/geometry/xff63fac4:hs-geo-transformation-properties-and-proofs/hs-geo-transformations-definitions/e/qualitatively-defining-rigid-transformations",
    (
        "geometry_area",
        "similarity and triangle proofs",
    ): "https://www.khanacademy.org/math/geometry/hs-geo-similarity/hs-geo-similar-and-congruent-triangles/e/solving-problems-with-similar-and-congruent-triangles",
    (
        "geometry_area",
        "analytic geometry and coordinate proofs",
    ): "https://www.khanacademy.org/math/geometry/hs-geo-analytic-geometry/hs-geo-dist-problems/e/coordinate-plane-word-problems-with-polygons",
    (
        "geometry_area",
        "circles and arc relationships",
    ): "https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-geometry/cc-7th-area-circumference/e/find-the-radius-or-diameter-of-a-circle-from-the-circumference-or-area",
    (
        "trig_right_triangle",
        "matrices and linear transformations",
    ): "https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:matrices/x9e81a4f98389efdf:using-matrices-to-transform-the-plane/e/use-matrices-to-transform-the-plane",
    (
        "trig_right_triangle",
        "conic sections",
    ): "https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:conics/x9e81a4f98389efdf:ellipse-foci/e/equation-of-ellipse-from-foci",
    (
        "trig_right_triangle",
        "trigonometric modeling and equations",
    ): "https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:trig/x9e81a4f98389efdf:sinus-models/e/interpret-solutions-of-trigonometric-equations-in-context",
    (
        "trig_right_triangle",
        "probability and combinatorics (precalculus)",
    ): "https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:prob-comb/x9e81a4f98389efdf:expected-value/e/mean-expected-value-discrete-random-variable",
    (
        "stats_probability",
        "conditional probability",
    ): "https://www.khanacademy.org/math/ap-statistics/probability-ap/stats-conditional-probability/e/calculating-conditional-probability",
    (
        "stats_probability",
        "random variables and expected value",
    ): "https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:prob-comb/x9e81a4f98389efdf:expected-value/e/mean-expected-value-discrete-random-variable",
    (
        "statistics",
        "integrated descriptive statistics and probability",
    ): "https://www.khanacademy.org/math/statistics-probability",
    (
        "trig_right_triangle",
        "right-triangle trig ratios",
    ): "https://www.khanacademy.org/math/precalculus",
    (
        "sat_math",
        "sat algebra modeling",
    ): "https://www.khanacademy.org/digital-sat/start",
    (
        "psat_math",
        "psat algebra modeling",
    ): "https://www.khanacademy.org/digital-sat/start",
    (
        "gre_quant",
        "gre quantitative comparison",
    ): "https://www.khanacademy.org/math/algebra2",
}


@dataclass(frozen=True)
class RegistryEntry:
    skill: str
    skill_label: str
    subskill: str
    khan_query: str
    khan_unit_url: str
    khan_assignable_url: str
    pull_status: str
    source: str


def build_registry(include_legacy: bool = False) -> list[RegistryEntry]:
    entries: list[RegistryEntry] = []
    for spec in early_math_specs():
        entries.append(
            RegistryEntry(
                skill=spec.skill,
                skill_label=SKILL_LABELS.get(spec.skill, spec.skill),
                subskill=spec.subskill,
                khan_query=spec.khan_query,
                khan_unit_url=khan_url_for(spec.skill),
                khan_assignable_url=spec.khan_assignable_url,
                pull_status="seeded",
                source="khan-academy-connector",
            )
        )
    skills = list(SKILL_ORDER)
    if include_legacy:
        for legacy_skill in sorted(LEGACY_SKILLS):
            if legacy_skill not in skills:
                skills.append(legacy_skill)
    for skill in skills:
        if skill in EARLY_MATH_SKILLS:
            continue
        if (not include_legacy) and skill in LEGACY_SKILLS:
            continue
        subskills = SKILL_SUBSKILLS.get(skill, ())
        if not subskills:
            continue
        label = SKILL_LABELS.get(skill, skill)
        for subskill in subskills:
            lowered = subskill.strip().lower()
            entries.append(
                RegistryEntry(
                    skill=skill,
                    skill_label=label,
                    subskill=subskill,
                    khan_query=_query_for(skill, subskill),
                    khan_unit_url=KHAN_UNIT_URL_BY_SKILL.get(skill, ""),
                    khan_assignable_url=KHAN_ASSIGNABLE_URL_OVERRIDES.get((skill, lowered), ""),
                    pull_status="seeded",
                    source="khan-academy-connector",
                )
            )
    return entries


def _query_for(skill: str, subskill: str) -> str:
    clean = subskill.strip().lower()
    skill_words = SKILL_LABELS.get(skill, skill).replace("/", " ").lower()
    return f"{skill_words} {clean}".strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Khan subskill registry for all internal skills.")
    parser.add_argument(
        "--out",
        default="scripts/catalogs/khan_subskill_registry.json",
        help="Output JSON path",
    )
    parser.add_argument(
        "--include-legacy",
        action="store_true",
        help="Include legacy skills (for example calculus_slope).",
    )
    args = parser.parse_args()

    entries = build_registry(include_legacy=args.include_legacy)
    payload = {
        "version": 1,
        "generated_at": now_iso(),
        "entry_count": len(entries),
        "entries": [asdict(item) for item in entries],
    }
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"wrote {out_path} entries={len(entries)}")


if __name__ == "__main__":
    main()
