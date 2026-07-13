from __future__ import annotations

from datetime import datetime, timezone
import re
import sqlite3

from .summer_program_preview_template_seed import (
    PREVIEW_EXPRESSION_TARGETS,
    PREVIEW_SEED_PATTERNS,
    PREVIEW_WORD_TARGETS,
)
from .summer_program_seed_types import SeedPattern


EXPRESSION_TARGETS: dict[tuple[str, str], int] = {
    ("place_value", "Ones, tens, and hundreds identification"): 8,
    ("place_value", "Expanded form"): 8,
    ("place_value", "Compare numbers by place value"): 8,
    ("place_value", "Decimal place value and comparison"): 8,
    ("fractions", "Unit fractions"): 10,
    ("fractions", "Equivalent fractions"): 10,
    ("fractions", "Shaded region meaning"): 10,
    ("fractions", "Fraction to decimal"): 10,
    ("fractions", "Compare fractions and mixed numbers"): 10,
    ("measurement", "Length unit conversion"): 8,
    ("measurement", "Time reading and arithmetic"): 8,
    ("measurement", "Temperature basics"): 8,
    ("measurement", "Metric and customary conversions"): 8,
    ("measurement", "Elapsed time"): 8,
    ("money", "Dollar-coin values"): 8,
    ("money", "Making change"): 8,
    ("money", "Budget-style totals"): 8,
    ("money", "Place-value in currency"): 8,
    ("ratios", "Ratio language (to:of)"): 8,
    ("ratios", "Equivalent ratios"): 8,
    ("ratios", "Fractional comparison"): 8,
    ("ratios", "Unit rates and proportional relationships"): 8,
    ("pre_algebra", "Integer and fraction fluency"): 12,
    ("pre_algebra", "Order of operations"): 12,
    ("pre_algebra", "Expressions and variables"): 12,
    ("pre_algebra", "One-step equations"): 12,
    ("pre_algebra", "Two-step equations and inequalities"): 12,
    ("pre_algebra", "Ratios, rates, and proportional relationships"): 12,
    ("pre_algebra", "Percent problems"): 12,
    ("pre_algebra", "Exponents, roots, and scientific notation"): 12,
    ("pre_algebra", "Coordinate plane and function tables"): 12,
}
EXPRESSION_TARGETS.update(PREVIEW_EXPRESSION_TARGETS)

WORD_TARGETS: dict[tuple[str, str], int] = {
    ("pre_algebra", "Ratios, rates, and proportional relationships"): 6,
    ("pre_algebra", "Percent problems"): 6,
    ("pre_algebra", "Coordinate plane and function tables"): 6,
}
WORD_TARGETS.update(PREVIEW_WORD_TARGETS)


SEED_PATTERNS: dict[tuple[str, str, str], tuple[SeedPattern, ...]] = {
    ("place_value", "Ones, tens, and hundreds identification", "expression"): (
        SeedPattern("What digit is in the hundreds place of {h}{te}{o}?", "h", "", "The hundreds place is the third digit from the right.", ({"name": "h", "kind": "int", "min": 1, "max": 9, "step": 1}, {"name": "te", "kind": "int", "min": 0, "max": 9, "step": 1}, {"name": "o", "kind": "int", "min": 0, "max": 9, "step": 1})),
        SeedPattern("What value does the tens digit represent in {h}{te}{o}?", "te * 10", "", "A tens digit counts groups of ten.", ({"name": "h", "kind": "int", "min": 1, "max": 9, "step": 1}, {"name": "te", "kind": "int", "min": 1, "max": 9, "step": 1}, {"name": "o", "kind": "int", "min": 0, "max": 9, "step": 1}), 20.0),
    ),
    ("place_value", "Expanded form", "expression"): (
        SeedPattern("In {h}{te}{o}, how much is the hundreds part worth?", "h * 100", "", "Expanded form separates the hundreds, tens, and ones parts.", ({"name": "h", "kind": "int", "min": 1, "max": 9, "step": 1}, {"name": "te", "kind": "int", "min": 0, "max": 9, "step": 1}, {"name": "o", "kind": "int", "min": 0, "max": 9, "step": 1}), 80.0),
        SeedPattern("What is the tens-value term in the expanded form of {h}{te}{o}?", "te * 10", "", "The tens-value term is the tens digit times ten.", ({"name": "h", "kind": "int", "min": 1, "max": 9, "step": 1}, {"name": "te", "kind": "int", "min": 1, "max": 9, "step": 1}, {"name": "o", "kind": "int", "min": 0, "max": 9, "step": 1}), 20.0),
    ),
    ("place_value", "Compare numbers by place value", "expression"): (
        SeedPattern("Which number is greater: {a_h}{a_t}{a_o} or {b_h}{b_t}{b_o}? Enter the greater number.", "(a_h * 100 + a_t * 10 + a_o) if (a_h * 100 + a_t * 10 + a_o) > (b_h * 100 + b_t * 10 + b_o) else (b_h * 100 + b_t * 10 + b_o)", "(a_h * 100 + a_t * 10 + a_o) != (b_h * 100 + b_t * 10 + b_o)", "Compare the highest place first.", ({"name": "a_h", "kind": "int", "min": 1, "max": 9, "step": 1}, {"name": "a_t", "kind": "int", "min": 0, "max": 9, "step": 1}, {"name": "a_o", "kind": "int", "min": 0, "max": 9, "step": 1}, {"name": "b_h", "kind": "int", "min": 1, "max": 9, "step": 1}, {"name": "b_t", "kind": "int", "min": 0, "max": 9, "step": 1}, {"name": "b_o", "kind": "int", "min": 0, "max": 9, "step": 1}), 120.0),
    ),
    ("place_value", "Decimal place value and comparison", "expression"): (
        SeedPattern("What digit is in the tenths place of {w}.{t}{h}?", "t", "", "The tenths place is the first digit to the right of the decimal.", ({"name": "w", "kind": "int", "min": 1, "max": 9, "step": 1}, {"name": "t", "kind": "int", "min": 0, "max": 9, "step": 1}, {"name": "h", "kind": "int", "min": 0, "max": 9, "step": 1})),
        SeedPattern("What value does the hundredths digit represent in {w}.{t}{h}?", "h / 100", "", "The hundredths place means parts of one hundred.", ({"name": "w", "kind": "int", "min": 1, "max": 9, "step": 1}, {"name": "t", "kind": "int", "min": 0, "max": 9, "step": 1}, {"name": "h", "kind": "int", "min": 1, "max": 9, "step": 1}), 1.0),
    ),
    ("fractions", "Unit fractions", "expression"): (SeedPattern("A whole is split into {d} equal parts. What decimal value is 1/{d}?", "1 / d", "d > 1", "A unit fraction has one part of the whole.", ({"name": "d", "kind": "int", "min": 2, "max": 12, "step": 1},), 1.2),),
    ("fractions", "Equivalent fractions", "expression"): (SeedPattern("Fill in the blank: {n}/{d} = x/{scaled_d}. What is x?", "n * scale", "scaled_d == d * scale", "Multiply numerator and denominator by the same scale factor.", ({"name": "n", "kind": "int", "min": 1, "max": 8, "step": 1}, {"name": "d", "kind": "int", "min": 2, "max": 12, "step": 1}, {"name": "scale", "kind": "int", "min": 2, "max": 6, "step": 1}, {"name": "scaled_d", "kind": "int", "min": 4, "max": 72, "step": 1}), 8.0),),
    ("fractions", "Shaded region meaning", "expression"): (SeedPattern("A shape has {d} equal parts and {n} are shaded. What percent is shaded?", "(n / d) * 100", "n < d", "The shaded amount is the part over the whole.", ({"name": "n", "kind": "int", "min": 1, "max": 7, "step": 1}, {"name": "d", "kind": "int", "min": 2, "max": 8, "step": 1}), 25.0),),
    ("fractions", "Fraction to decimal", "expression"): (SeedPattern("Write {n}/{d} as a decimal.", "n / d", "n < d", "Divide numerator by denominator to convert the fraction.", ({"name": "n", "kind": "int", "min": 1, "max": 9, "step": 1}, {"name": "d", "kind": "int", "min": 2, "max": 10, "step": 1}), 1.5),),
    ("fractions", "Compare fractions and mixed numbers", "expression"): (SeedPattern("Which is greater: {a}/{d} or {b}/{d}? Enter the greater numerator.", "a if a > b else b", "a != b", "With equal denominators, the larger numerator is greater.", ({"name": "a", "kind": "int", "min": 1, "max": 8, "step": 1}, {"name": "b", "kind": "int", "min": 1, "max": 8, "step": 1}, {"name": "d", "kind": "int", "min": 2, "max": 10, "step": 1}), 4.0),),
    ("measurement", "Length unit conversion", "expression"): (SeedPattern("How many inches are in {feet} feet?", "feet * 12", "", "Multiply feet by 12 to convert to inches.", ({"name": "feet", "kind": "int", "min": 1, "max": 12, "step": 1},), 24.0),),
    ("measurement", "Time reading and arithmetic", "expression"): (SeedPattern("How many minutes are in {hours} hours?", "hours * 60", "", "Each hour has 60 minutes.", ({"name": "hours", "kind": "int", "min": 1, "max": 10, "step": 1},), 40.0),),
    ("measurement", "Temperature basics", "expression"): (SeedPattern("A thermometer rises from {start} to {end}. How many degrees did it rise?", "end - start", "end > start", "Temperature change is the ending temperature minus the starting temperature.", ({"name": "start", "kind": "int", "min": -10, "max": 70, "step": 1}, {"name": "end", "kind": "int", "min": -5, "max": 90, "step": 1}), 12.0),),
    ("measurement", "Metric and customary conversions", "expression"): (SeedPattern("How many centimeters are in {meters} meters?", "meters * 100", "", "Each meter is 100 centimeters.", ({"name": "meters", "kind": "int", "min": 1, "max": 12, "step": 1},), 60.0),),
    ("measurement", "Elapsed time", "expression"): (SeedPattern("A trip lasts {hours} hours and {minutes} minutes. How many minutes is that in all?", "hours * 60 + minutes", "", "Convert the hours to minutes, then add the extra minutes.", ({"name": "hours", "kind": "int", "min": 1, "max": 8, "step": 1}, {"name": "minutes", "kind": "int", "min": 5, "max": 55, "step": 5}), 45.0),),
    ("money", "Dollar-coin values", "expression"): (SeedPattern("How many cents are in ${d}.{c}?", "d * 100 + c", "", "One dollar is one hundred cents.", ({"name": "d", "kind": "int", "min": 0, "max": 12, "step": 1}, {"name": "c", "kind": "int", "min": 0, "max": 99, "step": 1}), 45.0),),
    ("money", "Making change", "expression"): (SeedPattern("You pay {paid} cents for an item costing {cost} cents. How much change do you get?", "paid - cost", "paid > cost", "Subtract the cost from the amount paid.", ({"name": "paid", "kind": "int", "min": 100, "max": 900, "step": 5}, {"name": "cost", "kind": "int", "min": 25, "max": 700, "step": 5}), 45.0),),
    ("money", "Budget-style totals", "expression"): (SeedPattern("A snack costs {a} cents and a drink costs {b} cents. What is the total cost?", "a + b", "", "Add the two prices to get the budget total.", ({"name": "a", "kind": "int", "min": 25, "max": 500, "step": 5}, {"name": "b", "kind": "int", "min": 25, "max": 500, "step": 5}), 40.0),),
    ("money", "Place-value in currency", "expression"): (SeedPattern("What is the value of the dollars digit in ${d}.{c}?", "d * 100", "", "The dollars digit counts hundreds of cents.", ({"name": "d", "kind": "int", "min": 1, "max": 9, "step": 1}, {"name": "c", "kind": "int", "min": 0, "max": 99, "step": 1}), 80.0),),
    ("ratios", "Ratio language (to:of)", "expression"): (SeedPattern("A mix uses {a} parts red to {b} parts blue. How many total parts are there?", "a + b", "", "A ratio compares two parts; total parts combine them.", ({"name": "a", "kind": "int", "min": 1, "max": 8, "step": 1}, {"name": "b", "kind": "int", "min": 1, "max": 9, "step": 1}), 10.0),),
    ("ratios", "Equivalent ratios", "expression"): (SeedPattern("Scale the ratio {a}:{b} by {scale}. What is the new second number?", "b * scale", "", "Equivalent ratios scale both parts by the same factor.", ({"name": "a", "kind": "int", "min": 1, "max": 8, "step": 1}, {"name": "b", "kind": "int", "min": 1, "max": 9, "step": 1}, {"name": "scale", "kind": "int", "min": 2, "max": 6, "step": 1}), 12.0),),
    ("ratios", "Fractional comparison", "expression"): (SeedPattern("A ratio is {a}:{b}. How many total parts are in the whole comparison?", "a + b", "", "Part-to-whole comparison uses the total number of parts.", ({"name": "a", "kind": "int", "min": 1, "max": 8, "step": 1}, {"name": "b", "kind": "int", "min": 1, "max": 9, "step": 1}), 10.0),),
    ("ratios", "Unit rates and proportional relationships", "expression"): (SeedPattern("If one notebook costs {rate} dollars, how much do {count} notebooks cost?", "rate * count", "", "Multiply the unit rate by the number of groups.", ({"name": "rate", "kind": "int", "min": 2, "max": 12, "step": 1}, {"name": "count", "kind": "int", "min": 2, "max": 12, "step": 1}), 20.0),),
    ("pre_algebra", "Integer and fraction fluency", "expression"): (
        SeedPattern("Evaluate: {a} + ({b})", "a + b", "", "Signed arithmetic keeps track of direction and magnitude.", ({"name": "a", "kind": "int", "min": -20, "max": 20, "step": 1}, {"name": "b", "kind": "int", "min": -20, "max": 20, "step": 1}), 8.0),
        SeedPattern("Convert {n}/{d} to a decimal.", "n / d", "n < d", "A fraction becomes a decimal by division.", ({"name": "n", "kind": "int", "min": 1, "max": 9, "step": 1}, {"name": "d", "kind": "int", "min": 2, "max": 10, "step": 1}), 1.5),
    ),
    ("pre_algebra", "Order of operations", "expression"): (
        SeedPattern("Evaluate ({a} + {b}) x {c}.", "(a + b) * c", "", "Parentheses group work that must happen before multiplication.", ({"name": "a", "kind": "int", "min": 2, "max": 15, "step": 1}, {"name": "b", "kind": "int", "min": 2, "max": 15, "step": 1}, {"name": "c", "kind": "int", "min": 2, "max": 8, "step": 1}), 18.0),
        SeedPattern("Evaluate {a} + {b} x {c}.", "a + b * c", "", "Multiplication happens before addition when there are no parentheses.", ({"name": "a", "kind": "int", "min": 2, "max": 20, "step": 1}, {"name": "b", "kind": "int", "min": 2, "max": 10, "step": 1}, {"name": "c", "kind": "int", "min": 2, "max": 8, "step": 1}), 18.0),
    ),
    ("pre_algebra", "Expressions and variables", "expression"): (
        SeedPattern("Evaluate {a}x + ({b}) when x = {x}.", "a * x + b", "a != 0", "Substitute the value for x, then simplify.", ({"name": "a", "kind": "int", "min": -6, "max": 6, "step": 1}, {"name": "b", "kind": "int", "min": -12, "max": 12, "step": 1}, {"name": "x", "kind": "int", "min": -6, "max": 8, "step": 1}), 10.0),
        SeedPattern("Evaluate ({a}x) + ({b}x) + {c} when x = {x}.", "(a + b) * x + c", "a != 0 and b != 0", "Combine like terms before substituting.", ({"name": "a", "kind": "int", "min": -5, "max": 5, "step": 1}, {"name": "b", "kind": "int", "min": -5, "max": 5, "step": 1}, {"name": "c", "kind": "int", "min": -9, "max": 9, "step": 1}, {"name": "x", "kind": "int", "min": -6, "max": 8, "step": 1}), 10.0),
    ),
    ("pre_algebra", "One-step equations", "expression"): (
        SeedPattern("Solve for x: x + {offset} = {rhs}", "rhs - offset", "", "Undo the addition or subtraction trapping the variable.", ({"name": "offset", "kind": "int", "min": -12, "max": 12, "step": 1}, {"name": "rhs", "kind": "int", "min": -18, "max": 28, "step": 1}), 10.0),
        SeedPattern("Solve for x: {coeff}x = {rhs}", "rhs / coeff", "coeff != 0 and rhs % coeff == 0", "Divide both sides by the coefficient.", ({"name": "coeff", "kind": "int", "min": 2, "max": 9, "step": 1}, {"name": "rhs", "kind": "int", "min": 4, "max": 81, "step": 1}), 10.0),
    ),
    ("pre_algebra", "Two-step equations and inequalities", "expression"): (
        SeedPattern("Solve for x: {coeff}x + {bias} = {rhs}", "(rhs - bias) / coeff", "coeff != 0 and (rhs - bias) % coeff == 0", "Undo the constant first, then divide.", ({"name": "coeff", "kind": "int", "min": 2, "max": 8, "step": 1}, {"name": "bias", "kind": "int", "min": -12, "max": 12, "step": 1}, {"name": "rhs", "kind": "int", "min": -20, "max": 40, "step": 1}), 10.0),
    ),
    ("pre_algebra", "Ratios, rates, and proportional relationships", "expression"): (
        SeedPattern("Complete the proportion: {a}/{b} = x/{scaled_b}. What is x?", "a * scale", "scaled_b == b * scale", "Equivalent ratios scale together.", ({"name": "a", "kind": "int", "min": 1, "max": 8, "step": 1}, {"name": "b", "kind": "int", "min": 2, "max": 12, "step": 1}, {"name": "scale", "kind": "int", "min": 2, "max": 6, "step": 1}, {"name": "scaled_b", "kind": "int", "min": 4, "max": 72, "step": 1}), 10.0),
        SeedPattern("At {rate} dollars per notebook, what is the total cost for {count} notebooks?", "rate * count", "", "Multiply the unit rate by the number of notebooks.", ({"name": "rate", "kind": "int", "min": 2, "max": 15, "step": 1}, {"name": "count", "kind": "int", "min": 2, "max": 12, "step": 1}), 18.0),
    ),
    ("pre_algebra", "Ratios, rates, and proportional relationships", "word"): (
        SeedPattern("A recipe uses {a} cups of water for every {b} scoops of mix. If it is doubled, how many scoops of mix are needed?", "b * 2", "", "Keep both parts of the ratio in the same scale.", ({"name": "a", "kind": "int", "min": 1, "max": 6, "step": 1}, {"name": "b", "kind": "int", "min": 1, "max": 6, "step": 1}), 8.0),
        SeedPattern("{notebooks} notebooks cost ${cost}. What is the cost of {double_count} notebooks if the price stays proportional?", "(cost / notebooks) * double_count", "cost % notebooks == 0 and double_count > notebooks", "A proportional relationship keeps the same unit rate.", ({"name": "notebooks", "kind": "int", "min": 2, "max": 6, "step": 1}, {"name": "cost", "kind": "int", "min": 6, "max": 30, "step": 1}, {"name": "double_count", "kind": "int", "min": 4, "max": 12, "step": 1}), 12.0),
    ),
    ("pre_algebra", "Percent problems", "expression"): (
        SeedPattern("What is {pct}% of {whole}?", "(pct / 100) * whole", "", "Convert the percent to a decimal, then multiply.", ({"name": "pct", "kind": "int", "min": 5, "max": 75, "step": 5}, {"name": "whole", "kind": "int", "min": 20, "max": 240, "step": 5}), 18.0),
        SeedPattern("{part} is what percent of {whole}? Enter the percent number.", "(part / whole) * 100", "part < whole", "Divide the part by the whole, then convert to a percent.", ({"name": "part", "kind": "int", "min": 5, "max": 90, "step": 5}, {"name": "whole", "kind": "int", "min": 20, "max": 120, "step": 5}), 18.0),
    ),
    ("pre_algebra", "Percent problems", "word"): (
        SeedPattern("A store marks a ${price} item down by 20%. How many dollars is the discount?", "price * 0.2", "", "Twenty percent is two tenths of the original price.", ({"name": "price", "kind": "int", "min": 20, "max": 200, "step": 5},), 12.0),
        SeedPattern("A class of {whole} students has {part} students in the choir. What percent of the class is in the choir?", "(part / whole) * 100", "part < whole", "Percent means part out of one hundred.", ({"name": "whole", "kind": "int", "min": 20, "max": 40, "step": 1}, {"name": "part", "kind": "int", "min": 5, "max": 20, "step": 1}), 18.0),
    ),
    ("pre_algebra", "Exponents, roots, and scientific notation", "expression"): (
        SeedPattern("Evaluate: {base}^{exp}", "base ** exp", "", "An exponent means repeated multiplication.", ({"name": "base", "kind": "int", "min": 2, "max": 9, "step": 1}, {"name": "exp", "kind": "int", "min": 2, "max": 4, "step": 1}), 40.0),
        SeedPattern("Evaluate sqrt({square}).", "square ** 0.5", "", "A square root asks for the number that squares to the original.", ({"name": "square", "kind": "int", "min": 4, "max": 81, "step": 1},), 8.0),
        SeedPattern("In scientific notation, {coeff} x 10^{exp} uses what exponent on 10?", "exp", "", "Scientific notation writes numbers using a coefficient and a power of ten.", ({"name": "coeff", "kind": "float", "min": 1.2, "max": 9.9, "step": 0.1}, {"name": "exp", "kind": "int", "min": -5, "max": 7, "step": 1}), 4.0),
    ),
    ("pre_algebra", "Coordinate plane and function tables", "expression"): (
        SeedPattern("For y = {m}x + {b}, what is y when x = {x}?", "m * x + b", "", "Use the rule to map x to y.", ({"name": "m", "kind": "int", "min": -5, "max": 5, "step": 1}, {"name": "b", "kind": "int", "min": -8, "max": 8, "step": 1}, {"name": "x", "kind": "int", "min": -4, "max": 6, "step": 1}), 12.0),
        SeedPattern("Point P is at ({x}, {y}). How far is P from the y-axis?", "abs(x)", "", "Distance from the y-axis is the absolute value of x.", ({"name": "x", "kind": "int", "min": -8, "max": 8, "step": 1}, {"name": "y", "kind": "int", "min": -8, "max": 8, "step": 1}), 8.0),
    ),
    ("pre_algebra", "Coordinate plane and function tables", "word"): (
        SeedPattern("A taxi charges ${m} per mile plus a ${b} starting fee. What is the cost of a {x}-mile ride?", "m * x + b", "", "This story follows the same function rule every time.", ({"name": "m", "kind": "int", "min": 2, "max": 6, "step": 1}, {"name": "b", "kind": "int", "min": 1, "max": 8, "step": 1}, {"name": "x", "kind": "int", "min": 2, "max": 12, "step": 1}), 12.0),
        SeedPattern("A game rule says score = {m} x level + {b}. What score does a player get at level {x}?", "m * x + b", "", "Follow the rule like a function table.", ({"name": "m", "kind": "int", "min": 2, "max": 6, "step": 1}, {"name": "b", "kind": "int", "min": 0, "max": 10, "step": 1}, {"name": "x", "kind": "int", "min": 1, "max": 10, "step": 1}), 12.0),
    ),
}
SEED_PATTERNS.update(PREVIEW_SEED_PATTERNS)


def ensure_summer_program_templates(conn: sqlite3.Connection) -> None:
    for (skill, subskill), target in EXPRESSION_TARGETS.items():
        _ensure_mode_target(conn, skill, subskill, "expression", target)
    for (skill, subskill), target in WORD_TARGETS.items():
        _ensure_mode_target(conn, skill, subskill, "word", target)


def _ensure_mode_target(conn: sqlite3.Connection, skill: str, subskill: str, mode: str, target: int) -> None:
    patterns = SEED_PATTERNS.get((skill, subskill, mode), ())
    if not patterns:
        return
    current = _count_templates(conn, skill, subskill, mode)
    missing = max(0, int(target) - current)
    for idx in range(missing):
        pattern = patterns[idx % len(patterns)]
        external_id = f"summer.depth.{_slug(skill)}.{_slug(subskill)}.{mode}.{current + idx + 1}"
        _insert_template(conn, external_id, skill, subskill, mode, idx + 1, pattern)


def _count_templates(conn: sqlite3.Connection, skill: str, subskill: str, mode: str) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM question_templates
        WHERE active = 1 AND skill = ? AND subskill = ? AND mode = ?
        """,
        (skill, subskill, mode),
    ).fetchone()
    assert row is not None
    return int(row[0])


def _insert_template(
    conn: sqlite3.Connection,
    external_id: str,
    skill: str,
    subskill: str,
    mode: str,
    variant_index: int,
    pattern: SeedPattern,
) -> None:
    exists = conn.execute(
        "SELECT 1 FROM question_templates WHERE external_id = ?",
        (external_id,),
    ).fetchone()
    if exists is not None:
        return
    created_at = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        """
        INSERT INTO question_templates
        (book_id, external_id, skill, subskill, label, mode, prompt_template, answer_expr, constraint_expr,
         explanation_template, min_level, max_level, choice_spread, active, created_at)
        VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 3, ?, 1, ?)
        """,
        (
            external_id,
            skill,
            subskill,
            f"Summer depth {variant_index}",
            mode,
            pattern.prompt_template,
            pattern.answer_expr,
            pattern.constraint_expr,
            pattern.explanation_template,
            float(pattern.choice_spread),
            created_at,
        ),
    )
    template_id = int(cur.lastrowid)
    for var in pattern.vars:
        conn.execute(
            """
            INSERT INTO template_vars (template_id, name, kind, min_value, max_value, step)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                template_id,
                str(var["name"]),
                str(var["kind"]),
                float(var["min"]),
                float(var["max"]),
                float(var["step"]),
            ),
        )


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
