from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.khan_connector_early_math_arithmetic_expansion import (
    build_arithmetic_expansion_groups,
)


OUT_MANIFEST = Path("scripts/template_manifests/khan_connector_early_math_v1.json")
OUT_CATALOG = Path("scripts/catalogs/khan_connector_early_math_v1.json")
PULLED_ON = "2026-04-17"


def _template(
    *,
    external_id: str,
    skill: str,
    subskill: str,
    label: str,
    prompt: str,
    answer_expr: str,
    explanation: str,
    mode: str = "expression",
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
        "constraint_expr": "",
        "explanation_template": explanation,
        "min_level": 1,
        "max_level": 3,
        "choice_spread": spread,
        "active": True,
        "vars": [],
    }


def _group(
    *,
    query: str,
    title: str,
    assignable_url: str,
    templates: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "query": query,
        "title": title,
        "assignable_url": assignable_url,
        "pulled_on": PULLED_ON,
        "pulled_via": "khan-academy-connector",
        "templates": templates,
    }


def build_groups() -> list[dict[str, object]]:
    groups = [
        _group(
            query="arithmetic equivalent fractions",
            title="Equivalent fractions",
            assignable_url="https://www.khanacademy.org/math/cc-third-grade-math/equivalent-fractions-and-comparing-fractions/imp-equivalent-fractions/e/equivalent-fraction?utm_campaign=teacher_assign_tool&utm_medium=referral&utm_source=chatgpt",
            templates=[
                _template(
                    external_id="khan.connector.early_math.fractions.equivalent.01.v1",
                    skill="fractions",
                    subskill="Equivalent fractions",
                    label="Pulled equivalent fraction",
                    prompt="What number could replace t below? 1/3 = t/6. Enter only the number for t.",
                    answer_expr="2",
                    explanation="1/3 is equal to 2/6, so t = 2.",
                    spread=3.0,
                ),
                _template(
                    external_id="khan.connector.early_math.fractions.equivalent.02.v1",
                    skill="fractions",
                    subskill="Equivalent fractions",
                    label="Pulled equivalent fraction",
                    prompt="What number could replace m below? m/8 = 1/2. Enter only the number for m.",
                    answer_expr="4",
                    explanation="1/2 of 8 is 4, so m = 4.",
                    spread=3.0,
                ),
                _template(
                    external_id="khan.connector.early_math.fractions.equivalent.03.v1",
                    skill="fractions",
                    subskill="Equivalent fractions",
                    label="Pulled equivalent fraction",
                    prompt="What number could replace p below? p/4 = 6/8. Enter only the number for p.",
                    answer_expr="3",
                    explanation="6/8 simplifies to 3/4, so p = 3.",
                    spread=3.0,
                ),
                _template(
                    external_id="khan.connector.early_math.fractions.equivalent.04.v1",
                    skill="fractions",
                    subskill="Equivalent fractions",
                    label="Pulled equivalent fraction",
                    prompt="What value of k makes the equation true? 4/k = 2/3. Enter only the number for k.",
                    answer_expr="6",
                    explanation="Cross-multiply: 4 * 3 = 2 * k, so k = 6.",
                    spread=3.0,
                ),
                _template(
                    external_id="khan.connector.early_math.fractions.equivalent.05.v1",
                    skill="fractions",
                    subskill="Equivalent fractions",
                    label="Pulled equivalent fraction",
                    prompt="What value of w makes the equation true? 1/4 = 2/w. Enter only the number for w.",
                    answer_expr="8",
                    explanation="1/4 is equal to 2/8, so w = 8.",
                    spread=3.0,
                ),
            ],
        ),
        _group(
            query="pre algebra two-step equations",
            title="Two-step equations",
            assignable_url="https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-variables-expressions/cc-7th-2-step-equations-intro/e/linear_equations_2?utm_campaign=teacher_assign_tool&utm_medium=referral&utm_source=chatgpt",
            templates=[
                _template(
                    external_id="khan.connector.early_math.pre_algebra.two_step.01.v1",
                    skill="pre_algebra",
                    subskill="Two-step equations and inequalities",
                    label="Pulled two-step equation",
                    prompt="Solve for b: -11b + 7 = 40. Enter only the value of b.",
                    answer_expr="-3",
                    explanation="Subtract 7 from both sides, then divide by -11.",
                    spread=8.0,
                ),
                _template(
                    external_id="khan.connector.early_math.pre_algebra.two_step.02.v1",
                    skill="pre_algebra",
                    subskill="Two-step equations and inequalities",
                    label="Pulled two-step equation",
                    prompt="Solve for g: 3 = g/(-4) - 5. Enter only the value of g.",
                    answer_expr="-32",
                    explanation="Add 5 to both sides, then multiply by -4.",
                    spread=12.0,
                ),
                _template(
                    external_id="khan.connector.early_math.pre_algebra.two_step.03.v1",
                    skill="pre_algebra",
                    subskill="Two-step equations and inequalities",
                    label="Pulled two-step equation",
                    prompt="Solve for h: h/6 - 1 = -3. Enter only the value of h.",
                    answer_expr="-12",
                    explanation="Add 1 to both sides, then multiply by 6.",
                    spread=8.0,
                ),
                _template(
                    external_id="khan.connector.early_math.pre_algebra.two_step.04.v1",
                    skill="pre_algebra",
                    subskill="Two-step equations and inequalities",
                    label="Pulled two-step equation",
                    prompt="Solve for j: j/(-2) + 7 = -12. Enter only the value of j.",
                    answer_expr="38",
                    explanation="Subtract 7 from both sides, then multiply by -2.",
                    spread=10.0,
                ),
                _template(
                    external_id="khan.connector.early_math.pre_algebra.two_step.05.v1",
                    skill="pre_algebra",
                    subskill="Two-step equations and inequalities",
                    label="Pulled two-step equation",
                    prompt="Solve for r: -13 = r/9 + 8. Enter only the value of r.",
                    answer_expr="-189",
                    explanation="Subtract 8 from both sides, then multiply by 9.",
                    spread=20.0,
                ),
            ],
        ),
        _group(
            query="metric conversions word problems arithmetic",
            title="Convert units word problems (metrics)",
            assignable_url="https://www.khanacademy.org/math/cc-fifth-grade-math/imp-measurement-and-data-3/converting-metric-units-word-problems/e/convert-units-word-problems--metrics-?utm_campaign=teacher_assign_tool&utm_medium=referral&utm_source=chatgpt",
            templates=[
                _template(
                    external_id="khan.connector.early_math.measurement.metric.01.v1",
                    skill="measurement",
                    subskill="Metric and customary conversions",
                    label="Pulled metric word problem",
                    mode="word",
                    prompt="Gina made 9,350 mL of lentil soup. She and her kids ate 1.8 L of the soup for lunch. How many milliliters of soup did Gina have leftover? Enter only the number of milliliters.",
                    answer_expr="7550",
                    explanation="Convert 1.8 L to 1,800 mL, then subtract from 9,350 mL.",
                    spread=250.0,
                ),
                _template(
                    external_id="khan.connector.early_math.measurement.metric.02.v1",
                    skill="measurement",
                    subskill="Metric and customary conversions",
                    label="Pulled metric word problem",
                    mode="word",
                    prompt="George filled 10 mugs with coffee. He filled each mug with 240 mL of coffee. How many liters of coffee did George use in total? Enter only the number of liters.",
                    answer_expr="2.4",
                    explanation="10 times 240 mL is 2,400 mL, and 2,400 mL is 2.4 L.",
                    spread=1.0,
                ),
                _template(
                    external_id="khan.connector.early_math.measurement.metric.03.v1",
                    skill="measurement",
                    subskill="Metric and customary conversions",
                    label="Pulled metric word problem",
                    mode="word",
                    prompt="Coach Jill brought 28 L of sports drink to a game. She divided the sports drink equally between 7 coolers. How many milliliters of sports drink did Coach Jill put in each cooler? Enter only the number of milliliters.",
                    answer_expr="4000",
                    explanation="28 L divided by 7 is 4 L, and 4 L is 4,000 mL.",
                    spread=200.0,
                ),
                _template(
                    external_id="khan.connector.early_math.measurement.metric.04.v1",
                    skill="measurement",
                    subskill="Metric and customary conversions",
                    label="Pulled metric word problem",
                    mode="word",
                    prompt="Jim has 19,700 g of sand in his sandbox and adds another 6,300 g. How many kilograms of sand does Jim have in his sandbox now? Enter only the number of kilograms.",
                    answer_expr="26",
                    explanation="19,700 g plus 6,300 g is 26,000 g, and 26,000 g is 26 kg.",
                    spread=5.0,
                ),
                _template(
                    external_id="khan.connector.early_math.measurement.metric.05.v1",
                    skill="measurement",
                    subskill="Metric and customary conversions",
                    label="Pulled metric word problem",
                    mode="word",
                    prompt="Ally sliced 32 kg of watermelon for a party and divided it equally between 8 large bowls. How many grams of watermelon did Ally put in each bowl? Enter only the number of grams.",
                    answer_expr="4000",
                    explanation="32 kg divided by 8 is 4 kg, and 4 kg is 4,000 g.",
                    spread=200.0,
                ),
            ],
        ),
    ]
    groups.extend(build_arithmetic_expansion_groups())
    return groups


def build_manifest() -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for group in build_groups():
        for item in group["templates"]:
            external_id = str(item["external_id"])
            if external_id in seen_ids:
                raise ValueError(f"Duplicate external_id: {external_id}")
            seen_ids.add(external_id)
            items.append(item)
    return items


def build_catalog() -> dict[str, object]:
    groups = build_groups()
    return {
        "version": 1,
        "pulled_on": PULLED_ON,
        "group_count": len(groups),
        "template_count": sum(len(group["templates"]) for group in groups),
        "groups": [
            {
                "query": group["query"],
                "title": group["title"],
                "assignable_url": group["assignable_url"],
                "pulled_on": group["pulled_on"],
                "pulled_via": group["pulled_via"],
                "external_ids": [str(item["external_id"]) for item in group["templates"]],
            }
            for group in groups
        ],
    }


def main() -> None:
    manifest = build_manifest()
    catalog = build_catalog()
    OUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    OUT_CATALOG.parent.mkdir(parents=True, exist_ok=True)
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    OUT_CATALOG.write_text(json.dumps(catalog, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT_MANIFEST} items={len(manifest)}")
    print(f"wrote {OUT_CATALOG} groups={len(catalog['groups'])}")


if __name__ == "__main__":
    main()
