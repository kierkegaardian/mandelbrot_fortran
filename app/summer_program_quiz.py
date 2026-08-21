from __future__ import annotations

from dataclasses import dataclass
import json
import random

from . import db, summer_program
from .models import ScaffoldStep
from .quiz_engine import Question, generate_question
from .content_depth.summer import cumulative_target_schedule, cumulative_targets_for_task, program_question
from .summer_program_defs import FOUNDATION_BRIDGE_LANE, lane_display_name


@dataclass(frozen=True)
class SummerProgramLaunch:
    profile_id: int
    program_id: int
    task_id: int


@dataclass(frozen=True)
class ProgramQuizPlan:
    questions: list[Question]
    attempt_skill: str
    meta: str
    question_type: str
    level: int
    launch_context: str


BlueprintItem = tuple[str, str, str]

PLACEMENT_BLUEPRINT: tuple[BlueprintItem, ...] = (
    ("fractions", "fractions", "Equivalent fractions"),
    ("fractions", "fractions", "Fraction to decimal"),
    ("fractions", "fractions", "Compare fractions and mixed numbers"),
    ("fractions", "pre_algebra", "Integer and fraction fluency"),
    ("integer_order_fluency", "pre_algebra", "Integer and fraction fluency"),
    ("integer_order_fluency", "pre_algebra", "Order of operations"),
    ("integer_order_fluency", "integers", "Negative arithmetic"),
    ("integer_order_fluency", "order_of_operations", "Parentheses first"),
    ("variables_equations", "pre_algebra", "Expressions and variables"),
    ("variables_equations", "pre_algebra", "One-step equations"),
    ("variables_equations", "pre_algebra", "Two-step equations and inequalities"),
    ("variables_equations", "pre_algebra", "One-step equations"),
    ("ratios_percent", "pre_algebra", "Ratios, rates, and proportional relationships"),
    ("ratios_percent", "pre_algebra", "Percent problems"),
    ("ratios_percent", "ratios", "Unit rates and proportional relationships"),
    ("exponents_coordinates", "pre_algebra", "Exponents, roots, and scientific notation"),
    ("exponents_coordinates", "pre_algebra", "Coordinate plane and function tables"),
    ("exponents_coordinates", "pre_algebra", "Coordinate plane and function tables"),
)

FOUNDATION_ASSESSMENT_BLUEPRINT: tuple[BlueprintItem, ...] = (
    ("place_value", "place_value", "Expanded form"),
    ("place_value", "place_value", "Compare numbers by place value"),
    ("add_subtract", "add_subtract", "Word problems"),
    ("multiply_divide", "multiply", "Simple product facts"),
    ("multiply_divide", "divide", "Inverse thinking"),
    ("fractions", "fractions", "Equivalent fractions"),
    ("fractions", "fractions", "Compare fractions and mixed numbers"),
    ("money_measurement", "money", "Making change"),
    ("money_measurement", "measurement", "Metric and customary conversions"),
    ("geometry_shapes", "geometry_shapes", "2D shape attributes"),
    ("data_displays", "data_displays", "Picture and bar graphs"),
    ("data_displays", "data_displays", "Frequency tables"),
    ("financial_literacy", "financial_literacy", "Income, gifts, wants, and needs"),
    ("financial_literacy", "financial_literacy", "Saving, spending, giving, borrowing, and lending"),
    ("ratios", "ratios", "Equivalent ratios"),
    ("order_ops", "order_of_operations", "Parentheses first"),
    ("order_ops", "order_of_operations", "Expression grouping"),
)

PREALGEBRA_ASSESSMENT_BLUEPRINT: tuple[BlueprintItem, ...] = (
    ("fluency", "pre_algebra", "Integer and fraction fluency"),
    ("order_ops", "pre_algebra", "Order of operations"),
    ("expressions", "pre_algebra", "Expressions and variables"),
    ("one_step", "pre_algebra", "One-step equations"),
    ("two_step", "pre_algebra", "Two-step equations and inequalities"),
    ("ratios", "pre_algebra", "Ratios, rates, and proportional relationships"),
    ("percent", "pre_algebra", "Percent problems"),
    ("exponents", "pre_algebra", "Exponents, roots, and scientific notation"),
    ("coordinates", "pre_algebra", "Coordinate plane and function tables"),
    ("geometry_measurement", "geometry_area", "Area of triangles and parallelograms"),
    ("geometry_measurement", "geometry_area", "Surface area and volume"),
    ("data_probability", "data_analysis", "Histograms"),
    ("data_probability", "data_analysis", "Median, range, and IQR"),
    ("data_probability", "data_analysis", "Sample inferences from displays"),
    ("data_probability", "stats_probability", "Probability models"),
    ("financial_literacy", "financial_literacy", "Accounts, credit reports, and education income"),
    ("financial_literacy", "financial_literacy", "Budget percentages, net worth, interest, and incentives"),
)


def assessment_blueprint_for_lane(lane: str) -> tuple[BlueprintItem, ...]:
    if lane == FOUNDATION_BRIDGE_LANE:
        return FOUNDATION_ASSESSMENT_BLUEPRINT
    return PREALGEBRA_ASSESSMENT_BLUEPRINT


def summer_unit_targets(unit_code: str, skill: str, subskill: str | None) -> tuple[tuple[str, str | None], ...]:
    return tuple(_targets_for_unit(unit_code, skill, subskill, "lesson"))


def scaffold_step_count_for_target(skill: str, subskill: str | None) -> int:
    question = _scaffolded_question(skill, subskill, 0)
    if question is None or not question.scaffold_steps:
        return 0
    return len(question.scaffold_steps)


def build_task_quiz_plan(launch: SummerProgramLaunch) -> ProgramQuizPlan:
    program = db.get_summer_program(launch.program_id)
    task = db.get_summer_program_task(launch.task_id)
    if program is None or task is None:
        raise ValueError("Summer Program task was not found.")
    if task.task_kind == "placement_assessment":
        questions = _build_placement_questions()
    elif task.task_kind == "remediation_review":
        questions = _build_remediation_questions(program.lane, task)
    elif task.task_kind in {"midpoint_assessment", "exit_assessment"}:
        questions = _build_task_assessment_questions(program.lane, task)
    else:
        questions = _build_unit_questions(program.lane, task)
    meta = f"Summer Program • {lane_display_name(program.lane)} • {_task_label(task.task_kind)}"
    notes = _task_notes(task)
    remediation_message = _string_or_none(notes.get("remediation_message"))
    catch_up_note = _string_or_none(notes.get("catch_up_note"))
    if remediation_message:
        meta = f"{meta} • Remediation"
    elif catch_up_note:
        meta = f"{meta} • Catch-up"
    return ProgramQuizPlan(
        questions=questions,
        attempt_skill=task.skill,
        meta=meta,
        question_type="typed",
        level=1 if program.lane == FOUNDATION_BRIDGE_LANE else 2,
        launch_context="summer_program",
    )


def _build_unit_questions(lane: str, task) -> list[Question]:
    count = 3 if task.task_kind == "lesson" else 6 if task.task_kind == "checkpoint" else 5
    current_targets = _targets_for_task(task)
    if task.task_kind in {"mixed_review", "checkpoint"}:
        all_targets = cumulative_targets_for_task(task, _targets_for_unit) or current_targets
        schedule = cumulative_target_schedule(current_targets, all_targets, count)
    else:
        schedule = [(current_targets[idx % len(current_targets)], False) for idx in range(count)]
    questions: list[Question] = []
    scaffold_slots = count if task.task_kind == "lesson" else 0
    level = 1 if lane == FOUNDATION_BRIDGE_LANE else 2
    used: dict[tuple[str, str], set[str]] = {}
    for idx, ((skill, subskill), application) in enumerate(schedule):
        question = _scaffolded_question(skill, subskill, idx) if idx < scaffold_slots else None
        if question is None:
            question = program_question(
                skill, subskill, level, used,
                application=application,
            )
        question.question_label = _task_label(task.task_kind)
        questions.append(question)
    return questions


def _build_remediation_questions(lane: str, task) -> list[Question]:
    targets = _targets_for_task(task)
    questions: list[Question] = []
    level = 1 if lane == FOUNDATION_BRIDGE_LANE else 2
    for idx in range(4):
        skill, subskill = targets[idx % len(targets)]
        question = _scaffolded_question(skill, subskill, idx)
        if question is None:
            question = generate_question(skill, level, "typed", subskill=subskill)
        question.question_label = _task_label(task.task_kind)
        questions.append(question)
    return questions


def _build_placement_questions() -> list[Question]:
    return _assessment_questions_from_blueprint(PLACEMENT_BLUEPRINT, label_prefix="Placement")


def _build_assessment_questions(lane: str, task_kind: str) -> list[Question]:
    label = "Midpoint" if task_kind == "midpoint_assessment" else "Exit"
    return _assessment_questions_from_blueprint(assessment_blueprint_for_lane(lane), label_prefix=label)


def _build_task_assessment_questions(lane: str, task) -> list[Question]:
    label = "Midpoint" if task.task_kind == "midpoint_assessment" else "Exit"
    current_targets = _targets_for_task(task)
    all_targets = cumulative_targets_for_task(task, _targets_for_unit) or current_targets
    count = len(assessment_blueprint_for_lane(lane))
    schedule = cumulative_target_schedule(current_targets, all_targets, count)
    level = 1 if lane == FOUNDATION_BRIDGE_LANE else 2
    used: dict[tuple[str, str], set[str]] = {}
    questions: list[Question] = []
    for (skill, subskill), application in schedule:
        question = program_question(
            skill, subskill, level, used, application=application
        )
        question.scaffold_steps = None
        question.question_label = label
        questions.append(question)
    remediation = summer_program.remediation_targets_for_task(task)
    if not remediation:
        return questions
    remediation_questions: list[Question] = []
    slots = min(3, len(questions))
    for idx in range(slots):
        skill, subskill = remediation[idx % len(remediation)]
        question = program_question(skill, subskill, level, used, application=False)
        question.scaffold_steps = None
        question.question_label = questions[idx].question_label
        remediation_questions.append(question)
    return remediation_questions + questions[slots:]


def _assessment_questions_from_blueprint(
    blueprint: tuple[BlueprintItem, ...],
    *,
    label_prefix: str,
) -> list[Question]:
    questions: list[Question] = []
    for idx, (strand, skill, subskill) in enumerate(blueprint):
        level = 1 if skill in {"place_value", "add_subtract", "multiply", "divide", "fractions", "money", "measurement"} else 2
        question = generate_question(skill, level, "typed", subskill=subskill)
        question.question_label = f"{label_prefix} • {strand}"
        questions.append(question)
    return questions


def _targets_for_unit(unit_code: str, skill: str, subskill: str | None, task_kind: str) -> list[tuple[str, str | None]]:
    if unit_code == "multiply_divide_fluency":
        return [("multiply", "Simple product facts"), ("divide", "Inverse thinking")]
    if unit_code == "money_measurement":
        return [("money", "Making change"), ("measurement", "Metric and customary conversions")]
    if unit_code == "fractions_equivalence":
        return [("fractions", "Unit fractions"), ("fractions", "Equivalent fractions"), ("fractions", "Shaded region meaning")]
    if unit_code == "add_subtract_fluency":
        return [("add_subtract", "Single-digit addition"), ("add_subtract", "Single-digit subtraction"), ("add_subtract", "Missing addends")]
    if unit_code == "place_value":
        return [("place_value", "Ones, tens, and hundreds identification"), ("place_value", "Expanded form"), ("place_value", "Compare numbers by place value")]
    if unit_code == "ratio_language_patterning":
        return [("ratios", "Ratio language (to:of)"), ("ratios", "Equivalent ratios"), ("ratios", "Unit rates and proportional relationships")]
    if unit_code == "order_operations_intro":
        return [("order_of_operations", "Parentheses first"), ("order_of_operations", "Expression grouping")]
    if unit_code == "mixed_review_exit_prep":
        return [
            ("pre_algebra", "Expressions and variables"),
            ("pre_algebra", "Ratios, rates, and proportional relationships"),
            ("pre_algebra", "Percent problems"),
            ("pre_algebra", "Coordinate plane and function tables"),
        ]
    if unit_code == "linear_relationships_preview":
        return [
            ("algebra_linear", "Slope from points"),
            ("algebra_linear", "Slope-intercept interpretation"),
            ("algebra_linear", "Direct variation"),
            ("algebra_linear", "Rate and unit-rate modeling"),
            ("algebra_linear", "Word problems with linear models"),
        ]
    if unit_code == "functions_patterns_preview":
        return [
            ("algebra_1", "Functions"),
            ("algebra_1", "Sequences"),
            ("algebra_1", "Linear equations & graphs"),
            ("algebra_1", "Solving equations & inequalities"),
        ]
    if unit_code == "algebra_1_preview_capstone":
        return [
            ("algebra_1", "Slope from points"),
            ("algebra_1", "Functions"),
            ("algebra_1", "Slope-intercept form"),
            ("algebra_1", "Sequences"),
            ("algebra_1", "Graphing linear inequalities"),
            ("algebra_1", "Solving equations & inequalities"),
        ]
    if unit_code == "geometry_measurement_preview":
        return [
            ("geometry_area", "Perimeter and missing sides"),
            ("geometry_area", "Area of triangles and parallelograms"),
            ("geometry_area", "Circumference and area of circles"),
            ("geometry_area", "Surface area and volume"),
            ("geometry_area", "Pythagorean theorem"),
        ]
    if unit_code == "coordinate_geometry_preview":
        return [
            ("geometry_area", "Coordinate geometry distance and midpoint"),
            ("geometry_area", "Transformations and congruence"),
            ("geometry_area", "Similarity and scale factor"),
            ("geometry_area", "Analytic geometry and coordinate proofs"),
            ("algebra_linear", "Slope from points"),
        ]
    if unit_code == "geometry_preview_capstone":
        return [
            ("geometry_area", "Circumference and area of circles"),
            ("geometry_area", "Pythagorean theorem"),
            ("geometry_area", "Coordinate geometry distance and midpoint"),
            ("geometry_area", "Transformations and congruence"),
            ("geometry_area", "Similarity and scale factor"),
        ]
    if subskill is not None:
        return [(skill, subskill)]
    return [(skill, None)]


def _targets_for_task(task) -> list[tuple[str, str | None]]:
    remediation = summer_program.remediation_targets_for_task(task)
    base = _targets_for_unit(task.unit_code, task.skill, task.subskill, task.task_kind)
    if not remediation:
        return base
    merged: list[tuple[str, str | None]] = list(remediation)
    for item in base:
        if item not in merged:
            merged.append(item)
    return merged


def _scaffolded_question(skill: str, subskill: str | None, seed: int) -> Question | None:
    if subskill == "Integer and fraction fluency":
        start = 8 + seed
        move = 3 + seed
        result = start - move
        return Question(
            skill="pre_algebra",
            prompt=f"Evaluate {start} + (-{move}).",
            correct_answer=str(result),
            explanation="Adding a negative moves left on the number line.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is {start} - {move}?", expected_answer=str(result), hint="Adding a negative is the same move as subtracting."),
                ScaffoldStep(prompt=f"So what is {start} + (-{move})?", expected_answer=str(result), hint="Use the subtraction result."),
            ],
        )
    if subskill == "Order of operations":
        left = 4 + seed
        right = 3
        multiplier = 2 + (seed % 3)
        group_value = left + right
        result = group_value * multiplier
        return Question(
            skill="pre_algebra",
            prompt=f"Evaluate ({left} + {right}) x {multiplier}.",
            correct_answer=str(result),
            explanation="Grouped work happens before multiplication.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is inside the parentheses: {left} + {right}?", expected_answer=str(group_value), hint="Do grouped work first."),
                ScaffoldStep(prompt=f"What is {group_value} x {multiplier}?", expected_answer=str(result), hint="Now multiply the grouped value."),
            ],
        )
    if subskill == "Expressions and variables":
        coeff = 2 + (seed % 4)
        x_value = 3 + seed
        bias = 4 + seed
        product = coeff * x_value
        result = product + bias
        return Question(
            skill="pre_algebra",
            prompt=f"Evaluate {coeff}x + {bias} when x = {x_value}.",
            correct_answer=str(result),
            explanation="Substitute the value for x, then simplify.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is {coeff} x {x_value}?", expected_answer=str(product), hint="Replace x with the given value."),
                ScaffoldStep(prompt=f"What is {product} + {bias}?", expected_answer=str(result), hint="Finish the expression after multiplying."),
            ],
        )
    if subskill == "Exponents, roots, and scientific notation":
        base = 3 + seed
        result = base * base
        return Question(
            skill="pre_algebra",
            prompt=f"Evaluate {base}^2.",
            correct_answer=str(result),
            explanation="An exponent of 2 means multiply the base by itself.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What multiplication does {base}^2 mean?", expected_answer=f"{base} x {base}", hint="The exponent tells how many copies of the base to multiply."),
                ScaffoldStep(prompt=f"What is {base} x {base}?", expected_answer=str(result), hint="Now multiply the two copies."),
            ],
        )
    if subskill == "One-step equations":
        solution = 4 + seed
        offset = 5 + seed
        rhs = solution + offset
        return Question(
            skill="pre_algebra",
            prompt=f"Solve for x: x + {offset} = {rhs}",
            correct_answer=str(solution),
            explanation="Undo the addition to isolate x.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is {rhs} - {offset}?", expected_answer=str(solution), hint="Undo the addition first."),
                ScaffoldStep(prompt="Now what is x?", expected_answer=str(solution), hint="After undoing the addition, the remaining value is x."),
            ],
        )
    if subskill == "Two-step equations and inequalities":
        solution = 3 + seed
        coeff = 2 + (seed % 3)
        bias = 3 + seed
        rhs = coeff * solution + bias
        return Question(
            skill="pre_algebra",
            prompt=f"Solve for x: {coeff}x + {bias} = {rhs}",
            correct_answer=str(solution),
            explanation="Undo the constant first, then divide by the coefficient.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is {rhs} - {bias}?", expected_answer=str(coeff * solution), hint="Subtract the constant from both sides."),
                ScaffoldStep(prompt=f"What is {coeff * solution} / {coeff}?", expected_answer=str(solution), hint="Now divide by the coefficient."),
            ],
        )
    if subskill == "Ratios, rates, and proportional relationships":
        unit_rate = 2 + seed
        quantity = 4 + seed
        return Question(
            skill="pre_algebra",
            prompt=f"If 1 notebook costs ${unit_rate}, how much do {quantity} notebooks cost?",
            correct_answer=str(unit_rate * quantity),
            explanation="Find the unit rate, then scale to the full quantity.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt="What is the cost of 1 notebook?", expected_answer=str(unit_rate), hint="The unit rate is already given."),
                ScaffoldStep(prompt=f"What is {unit_rate} x {quantity}?", expected_answer=str(unit_rate * quantity), hint="Multiply the unit rate by the number of notebooks."),
            ],
        )
    if subskill == "Percent problems":
        total = 40 + (seed * 10)
        return Question(
            skill="pre_algebra",
            prompt=f"What is 25% of {total}?",
            correct_answer=str(total // 4),
            explanation="A quarter is 25% of the whole.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is 10% of {total}?", expected_answer=str(total // 10), hint="Move one place to find 10%."),
                ScaffoldStep(prompt=f"What is 5% of {total}?", expected_answer=str(total // 20), hint="Half of 10% is 5%."),
                ScaffoldStep(prompt=f"Add 20% and 5% of {total}.", expected_answer=str(total // 4), hint="25% is 20% + 5%."),
            ],
        )
    if subskill == "Coordinate plane and function tables":
        x_value = 3 + seed
        slope = 2
        intercept = 1 + seed
        return Question(
            skill="pre_algebra",
            prompt=f"For y = {slope}x + {intercept}, what is y when x = {x_value}?",
            correct_answer=str((slope * x_value) + intercept),
            explanation="Use the rule on the input x to get the output y.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is {slope} x {x_value}?", expected_answer=str(slope * x_value), hint="Multiply the coefficient by x first."),
                ScaffoldStep(prompt=f"What is {(slope * x_value)} + {intercept}?", expected_answer=str((slope * x_value) + intercept), hint="Then add the intercept."),
            ],
        )
    if subskill == "Slope from points":
        x1 = seed
        y1 = 2 + seed
        x2 = x1 + 2
        slope = 3
        y2 = y1 + (slope * (x2 - x1))
        return Question(
            skill=skill if skill in {"algebra_linear", "algebra_1"} else "algebra_linear",
            prompt=f"Find the slope of the line through ({x1}, {y1}) and ({x2}, {y2}).",
            correct_answer=str(slope),
            explanation="Slope is rise over run.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is the change in y: {y2} - {y1}?", expected_answer=str(y2 - y1), hint="Subtract the y-values."),
                ScaffoldStep(prompt=f"What is the change in x: {x2} - {x1}?", expected_answer=str(x2 - x1), hint="Subtract the x-values."),
                ScaffoldStep(prompt=f"What is {(y2 - y1)}/{(x2 - x1)}?", expected_answer=str(slope), hint="Divide rise by run."),
            ],
        )
    if subskill == "Slope-intercept form":
        slope = 2 + (seed % 3)
        intercept = 4 + seed
        return Question(
            skill="algebra_1",
            prompt=f"In y = {slope}x + {intercept}, what is y when x = 0?",
            correct_answer=str(intercept),
            explanation="In y = mx + b, b is the starting output when x is 0.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is {slope} x 0?", expected_answer="0", hint="Any slope times zero gives zero."),
                ScaffoldStep(prompt=f"What is 0 + {intercept}?", expected_answer=str(intercept), hint="The leftover value is the y-intercept."),
            ],
        )
    if subskill == "Slope-intercept interpretation":
        slope = 2 + (seed % 3)
        intercept = 4 + seed
        x_value = 3
        return Question(
            skill="algebra_linear",
            prompt=f"For y = {slope}x + {intercept}, what is y when x = {x_value}?",
            correct_answer=str((slope * x_value) + intercept),
            explanation="The slope multiplies x, then the intercept shifts the output.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is {slope} x {x_value}?", expected_answer=str(slope * x_value), hint="Multiply slope by x first."),
                ScaffoldStep(prompt=f"What is {(slope * x_value)} + {intercept}?", expected_answer=str((slope * x_value) + intercept), hint="Then add the intercept."),
            ],
        )
    if subskill == "Graphing linear inequalities":
        slope = 2 + (seed % 3)
        intercept = 1 + seed
        x_value = 3
        boundary = (slope * x_value) + intercept
        return Question(
            skill="algebra_1",
            prompt=f"For y > {slope}x + {intercept}, at x = {x_value}, what boundary y-value should you compare against?",
            correct_answer=str(boundary),
            explanation="Find the boundary line value first; greater-than shades above that line.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is {slope} x {x_value}?", expected_answer=str(slope * x_value), hint="Evaluate the line rule at the given x-value."),
                ScaffoldStep(prompt=f"What is {(slope * x_value)} + {intercept}?", expected_answer=str(boundary), hint="This is the boundary y-value before shading."),
                ScaffoldStep(prompt="Does y > boundary shade above or below the line?", expected_answer="above", hint="Greater y-values are above the boundary line."),
            ],
        )
    if subskill == "Direct variation":
        constant = 2 + (seed % 5)
        x_value = 3 + (seed % 6)
        return Question(
            skill="algebra_linear",
            prompt=f"A direct variation has y = {constant}x. What is y when x = {x_value}?",
            correct_answer=str(constant * x_value),
            explanation="Direct variation multiplies every x-value by the same constant.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt="What is the constant of variation?", expected_answer=str(constant), hint="It is the number multiplying x."),
                ScaffoldStep(prompt=f"What is {constant} x {x_value}?", expected_answer=str(constant * x_value), hint="Multiply the constant by the x-value."),
            ],
        )
    if subskill == "Rate and unit-rate modeling":
        unit_rate = 3 + (seed % 6)
        quantity = 4 + (seed % 5)
        total = unit_rate * quantity
        return Question(
            skill="algebra_linear",
            prompt=f"{quantity} notebooks cost ${total}. What is the unit cost per notebook?",
            correct_answer=str(unit_rate),
            explanation="A unit rate tells what one item costs.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What total cost are you splitting?", expected_answer=str(total), hint="Use the full cost in the story."),
                ScaffoldStep(prompt=f"What is {total} / {quantity}?", expected_answer=str(unit_rate), hint="Divide total cost by number of notebooks."),
            ],
        )
    if subskill == "Word problems with linear models":
        starting = 5 + seed
        rate = 2 + (seed % 5)
        weeks = 3 + (seed % 6)
        return Question(
            skill="algebra_linear",
            prompt=f"A club starts with ${starting} and adds ${rate} each week. How much after {weeks} weeks?",
            correct_answer=str(starting + (rate * weeks)),
            explanation="Linear stories use a starting value plus the same change each step.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is {rate} x {weeks}?", expected_answer=str(rate * weeks), hint="Find the repeated weekly change."),
                ScaffoldStep(prompt=f"What is {starting} + {(rate * weeks)}?", expected_answer=str(starting + (rate * weeks)), hint="Add the starting amount."),
            ],
        )
    if subskill == "Functions":
        x_value = 2 + seed
        coeff = 2
        bias = 3 + seed
        return Question(
            skill="algebra_1",
            prompt=f"If f(x) = {coeff}x + {bias}, what is f({x_value})?",
            correct_answer=str((coeff * x_value) + bias),
            explanation="A function rule gives an output when you substitute the input.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is {coeff} x {x_value}?", expected_answer=str(coeff * x_value), hint="Apply the coefficient to the input."),
                ScaffoldStep(prompt=f"What is {(coeff * x_value)} + {bias}?", expected_answer=str((coeff * x_value) + bias), hint="Then add the constant term."),
            ],
        )
    if subskill == "Sequences":
        first = 4 + seed
        step = 3
        term_number = 5
        fourth_offset = term_number - 1
        return Question(
            skill="algebra_1",
            prompt=f"An arithmetic sequence starts at {first} and increases by {step}. What is term {term_number}?",
            correct_answer=str(first + (fourth_offset * step)),
            explanation="Add the common difference once for each step after the first term.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"How much total increase after {fourth_offset} steps of {step}?", expected_answer=str(fourth_offset * step), hint="Multiply the step size by the number of jumps."),
                ScaffoldStep(prompt=f"What is {first} + {(fourth_offset * step)}?", expected_answer=str(first + (fourth_offset * step)), hint="Add the increase to the first term."),
            ],
        )
    if subskill == "Linear equations & graphs":
        slope = 2 + (seed % 4)
        intercept = 1 + seed
        x_value = 3 + (seed % 5)
        return Question(
            skill="algebra_1",
            prompt=f"For y = {slope}x + {intercept}, find y when x = {x_value}.",
            correct_answer=str((slope * x_value) + intercept),
            explanation="A linear graph rule gives the y-value for each x-value.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is {slope} x {x_value}?", expected_answer=str(slope * x_value), hint="Apply the slope to the x-value."),
                ScaffoldStep(prompt=f"What is {(slope * x_value)} + {intercept}?", expected_answer=str((slope * x_value) + intercept), hint="Add the starting value after multiplying."),
            ],
        )
    if subskill == "Solving equations & inequalities":
        solution = 2 + seed
        coeff = 2 + (seed % 5)
        bias = 3 + seed
        rhs = (coeff * solution) + bias
        return Question(
            skill="algebra_1",
            prompt=f"Solve for x: {coeff}x + {bias} = {rhs}",
            correct_answer=str(solution),
            explanation="Undo the addition first, then undo the multiplication.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is {rhs} - {bias}?", expected_answer=str(rhs - bias), hint="Move the constant away from the variable term."),
                ScaffoldStep(prompt=f"What is {(rhs - bias)} / {coeff}?", expected_answer=str(solution), hint="Divide by the coefficient of x."),
            ],
        )
    if subskill == "Perimeter and missing sides":
        width = 3 + seed
        length = 7 + seed
        perimeter = 2 * (length + width)
        half_perimeter = perimeter // 2
        return Question(
            skill="geometry_area",
            prompt=f"A rectangle has perimeter {perimeter} and width {width}. What is its length?",
            correct_answer=str(length),
            explanation="Half the perimeter is one length plus one width.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is {perimeter} / 2?", expected_answer=str(half_perimeter), hint="A rectangle has two matching length-width pairs."),
                ScaffoldStep(prompt=f"What is {half_perimeter} - {width}?", expected_answer=str(length), hint="Subtract the known width to isolate the length."),
            ],
        )
    if subskill == "Area of triangles and parallelograms":
        base = 6 + seed
        height = 4
        return Question(
            skill="geometry_area",
            prompt=f"What is the area of a triangle with base {base} and height {height}?",
            correct_answer=str((base * height) // 2),
            explanation="Triangle area is one half of base times height.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is {base} x {height}?", expected_answer=str(base * height), hint="Find the rectangle/parallelogram area first."),
                ScaffoldStep(prompt=f"What is {(base * height)} / 2?", expected_answer=str((base * height) // 2), hint="A triangle is half of that area."),
            ],
        )
    if subskill == "Circumference and area of circles":
        radius = 3 + seed
        diameter = radius * 2
        circumference = diameter * 3
        return Question(
            skill="geometry_area",
            prompt=f"Using pi = 3, what is the circumference of a circle with radius {radius}?",
            correct_answer=str(circumference),
            explanation="Circumference is the distance around a circle.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is the diameter if the radius is {radius}?", expected_answer=str(diameter), hint="Diameter is two radii across."),
                ScaffoldStep(prompt=f"What is 3 x {diameter}?", expected_answer=str(circumference), hint="Using pi = 3, multiply pi by the diameter."),
            ],
        )
    if subskill == "Surface area and volume":
        length = 4 + seed
        width = 3 + seed
        height = 2 + seed
        base_area = length * width
        volume = base_area * height
        return Question(
            skill="geometry_area",
            prompt=f"What is the volume of a box with length {length}, width {width}, and height {height}?",
            correct_answer=str(volume),
            explanation="Volume counts cubic units inside a three-dimensional shape.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is the base area: {length} x {width}?", expected_answer=str(base_area), hint="Find one rectangular layer first."),
                ScaffoldStep(prompt=f"What is {base_area} x {height}?", expected_answer=str(volume), hint="Stack that base area through the height."),
            ],
        )
    if subskill == "Pythagorean theorem":
        scale = 2 + seed
        leg_a = 3 * scale
        leg_b = 4 * scale
        hypotenuse = 5 * scale
        return Question(
            skill="geometry_area",
            prompt=f"A 3-4-5 right triangle is scaled by {scale}. What is the hypotenuse?",
            correct_answer=str(hypotenuse),
            explanation="A scaled 3-4-5 triangle keeps the same side pattern.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is 3 x {scale}?", expected_answer=str(leg_a), hint="Scale the first leg."),
                ScaffoldStep(prompt=f"What is 4 x {scale}?", expected_answer=str(leg_b), hint="Scale the second leg."),
                ScaffoldStep(prompt=f"What is 5 x {scale}?", expected_answer=str(hypotenuse), hint="Scale the hypotenuse by the same factor."),
            ],
        )
    if subskill == "Coordinate geometry distance and midpoint":
        x1 = seed
        y1 = 2 + seed
        x2 = x1 + 4
        y2 = y1 + 6
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        return Question(
            skill="geometry_area",
            prompt=f"What is the midpoint of the segment from ({x1}, {y1}) to ({x2}, {y2})? Enter the y-coordinate.",
            correct_answer=str(mid_y),
            explanation="The midpoint averages the x-values and the y-values.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is ({y1} + {y2}) / 2?", expected_answer=str(mid_y), hint="Average the y-values to get the midpoint's y-coordinate."),
                ScaffoldStep(prompt=f"What is ({x1} + {x2}) / 2?", expected_answer=str(mid_x), hint="Average the x-values too, even though only the y-coordinate is graded."),
            ],
        )
    if subskill == "Transformations and congruence":
        x_value = 2 + seed
        y_value = 3 + seed
        dx = 4
        dy = 2 + (seed % 3)
        new_x = x_value + dx
        new_y = y_value + dy
        return Question(
            skill="geometry_area",
            prompt=f"Point ({x_value}, {y_value}) is translated right {dx} and up {dy}. What is the new x-coordinate?",
            correct_answer=str(new_x),
            explanation="A translation slides each coordinate by the same amount and preserves congruence.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is the new x-coordinate: {x_value} + {dx}?", expected_answer=str(new_x), hint="Right means add to x."),
                ScaffoldStep(prompt=f"What is the new y-coordinate: {y_value} + {dy}?", expected_answer=str(new_y), hint="Up means add to y."),
            ],
        )
    if subskill == "Similarity and scale factor":
        scale = 2 + (seed % 2)
        side = 3 + seed
        return Question(
            skill="geometry_area",
            prompt=f"A figure is dilated by scale factor {scale}. If the original side length is {side}, what is the new side length?",
            correct_answer=str(scale * side),
            explanation="A dilation multiplies every length by the scale factor.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt="What does the scale factor multiply?", expected_answer="side length", hint="It multiplies every length in the figure."),
                ScaffoldStep(prompt=f"What is {scale} x {side}?", expected_answer=str(scale * side), hint="Multiply the original length by the scale factor."),
            ],
        )
    if subskill == "Analytic geometry and coordinate proofs":
        x1 = seed
        y = 4 + seed
        length = 5
        x2 = x1 + length
        return Question(
            skill="geometry_area",
            prompt=f"A horizontal segment goes from ({x1}, {y}) to ({x2}, {y}). What is its length?",
            correct_answer=str(length),
            explanation="Coordinate proofs use equal coordinates and coordinate differences to prove lengths.",
            choices=None,
            visual=None,
            subskill=subskill,
            scaffold_steps=[
                ScaffoldStep(prompt=f"What is the change in x: {x2} - {x1}?", expected_answer=str(length), hint="Horizontal distance is the x-difference."),
                ScaffoldStep(prompt=f"What is the change in y: {y} - {y}?", expected_answer="0", hint="Equal y-values make the side horizontal."),
            ],
        )
    return None


def _task_label(task_kind: str) -> str:
    labels = {
        "lesson": "Lesson",
        "practice_a": "Practice A",
        "practice_b": "Practice B",
        "mixed_review": "Mixed Review",
        "checkpoint": "Checkpoint",
        "placement_assessment": "Placement",
        "midpoint_assessment": "Midpoint",
        "exit_assessment": "Exit",
    }
    return labels.get(task_kind, task_kind.replace("_", " ").title())


def _task_notes(task) -> dict[str, object]:
    try:
        raw = json.loads(task.notes_json or "{}")
    except json.JSONDecodeError:
        return {}
    return raw if isinstance(raw, dict) else {}


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
