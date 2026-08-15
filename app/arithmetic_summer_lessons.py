from __future__ import annotations

from dataclasses import dataclass


SUPPORTED_SUMMER_LESSON_SKILLS: frozenset[str] = frozenset(
    {
        "counting",
        "place_value",
        "add_subtract",
        "multiply",
        "divide",
        "fractions",
        "money",
        "measurement",
        "geometry_shapes",
        "data_displays",
        "pre_algebra",
    }
)


@dataclass(frozen=True)
class LessonStep:
    title: str
    prompt: str
    hint: str
    expected_answer: str | None
    presets: dict[str, int | str]


def supports_summer_lesson(skill: str) -> bool:
    return skill in SUPPORTED_SUMMER_LESSON_SKILLS


def build_summer_lesson(skill: str, *, subskill: str | None = None) -> list[LessonStep]:
    subskill_text = (subskill or "").strip().lower()
    if skill == "counting":
        return [
            LessonStep(
                title="Look Closely",
                prompt="Count each object once. The last count word tells the total.",
                hint="Point to each object and do not start over.",
                expected_answer=None,
                presets={"count_var": 7},
            ),
            LessonStep(
                title="Your Turn",
                prompt="How many objects are shown now?",
                hint="Count on your fingers or tap each object once.",
                expected_answer="9",
                presets={"count_var": 9},
            ),
            LessonStep(
                title="One More",
                prompt="Count this new set by yourself.",
                hint="Slow down and match one number word to one object.",
                expected_answer="12",
                presets={"count_var": 12},
            ),
        ]
    if skill == "place_value":
        return [
            LessonStep(
                title="Places Have Jobs",
                prompt="In 345, the 3 is worth 300 because it is in the hundreds place.",
                hint="Read the digit and its place together: 3 hundreds, 4 tens, 5 ones.",
                expected_answer=None,
                presets={"long_a_var": 345},
            ),
            LessonStep(
                title="Your Turn",
                prompt="In 482, what value does the 8 represent?",
                hint="The 8 is in the tens place, so think 8 tens.",
                expected_answer="80",
                presets={"long_a_var": 482},
            ),
            LessonStep(
                title="One More",
                prompt="In 507, what value does the 5 represent?",
                hint="The 5 is in the hundreds place, even though the tens digit is 0.",
                expected_answer="500",
                presets={"long_a_var": 507},
            ),
        ]
    if skill == "multiply":
        return [
            LessonStep(
                title="Equal Groups",
                prompt="This array has 3 rows of 4. Multiplication is equal groups.",
                hint="Rows are groups. Columns are items in each group.",
                expected_answer=None,
                presets={"rows_var": 3, "cols_var": 4},
            ),
            LessonStep(
                title="Your Turn",
                prompt="What is 4 x 3?",
                hint="Think 4 groups with 3 in each group.",
                expected_answer="12",
                presets={"rows_var": 4, "cols_var": 3},
            ),
            LessonStep(
                title="One More",
                prompt="Now solve 5 x 2.",
                hint="You can count by 2s: 2, 4, 6, 8, 10.",
                expected_answer="10",
                presets={"rows_var": 5, "cols_var": 2},
            ),
        ]
    if skill == "divide":
        return [
            LessonStep(
                title="Fair Sharing",
                prompt="12 objects shared into 3 equal groups means each group gets the same amount.",
                hint="Share one object to each group until you run out.",
                expected_answer=None,
                presets={"total_var": 12, "groups_var": 3},
            ),
            LessonStep(
                title="Your Turn",
                prompt="What is 15 / 3?",
                hint="How many objects end up in each equal group?",
                expected_answer="5",
                presets={"total_var": 15, "groups_var": 3},
            ),
            LessonStep(
                title="One More",
                prompt="Now solve 18 / 6.",
                hint="Ask how many fit in each group when the sharing is fair.",
                expected_answer="3",
                presets={"total_var": 18, "groups_var": 6},
            ),
        ]
    if skill == "fractions":
        return [
            LessonStep(
                title="Whole and Parts",
                prompt="The denominator tells how many equal parts there are. The numerator tells how many are shaded.",
                hint="Say the denominator first, then count the shaded pieces.",
                expected_answer=None,
                presets={"frac_num_var": 3, "frac_den_var": 4},
            ),
            LessonStep(
                title="Your Turn",
                prompt="What fraction is shaded?",
                hint="Count shaded parts over total equal parts.",
                expected_answer="2/5",
                presets={"frac_num_var": 2, "frac_den_var": 5},
            ),
            LessonStep(
                title="One More",
                prompt="What fraction is shaded now?",
                hint="Denominator is the whole split. Numerator is the shaded part.",
                expected_answer="5/8",
                presets={"frac_num_var": 5, "frac_den_var": 8},
            ),
        ]
    if skill == "money":
        return [
            LessonStep(
                title="Dollars and Cents",
                prompt="Money is place value. $2.35 means 2 dollars and 35 cents, or 235 cents total.",
                hint="Each dollar is 100 cents.",
                expected_answer=None,
                presets={"money_dollars_var": 2, "money_cents_var": 35},
            ),
            LessonStep(
                title="Your Turn",
                prompt="How many cents are in $4.20?",
                hint="4 dollars is 400 cents, then add 20 cents.",
                expected_answer="420",
                presets={"money_dollars_var": 4, "money_cents_var": 20},
            ),
            LessonStep(
                title="One More",
                prompt="How many cents are in $3.05?",
                hint="Do not drop the zero in the tens-of-cents place.",
                expected_answer="305",
                presets={"money_dollars_var": 3, "money_cents_var": 5},
            ),
        ]
    if skill == "measurement":
        if "time" in subskill_text or "elapsed" in subskill_text:
            return [
                LessonStep(
                    title="Hours to Minutes",
                    prompt="2 hours means 2 groups of 60 minutes.",
                    hint="Multiply the number of hours by 60.",
                    expected_answer=None,
                    presets={"long_a_var": 2, "long_b_var": 60},
                ),
                LessonStep(
                    title="Your Turn",
                    prompt="How many minutes are in 3 hours?",
                    hint="Think 3 groups of 60.",
                    expected_answer="180",
                    presets={"long_a_var": 3, "long_b_var": 60},
                ),
                LessonStep(
                    title="One More",
                    prompt="How many minutes are in 5 hours?",
                    hint="Count by 60s or multiply 5 x 60.",
                    expected_answer="300",
                    presets={"long_a_var": 5, "long_b_var": 60},
                ),
            ]
        if "metric" in subskill_text:
            return [
                LessonStep(
                    title="Meters to Centimeters",
                    prompt="1 meter means 100 centimeters, so 2 meters means 200 centimeters.",
                    hint="Multiply the meters by 100.",
                    expected_answer=None,
                    presets={"long_a_var": 2, "long_b_var": 100},
                ),
                LessonStep(
                    title="Your Turn",
                    prompt="How many centimeters are in 4 meters?",
                    hint="4 groups of 100.",
                    expected_answer="400",
                    presets={"long_a_var": 4, "long_b_var": 100},
                ),
                LessonStep(
                    title="One More",
                    prompt="How many centimeters are in 7 meters?",
                    hint="Multiply 7 by 100.",
                    expected_answer="700",
                    presets={"long_a_var": 7, "long_b_var": 100},
                ),
            ]
        return [
            LessonStep(
                title="Feet to Inches",
                prompt="1 foot means 12 inches, so 3 feet means 3 groups of 12 inches.",
                hint="Multiply the number of feet by 12.",
                expected_answer=None,
                presets={"long_a_var": 3, "long_b_var": 12},
            ),
            LessonStep(
                title="Your Turn",
                prompt="How many inches are in 5 feet?",
                hint="Think 5 groups of 12.",
                expected_answer="60",
                presets={"long_a_var": 5, "long_b_var": 12},
            ),
            LessonStep(
                title="One More",
                prompt="How many inches are in 7 feet?",
                hint="Count by 12s or multiply 7 x 12.",
                expected_answer="84",
                presets={"long_a_var": 7, "long_b_var": 12},
            ),
        ]
    if skill == "geometry_shapes":
        if "equal" in subskill_text or "share" in subskill_text:
            return [
                LessonStep(
                    title="Fair Shares",
                    prompt="Two halves must be the same size. Equal parts make the share fair.",
                    hint="Same whole, same-size pieces.",
                    expected_answer=None,
                    presets={"frac_num_var": 1, "frac_den_var": 2},
                ),
                LessonStep(
                    title="Your Turn",
                    prompt="If a rectangle is split into 4 equal parts, what are the parts called?",
                    hint="Four equal shares are fourths.",
                    expected_answer="fourths",
                    presets={"frac_num_var": 1, "frac_den_var": 4},
                ),
                LessonStep(
                    title="One More",
                    prompt="Are two pieces still halves if one piece is larger?",
                    hint="Halves must be equal.",
                    expected_answer="no",
                    presets={"frac_num_var": 1, "frac_den_var": 2},
                ),
            ]
        return [
            LessonStep(
                title="Attributes Matter",
                prompt="A triangle has 3 sides and 3 vertices. Size and color do not change the shape name.",
                hint="Count sides and corners.",
                expected_answer=None,
                presets={"geom_shape_var": "triangle"},
            ),
            LessonStep(
                title="Your Turn",
                prompt="How many sides does a rectangle have?",
                hint="Trace around the outside edge.",
                expected_answer="4",
                presets={"geom_shape_var": "rectangle"},
            ),
            LessonStep(
                title="One More",
                prompt="Two squares side by side can compose what shape?",
                hint="Look at the outside boundary after the pieces touch.",
                expected_answer="rectangle",
                presets={"geom_shape_var": "square"},
            ),
        ]
    if skill == "data_displays":
        return [
            LessonStep(
                title="Sort Before Counting",
                prompt="Data starts as items. Put each item into one category, then count each group.",
                hint="One item gets one mark.",
                expected_answer=None,
                presets={"mean_a_var": 3, "mean_b_var": 5, "mean_c_var": 2},
            ),
            LessonStep(
                title="Your Turn",
                prompt="A graph shows apples: 3, bananas: 5, oranges: 2. Which category has the most?",
                hint="Find the largest count.",
                expected_answer="bananas",
                presets={"mean_a_var": 3, "mean_b_var": 5, "mean_c_var": 2},
            ),
            LessonStep(
                title="One More",
                prompt="A dot plot has 4 dots above cats. How many cats were counted?",
                hint="Each dot stands for one item.",
                expected_answer="4",
                presets={"mean_a_var": 4, "mean_b_var": 1, "mean_c_var": 3},
            ),
        ]
    if skill == "pre_algebra":
        if "integer and fraction" in subskill_text or "fluency" in subskill_text:
            return [
                LessonStep(
                    title="Signed Numbers Have Direction",
                    prompt="On a number line, adding a negative means move left and subtracting a negative means move right.",
                    hint="Keep track of direction first, then total distance.",
                    expected_answer=None,
                    presets={"int_a_var": -3, "int_b_var": 5, "int_op1_var": "+", "int_op2_var": "+"},
                ),
                LessonStep(
                    title="Your Turn",
                    prompt="What is -6 + 9?",
                    hint="Start at -6 and move 9 spaces right.",
                    expected_answer="3",
                    presets={"int_a_var": -6, "int_b_var": 9, "int_op1_var": "+", "int_op2_var": "+"},
                ),
                LessonStep(
                    title="One More",
                    prompt="Write 3/4 as a decimal.",
                    hint="Divide the numerator by the denominator.",
                    expected_answer="0.75",
                    presets={"frac_num_var": 3, "frac_den_var": 4},
                ),
            ]
        if "percent" in subskill_text:
            return [
                LessonStep(
                    title="Percent Means Out of 100",
                    prompt="25% of 80 means 25 out of every 100 parts of 80.",
                    hint="Find 10%, then build up to 25%.",
                    expected_answer=None,
                    presets={"percent_value_var": 25, "percent_total_var": 80},
                ),
                LessonStep(
                    title="Your Turn",
                    prompt="What is 20% of 50?",
                    hint="10% of 50 is 5, so 20% is double that.",
                    expected_answer="10",
                    presets={"percent_value_var": 20, "percent_total_var": 50},
                ),
                LessonStep(
                    title="One More",
                    prompt="What is 15% of 60?",
                    hint="10% of 60 is 6 and 5% of 60 is 3.",
                    expected_answer="9",
                    presets={"percent_value_var": 15, "percent_total_var": 60},
                ),
            ]
        if "ratio" in subskill_text or "proport" in subskill_text:
            return [
                LessonStep(
                    title="Scale Both Parts",
                    prompt="A ratio stays the same when both parts scale together: 2:3 becomes 4:6.",
                    hint="Double both parts, not just one part.",
                    expected_answer=None,
                    presets={"ratio_a_var": 2, "ratio_b_var": 3},
                ),
                LessonStep(
                    title="Your Turn",
                    prompt="If 3 notebooks cost $6, how much do 6 notebooks cost?",
                    hint="Doubling the notebooks doubles the total cost.",
                    expected_answer="12",
                    presets={"ratio_a_var": 3, "ratio_b_var": 6},
                ),
                LessonStep(
                    title="One More",
                    prompt="If 4 cups of water use 2 scoops of mix, how many scoops are needed for 8 cups?",
                    hint="When one part doubles, the matched part doubles too.",
                    expected_answer="4",
                    presets={"ratio_a_var": 4, "ratio_b_var": 2},
                ),
            ]
        if "expression" in subskill_text or "variable" in subskill_text:
            return [
                LessonStep(
                    title="A Variable Stands for a Number",
                    prompt="In 3x + 2, x is a slot that can hold different numbers.",
                    hint="Substitute first, then simplify.",
                    expected_answer=None,
                    presets={"algebra_a_var": 3, "algebra_b_var": 2, "algebra_c_var": 11},
                ),
                LessonStep(
                    title="Your Turn",
                    prompt="If x = 4, what is 2x + 3?",
                    hint="Replace x with 4 before you calculate.",
                    expected_answer="11",
                    presets={"algebra_a_var": 2, "algebra_b_var": 3, "algebra_c_var": 11},
                ),
                LessonStep(
                    title="One More",
                    prompt="If x = 5, what is 4x - 1?",
                    hint="Multiply first, then subtract 1.",
                    expected_answer="19",
                    presets={"algebra_a_var": 4, "algebra_b_var": -1, "algebra_c_var": 19},
                ),
            ]
        if "one-step" in subskill_text:
            return [
                LessonStep(
                    title="Undo the One Thing",
                    prompt="If x + 5 = 11, undo the +5 so x stands alone.",
                    hint="Use the opposite operation on both sides.",
                    expected_answer=None,
                    presets={"algebra_a_var": 1, "algebra_b_var": 5, "algebra_c_var": 11},
                ),
                LessonStep(
                    title="Your Turn",
                    prompt="Solve x + 7 = 15. What is x?",
                    hint="Subtract 7 from both sides.",
                    expected_answer="8",
                    presets={"algebra_a_var": 1, "algebra_b_var": 7, "algebra_c_var": 15},
                ),
                LessonStep(
                    title="One More",
                    prompt="Solve 4x = 20. What is x?",
                    hint="Divide both sides by 4.",
                    expected_answer="5",
                    presets={"algebra_a_var": 4, "algebra_b_var": 0, "algebra_c_var": 20},
                ),
            ]
        if "two-step" in subskill_text or "inequal" in subskill_text:
            return [
                LessonStep(
                    title="Undo the Constant First",
                    prompt="In 3x + 4 = 19, subtract 4 before you divide by 3.",
                    hint="Peel away the outside operation first.",
                    expected_answer=None,
                    presets={"algebra_a_var": 3, "algebra_b_var": 4, "algebra_c_var": 19},
                ),
                LessonStep(
                    title="Your Turn",
                    prompt="Solve 2x + 6 = 18. What is x?",
                    hint="Subtract 6, then divide by 2.",
                    expected_answer="6",
                    presets={"algebra_a_var": 2, "algebra_b_var": 6, "algebra_c_var": 18},
                ),
                LessonStep(
                    title="One More",
                    prompt="Solve 5x - 5 = 20. What is x?",
                    hint="Add 5 first, then divide by 5.",
                    expected_answer="5",
                    presets={"algebra_a_var": 5, "algebra_b_var": -5, "algebra_c_var": 20},
                ),
            ]
        if "exponent" in subskill_text or "scientific" in subskill_text or "root" in subskill_text:
            return [
                LessonStep(
                    title="Exponents Are Repeated Multiplication",
                    prompt="3^2 means 3 x 3. A square root asks what number multiplied by itself gives the original value.",
                    hint="Match the notation to the repeated multiplication idea.",
                    expected_answer=None,
                    presets={"int_a_var": 3, "int_b_var": 2, "int_c_var": 0, "int_op1_var": "*", "int_op2_var": "*"},
                ),
                LessonStep(
                    title="Your Turn",
                    prompt="What is 2^4?",
                    hint="Multiply four 2s together.",
                    expected_answer="16",
                    presets={"int_a_var": 2, "int_b_var": 4, "int_c_var": 0, "int_op1_var": "*", "int_op2_var": "*"},
                ),
                LessonStep(
                    title="One More",
                    prompt="What is sqrt(49)?",
                    hint="Ask which number times itself gives 49.",
                    expected_answer="7",
                    presets={"int_a_var": 7, "int_b_var": 7, "int_c_var": 0, "int_op1_var": "*", "int_op2_var": "*"},
                ),
            ]
        if "coordinate" in subskill_text or "function" in subskill_text:
            return [
                LessonStep(
                    title="A Rule Turns x Into y",
                    prompt="A function table follows one rule every time. If y = 2x + 1, plug in x and follow the same steps.",
                    hint="Multiply by the coefficient, then add the intercept.",
                    expected_answer=None,
                    presets={"algebra_a_var": 2, "algebra_b_var": 1, "algebra_c_var": 9},
                ),
                LessonStep(
                    title="Your Turn",
                    prompt="If y = 3x + 2, what is y when x = 4?",
                    hint="Find 3 x 4 first, then add 2.",
                    expected_answer="14",
                    presets={"algebra_a_var": 3, "algebra_b_var": 2, "algebra_c_var": 14},
                ),
                LessonStep(
                    title="One More",
                    prompt="Point P is at (-5, 2). How far is it from the y-axis?",
                    hint="Distance from the y-axis is the absolute value of x.",
                    expected_answer="5",
                    presets={"algebra_a_var": -5, "algebra_b_var": 2, "algebra_c_var": 5},
                ),
            ]
        return [
            LessonStep(
                title="Make a Chunk First",
                prompt="Parentheses make one chunk. Solve that chunk before anything outside it.",
                hint="Inside first, then multiply or subtract.",
                expected_answer=None,
                presets={"int_a_var": 3, "int_b_var": 2, "int_c_var": 4, "int_op1_var": "+", "int_op2_var": "*", "order_shape_var": "(a op b) op c"},
            ),
            LessonStep(
                title="Your Turn",
                prompt="What is (6 + 3) x 2?",
                hint="Finish the parentheses first.",
                expected_answer="18",
                presets={"int_a_var": 6, "int_b_var": 3, "int_c_var": 2, "int_op1_var": "+", "int_op2_var": "*", "order_shape_var": "(a op b) op c"},
            ),
            LessonStep(
                title="One More",
                prompt="What is 8 - (3 x 2)?",
                hint="Multiply inside the chunk before subtracting.",
                expected_answer="2",
                presets={"int_a_var": 8, "int_b_var": 3, "int_c_var": 2, "int_op1_var": "-", "int_op2_var": "*", "order_shape_var": "a op (b op c)"},
            ),
        ]

    subtraction = (
        subskill_text.find("subtract") >= 0
        or subskill_text.find("missing") >= 0
        or subskill_text.find("word") >= 0
    )
    if subtraction:
        return [
            LessonStep(
                title="Take Away",
                prompt="Start with 9 and take away 4. Subtraction asks what is left.",
                hint="Count back or cover 4 objects.",
                expected_answer=None,
                presets={"a_var": 9, "b_var": 4, "op_var": "subtract"},
            ),
            LessonStep(
                title="Your Turn",
                prompt="What is 8 - 3?",
                hint="Start at 8 and count back 3 steps.",
                expected_answer="5",
                presets={"a_var": 8, "b_var": 3, "op_var": "subtract"},
            ),
            LessonStep(
                title="One More",
                prompt="Now solve 13 - 5.",
                hint="You can count back or think about the difference.",
                expected_answer="8",
                presets={"a_var": 13, "b_var": 5, "op_var": "subtract"},
            ),
        ]
    return [
        LessonStep(
            title="Put Together",
            prompt="8 and 5 make one larger total. Addition combines groups.",
            hint="Start at 8 and count on 5 more.",
            expected_answer=None,
            presets={"a_var": 8, "b_var": 5, "op_var": "add"},
        ),
        LessonStep(
            title="Your Turn",
            prompt="What is 6 + 7?",
            hint="Make a 10 first: 6 + 4 + 3.",
            expected_answer="13",
            presets={"a_var": 6, "b_var": 7, "op_var": "add"},
        ),
        LessonStep(
            title="One More",
            prompt="Now solve 9 + 4.",
            hint="Think 9 needs 1 more to make 10.",
            expected_answer="13",
            presets={"a_var": 9, "b_var": 4, "op_var": "add"},
        ),
    ]
