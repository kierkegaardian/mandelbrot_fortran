from __future__ import annotations

import json
from pathlib import Path


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
    min_level: int = 1,
    max_level: int = 3,
    choice_spread: float = 6.0,
    constraint_expr: str = "",
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


def build_manifest() -> list[dict[str, object]]:
    items: list[dict[str, object]] = []

    # Khan-seeded: percent word, ratio word, linear-fee word, slope, probability models.
    for i in range(1, 7):
        items.append(
            _tpl(
                external_id=f"khan.v2.add_subtract.word.total.v{i}",
                skill="add_subtract",
                subskill="Word totals and differences",
                label="Word total",
                mode="word",
                prompt_template=(
                    "A class has {a} notebooks and buys {b} more. "
                    "How many notebooks are there now?"
                ),
                answer_expr="a+b",
                explanation_template="Add the starting amount and added amount.",
                vars=[_var("a", 20, 300), _var("b", 10, 180)],
                min_level=1,
                max_level=2,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.add_subtract.word.left.v{i}",
                skill="add_subtract",
                subskill="Word totals and differences",
                label="Word difference",
                mode="word",
                prompt_template=(
                    "A shelf had {a} books. {b} were checked out. "
                    "How many books remain?"
                ),
                answer_expr="a-b",
                explanation_template="Subtract checked-out books from the starting total.",
                vars=[_var("a", 60, 500), _var("b", 15, 240)],
                min_level=1,
                max_level=2,
                constraint_expr="a>b",
            )
        )

    for i in range(1, 7):
        items.append(
            _tpl(
                external_id=f"khan.v2.integers.ops.v{i}",
                skill="integers",
                subskill="Integer arithmetic",
                label="Integer expression",
                mode="expression",
                prompt_template="Evaluate: ({a}) - ({b}) + ({c})",
                answer_expr="a-b+c",
                explanation_template="Subtract and add signed values carefully.",
                vars=[_var("a", -30, 30), _var("b", -25, 25), _var("c", -20, 20)],
                min_level=1,
                max_level=3,
                choice_spread=9.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.order_ops.exp.v{i}",
                skill="order_of_operations",
                subskill="Order of operations",
                label="Evaluate expression",
                mode="expression",
                prompt_template="Evaluate: {a}*{b}+{c}^{p}",
                answer_expr="a*b+(c**p)",
                explanation_template="Compute exponent first, then multiply, then add.",
                vars=[_var("a", 2, 12), _var("b", 2, 10), _var("c", 2, 9), _var("p", 2, 3)],
                min_level=1,
                max_level=3,
                choice_spread=12.0,
            )
        )

    for i in range(1, 7):
        items.append(
            _tpl(
                external_id=f"khan.v2.ratios.word.scale.v{i}",
                skill="ratios",
                subskill="Equivalent ratio word problems",
                label="Scale ratio",
                mode="word",
                prompt_template=(
                    "A recipe uses {a} cups of water for {b} cups of rice. "
                    "If you use {k} cups of rice, how many cups of water are needed?"
                ),
                answer_expr="a*k/b",
                explanation_template="Use equivalent ratios and scale both terms equally.",
                vars=[_var("a", 2, 18), _var("b", 2, 18), _var("k", 2, 30)],
                min_level=1,
                max_level=3,
                constraint_expr="a>0 and b>0 and k>0 and (a*k)%b==0",
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.fractions.equiv.v{i}",
                skill="fractions",
                subskill="Equivalent fractions",
                label="Solve equivalent fraction",
                mode="expression",
                prompt_template="Find x: {a}/{b} = x/{d}",
                answer_expr="a*d/b",
                explanation_template="Multiply numerator and denominator by the same factor.",
                vars=[_var("a", 1, 12), _var("b", 2, 12), _var("d", 4, 60)],
                min_level=1,
                max_level=3,
                constraint_expr="a<b and (a*d)%b==0",
            )
        )

    for i in range(1, 11):
        items.append(
            _tpl(
                external_id=f"khan.v2.algebra_linear.solve.v{i}",
                skill="algebra_linear",
                subskill="Linear equations",
                label="Solve one-variable linear equation",
                mode="expression",
                prompt_template="Solve for x: {m}x + {c} = {rhs}",
                answer_expr="(rhs-c)/m",
                explanation_template="Undo addition/subtraction, then divide by the coefficient.",
                vars=[_var("m", 1, 15), _var("c", -30, 30), _var("rhs", -120, 120)],
                min_level=2,
                max_level=3,
                constraint_expr="(rhs-c)%m==0",
                choice_spread=10.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.algebra_linear.word.intercept.v{i}",
                skill="algebra_linear",
                subskill="Linear equation word problems",
                label="Initial fee from linear model",
                mode="word",
                prompt_template=(
                    "A service charges total cost C = {m}n + {b}, where n is number of items. "
                    "What is the initial fee?"
                ),
                answer_expr="b",
                explanation_template="In C = mn + b, the constant b is the initial fee.",
                vars=[_var("m", 1, 25), _var("b", 2, 180)],
                min_level=2,
                max_level=3,
                choice_spread=8.0,
            )
        )

    for i in range(1, 9):
        items.append(
            _tpl(
                external_id=f"khan.v2.geometry_area.rect.v{i}",
                skill="geometry_area",
                subskill="Area and perimeter",
                label="Rectangle area",
                mode="expression",
                prompt_template="Find the area of a rectangle with length {l} and width {w}.",
                answer_expr="l*w",
                explanation_template="Area of a rectangle is length times width.",
                vars=[_var("l", 3, 40), _var("w", 2, 30)],
                min_level=1,
                max_level=2,
                choice_spread=12.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.geometry_area.word.paint.v{i}",
                skill="geometry_area",
                subskill="Area word problems",
                label="Paint/tile area problem",
                mode="word",
                prompt_template=(
                    "A wall is {l} meters by {w} meters. "
                    "Paint covers {r} square meters per liter. How many liters are needed?"
                ),
                answer_expr="(l*w)/r",
                explanation_template="Find wall area, then divide by coverage per liter.",
                vars=[_var("l", 4, 24), _var("w", 3, 18), _var("r", 2, 12)],
                min_level=1,
                max_level=3,
                constraint_expr="(l*w)%r==0",
            )
        )

    for i in range(1, 9):
        items.append(
            _tpl(
                external_id=f"khan.v2.stats_percent.word.v{i}",
                skill="stats_percent",
                subskill="Percent word problems",
                label="Part as a percent of whole",
                mode="word",
                prompt_template=(
                    "A survey has {part} responses in one category out of {whole} total. "
                    "What percent is that?"
                ),
                answer_expr="(100*part)/whole",
                explanation_template="Percent equals part divided by whole, times 100.",
                vars=[_var("part", 2, 90), _var("whole", 20, 240)],
                min_level=1,
                max_level=3,
                constraint_expr="whole>part",
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.stats_percent.word.intuition.v{i}",
                skill="stats_percent",
                subskill="Percent word problems",
                label="Percent denominator setup",
                mode="intuition",
                prompt_template=(
                    "A survey has {part} responses in one category out of {whole} total. "
                    "What total belongs in the denominator before you convert the ratio to a percent?"
                ),
                answer_expr="whole",
                explanation_template="Percent setup starts with part over whole, so the denominator is the full sample size.",
                vars=[_var("part", 2, 90), _var("whole", 20, 240)],
                min_level=1,
                max_level=3,
                constraint_expr="whole>part",
                choice_spread=12.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.stats_mean.list.v{i}",
                skill="stats_mean",
                subskill="Mean",
                label="Arithmetic mean",
                mode="expression",
                prompt_template="Find the mean of: {a}, {b}, {c}, and {d}.",
                answer_expr="(a+b+c+d)/4",
                explanation_template="Add all values and divide by 4.",
                vars=[_var("a", 1, 30), _var("b", 1, 30), _var("c", 1, 30), _var("d", 1, 30)],
                min_level=1,
                max_level=3,
                constraint_expr="(a+b+c+d)%4==0",
                choice_spread=4.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.stats_mean.list.intuition.v{i}",
                skill="stats_mean",
                subskill="Mean",
                label="Mean total before divide",
                mode="intuition",
                prompt_template="Before dividing by 4, what total do you get from {a}, {b}, {c}, and {d}?",
                answer_expr="a+b+c+d",
                explanation_template="The mean starts with the total of all values before you divide by the count.",
                vars=[_var("a", 1, 30), _var("b", 1, 30), _var("c", 1, 30), _var("d", 1, 30)],
                min_level=1,
                max_level=3,
                choice_spread=12.0,
            )
        )

    for i in range(1, 9):
        items.append(
            _tpl(
                external_id=f"khan.v2.stats_probability.model.v{i}",
                skill="stats_probability",
                subskill="Probability models",
                label="Simple probability from counts",
                mode="word",
                prompt_template=(
                    "A bag has {a} red, {b} blue, and {c} green marbles. "
                    "What is the probability (as a percent) of drawing red?"
                ),
                answer_expr="(100*a)/(a+b+c)",
                explanation_template="Probability is favorable over total outcomes, then convert to percent.",
                vars=[_var("a", 2, 40), _var("b", 2, 40), _var("c", 2, 40)],
                min_level=1,
                max_level=3,
                constraint_expr="(100*a)%(a+b+c)==0",
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.stats_probability.model.intuition.v{i}",
                skill="stats_probability",
                subskill="Probability models",
                label="Probability denominator",
                mode="intuition",
                prompt_template=(
                    "A bag has {a} red, {b} blue, and {c} green marbles. "
                    "How many total marbles belong in the denominator of the probability ratio?"
                ),
                answer_expr="a+b+c",
                explanation_template="Probability uses favorable outcomes over total outcomes, so first count all possible outcomes.",
                vars=[_var("a", 2, 40), _var("b", 2, 40), _var("c", 2, 40)],
                min_level=1,
                max_level=3,
                choice_spread=12.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.calculus_slope.twopoints.v{i}",
                skill="calculus_slope",
                subskill="Slope from two points",
                label="Slope from coordinates",
                mode="expression",
                prompt_template="Find slope through ({x1},{y1}) and ({x2},{y2}).",
                answer_expr="(y2-y1)/(x2-x1)",
                explanation_template="Use slope formula: rise over run.",
                vars=[_var("x1", -12, 6), _var("y1", -20, 20), _var("x2", 7, 20), _var("y2", -20, 20)],
                min_level=2,
                max_level=3,
                constraint_expr="",
                choice_spread=7.0,
            )
        )

    for i in range(1, 11):
        items.append(
            _tpl(
                external_id=f"khan.v2.pre_algebra.mixed.v{i}",
                skill="pre_algebra",
                subskill="Order of operations",
                label="Pre-algebra mixed",
                mode="expression",
                prompt_template="Evaluate: ({a} - {b})*{c} + {d}",
                answer_expr="(a-b)*c+d",
                explanation_template="Follow order of operations and signed arithmetic.",
                vars=[_var("a", 10, 60), _var("b", 2, 40), _var("c", 2, 9), _var("d", -25, 25)],
                min_level=2,
                max_level=3,
                constraint_expr="a>b",
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.algebra1.solve.v{i}",
                skill="algebra_1",
                subskill="Linear equations and modeling",
                label="Algebra 1 linear solve",
                mode="expression",
                prompt_template="Solve for x: {m}x + {b} = {rhs}",
                answer_expr="(rhs-b)/m",
                explanation_template="Use inverse operations to isolate x.",
                vars=[_var("m", 1, 18), _var("b", -30, 30), _var("rhs", -150, 150)],
                min_level=2,
                max_level=3,
                constraint_expr="(rhs-b)%m==0",
            )
        )

    for i in range(1, 9):
        items.append(
            _tpl(
                external_id=f"khan.v2.algebra2.poly_eval.v{i}",
                skill="algebra_2",
                subskill="Expression and function structure",
                label="Polynomial-style evaluation",
                mode="expression",
                prompt_template="Evaluate f(x) = {a}x^2 + {b}x + {c} at x = {x}.",
                answer_expr="a*(x**2)+b*x+c",
                explanation_template="Substitute x, evaluate power, then combine terms.",
                vars=[_var("a", 1, 8), _var("b", -12, 12), _var("c", -20, 20), _var("x", -6, 6)],
                min_level=2,
                max_level=3,
                choice_spread=16.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.statistics.core.v{i}",
                skill="statistics",
                subskill="Integrated descriptive statistics and probability",
                label="Statistics integrated question",
                mode="word",
                prompt_template=(
                    "A sample has {a} red, {b} blue, and {c} green items. "
                    "What percent are blue?"
                ),
                answer_expr="(100*b)/(a+b+c)",
                explanation_template="Compute blue divided by total, then convert to percent.",
                vars=[_var("a", 5, 40), _var("b", 5, 40), _var("c", 5, 40)],
                min_level=1,
                max_level=3,
                constraint_expr="(100*b)%(a+b+c)==0",
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.statistics.core.intuition.v{i}",
                skill="statistics",
                subskill="Integrated descriptive statistics and probability",
                label="Statistics sample total",
                mode="intuition",
                prompt_template=(
                    "A sample has {a} red, {b} blue, and {c} green items. "
                    "How many total items are in the sample before you compute any percent?"
                ),
                answer_expr="a+b+c",
                explanation_template="Integrated statistics questions still start by identifying the full sample size before comparing categories.",
                vars=[_var("a", 5, 40), _var("b", 5, 40), _var("c", 5, 40)],
                min_level=1,
                max_level=3,
                choice_spread=12.0,
            )
        )

    for i in range(1, 9):
        items.append(
            _tpl(
                external_id=f"khan.v2.sat_math.linear_fee.v{i}",
                skill="sat_math",
                subskill="SAT algebra modeling",
                label="Linear fee model",
                mode="word",
                prompt_template="A plan charges a ${b} fee plus ${m} per month. After {n} months, what is total cost?",
                answer_expr="b+m*n",
                explanation_template="Model as fixed fee plus per-month cost.",
                vars=[_var("b", 10, 200), _var("m", 5, 60), _var("n", 2, 24)],
                min_level=2,
                max_level=3,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.sat_math.linear_fee.intuition.v{i}",
                skill="sat_math",
                subskill="SAT algebra modeling",
                label="Linear fee setup",
                mode="intuition",
                prompt_template=(
                    "A plan charges a ${b} fee plus ${m} per month for {n} months. "
                    "Before adding the fixed fee, how much comes from the monthly charges?"
                ),
                answer_expr="m*n",
                explanation_template="Separate the repeated monthly charge from the fixed fee before building the full model.",
                vars=[_var("b", 10, 200), _var("m", 5, 60), _var("n", 2, 24)],
                min_level=2,
                max_level=3,
                choice_spread=14.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.sat_math.percent_change.v{i}",
                skill="sat_math",
                subskill="SAT percent and data",
                label="Percent increase/decrease",
                mode="word",
                prompt_template="A value changes from {a} to {b}. What is the percent change from the original value?",
                answer_expr="((b-a)*100)/a",
                explanation_template="Percent change is (new-old)/old times 100.",
                vars=[_var("a", 20, 200), _var("b", 10, 260)],
                min_level=2,
                max_level=3,
                constraint_expr="a!=0 and ((b-a)*100)%a==0",
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.sat_math.percent_change.intuition.v{i}",
                skill="sat_math",
                subskill="SAT percent and data",
                label="Percent change setup",
                mode="intuition",
                prompt_template="A value changes from {a} to {b}. What is the signed change before you divide by the original value?",
                answer_expr="b-a",
                explanation_template="Percent change starts with new minus original before converting that change to a relative comparison.",
                vars=[_var("a", 20, 200), _var("b", 10, 260)],
                min_level=2,
                max_level=3,
                choice_spread=16.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.sat_math.slope_points.v{i}",
                skill="sat_math",
                subskill="SAT linear relationships",
                label="Slope from two points",
                mode="expression",
                prompt_template="Find the slope through ({x1},{y1}) and ({x2},{y2}).",
                answer_expr="(y2-y1)/(x2-x1)",
                explanation_template="Use rise over run.",
                vars=[_var("x1", -10, 5), _var("y1", -20, 20), _var("x2", 6, 20), _var("y2", -20, 20)],
                min_level=2,
                max_level=3,
                choice_spread=7.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.sat_math.slope_points.intuition.v{i}",
                skill="sat_math",
                subskill="SAT linear relationships",
                label="Rise before slope",
                mode="intuition",
                prompt_template="Between ({x1},{y1}) and ({x2},{y2}), what is the vertical change (rise)?",
                answer_expr="y2-y1",
                explanation_template="Slope compares rise to run, so identify the rise first before forming the ratio.",
                vars=[_var("x1", -10, 5), _var("y1", -20, 20), _var("x2", 6, 20), _var("y2", -20, 20)],
                min_level=2,
                max_level=3,
                choice_spread=9.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.sat_math.mean_table.v{i}",
                skill="sat_math",
                subskill="SAT statistics",
                label="Mean from data",
                mode="expression",
                prompt_template="Find the mean of {a}, {b}, {c}, {d}, {e}.",
                answer_expr="(a+b+c+d+e)/5",
                explanation_template="Add all values and divide by 5.",
                vars=[_var("a", 10, 80), _var("b", 10, 80), _var("c", 10, 80), _var("d", 10, 80), _var("e", 10, 80)],
                min_level=2,
                max_level=3,
                constraint_expr="(a+b+c+d+e)%5==0",
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.sat_math.mean_table.intuition.v{i}",
                skill="sat_math",
                subskill="SAT statistics",
                label="Total before mean",
                mode="intuition",
                prompt_template="Before dividing by 5, what total do you get from {a}, {b}, {c}, {d}, and {e}?",
                answer_expr="a+b+c+d+e",
                explanation_template="Statistics questions about means begin with the total of all data values before dividing by the count.",
                vars=[_var("a", 10, 80), _var("b", 10, 80), _var("c", 10, 80), _var("d", 10, 80), _var("e", 10, 80)],
                min_level=2,
                max_level=3,
                choice_spread=16.0,
            )
        )

    for i in range(1, 13):
        items.append(
            _tpl(
                external_id=f"khan.v2.sat_math.mixed.v{i}",
                skill="sat_math",
                subskill="SAT mixed-domain",
                label="Discounted plan total",
                mode="word",
                prompt_template=(
                    "A tutoring package charges a fixed fee of ${b} plus ${m} per session. "
                    "A student attends {n} sessions and then gets a {pct}% discount on the total bill. "
                    "What is the discounted total cost?"
                ),
                answer_expr="(b+m*n)*(100-pct)/100",
                explanation_template="Build the original linear total first, then keep the remaining percent after the discount.",
                vars=[_var("b", 20, 180), _var("m", 6, 35), _var("n", 2, 18), _var("pct", 5, 40, 5)],
                min_level=2,
                max_level=3,
                constraint_expr="((b+m*n)*(100-pct))%100==0",
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.sat_math.mixed.intuition.v{i}",
                skill="sat_math",
                subskill="SAT mixed-domain",
                label="Original total before discount",
                mode="intuition",
                prompt_template=(
                    "A tutoring package charges a fixed fee of ${b} plus ${m} per session for {n} sessions. "
                    "Before applying a {pct}% discount, what is the original total bill?"
                ),
                answer_expr="b+m*n",
                explanation_template="Mixed-domain problems are easier when you separate the linear total from the later percent adjustment.",
                vars=[_var("b", 20, 180), _var("m", 6, 35), _var("n", 2, 18), _var("pct", 5, 40, 5)],
                min_level=2,
                max_level=3,
                choice_spread=16.0,
            )
        )

    for i in range(1, 9):
        items.append(
            _tpl(
                external_id=f"khan.v2.psat_math.linear_fee.v{i}",
                skill="psat_math",
                subskill="PSAT algebra modeling",
                label="Linear fee model",
                mode="word",
                prompt_template="A school club charges a ${b} signup fee plus ${m} per event. After {n} events, what is total cost?",
                answer_expr="b+m*n",
                explanation_template="Model as initial fee plus repeated per-event cost.",
                vars=[_var("b", 5, 120), _var("m", 3, 35), _var("n", 2, 18)],
                min_level=1,
                max_level=3,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.psat_math.linear_fee.intuition.v{i}",
                skill="psat_math",
                subskill="PSAT algebra modeling",
                label="Event-cost setup",
                mode="intuition",
                prompt_template=(
                    "A school club charges a ${b} signup fee plus ${m} per event for {n} events. "
                    "Before adding the signup fee, how much comes from the event charges?"
                ),
                answer_expr="m*n",
                explanation_template="Separate the repeated event cost from the one-time fee before building the final expression.",
                vars=[_var("b", 5, 120), _var("m", 3, 35), _var("n", 2, 18)],
                min_level=1,
                max_level=3,
                choice_spread=12.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.psat_math.percent_part.v{i}",
                skill="psat_math",
                subskill="PSAT percentages",
                label="Part-to-percent",
                mode="word",
                prompt_template="A sample has {part} items out of {whole} total in one category. What percent are in that category?",
                answer_expr="(100*part)/whole",
                explanation_template="Part divided by whole times 100.",
                vars=[_var("part", 5, 90), _var("whole", 20, 180)],
                min_level=1,
                max_level=3,
                constraint_expr="whole>part and (100*part)%whole==0",
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.psat_math.percent_part.intuition.v{i}",
                skill="psat_math",
                subskill="PSAT percentages",
                label="Percent denominator",
                mode="intuition",
                prompt_template=(
                    "A sample has {part} items out of {whole} total in one category. "
                    "What total belongs in the denominator before converting the ratio to a percent?"
                ),
                answer_expr="whole",
                explanation_template="Part-to-percent questions start with part over whole, so the denominator is the full sample.",
                vars=[_var("part", 5, 90), _var("whole", 20, 180)],
                min_level=1,
                max_level=3,
                constraint_expr="whole>part",
                choice_spread=12.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.psat_math.area_word.v{i}",
                skill="psat_math",
                subskill="PSAT geometry",
                label="Area word problem",
                mode="word",
                prompt_template="A rectangle has length {l} and width {w}. Each square unit costs ${c}. What is total cost?",
                answer_expr="l*w*c",
                explanation_template="Compute area, then multiply by per-unit cost.",
                vars=[_var("l", 4, 20), _var("w", 3, 16), _var("c", 2, 15)],
                min_level=1,
                max_level=3,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.psat_math.area_word.intuition.v{i}",
                skill="psat_math",
                subskill="PSAT geometry",
                label="Area before cost",
                mode="intuition",
                prompt_template=(
                    "A rectangle has length {l} and width {w}. "
                    "Before multiplying by the ${c} cost per square unit, what is the rectangle's area?"
                ),
                answer_expr="l*w",
                explanation_template="Word geometry problems often separate the geometric quantity first and the cost calculation second.",
                vars=[_var("l", 4, 20), _var("w", 3, 16), _var("c", 2, 15)],
                min_level=1,
                max_level=3,
                choice_spread=14.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.psat_math.simple_eq.v{i}",
                skill="psat_math",
                subskill="PSAT equation solving",
                label="Solve one-step/two-step equation",
                mode="expression",
                prompt_template="Solve for x: {m}x + {b} = {rhs}",
                answer_expr="(rhs-b)/m",
                explanation_template="Undo addition/subtraction, then divide by coefficient.",
                vars=[_var("m", 1, 12), _var("b", -24, 24), _var("rhs", -120, 120)],
                min_level=1,
                max_level=3,
                constraint_expr="(rhs-b)%m==0",
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.psat_math.simple_eq.intuition.v{i}",
                skill="psat_math",
                subskill="PSAT equation solving",
                label="Undo the constant first",
                mode="intuition",
                prompt_template="In {m}x + {b} = {rhs}, what value remains after you undo the constant term?",
                answer_expr="rhs-b",
                explanation_template="Equation solving starts by removing the constant term before dividing by the coefficient.",
                vars=[_var("m", 1, 12), _var("b", -24, 24), _var("rhs", -120, 120)],
                min_level=1,
                max_level=3,
                choice_spread=16.0,
            )
        )

    for i in range(1, 13):
        items.append(
            _tpl(
                external_id=f"khan.v2.psat_math.mixed.v{i}",
                skill="psat_math",
                subskill="PSAT mixed-domain",
                label="Discounted club total",
                mode="word",
                prompt_template=(
                    "A school club charges a signup fee of ${b} plus ${m} per event. "
                    "A student attends {n} events and then receives a {pct}% discount on the final bill. "
                    "What is the discounted total cost?"
                ),
                answer_expr="(b+m*n)*(100-pct)/100",
                explanation_template="Build the original linear total first, then apply the percent discount to that total.",
                vars=[_var("b", 10, 120), _var("m", 4, 24), _var("n", 2, 16), _var("pct", 5, 40, 5)],
                min_level=1,
                max_level=3,
                constraint_expr="((b+m*n)*(100-pct))%100==0",
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.psat_math.mixed.intuition.v{i}",
                skill="psat_math",
                subskill="PSAT mixed-domain",
                label="Total before discount",
                mode="intuition",
                prompt_template=(
                    "A school club charges a signup fee of ${b} plus ${m} per event for {n} events. "
                    "Before a {pct}% discount is applied, what is the original total bill?"
                ),
                answer_expr="b+m*n",
                explanation_template="Mixed-domain problems are easier when you first write the undiscounted total and only then handle the percent change.",
                vars=[_var("b", 10, 120), _var("m", 4, 24), _var("n", 2, 16), _var("pct", 5, 40, 5)],
                min_level=1,
                max_level=3,
                choice_spread=14.0,
            )
        )

    for i in range(1, 13):
        items.append(
            _tpl(
                external_id=f"khan.v2.gre_quant.qc.v{i}",
                skill="gre_quant",
                subskill="GRE quantitative comparison",
                label="Quantitative comparison difference",
                mode="expression",
                prompt_template=(
                    "Quantity A is {a}/{b}. Quantity B is {c}/{d}. "
                    "Compute Quantity A - Quantity B."
                ),
                answer_expr="(a/b)-(c/d)",
                explanation_template="Comparing two quantities is often easiest if you subtract one from the other after finding a common denominator.",
                vars=[_var("a", 2, 40), _var("b", 2, 20), _var("c", 2, 40), _var("d", 2, 20)],
                min_level=2,
                max_level=3,
                choice_spread=3.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.gre_quant.qc.intuition.v{i}",
                skill="gre_quant",
                subskill="GRE quantitative comparison",
                label="Common denominator setup",
                mode="intuition",
                prompt_template="To compare {a}/{b} and {c}/{d}, what common denominator could you use?",
                answer_expr="b*d",
                explanation_template="A common denominator turns both fractions into comparable quantities before you decide which is larger.",
                vars=[_var("a", 2, 40), _var("b", 2, 20), _var("c", 2, 40), _var("d", 2, 20)],
                min_level=2,
                max_level=3,
                choice_spread=12.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.gre_quant.ratio_word.v{i}",
                skill="gre_quant",
                subskill="GRE ratios and proportions",
                label="Ratio scaling word problem",
                mode="word",
                prompt_template="A recipe uses {a} units for every {b} servings. How many units are needed for {k} servings?",
                answer_expr="(a*k)/b",
                explanation_template="Scale both sides of the ratio by the same factor.",
                vars=[_var("a", 2, 25), _var("b", 2, 20), _var("k", 4, 60)],
                min_level=2,
                max_level=3,
                constraint_expr="(a*k)%b==0",
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.gre_quant.ratio_word.intuition.v{i}",
                skill="gre_quant",
                subskill="GRE ratios and proportions",
                label="Ratio scaling factor",
                mode="intuition",
                prompt_template="A recipe covers {b} servings. If you need {k} servings, by what factor do you scale the recipe?",
                answer_expr="k/b",
                explanation_template="Ratio problems are easier when you find the scale factor first and apply it to each quantity after that.",
                vars=[_var("a", 2, 25), _var("b", 2, 20), _var("k", 4, 60)],
                min_level=2,
                max_level=3,
                constraint_expr="k%b==0",
                choice_spread=3.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.gre_quant.percent_delta.v{i}",
                skill="gre_quant",
                subskill="GRE percent reasoning",
                label="Percent difference",
                mode="word",
                prompt_template="A value rises from {a} to {b}. What is the percent increase?",
                answer_expr="((b-a)*100)/a",
                explanation_template="Compute increase over original times 100.",
                vars=[_var("a", 25, 220), _var("b", 30, 320)],
                min_level=2,
                max_level=3,
                constraint_expr="b>a and ((b-a)*100)%a==0",
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.gre_quant.percent_delta.intuition.v{i}",
                skill="gre_quant",
                subskill="GRE percent reasoning",
                label="Raw increase before percent",
                mode="intuition",
                prompt_template="A value rises from {a} to {b}. Before converting the increase to a percent, what is the increase amount?",
                answer_expr="b-a",
                explanation_template="Percent reasoning begins with the raw increase before you compare it to the original value.",
                vars=[_var("a", 25, 220), _var("b", 30, 320)],
                min_level=2,
                max_level=3,
                constraint_expr="b>a",
                choice_spread=12.0,
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.gre_quant.mean_set.v{i}",
                skill="gre_quant",
                subskill="GRE data interpretation",
                label="Mean from set",
                mode="expression",
                prompt_template="Find the mean of {a}, {b}, {c}, and {d}.",
                answer_expr="(a+b+c+d)/4",
                explanation_template="Average is total divided by count.",
                vars=[_var("a", 10, 90), _var("b", 10, 90), _var("c", 10, 90), _var("d", 10, 90)],
                min_level=2,
                max_level=3,
                constraint_expr="(a+b+c+d)%4==0",
            )
        )
        items.append(
            _tpl(
                external_id=f"khan.v2.gre_quant.mean_set.intuition.v{i}",
                skill="gre_quant",
                subskill="GRE data interpretation",
                label="Total before average",
                mode="intuition",
                prompt_template="Before dividing by 4, what total do you get from {a}, {b}, {c}, and {d}?",
                answer_expr="a+b+c+d",
                explanation_template="Data interpretation with averages starts by combining the full total before dividing by the number of values.",
                vars=[_var("a", 10, 90), _var("b", 10, 90), _var("c", 10, 90), _var("d", 10, 90)],
                min_level=2,
                max_level=3,
                choice_spread=16.0,
            )
        )

    return items


def main() -> int:
    items = build_manifest()
    out_path = Path("scripts/template_manifests/khan_sat_focus_v2.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(items, indent=2), encoding="utf-8")
    print(f"wrote {len(items)} templates to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
