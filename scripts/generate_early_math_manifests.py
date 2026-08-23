from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.early_math_catalog import early_math_specs  # noqa: E402


OUT_DIR = ROOT / "scripts" / "template_manifests"


def v(name: str, lo: int, hi: int, step: int = 1, kind: str = "int") -> dict[str, object]:
    return {"name": name, "min": lo, "max": hi, "step": step, "kind": kind}


def t(
    external_id: str,
    skill: str,
    subskill: str,
    label: str,
    prompt_template: str,
    answer_expr: str,
    explanation_template: str,
    *,
    mode: str = "expression",
    vars: list[dict[str, object]] | None = None,
    constraint_expr: str = "",
    min_level: int = 1,
    max_level: int = 3,
    choice_spread: float = 6.0,
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
        "vars": vars or [],
    }


def _counting_and_place_value() -> list[dict[str, object]]:
    return [
        t("khan.early_math.counting.number_recognition.v1", "counting", "Number recognition", "Write numeral", "Write the numeral for {n}.", "n", "The numeral matches the size of the set.", vars=[v("n", 0, 30)]),
        t("khan.early_math.counting.number_recognition.v2", "counting", "Number recognition", "Next number", "What number comes after {n}?", "n + 1", "Counting forward by 1 gives the next numeral.", vars=[v("n", 0, 49)]),
        t("khan.early_math.counting.skip_counting.v1", "counting", "Skip-counting", "Continue skip-count", "Starting at {start}, skip-count by {step} for three jumps. What number do you reach?", "start + step + step + step", "Skip-counting adds the same jump size each time.", vars=[v("step", 2, 10), v("start", 0, 40)], constraint_expr="step != 3 and step != 4 and step != 6 and step != 7 and step != 8 and step != 9"),
        t("khan.early_math.counting.skip_counting.v2", "counting", "Skip-counting", "Nth skip-count term", "Starting at {start}, what is the 4th number when you skip-count by {step}?", "start + step + step + step", "The 4th term is three equal jumps after the start.", vars=[v("step", 2, 10), v("start", 0, 30)], constraint_expr="step != 3 and step != 4 and step != 6 and step != 7 and step != 8 and step != 9"),
        t("khan.early_math.counting.count_match.v1", "counting", "Count-to-number matching", "Match final count", "A student finishes counting a set and says {n}. How many objects were counted?", "n", "The last count word names the total in the set.", vars=[v("n", 1, 40)]),
        t("khan.early_math.counting.count_match.v2", "counting", "Count-to-number matching", "Numeral match", "A bin holds {n} counters. Which numeral matches the total?", "n", "Match the quantity to the numeral that names it.", vars=[v("n", 1, 40)]),
        t("khan.early_math.place_value.place_digit.v1", "place_value", "Ones, tens, and hundreds identification", "Digit in place", "What digit is in the tens place of {h}{te}{o}?", "te", "The tens place is the second digit from the right.", vars=[v("h", 1, 9), v("te", 0, 9), v("o", 0, 9)]),
        t("khan.early_math.place_value.place_digit.v2", "place_value", "Ones, tens, and hundreds identification", "Value of digit", "What value does the hundreds digit represent in {h}{te}{o}?", "h * 100", "The hundreds digit counts hundreds, not ones.", vars=[v("h", 1, 9), v("te", 0, 9), v("o", 0, 9)], choice_spread=80.0),
        t("khan.early_math.place_value.expanded_form.v1", "place_value", "Expanded form", "Build number", "What number is represented by {h} hundreds, {te} tens, and {o} ones?", "h * 100 + te * 10 + o", "Add each place-value part back into one number.", vars=[v("h", 1, 9), v("te", 0, 9), v("o", 0, 9)], choice_spread=80.0),
        t("khan.early_math.place_value.expanded_form.v2", "place_value", "Expanded form", "Missing expanded part", "In {h}{te}{o}, what is the value of the tens part?", "te * 10", "The tens part is the tens digit times 10.", vars=[v("h", 1, 9), v("te", 1, 9), v("o", 0, 9)], choice_spread=20.0),
        t("khan.early_math.place_value.compare.v1", "place_value", "Compare numbers by place value", "Larger number", "Which number is larger: {a} or {b}?", "a", "Compare from the highest place where the numbers differ.", vars=[v("a", 200, 999), v("b", 100, 998)], constraint_expr="a > b", choice_spread=80.0),
        t("khan.early_math.place_value.compare.v2", "place_value", "Compare numbers by place value", "Smaller number", "Which number is smaller: {a} or {b}?", "a", "The smaller number has the smaller first different place value.", vars=[v("a", 100, 900), v("b", 101, 999)], constraint_expr="a < b", choice_spread=80.0),
        t("khan.early_math.place_value.decimals.v1", "place_value", "Decimal place value and comparison", "Tenths digit", "What digit is in the tenths place of {w}.{te}{hu}?", "te", "The tenths place is the first place to the right of the decimal point.", vars=[v("w", 0, 9), v("te", 0, 9), v("hu", 0, 9)]),
        t("khan.early_math.place_value.decimals.v2", "place_value", "Decimal place value and comparison", "Decimal to hundredths", "Write {w}.{te}{hu} as a number of hundredths.", "w * 100 + te * 10 + hu", "One whole is 100 hundredths, each tenth is 10 hundredths, and each hundredth is 1 hundredth.", vars=[v("w", 0, 4), v("te", 0, 9), v("hu", 0, 9)], choice_spread=30.0),
    ]


def _operations_and_long() -> list[dict[str, object]]:
    items = [
        t("khan.early_math.add.single.v1", "add_subtract", "Single-digit addition", "Single-digit sum", "{a} + {b} = ?", "a + b", "Single-digit addition combines two small groups.", vars=[v("a", 1, 9), v("b", 1, 9)]),
        t("khan.early_math.add.single.v2", "add_subtract", "Single-digit addition", "Addition count on", "What is {a} + {b}?", "a + b", "Count on from the first addend by the second addend.", vars=[v("a", 1, 9), v("b", 1, 9)]),
        t("khan.early_math.sub.single.v1", "add_subtract", "Single-digit subtraction", "Single-digit difference", "{a} - {b} = ?", "a - b", "Subtraction removes part of a group.", vars=[v("a", 2, 9), v("b", 1, 8)], constraint_expr="a > b"),
        t("khan.early_math.sub.single.v2", "add_subtract", "Single-digit subtraction", "Count back", "If you count back {b} from {a}, where do you land?", "a - b", "Counting back models subtraction on a number line.", vars=[v("a", 2, 9), v("b", 1, 8)], constraint_expr="a > b"),
        t("khan.early_math.add.carry.v1", "add_subtract", "Borrowing and carrying basics", "Carry in addition", "{a} + {b} = ?", "a + b", "When a column reaches 10, regroup 10 ones as 1 ten.", vars=[v("a", 15, 89), v("b", 15, 89)], constraint_expr="(a % 10) + (b % 10) >= 10", choice_spread=20.0),
        t("khan.early_math.sub.borrow.v2", "add_subtract", "Borrowing and carrying basics", "Borrow in subtraction", "{a} - {b} = ?", "a - b", "Borrowing trades 1 ten for 10 ones so the subtraction can happen.", vars=[v("a", 31, 98), v("b", 12, 89)], constraint_expr="a > b and (a % 10) < (b % 10)", choice_spread=20.0),
        t("khan.early_math.add.word.v1", "add_subtract", "Word problems", "Join story", "A shelf had {a} books. {b} more were added. How many books are there now?", "a + b", "This story joins two amounts into one total.", mode="word", vars=[v("a", 5, 45), v("b", 3, 30)], choice_spread=18.0),
        t("khan.early_math.add.word.v2", "add_subtract", "Word problems", "Difference story", "A class had {a} pencils and used {b}. How many pencils are left?", "a - b", "This story removes part of the starting amount.", vars=[v("a", 15, 60), v("b", 4, 25)], constraint_expr="a > b", choice_spread=18.0),
        t("khan.early_math.add.word.v3", "add_subtract", "Word problems", "Total with difference", "There were {a} apples in one basket and {b} in another. How many apples altogether?", "a + b", "Add the two basket counts to get the total.", vars=[v("a", 8, 40), v("b", 7, 35)], choice_spread=18.0),
        t("khan.early_math.add.missing.v1", "add_subtract", "Missing addends", "Missing addend", "{a} + x = {total}. What is x?", "total - a", "Find the missing part by subtracting the known addend from the total.", vars=[v("a", 3, 30), v("total", 8, 50)], constraint_expr="total > a", choice_spread=14.0),
        t("khan.early_math.add.missing.v2", "add_subtract", "Missing addends", "Missing addend with total", "What number must be added to {a} to make {total}?", "total - a", "A missing addend is the amount needed to reach the target total.", vars=[v("a", 4, 35), v("total", 9, 60)], constraint_expr="total > a", choice_spread=14.0),
        t("khan.early_math.add.regroup.v1", "add_subtract", "Multi-digit regrouping", "Regrouping sum", "{a} + {b} = ?", "a + b", "Regroup tens or hundreds when a column reaches 10 or more.", vars=[v("a", 125, 689), v("b", 125, 489)], constraint_expr="((a % 10) + (b % 10) >= 10) or (((a // 10) % 10) + ((b // 10) % 10) >= 10)", choice_spread=60.0),
        t("khan.early_math.add.regroup.v2", "add_subtract", "Multi-digit regrouping", "Regrouping difference", "{a} - {b} = ?", "a - b", "Regroup from the next place when the current place is too small to subtract.", vars=[v("a", 350, 980), v("b", 111, 689)], constraint_expr="a > b and (((a % 10) < (b % 10)) or (((a // 10) % 10) < ((b // 10) % 10)))", choice_spread=60.0),
        t("ray.early_math.add.regroup.word.v1", "add_subtract", "Multi-digit regrouping", "Regrouping word problem", "A library had {a} pages copied on Monday and {b} on Tuesday. How many pages were copied in all?", "a + b", "Add the two multi-digit amounts and regroup where needed.", mode="word", vars=[v("a", 125, 689), v("b", 125, 489)], constraint_expr="((a % 10) + (b % 10) >= 10) or (((a // 10) % 10) + ((b // 10) % 10) >= 10)", choice_spread=60.0),
        t("khan.early_math.multiply.repeated.v1", "multiply", "Repeated addition", "Repeated sum", "What is {groups} groups of {size}?", "groups * size", "Repeated addition can be compressed into multiplication.", vars=[v("groups", 2, 9), v("size", 2, 9)]),
        t("khan.early_math.multiply.repeated.v2", "multiply", "Repeated addition", "Add equal groups", "Add {size} + {size} + {size} + {size}. What is the total?", "size * 4", "Four equal addends make 4 groups of the same size.", vars=[v("size", 2, 9)]),
        t("khan.early_math.multiply.tables.v1", "multiply", "Times tables", "Fact fluency", "{a} x {b} = ?", "a * b", "A multiplication fact gives the total for equal groups.", vars=[v("a", 2, 12), v("b", 2, 12)]),
        t("khan.early_math.multiply.tables.v2", "multiply", "Times tables", "Missing factor", "{a} x x = {product}. What is x?", "product / a", "Use the fact family in reverse to find the missing factor.", vars=[v("a", 2, 12), v("product", 12, 120)], constraint_expr="product % a == 0 and product / a >= 2 and product / a <= 12", choice_spread=5.0),
        t("khan.early_math.multiply.array.v1", "multiply", "Array and grid models", "Rows and columns", "An array has {rows} rows and {cols} columns. How many objects are in the array?", "rows * cols", "Rows times columns gives the total in the array.", vars=[v("rows", 2, 10), v("cols", 2, 10)]),
        t("khan.early_math.multiply.array.v2", "multiply", "Array and grid models", "Rectangle grid", "A grid has {rows} rows of {cols} squares. How many squares are there?", "rows * cols", "Each row has the same number of squares, so multiply rows by columns.", vars=[v("rows", 2, 10), v("cols", 2, 10)]),
        t("khan.early_math.multiply.facts.v1", "multiply", "Simple product facts", "Product fact", "What is {a} x {b}?", "a * b", "The product is the total after grouping equally.", vars=[v("a", 2, 12), v("b", 2, 12)]),
        t("khan.early_math.multiply.facts.v2", "multiply", "Simple product facts", "Complete fact family", "What number times {b} equals {product}?", "product / b", "Division checks the multiplication fact.", vars=[v("b", 2, 12), v("product", 12, 120)], constraint_expr="product % b == 0 and product / b >= 2 and product / b <= 12"),
        t("khan.early_math.multiply.compare.v1", "multiply", "Multiplicative comparison and estimation", "Times as many", "A box holds {base} marbles. Another box has {times} times as many. How many marbles are in the second box?", "base * times", "Times as many means multiply the original amount by the scale factor.", vars=[v("base", 2, 15), v("times", 2, 9)], choice_spread=20.0),
        t("khan.early_math.multiply.compare.v2", "multiply", "Multiplicative comparison and estimation", "Round then estimate", "Estimate {tens} x {ones} by using {rounded} x {ones}. What estimate do you get?", "rounded * ones", "Round first, then multiply the easier numbers.", vars=[v("tens", 21, 89), v("rounded", 20, 90, 10), v("ones", 2, 9)], constraint_expr="(tens - rounded <= 4 and tens - rounded >= 0) or (rounded - tens <= 5 and rounded - tens >= 0)", choice_spread=20.0),
        t("ray.early_math.multiply.compare.word.v1", "multiply", "Multiplicative comparison and estimation", "Comparison story", "One crate has {base} jars. A truck carries {times} times as many jars as one crate. How many jars does the truck carry?", "base * times", "Multiply the single-crate amount by the comparison factor.", mode="word", vars=[v("base", 3, 18), v("times", 2, 6)], choice_spread=20.0),
        t("khan.early_math.divide.share.v1", "divide", "Equal sharing", "Fair share", "{total} objects are shared equally among {groups} groups. How many are in each group?", "total / groups", "Equal sharing means divide the total by the number of groups.", vars=[v("total", 12, 96), v("groups", 2, 12)], constraint_expr="total % groups == 0", choice_spread=8.0),
        t("khan.early_math.divide.share.v2", "divide", "Equal sharing", "Per group count", "If {total} stickers are split evenly into {groups} piles, how many stickers are in each pile?", "total / groups", "Division finds the amount in each equal pile.", vars=[v("total", 18, 108), v("groups", 2, 12)], constraint_expr="total % groups == 0", choice_spread=8.0),
        t("khan.early_math.divide.repeat.v1", "divide", "Division as repeated subtraction", "Subtract equal groups", "How many times can you subtract {group} from {total} before reaching 0?", "total / group", "Each subtraction removes one full group.", vars=[v("total", 12, 96), v("group", 2, 12)], constraint_expr="total % group == 0", choice_spread=8.0),
        t("khan.early_math.divide.repeat.v2", "divide", "Division as repeated subtraction", "Repeated subtraction count", "If you keep taking away {group} from {total}, how many full subtractions happen?", "total / group", "The number of subtractions matches the quotient.", vars=[v("total", 15, 90), v("group", 2, 10)], constraint_expr="total % group == 0", choice_spread=8.0),
        t("khan.early_math.divide.remainder.v1", "divide", "Remainders", "Find remainder", "What is the remainder when {total} is divided by {group}?", "total % group", "The remainder is what is left after the largest possible equal groups.", vars=[v("total", 13, 99), v("group", 2, 12)], constraint_expr="total % group != 0", choice_spread=4.0),
        t("khan.early_math.divide.remainder.v2", "divide", "Remainders", "Find whole groups", "How many full groups of {group} can you make from {total}?", "total // group", "The quotient counts only the complete groups.", vars=[v("total", 13, 99), v("group", 2, 12)], constraint_expr="total % group != 0", choice_spread=6.0),
        t("ray.early_math.divide.remainder.word.v1", "divide", "Remainders", "Leftover story", "{total} stickers are shared equally among {group} students. How many stickers are left over?", "total % group", "The leftover stickers are the remainder after making equal groups.", mode="word", vars=[v("total", 13, 99), v("group", 2, 12)], constraint_expr="total % group != 0", choice_spread=4.0),
        t("khan.early_math.divide.inverse.v1", "divide", "Inverse thinking", "Missing factor from quotient", "{group} x ? = {total}. What is the missing number?", "total / group", "Use multiplication and division as inverse operations.", vars=[v("total", 12, 108), v("group", 2, 12)], constraint_expr="total % group == 0", choice_spread=8.0),
        t("khan.early_math.divide.inverse.v2", "divide", "Inverse thinking", "Division check", "If {total} / {group} = x, what is x?", "total / group", "Division undoes multiplication by the same factor.", vars=[v("total", 12, 108), v("group", 2, 12)], constraint_expr="total % group == 0", choice_spread=8.0),
        t("khan.early_math.divide.interpret.v1", "divide", "Remainder interpretation and estimation", "Estimate quotient", "About how many groups of {group} fit in {estimate_total} if you use {rounded_total} instead?", "rounded_total / group", "Estimate division with a nearby friendly multiple.", vars=[v("estimate_total", 35, 95), v("rounded_total", 30, 100, 10), v("group", 2, 10)], constraint_expr="rounded_total % group == 0 and ((estimate_total - rounded_total <= 5 and estimate_total - rounded_total >= 0) or (rounded_total - estimate_total <= 5 and rounded_total - estimate_total >= 0))", choice_spread=6.0),
        t("khan.early_math.divide.interpret.v2", "divide", "Remainder interpretation and estimation", "Estimate with friendly total", "Use {rounded_total} / {group} to estimate {estimate_total} / {group}. What estimate do you get?", "rounded_total / group", "A nearby multiple of the divisor gives a quick estimate for the quotient.", vars=[v("estimate_total", 35, 95), v("rounded_total", 30, 100, 10), v("group", 2, 10)], constraint_expr="rounded_total % group == 0 and ((estimate_total - rounded_total <= 5 and estimate_total - rounded_total >= 0) or (rounded_total - estimate_total <= 5 and rounded_total - estimate_total >= 0))", choice_spread=6.0),
        t("ray.early_math.divide.interpret.word.v1", "divide", "Remainder interpretation and estimation", "Remainder story", "{total} apples are packed into bags of {group}. How many full bags can be made?", "total // group", "The number of full bags is the whole-number quotient.", mode="word", vars=[v("total", 13, 99), v("group", 2, 12)], constraint_expr="total % group != 0", choice_spread=6.0),
    ]
    for skill, subskill, prefix, prompt, answer, explanation, var_specs, constraint, spread in [
        ("long_addition", "Column alignment", "long_add", "Line up the digits and add: {a} + {b}", "a + b", "Aligned columns keep ones with ones and tens with tens.", [v("a", 123, 789), v("b", 111, 689)], "", 60.0),
        ("long_addition", "Carry handling", "long_add_carry", "Add and show the carried value: {a} + {b}", "a + b", "A carry appears when a column totals 10 or more.", [v("a", 145, 789), v("b", 155, 689)], "((a % 10) + (b % 10) >= 10)", 60.0),
        ("long_addition", "Multi-digit accuracy", "long_add_accuracy", "Find the sum: {a} + {b}", "a + b", "Work one place-value column at a time.", [v("a", 234, 899), v("b", 101, 799)], "", 60.0),
        ("long_addition", "Place-value structure", "long_add_place", "What is {a} + {b}?", "a + b", "Think of the addends as hundreds, tens, and ones being combined.", [v("a", 305, 860), v("b", 120, 690)], "", 60.0),
        ("long_subtraction", "Borrowing", "long_sub_borrow", "Subtract with regrouping: {a} - {b}", "a - b", "Borrowing trades one larger unit for 10 smaller units.", [v("a", 301, 950), v("b", 112, 789)], "a > b and (a % 10) < (b % 10)", 60.0),
        ("long_subtraction", "Column alignment", "long_sub_align", "Find the difference: {a} - {b}", "a - b", "Keep each place in the correct column before subtracting.", [v("a", 350, 980), v("b", 101, 649)], "a > b", 60.0),
        ("long_subtraction", "Crossing zero safely", "long_sub_zero", "Subtract carefully: {a} - {b}", "a - b", "Zeros can still lend value after regrouping from the left.", [v("a", 400, 900), v("b", 101, 389)], "a > b and a % 10 == 0", 60.0),
        ("long_multiplication", "Partial products", "long_mul_partial", "Find the product: {a} x {b}", "a * b", "Each row is a partial product from one place-value part.", [v("a", 12, 99), v("b", 12, 39)], "", 120.0),
        ("long_multiplication", "Place-value breakdown", "long_mul_place", "Multiply {a} by {b}.", "a * b", "Split the factors into tens and ones mentally as you multiply.", [v("a", 14, 98), v("b", 11, 29)], "", 120.0),
        ("long_multiplication", "Two-digit multiplies", "long_mul_two_digit", "What is {a} x {b}?", "a * b", "Estimate first, then combine the partial products.", [v("a", 15, 96), v("b", 12, 48)], "", 120.0),
        ("long_division", "Division layout", "long_div_layout", "Compute {dividend} / {divisor}. Use the whole-number quotient only.", "dividend // divisor", "Place the quotient above the matching place-value column.", [v("dividend", 120, 980), v("divisor", 2, 12)], "dividend % divisor == 0", 8.0),
        ("long_division", "Quotient estimation", "long_div_estimate", "About how many times does {divisor} fit into {dividend}?", "dividend // divisor", "Estimate the quotient digit before subtracting.", [v("dividend", 120, 980), v("divisor", 2, 12)], "dividend % divisor == 0", 8.0),
        ("long_division", "Remainder handling", "long_div_remainder", "What remainder is left when {dividend} is divided by {divisor}?", "dividend % divisor", "The remainder must be smaller than the divisor.", [v("dividend", 121, 999), v("divisor", 2, 12)], "dividend % divisor != 0", 4.0),
    ]:
        items.append(t(f"khan.early_math.{prefix}.v1", skill, subskill, label=label_case(subskill), prompt_template=prompt, answer_expr=answer, explanation_template=explanation, vars=var_specs, constraint_expr=constraint, choice_spread=spread))
        items.append(t(f"khan.early_math.{prefix}.v2", skill, subskill, label=f"{label_case(subskill)} variation", prompt_template=prompt.replace("Find", "Work out").replace("Compute", "Find").replace("What is", "Calculate"), answer_expr=answer, explanation_template=explanation, vars=var_specs, constraint_expr=constraint, choice_spread=spread))
    return items


def _fractions_and_ratios() -> list[dict[str, object]]:
    return [
        t("khan.early_math.ratio.language.v1", "ratios", "Ratio language (to:of)", "Scale ratio", "For every {a} red beads there are {b} blue beads. If the pattern is repeated {scale} times, how many blue beads are there?", "b * scale", "Equivalent ratio groups scale both parts by the same factor.", vars=[v("a", 1, 8), v("b", 1, 9), v("scale", 2, 6)], choice_spread=10.0),
        t("khan.early_math.ratio.language.v2", "ratios", "Ratio language (to:of)", "Total from ratio", "One batch uses a ratio of {a}:{b}. How many total parts are in {scale} batches?", "(a + b) * scale", "Add the two parts of one batch, then scale the batch count.", vars=[v("a", 1, 8), v("b", 1, 9), v("scale", 2, 6)], choice_spread=10.0),
        t("ray.early_math.ratio.language.word.v1", "ratios", "Ratio language (to:of)", "Recipe story", "A recipe uses {a} cups of juice for every {b} cups of water. If the recipe is made {scale} times, how many cups of water are needed?", "b * scale", "Keep the two parts of the ratio in the same order and scale both together.", mode="word", vars=[v("a", 1, 6), v("b", 1, 8), v("scale", 2, 5)], choice_spread=8.0),
        t("khan.early_math.ratio.equivalent.v1", "ratios", "Equivalent ratios", "Missing term", "Scale the ratio {a}:{b} by {scale}. What is the new first number?", "a * scale", "Equivalent ratios multiply both parts by the same factor.", vars=[v("a", 1, 9), v("b", 2, 12), v("scale", 2, 6)], choice_spread=8.0),
        t("khan.early_math.ratio.equivalent.v2", "ratios", "Equivalent ratios", "Missing denominator", "Scale the ratio {a}:{b} by {scale}. What is the new second number?", "b * scale", "Scale the denominator by the same factor as the numerator.", vars=[v("a", 1, 9), v("b", 2, 12), v("scale", 2, 6)], choice_spread=8.0),
        t("ray.early_math.ratio.equivalent.word.v1", "ratios", "Equivalent ratios", "Group scaling story", "A map uses a scale of {a} inches to {b} miles. If the scale factor is repeated {scale} times, how many miles match the new map length?", "b * scale", "Equivalent ratios keep the same comparison after scaling.", mode="word", vars=[v("a", 1, 5), v("b", 2, 12), v("scale", 2, 5)], choice_spread=8.0),
        t("khan.early_math.ratio.fractional.v1", "ratios", "Fractional comparison", "Part of whole denominator", "If a class ratio is {a}:{b}, how many total parts are in the whole ratio?", "a + b", "A part-to-whole fraction uses the total parts in the denominator.", vars=[v("a", 1, 8), v("b", 1, 9)], choice_spread=6.0),
        t("khan.early_math.ratio.fractional.v2", "ratios", "Fractional comparison", "Part count from ratio", "In a ratio of {a}:{b}, how many parts belong to the second quantity?", "b", "The second number in the ratio names the second quantity's share.", vars=[v("a", 1, 8), v("b", 1, 9)], choice_spread=5.0),
        t("khan.early_math.ratio.unit_rate.v1", "ratios", "Unit rates and proportional relationships", "Find unit rate", "{total} miles are driven in {hours} hours. How many miles per hour is that?", "total / hours", "A unit rate tells the amount for 1 unit of the second quantity.", vars=[v("total", 12, 120), v("hours", 2, 12)], constraint_expr="total % hours == 0", choice_spread=8.0),
        t("khan.early_math.ratio.unit_rate.v2", "ratios", "Unit rates and proportional relationships", "Scale proportional pair", "If {a} notebooks cost ${b}, how much do {scale} equal groups of {a} notebooks cost?", "b * scale", "A proportional relationship scales both quantities by the same factor.", vars=[v("a", 1, 8), v("b", 2, 16), v("scale", 2, 6)], choice_spread=10.0),
        t("openstax.early_math.ratio.unit_rate.word.v1", "ratios", "Unit rates and proportional relationships", "Rate story", "A bike travels {total} miles in {hours} hours. At the same rate, how many miles does it travel in 1 hour?", "total / hours", "Find the per-1 amount before scaling to any other value.", mode="word", vars=[v("total", 18, 144), v("hours", 2, 12)], constraint_expr="total % hours == 0", choice_spread=8.0),
        t("khan.early_math.fraction.unit.v1", "fractions", "Unit fractions", "Denominator from slices", "A whole is split into {d} equal parts. One part is what unit fraction denominator?", "d", "A unit fraction uses 1 piece out of d equal pieces.", vars=[v("d", 2, 12)], choice_spread=4.0),
        t("khan.early_math.fraction.unit.v2", "fractions", "Unit fractions", "Pieces in whole", "How many unit fractions of size 1/{d} make one whole?", "d", "d copies of 1/d make a whole.", vars=[v("d", 2, 12)], choice_spread=4.0),
        t("khan.early_math.fraction.equivalent.v1", "fractions", "Equivalent fractions", "Missing numerator", "Scale the fraction {a}/{b} by {scale}. What is the new numerator?", "a * scale", "Multiply numerator and denominator by the same factor.", vars=[v("a", 1, 6), v("b", 2, 10), v("scale", 2, 5)], choice_spread=5.0),
        t("khan.early_math.fraction.equivalent.v2", "fractions", "Equivalent fractions", "Missing denominator", "Scale the fraction {a}/{b} by {scale}. What is the new denominator?", "b * scale", "The denominator scales by the same factor as the numerator.", vars=[v("a", 1, 6), v("b", 2, 10), v("scale", 2, 5)], choice_spread=5.0),
        t("khan.early_math.fraction.shaded.v1", "fractions", "Shaded region meaning", "Count shaded parts", "A shape is split into {d} equal parts and {n} are shaded. How many parts are shaded?", "n", "The numerator counts the selected equal parts.", vars=[v("d", 2, 12), v("n", 1, 10)], constraint_expr="d > n", choice_spread=4.0),
        t("khan.early_math.fraction.shaded.v2", "fractions", "Shaded region meaning", "Count total parts", "A model shows {n} shaded parts out of {d} equal parts. How many equal parts make the whole?", "d", "The denominator tells how many equal parts make the whole.", vars=[v("d", 2, 12), v("n", 1, 10)], constraint_expr="d > n", choice_spread=4.0),
        t("khan.early_math.fraction.decimal.v1", "fractions", "Fraction to decimal", "Fraction to decimal", "Write {n}/{d} as a decimal.", "n / d", "A fraction becomes a decimal by dividing the numerator by the denominator.", vars=[v("d", 2, 10), v("n", 1, 9)], constraint_expr="d > n and (d == 2 or d == 4 or d == 5 or d == 8 or d == 10)", choice_spread=1.5),
        t("khan.early_math.fraction.decimal.v2", "fractions", "Fraction to decimal", "Benchmark fraction decimal", "What decimal is equal to {n}/{d}?", "n / d", "Use place value to rewrite the fraction as tenths or hundredths when you can.", vars=[v("d", 2, 10), v("n", 1, 9)], constraint_expr="d > n and (d == 2 or d == 4 or d == 5 or d == 8 or d == 10)", choice_spread=1.5),
        t("khan.early_math.fraction.compare.v1", "fractions", "Compare fractions and mixed numbers", "Larger numerator", "Which is larger, {a}/{d} or {b}/{d}? Enter the numerator of the larger fraction.", "b", "With a common denominator, the larger numerator gives the larger fraction.", vars=[v("a", 1, 7), v("b", 2, 8), v("d", 3, 10)], constraint_expr="d > b and b > a", choice_spread=4.0),
        t("khan.early_math.fraction.compare.v2", "fractions", "Compare fractions and mixed numbers", "Larger whole part", "Which mixed number is larger: {w1} {n1}/{d} or {w2} {n2}/{d}? Enter the whole-number part of the larger mixed number.", "w2", "Compare whole numbers first when mixed numbers share the same fraction size.", vars=[v("w1", 1, 3), v("w2", 2, 5), v("n1", 1, 5), v("n2", 1, 5), v("d", 6, 10)], constraint_expr="w2 > w1 and d > n1 and d > n2", choice_spread=3.0),
    ]


def _money_measurement() -> list[dict[str, object]]:
    return [
        t("ray.early_math.money.value.v1", "money", "Dollar-coin values", "Money in cents", "How many cents are in ${d}.{c}?", "d * 100 + c", "One dollar is 100 cents.", mode="word", vars=[v("d", 0, 15), v("c", 0, 99)], choice_spread=30.0),
        t("khan.early_math.money.value.v2", "money", "Dollar-coin values", "Coin value", "A pouch has {quarters} quarters, {dimes} dimes, and {nickels} nickels. How many cents are in the pouch?", "quarters * 25 + dimes * 10 + nickels * 5", "Add the value of each coin type.", vars=[v("quarters", 0, 8), v("dimes", 0, 8), v("nickels", 0, 8)], choice_spread=25.0),
        t("khan.early_math.money.value.v3", "money", "Dollar-coin values", "Dollar to cents", "How many cents are in {d} dollars and {c} cents?", "d * 100 + c", "Convert dollars into hundreds of cents, then add the extra cents.", vars=[v("d", 0, 15), v("c", 0, 99)], choice_spread=30.0),
        t("ray.early_math.money.change.v1", "money", "Making change", "Find change", "An item costs ${cost_d}.{cost_c} and you pay ${pay_d}.{pay_c}. How many cents of change should you get?", "(pay_d * 100 + pay_c) - (cost_d * 100 + cost_c)", "Change is the amount paid minus the cost.", mode="word", vars=[v("cost_d", 0, 12), v("cost_c", 0, 95, 5), v("pay_d", 1, 20), v("pay_c", 0, 95, 5)], constraint_expr="(pay_d * 100 + pay_c) > (cost_d * 100 + cost_c)", choice_spread=30.0),
        t("khan.early_math.money.change.v2", "money", "Making change", "Change in cents", "You pay {paid} cents for an item that costs {cost} cents. How many cents are left as change?", "paid - cost", "Subtract the cost from the amount paid.", vars=[v("paid", 50, 900, 5), v("cost", 15, 700, 5)], constraint_expr="paid > cost", choice_spread=25.0),
        t("khan.early_math.money.change.v3", "money", "Making change", "Price difference", "Find the difference between {paid} cents and {cost} cents.", "paid - cost", "The difference tells how much change remains after paying.", vars=[v("paid", 50, 900, 5), v("cost", 15, 700, 5)], constraint_expr="paid > cost", choice_spread=25.0),
        t("ray.early_math.money.budget.v1", "money", "Budget-style totals", "Budget total", "A snack costs ${a_d}.{a_c} and a drink costs ${b_d}.{b_c}. How many cents is the total cost?", "(a_d * 100 + a_c) + (b_d * 100 + b_c)", "Add the two amounts in cents to get the total.", mode="word", vars=[v("a_d", 0, 8), v("a_c", 0, 95, 5), v("b_d", 0, 8), v("b_c", 0, 95, 5)], choice_spread=25.0),
        t("khan.early_math.money.budget.v2", "money", "Budget-style totals", "Add prices", "What is the total number of cents in ${a_d}.{a_c} + ${b_d}.{b_c}?", "(a_d * 100 + a_c) + (b_d * 100 + b_c)", "Convert both prices to cents, then add.", vars=[v("a_d", 0, 8), v("a_c", 0, 95, 5), v("b_d", 0, 8), v("b_c", 0, 95, 5)], choice_spread=25.0),
        t("khan.early_math.money.budget.v3", "money", "Budget-style totals", "Add cents totals", "What is {a} cents + {b} cents?", "a + b", "Add the two amounts to get the combined total.", vars=[v("a", 25, 900, 5), v("b", 25, 900, 5)], choice_spread=25.0),
        t("ray.early_math.money.place.v1", "money", "Place-value in currency", "Currency place value", "How many cents are in ${d}.{c}?", "d * 100 + c", "Dollars are wholes and cents are hundredths of a dollar.", mode="word", vars=[v("d", 0, 12), v("c", 0, 99)], choice_spread=30.0),
        t("khan.early_math.money.place.v2", "money", "Place-value in currency", "Cents to dollars", "{cents} cents is how many whole dollars?", "cents // 100", "Each 100 cents makes 1 whole dollar.", vars=[v("cents", 100, 1200, 25)], choice_spread=4.0),
        t("khan.early_math.money.place.v3", "money", "Place-value in currency", "Hundredths in amount", "How many hundredths of a dollar are in ${d}.{c}?", "d * 100 + c", "The number of hundredths matches the total cents in the amount.", vars=[v("d", 0, 12), v("c", 0, 99)], choice_spread=30.0),
        t("khan.early_math.measure.length.v1", "measurement", "Length unit conversion", "Feet to inches", "How many inches are in {feet} feet?", "feet * 12", "There are 12 inches in 1 foot.", vars=[v("feet", 1, 20)], choice_spread=20.0),
        t("khan.early_math.measure.length.v2", "measurement", "Length unit conversion", "Meters to centimeters", "How many centimeters are in {meters} meters?", "meters * 100", "There are 100 centimeters in 1 meter.", vars=[v("meters", 1, 20)], choice_spread=40.0),
        t("khan.early_math.measure.time.v1", "measurement", "Time reading and arithmetic", "Hours to minutes", "How many minutes are in {hours} hours and {minutes} minutes?", "hours * 60 + minutes", "Convert hours to minutes, then add the extra minutes.", vars=[v("hours", 1, 8), v("minutes", 5, 55, 5)], choice_spread=20.0),
        t("ray.early_math.measure.time.word.v1", "measurement", "Time reading and arithmetic", "Practice time", "A lesson lasts {hours} hours and {minutes} minutes. How many minutes is that altogether?", "hours * 60 + minutes", "Hours turn into 60-minute groups before you add the remainder.", mode="word", vars=[v("hours", 1, 5), v("minutes", 5, 55, 5)], choice_spread=20.0),
        t("khan.early_math.measure.time.v2", "measurement", "Time reading and arithmetic", "Add time parts", "How many minutes are in {start_h} hour and {start_m} minutes?", "start_h * 60 + start_m", "Convert the hour into 60 minutes, then add the remaining minutes.", vars=[v("start_h", 1, 8), v("start_m", 5, 55, 5)], choice_spread=20.0),
        t("khan.early_math.measure.capacity.v1", "measurement", "Capacity and weight units", "Quarts to cups", "How many cups are in {quarts} quarts?", "quarts * 4", "There are 4 cups in 1 quart.", vars=[v("quarts", 1, 10)], choice_spread=10.0),
        t("ray.early_math.measure.weight.word.v1", "measurement", "Capacity and weight units", "Pounds to ounces", "A bag weighs {pounds} pounds. How many ounces is that?", "pounds * 16", "There are 16 ounces in 1 pound.", mode="word", vars=[v("pounds", 1, 12)], choice_spread=16.0),
        t("khan.early_math.measure.weight.v2", "measurement", "Capacity and weight units", "Ounces in pounds", "How many ounces are in {pounds} pounds?", "pounds * 16", "Multiply pounds by 16 because each pound has 16 ounces.", vars=[v("pounds", 1, 12)], choice_spread=16.0),
        t("khan.early_math.measure.temp.v1", "measurement", "Temperature basics", "Fahrenheit to Celsius", "Use C = (F - 32) x 5 / 9. What is the Celsius temperature when F = {f}?", "(f - 32) * 5 / 9", "Substitute the Fahrenheit value into the conversion rule.", vars=[v("f", 32, 212, 18)], choice_spread=8.0),
        t("khan.early_math.measure.temp.v2", "measurement", "Temperature basics", "Compare temperatures", "What is the difference in degrees between {warm} degrees and {cold} degrees?", "warm - cold", "Subtract the colder temperature from the warmer one.", vars=[v("warm", 5, 40), v("cold", -10, 10)], constraint_expr="warm > cold", choice_spread=8.0),
        t("khan.early_math.measure.convert.v1", "measurement", "Metric and customary conversions", "Yards to feet", "How many feet are in {yards} yards?", "yards * 3", "There are 3 feet in 1 yard.", mode="word", vars=[v("yards", 1, 20)], choice_spread=10.0),
        t("khan.early_math.measure.convert.v2", "measurement", "Metric and customary conversions", "Liters to milliliters", "How many milliliters are in {liters} liters?", "liters * 1000", "There are 1000 milliliters in 1 liter.", vars=[v("liters", 1, 12)], choice_spread=60.0),
        t("khan.early_math.measure.convert.v3", "measurement", "Metric and customary conversions", "Mixed metric length", "How many centimeters are in {meters} meters and {centimeters} centimeters?", "meters * 100 + centimeters", "Convert the meters to centimeters, then add the extra centimeters.", vars=[v("meters", 1, 20), v("centimeters", 1, 99)], choice_spread=40.0),
        t("ray.early_math.measure.elapsed.v1", "measurement", "Elapsed time", "Elapsed minutes", "A game starts at hour {start_h} and minute {start_m}. It ends {elapsed} minutes later. How many minutes passed?", "elapsed", "Elapsed time measures the distance between the start and end times.", mode="word", vars=[v("start_h", 1, 10), v("start_m", 0, 50, 10), v("elapsed", 10, 90, 5)], choice_spread=10.0),
        t("khan.early_math.measure.elapsed.v2", "measurement", "Elapsed time", "End minus start", "A timer starts and then stops {elapsed} minutes later. How many minutes elapsed?", "elapsed", "The elapsed time is the amount of time between start and stop.", vars=[v("elapsed", 10, 120, 5)], choice_spread=10.0),
        t("khan.early_math.measure.elapsed.v3", "measurement", "Elapsed time", "Difference in minutes", "What is the elapsed time from {start} minutes to {end} minutes?", "end - start", "Elapsed time is the ending time minus the starting time.", vars=[v("start", 5, 120, 5), v("end", 10, 180, 5)], constraint_expr="end > start", choice_spread=10.0),
    ]


def _integers_and_order() -> list[dict[str, object]]:
    return [
        t("khan.early_math.integers.signed.v1", "integers", "Signed numbers", "Larger signed number", "Which number is larger: {a} or {b}?", "a", "On a number line, numbers farther right are larger.", vars=[v("a", -5, 12), v("b", -12, 11)], constraint_expr="a > b", choice_spread=8.0),
        t("khan.early_math.integers.signed.v2", "integers", "Signed numbers", "Distance from zero", "What number is {m} units to the left of 0?", "-m", "Moving left from zero gives a negative number.", vars=[v("m", 1, 12)], choice_spread=8.0),
        t("khan.early_math.integers.negative.v1", "integers", "Negative arithmetic", "Signed addition", "Evaluate {a} + ({b}).", "a + b", "Treat signed addition as movement on the number line.", vars=[v("a", -20, 20), v("b", -15, 15)], choice_spread=8.0),
        t("khan.early_math.integers.negative.v2", "integers", "Negative arithmetic", "Signed subtraction", "Evaluate {a} - ({b}).", "a - b", "Subtracting a negative changes the direction of the move.", vars=[v("a", -20, 20), v("b", -15, 15)], choice_spread=8.0),
        t("khan.early_math.integers.order.v1", "integers", "Order-dependent operations", "Compare order", "What is {a} - {b}?", "a - b", "Changing the order changes the result for subtraction.", vars=[v("a", -12, 12), v("b", -12, 12)], choice_spread=8.0),
        t("khan.early_math.integers.order.v2", "integers", "Order-dependent operations", "Signed expression", "Evaluate ({a} - {b}) + {c}.", "a - b + c", "Each signed operation changes the starting value for the next step.", vars=[v("a", -12, 12), v("b", -12, 12), v("c", -8, 8)], choice_spread=8.0),
        t("khan.early_math.integers.abs.v1", "integers", "Absolute value", "Absolute value", "What is |-{m}|?", "m", "Absolute value is distance from zero, so it is never negative.", vars=[v("m", 1, 15)], choice_spread=5.0),
        t("khan.early_math.integers.abs.v2", "integers", "Absolute value", "Absolute value compare", "If a diver is at -{m} meters, how far is the diver from sea level?", "m", "Distance from sea level uses the absolute value.", mode="word", vars=[v("m", 1, 20)], choice_spread=5.0),
        t("khan.early_math.integers.abs.v3", "integers", "Absolute value", "Distance to zero", "A point is at {n} on the number line. How many units is it from 0?", "0 - n", "Distance from zero ignores direction, so a negative location becomes a positive distance.", vars=[v("n", -20, -1)], choice_spread=5.0),
        t("khan.early_math.order.parentheses.v1", "order_of_operations", "Parentheses first", "Evaluate grouped expression", "Evaluate ({a} + {b}) * {c}.", "(a + b) * c", "Solve the parentheses before multiplying.", vars=[v("a", -9, 12), v("b", -9, 12), v("c", 2, 6)], choice_spread=10.0),
        t("khan.early_math.order.parentheses.v2", "order_of_operations", "Parentheses first", "Grouped subtraction", "Evaluate {a} - ({b} - {c}).", "a - (b - c)", "The grouped subtraction must be finished first.", vars=[v("a", -9, 12), v("b", -9, 12), v("c", -9, 12)], choice_spread=10.0),
        t("khan.early_math.order.mult_before_add.v1", "order_of_operations", "Multiplication vs addition/subtraction", "Multiply before add", "Evaluate {a} + {b} * {c}.", "a + b * c", "Multiplication happens before addition unless parentheses say otherwise.", vars=[v("a", -9, 12), v("b", 2, 9), v("c", 2, 9)], choice_spread=10.0),
        t("khan.early_math.order.mult_before_add.v2", "order_of_operations", "Multiplication vs addition/subtraction", "Multiply before subtract", "Evaluate {a} - {b} * {c}.", "a - b * c", "Form the product first, then combine it with the addition or subtraction.", vars=[v("a", -9, 20), v("b", 2, 9), v("c", 2, 9)], choice_spread=10.0),
        t("khan.early_math.order.grouping.v1", "order_of_operations", "Expression grouping", "Chunk expression", "Evaluate ({a} + {b}) - ({c} * {d}).", "(a + b) - (c * d)", "Simplify one grouped chunk at a time.", vars=[v("a", -9, 12), v("b", -9, 12), v("c", 2, 8), v("d", 2, 8)], choice_spread=12.0),
        t("khan.early_math.order.grouping.v2", "order_of_operations", "Expression grouping", "Mixed grouping", "Evaluate {a} + ({b} * {c}) - {d}.", "a + (b * c) - d", "Group the multiplication as one chunk before the last subtraction.", vars=[v("a", -9, 12), v("b", 2, 8), v("c", 2, 8), v("d", -9, 12)], choice_spread=12.0),
        t("khan.early_math.order.exponents.v1", "order_of_operations", "Exponents in expressions", "Evaluate exponent", "Evaluate {base}^{power}.", "base ** power", "An exponent means repeated multiplication of the base.", vars=[v("base", 2, 6), v("power", 2, 4)], choice_spread=15.0),
        t("khan.early_math.order.exponents.v2", "order_of_operations", "Exponents in expressions", "Exponent before addition", "Evaluate {a} + {base}^{power}.", "a + (base ** power)", "Compute the exponent before adding it to the rest of the expression.", vars=[v("a", 1, 20), v("base", 2, 5), v("power", 2, 4)], choice_spread=15.0),
    ]


def _pre_algebra() -> list[dict[str, object]]:
    return [
        t("openstax.prealgebra.fluency.v1", "pre_algebra", "Integer and fraction fluency", "Signed sum", "Evaluate {a} + ({b}).", "a + b", "Pre-algebra fluency starts with reliable signed-number work.", vars=[v("a", -20, 20), v("b", -20, 20)], choice_spread=8.0),
        t("openstax.prealgebra.fluency.v2", "pre_algebra", "Integer and fraction fluency", "Fraction as decimal", "Write {n}/{d} as a decimal.", "n / d", "Convert the fraction by dividing numerator by denominator.", vars=[v("d", 2, 10), v("n", 1, 9)], constraint_expr="d > n and (d == 2 or d == 4 or d == 5 or d == 8 or d == 10)", choice_spread=1.5),
        t("openstax.prealgebra.order.v1", "pre_algebra", "Order of operations", "Nested expression", "Evaluate ({a} + {b}) * {c}.", "(a + b) * c", "Finish grouped work before multiplication.", vars=[v("a", -9, 12), v("b", -9, 12), v("c", 2, 6)], choice_spread=10.0),
        t("openstax.prealgebra.order.v2", "pre_algebra", "Order of operations", "Mixed expression", "Evaluate {a} - ({b} * {c}) + {d}.", "a - (b * c) + d", "Apply multiplication before combining with the rest.", vars=[v("a", -9, 12), v("b", -9, 12), v("c", 2, 6), v("d", -9, 12)], choice_spread=10.0),
        t("openstax.prealgebra.expr.v1", "pre_algebra", "Expressions and variables", "Substitute value", "Evaluate {coeff}x + ({bias}) when x = {x}.", "coeff * x + bias", "Substitute the value for x, then simplify.", vars=[v("coeff", -6, 6), v("bias", -12, 12), v("x", -6, 9)], constraint_expr="coeff != 0", choice_spread=10.0),
        t("openstax.prealgebra.expr.v2", "pre_algebra", "Expressions and variables", "Combine like terms", "Evaluate ({a}x) + ({b}x) + ({c}) when x = {x}.", "(a + b) * x + c", "Combine like terms before substituting the value.", vars=[v("a", -5, 5), v("b", -5, 5), v("c", -10, 10), v("x", -6, 9)], constraint_expr="a != 0 and b != 0", choice_spread=10.0),
        t("openstax.prealgebra.one_step.v1", "pre_algebra", "One-step equations", "Additive equation", "Solve for x: x + ({offset}) = {rhs}", "rhs - offset", "Undo the addition or subtraction trapping the variable.", vars=[v("offset", -12, 12), v("rhs", -20, 30)], choice_spread=10.0),
        t("openstax.prealgebra.one_step.v2", "pre_algebra", "One-step equations", "Multiplicative equation", "Solve for x: {coeff}x = {rhs}", "rhs / coeff", "Divide by the coefficient to isolate the variable.", vars=[v("coeff", 2, 9), v("rhs", -81, 81)], constraint_expr="rhs % coeff == 0", choice_spread=10.0),
        t("openstax.prealgebra.two_step.v1", "pre_algebra", "Two-step equations and inequalities", "Solve two-step equation", "Solve for x: {coeff}x + ({bias}) = {rhs}", "(rhs - bias) / coeff", "Undo the constant term first, then divide by the coefficient.", vars=[v("coeff", 2, 8), v("bias", -15, 15), v("rhs", -90, 90)], constraint_expr="(rhs - bias) % coeff == 0", choice_spread=10.0),
        t("openstax.prealgebra.two_step.v2", "pre_algebra", "Two-step equations and inequalities", "Smallest integer solution", "Find the smallest integer x satisfying {coeff}x + {bias} > {rhs}", "((rhs - bias) // coeff) + 1", "Solve the inequality boundary, then take the next integer above it.", vars=[v("coeff", 2, 6), v("bias", -8, 8), v("rhs", 3, 50)], choice_spread=6.0),
        t("openstax.prealgebra.ratio.v1", "pre_algebra", "Ratios, rates, and proportional relationships", "Unit rate", "{total} miles are traveled in {hours} hours. What is the unit rate in miles per hour?", "total / hours", "Find the amount for 1 unit first.", vars=[v("total", 18, 180), v("hours", 2, 12)], constraint_expr="total % hours == 0", choice_spread=8.0),
        t("openstax.prealgebra.ratio.v2", "pre_algebra", "Ratios, rates, and proportional relationships", "Scale proportion", "If {a} tickets cost ${b}, how much do {scale} equal groups of {a} tickets cost?", "b * scale", "A proportional pair scales both quantities by the same factor.", vars=[v("a", 1, 8), v("b", 2, 16), v("scale", 2, 6)], choice_spread=10.0),
        t("openstax.prealgebra.ratio.word.v1", "pre_algebra", "Ratios, rates, and proportional relationships", "Rate story", "A printer makes {total} pages in {hours} hours. At the same rate, how many pages does it make in 1 hour?", "total / hours", "The unit rate is the per-1 amount.", mode="word", vars=[v("total", 18, 180), v("hours", 2, 12)], constraint_expr="total % hours == 0", choice_spread=8.0),
        t("openstax.prealgebra.percent.v1", "pre_algebra", "Percent problems", "Percent of a quantity", "What is {percent}% of {base}?", "percent * base / 100", "Convert the percent to a decimal or fraction of 100, then multiply.", vars=[v("percent", 5, 80, 5), v("base", 20, 240)], choice_spread=15.0),
        t("openstax.prealgebra.percent.v2", "pre_algebra", "Percent problems", "Percent change", "A value increases by {delta} from an original {base}. What is the percent change?", "delta * 100 / base", "Percent change compares the change to the original amount.", vars=[v("base", 20, 200), v("delta", 5, 60)], constraint_expr="(delta * 100) % base == 0", choice_spread=12.0),
        t("openstax.prealgebra.percent.word.v1", "pre_algebra", "Percent problems", "Discount story", "A shirt costs ${base} and is discounted by {percent}%. How many dollars is the discount?", "percent * base / 100", "Find the percent of the original price to get the discount amount.", mode="word", vars=[v("base", 20, 200), v("percent", 5, 50, 5)], choice_spread=12.0),
        t("openstax.prealgebra.exponents.v1", "pre_algebra", "Exponents, roots, and scientific notation", "Evaluate power", "Evaluate {base}^{power}.", "base ** power", "Exponents count repeated multiplication of the base.", vars=[v("base", 2, 9), v("power", 2, 4)], choice_spread=15.0),
        t("openstax.prealgebra.exponents.v2", "pre_algebra", "Exponents, roots, and scientific notation", "Scientific notation exponent", "Write {coefficient} x 10^{power} in scientific notation. What is the exponent on 10?", "power", "The exponent tracks how many places the decimal moved.", vars=[v("coefficient", 2, 9), v("power", -5, 7)], choice_spread=6.0),
        t("openstax.prealgebra.coordinate.v1", "pre_algebra", "Coordinate plane and function tables", "Function output", "A table follows y = {m}x + ({b}). What is y when x = {x}?", "m * x + b", "Use the rule to map the input x to its output.", vars=[v("m", -5, 5), v("b", -8, 8), v("x", -4, 6)], constraint_expr="m != 0", choice_spread=8.0),
        t("openstax.prealgebra.coordinate.v2", "pre_algebra", "Coordinate plane and function tables", "Distance from axis", "Point P is at ({x}, {y}). How far is P from the y-axis?", "x", "Distance from the y-axis depends only on the x-coordinate's magnitude.", vars=[v("x", 1, 9), v("y", -9, 9)], choice_spread=5.0),
        t("openstax.prealgebra.coordinate.word.v1", "pre_algebra", "Coordinate plane and function tables", "Coordinate story", "A point with coordinates ({x}, {y}) marks a drone's location. How far is the drone from the y-axis?", "x", "Distance from the y-axis is the absolute value of the x-coordinate.", mode="word", vars=[v("x", 1, 9), v("y", -9, 9)], choice_spread=5.0),
    ]


def _shapes_data() -> list[dict[str, object]]:
    return [
        t("local.early_math.shape.2d_attrs.v1", "geometry_shapes", "2D shape attributes", "Triangle sides", "How many sides does a triangle have?", "3", "A triangle has 3 sides and 3 vertices.", choice_spread=3.0),
        t("local.early_math.shape.2d_attrs.v2", "geometry_shapes", "2D shape attributes", "Rectangle vertices", "How many vertices does a rectangle have?", "4", "A rectangle has 4 corners, also called vertices.", choice_spread=3.0),
        t("local.early_math.shape.3d_attrs.v1", "geometry_shapes", "3D solid attributes", "Cube faces", "How many flat faces does a cube have?", "6", "A cube has 6 square flat faces.", choice_spread=3.0),
        t("local.early_math.shape.3d_attrs.v2", "geometry_shapes", "3D solid attributes", "Cylinder flat faces", "How many flat circular faces does a cylinder have?", "2", "A cylinder has 2 flat circular faces and one curved surface.", choice_spread=3.0),
        t("local.early_math.shape.compose.v1", "geometry_shapes", "Compose 2D shapes", "Squares compose rectangle", "How many same-size squares side by side can compose a rectangle?", "2", "Two same-size squares can join edge-to-edge to make a rectangle.", choice_spread=3.0),
        t("local.early_math.shape.compose.v2", "geometry_shapes", "Compose 2D shapes", "Triangles compose hexagon", "How many same-size triangles can meet at the center to compose a hexagon?", "6", "Six same-size triangles can compose a hexagon without gaps or overlaps.", choice_spread=3.0),
        t("local.early_math.shape.equal_shares.v1", "geometry_shapes", "Equal shares of shapes", "Halves parts", "How many equal parts make halves?", "2", "Halves split one whole into 2 equal parts.", choice_spread=3.0),
        t("local.early_math.shape.equal_shares.v2", "geometry_shapes", "Equal shares of shapes", "Fourths parts", "How many equal parts make fourths?", "4", "Fourths split one whole into 4 equal parts.", choice_spread=3.0),
        t("local.early_math.data.sort.v1", "data_displays", "Sort data into categories", "Category count", "A chart shows apples: 3, bananas: 5, oranges: 2. How many apples are shown?", "3", "Read the count next to the apples category.", choice_spread=3.0),
        t("local.early_math.data.sort.v2", "data_displays", "Sort data into categories", "Sorted total", "A chart shows red: 4 and blue: 6. How many items are sorted in all?", "10", "Add the category counts to get the total number of sorted items.", choice_spread=4.0),
        t("local.early_math.data.picture_bar.v1", "data_displays", "Picture and bar graphs", "Tallest bar count", "A bar graph shows cats: 4, dogs: 7, fish: 3. How many votes did dogs get?", "7", "Read the count from the dogs bar.", choice_spread=4.0),
        t("local.early_math.data.picture_bar.v2", "data_displays", "Picture and bar graphs", "Picture graph count", "A picture graph has 5 soccer balls. Each picture means 1 vote. How many votes is that?", "5", "Each picture stands for one vote, so count the pictures.", choice_spread=3.0),
        t("local.early_math.data.dot.v1", "data_displays", "Dot plots", "Dot count", "A dot plot has 4 dots above 6. How many data values are 6?", "4", "Each dot is one data value above that label.", choice_spread=3.0),
        t("local.early_math.data.dot.v2", "data_displays", "Dot plots", "Two labels dot count", "A dot plot has 3 dots above 2 and 5 dots above 3. How many dots are there in all?", "8", "Add the dots above both labels to count all data values.", choice_spread=4.0),
        t("local.early_math.data.frequency.v1", "data_displays", "Frequency tables", "Frequency lookup", "A frequency table shows apples: 4, bananas: 6, oranges: 3. What is the frequency for bananas?", "6", "Read the count listed beside bananas.", choice_spread=4.0),
        t("local.early_math.data.frequency.v2", "data_displays", "Frequency tables", "Frequency total", "A frequency table shows red: 5, blue: 4, green: 7. How many items are in the data set?", "16", "Add all frequencies to get the data set size.", choice_spread=5.0),
        t("local.early_math.data.stem_leaf.v1", "data_displays", "Stem-and-leaf plots", "Largest value", "In a stem-and-leaf plot, stem 4 has leaves 1, 5, 8. What is the greatest value?", "48", "Join the stem with the largest leaf to read 48.", choice_spread=8.0),
        t("local.early_math.data.stem_leaf.v2", "data_displays", "Stem-and-leaf plots", "Value count", "In a stem-and-leaf plot, stem 3 has leaves 0, 2, 2, 7. How many values are listed?", "4", "Each leaf represents one data value.", choice_spread=3.0),
        t("local.early_math.data.scatter.v1", "data_displays", "Scatterplots and paired data", "Paired rule", "Paired data follows y = 3x. What y-value pairs with x = 5?", "15", "Use the rule to find the matching y-value.", choice_spread=8.0),
        t("local.early_math.data.scatter.v2", "data_displays", "Scatterplots and paired data", "Ordered pair x", "A scatterplot point is (6, 18). What is its x-value?", "6", "The x-value is the first coordinate in the ordered pair.", choice_spread=5.0),
        t("local.early_math.data.questions.v1", "data_displays", "Questions from data displays", "How many more", "A graph shows apples: 7 and oranges: 3. How many more apples than oranges are there?", "4", "Subtract the smaller count from the larger count.", choice_spread=3.0),
        t("local.early_math.data.questions.v2", "data_displays", "Questions from data displays", "Graph total", "A graph shows 4 sunny days and 2 rainy days. How many days are shown in all?", "6", "Add the two displayed counts to answer a total question.", choice_spread=3.0),
    ]


def label_case(text: str) -> str:
    return text


def _band_map() -> dict[str, list[dict[str, object]]]:
    return {
        "early_math_number_place_value_v1.json": _counting_and_place_value(),
        "early_math_operations_long_v1.json": _operations_and_long(),
        "early_math_fractions_ratios_v1.json": _fractions_and_ratios(),
        "early_math_money_measurement_time_v1.json": _money_measurement(),
        "early_math_shapes_data_v1.json": _shapes_data(),
        "early_math_integers_order_v1.json": _integers_and_order(),
        "early_math_pre_algebra_structure_v1.json": _pre_algebra(),
    }


def _validate(items_by_file: dict[str, list[dict[str, object]]]) -> None:
    spec_modes = {(spec.skill, spec.subskill): set(spec.required_modes) for spec in early_math_specs()}
    expression_counts: dict[tuple[str, str], int] = defaultdict(int)
    mode_map: dict[tuple[str, str], set[str]] = defaultdict(set)
    seen_ids: set[str] = set()
    for items in items_by_file.values():
        for item in items:
            key = (str(item["skill"]), str(item["subskill"]))
            if key not in spec_modes:
                raise ValueError(f"Template without catalog spec: {key}")
            if item["mode"] == "expression":
                expression_counts[key] += 1
            mode_map[key].add(str(item["mode"]))
            external_id = str(item["external_id"])
            if external_id in seen_ids:
                raise ValueError(f"Duplicate external_id: {external_id}")
            seen_ids.add(external_id)
    for spec in early_math_specs():
        key = (spec.skill, spec.subskill)
        if expression_counts[key] < 2:
            raise ValueError(f"Need at least 2 expression templates for {key}, found {expression_counts[key]}")
        missing_modes = set(spec.required_modes).difference(mode_map[key])
        if missing_modes:
            raise ValueError(f"Missing required modes {sorted(missing_modes)} for {key}")


def main() -> None:
    items_by_file = _band_map()
    _validate(items_by_file)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, items in items_by_file.items():
        path = OUT_DIR / filename
        path.write_text(json.dumps(items, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        print(f"wrote {path} items={len(items)}")


if __name__ == "__main__":
    main()
