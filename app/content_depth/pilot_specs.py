from __future__ import annotations


Target = tuple[str, str]

PILOT_TARGETS: frozenset[Target] = frozenset(
    {
        ("place_value", "Ones, tens, and hundreds identification"),
        ("place_value", "Compare numbers by place value"),
        ("add_subtract", "Single-digit addition"),
        ("add_subtract", "Single-digit subtraction"),
        ("add_subtract", "Missing addends"),
        ("add_subtract", "Word problems"),
        ("money", "Dollar-coin values"),
        ("financial_literacy", "Income, gifts, wants, and needs"),
        ("fractions", "Equivalent fractions"),
        ("data_displays", "Picture and bar graphs"),
        ("financial_literacy", "Budget percentages, net worth, interest, and incentives"),
        ("pre_algebra", "Two-step equations and inequalities"),
        ("algebra_linear", "Slope from points"),
        ("algebra_1", "Systems by elimination"),
        ("geometry_area", "Triangle congruence criteria"),
        ("data_analysis", "Sample inferences from displays"),
    }
)


MISCONCEPTIONS: dict[Target, tuple[tuple[str, str, str], tuple[str, str, str]]] = {
    ("place_value", "Ones, tens, and hundreds identification"): (
        ("digit_only", "You named the digit but ignored the value of its position.", "Say the number as hundreds, tens, and ones before naming the digit's value."),
        ("wrong_place", "You assigned the digit to a different place-value column.", "Start at the ones place on the right and move left one column at a time."),
    ),
    ("place_value", "Compare numbers by place value"): (
        ("ones_first", "You compared the ones before checking the higher-value places.", "Compare from the leftmost place and stop at the first difference."),
        ("digit_size_only", "You chose a large digit without considering which place it occupies.", "Name each digit's place value before deciding which whole number is greater."),
    ),
    ("add_subtract", "Single-digit addition"): (
        ("operation_choice", "You used an operation that separates groups instead of joining them.", "Act out both groups joining before writing the equation."),
        ("counting_slip", "The joining model is right, but the total was counted inaccurately.", "Count on from the larger addend once for each object in the smaller group."),
    ),
    ("add_subtract", "Single-digit subtraction"): (
        ("adds_instead", "You joined the quantities instead of removing a part from the whole.", "Act out the starting group, remove the named part, and count what remains."),
        ("reverses_parts", "You reversed the whole and the removed part.", "Write the starting whole first, then subtract the part that leaves."),
    ),
    ("add_subtract", "Missing addends"): (
        ("adds_whole", "You added the known part to the whole instead of finding the missing part.", "Treat the total as the whole and count up from the known part."),
        ("uses_known_part", "You repeated the known addend instead of finding the other part.", "Use subtraction to check which part completes the total."),
    ),
    ("add_subtract", "Word problems"): (
        ("wrong_relationship", "You selected an operation before identifying whether the story joins, separates, or compares.", "Name the story relationship first, then write its equation."),
        ("calculation_slip", "The story model is close, but the calculation does not match the quantities.", "Point to each quantity in the equation and recompute one step at a time."),
    ),
    ("money", "Dollar-coin values"): (
        ("coin_count_not_value", "You reported how many coins there are instead of what the coins are worth.", "Multiply the coin count by the cents value of one coin."),
        ("dollars_cents_scale", "You used a cents total as though it were the same number of dollars.", "Keep the unit visible: one dollar equals 100 cents."),
    ),
    ("financial_literacy", "Income, gifts, wants, and needs"): (
        ("gift_as_income", "You used an income label without checking whether the money or item was earned.", "Ask whether work earned it; if not, it may be a gift or a different kind of choice."),
        ("context_need_want", "You used a need-or-want label without using the situation, or used it for a different question.", "First name whether the question is about source, purpose, or a job skill; needs and wants depend on context."),
    ),
    ("fractions", "Equivalent fractions"): (
        ("one_part_scaled", "Only one part of the fraction was scaled, so its value changed.", "Multiply the numerator and denominator by the same nonzero number."),
        ("reciprocal_confusion", "The fraction was flipped instead of renamed.", "Keep the same numerator-to-denominator relationship while scaling both parts."),
    ),
    ("data_displays", "Picture and bar graphs"): (
        ("ignores_scale", "You counted symbols or bar marks without applying the graph scale.", "Read the key or axis interval before comparing values."),
        ("wrong_comparison", "You read the display but compared the wrong categories or operation.", "Point to each named category and write its value before calculating."),
    ),
    ("financial_literacy", "Budget percentages, net worth, interest, and incentives"): (
        ("wrong_financial_model", "The quantities were combined with the wrong financial model.", "Name the target first: percent of income, assets minus liabilities, or principal times rate times time."),
        ("percent_or_sign_error", "A percent, debt, or time factor was used with the wrong sign or scale.", "Convert percent to a decimal and treat liabilities as amounts subtracted from assets."),
    ),
    ("pre_algebra", "Two-step equations and inequalities"): (
        ("inverse_order", "The operations were undone in an order that did not isolate the variable.", "Undo the added or subtracted amount, then undo multiplication or division."),
        ("inequality_direction", "The boundary or inequality direction was interpreted incorrectly.", "Check the result in the original inequality and describe which side of the boundary works."),
    ),
    ("algebra_linear", "Slope from points"): (
        ("run_over_rise", "The slope ratio was inverted.", "Use change in y over change in x in the same point order."),
        ("coordinate_sign", "A coordinate order or subtraction sign changed between numerator and denominator.", "Write (y2-y1)/(x2-x1) before substituting values."),
    ),
    ("algebra_1", "Systems by elimination"): (
        ("does_not_eliminate", "The equations were combined before a variable had opposite coefficients.", "Scale if needed, then add equations so one variable becomes zero."),
        ("elimination_sign", "A sign or final division error changed the remaining variable.", "Write the combined equation explicitly before dividing by its coefficient."),
    ),
    ("geometry_area", "Triangle congruence criteria"): (
        ("invalid_criterion", "The facts establish similarity or an ambiguous case, not triangle congruence.", "Use only SSS, SAS, ASA, AAS, or HL when its conditions are satisfied."),
        ("correspondence_error", "The named sides or angles do not correspond in the same order.", "Mark matching vertices first, then read every pair in that order."),
    ),
    ("data_analysis", "Sample inferences from displays"): (
        ("biased_sample", "The conclusion treats a biased or convenience sample as representative.", "Check how the sample was selected before generalizing."),
        ("unscaled_proportion", "The sample count was copied without scaling its proportion to the population.", "Compute sample successes divided by sample size, then multiply by the population."),
    ),
}


WORKED_EXAMPLES: dict[Target, tuple[tuple[str, str, str, str], ...]] = {
    ("place_value", "Ones, tens, and hundreds identification"): (
        ("model", "In 116, what value does the hundreds digit have?", "Decompose 116 as 100 + 10 + 6; the hundreds digit contributes 100.", "100"),
        ("guided", "In 84, what value does the digit 8 have?", "The 8 is in the tens place, so it contributes 8 tens, or 80.", "80"),
        ("transfer", "In 57, what value does the digit 7 have?", "The 7 is in the ones place, so it contributes 7.", "7"),
    ),
    ("place_value", "Compare numbers by place value"): (
        ("model", "Which is greater: 104 or 98?", "Compare hundreds first; 104 has one hundred while 98 has none.", "104"),
        ("guided", "Which is greater: 72 or 69?", "The tens differ first: 7 tens is greater than 6 tens.", "72"),
        ("transfer", "Which is greater: 45 or 43?", "The tens match, so compare ones: 5 is greater than 3.", "45"),
    ),
    ("add_subtract", "Single-digit addition"): (
        ("model", "Mia has 4 red counters and 3 blue counters. How many altogether?", "Join the two groups: 4 + 3 = 7.", "7"),
        ("guided", "Use counting on to find 6 + 2.", "Start at 6 and count two steps: 7, 8.", "8"),
        ("transfer", "Find 5 + 4 without recounting the first group.", "Count on four times from 5.", "9"),
    ),
    ("add_subtract", "Single-digit subtraction"): (
        ("model", "There are 9 counters and 4 are removed. How many remain?", "Model the whole, remove 4, and count the 5 counters left.", "5"),
        ("guided", "Use counting back to find 8 - 3.", "Start at 8 and move back three steps: 7, 6, 5.", "5"),
        ("transfer", "Find 7 - 2 and check it with addition.", "7 - 2 = 5, and 5 + 2 returns to 7.", "5"),
    ),
    ("add_subtract", "Missing addends"): (
        ("model", "Complete 6 + ? = 10.", "The missing part is the distance from 6 to 10, so it is 4.", "4"),
        ("guided", "What number makes 8 + ? = 13 true?", "Count up from 8 to 13 or subtract 13 - 8.", "5"),
        ("transfer", "A box holds 12 items; 7 are visible. How many are hidden?", "The hidden part completes 7 + ? = 12, so 5 are hidden.", "5"),
    ),
    ("add_subtract", "Word problems"): (
        ("model", "Sam has 6 shells and finds 3 more. How many altogether?", "The story joins groups, so use 6 + 3 = 9.", "9"),
        ("guided", "Ten birds are on a fence and 4 fly away. How many remain?", "The story separates a part, so use 10 - 4 = 6.", "6"),
        ("transfer", "Mia has 12 cards and Leo has 7. How many more does Mia have?", "The story compares amounts, so use 12 - 7 = 5.", "5"),
    ),
    ("money", "Dollar-coin values"): (
        ("model", "How many cents is one dime worth?", "A dime has the fixed value of 10 cents.", "10 cents"),
        ("guided", "How many cents are three nickels worth?", "Each nickel is 5 cents, so 3 x 5 = 15 cents.", "15 cents"),
        ("transfer", "How many cents equal one dollar?", "One dollar is the same value as 100 cents.", "100 cents"),
    ),
    ("financial_literacy", "Income, gifts, wants, and needs"): (
        ("model", "Mia earns six dollars for raking leaves. Is the source income or a gift?", "Mia received the money for work, so the source is income.", "income"),
        ("guided", "Kai must walk to school in heavy rain and has no umbrella. Is an umbrella a need or want here?", "The rain and missing umbrella make it necessary in this situation, so it is a need.", "need"),
        ("transfer", "Which skill helps a librarian place books in the correct sections?", "Sorting helps the librarian organize books into their correct sections.", "sorting"),
    ),
    ("fractions", "Equivalent fractions"): (
        ("model", "Rename 1/2 using fourths.", "Split each half into two equal pieces: 1/2 = 2/4.", "2/4"),
        ("guided", "Complete 2/3 = ?/9.", "The denominator was multiplied by 3, so multiply the numerator by 3 too.", "6"),
        ("transfer", "Write a fraction equivalent to 3/5 with denominator 20.", "Scale both parts by 4.", "12/20"),
    ),
    ("data_displays", "Picture and bar graphs"): (
        ("model", "A picture graph has 3 stars and each star means 2 votes. How many votes?", "Apply the key: 3 x 2 = 6 votes.", "6"),
        ("guided", "A bar reaches 12 while another reaches 7. How many more?", "Compare the labeled values: 12 - 7.", "5"),
        ("transfer", "Choose a display for counts in four pet categories.", "A bar or keyed picture graph compares categorical counts.", "bar graph"),
    ),
    ("financial_literacy", "Budget percentages, net worth, interest, and incentives"): (
        ("model", "Assets are $900 and liabilities are $250. Find net worth.", "Net worth = assets - liabilities = 900 - 250.", "$650"),
        ("guided", "Find 20% of a $500 monthly income.", "Convert 20% to 0.20, then multiply by 500.", "$100"),
        ("transfer", "Find simple interest on $400 at 5% for 2 years.", "Use I = Prt = 400 x 0.05 x 2.", "$40"),
    ),
    ("pre_algebra", "Two-step equations and inequalities"): (
        ("model", "Solve 3x + 5 = 20.", "Subtract 5, then divide by 3: 3x = 15, so x = 5.", "5"),
        ("guided", "Solve 4x - 7 = 13.", "Add 7 to both sides, then divide by 4.", "5"),
        ("transfer", "Find the greatest integer x with 2x + 3 <= 12.", "2x <= 9, so x <= 4.5; the greatest integer is 4.", "4"),
    ),
    ("algebra_linear", "Slope from points"): (
        ("model", "Find the slope through (1, 2) and (4, 8).", "Slope = (8 - 2)/(4 - 1) = 6/3.", "2"),
        ("guided", "Find the slope through (0, 5) and (2, 1).", "Use change in y over change in x: (1 - 5)/(2 - 0).", "-2"),
        ("transfer", "A ramp rises 3 units over a run of 12. Find its slope.", "Rise/run = 3/12 = 1/4.", "1/4"),
    ),
    ("algebra_1", "Systems by elimination"): (
        ("model", "Solve x + y = 7 and x - y = 1.", "Add the equations: 2x = 8, so x = 4; then y = 3.", "(4, 3)"),
        ("guided", "Solve 2x + y = 8 and -2x + 2y = 1 for y.", "Add to eliminate x: 3y = 9.", "3"),
        ("transfer", "Two ticket counts and revenues form a system. What must happen before adding?", "Make one variable's coefficients opposites.", "opposite coefficients"),
    ),
    ("geometry_area", "Triangle congruence criteria"): (
        ("model", "Two side pairs and their included angles match. Name the criterion.", "The angle lies between the two known sides, so this is SAS.", "SAS"),
        ("guided", "Three corresponding side pairs match. Name the criterion.", "Three matching side pairs establish SSS.", "SSS"),
        ("transfer", "Three angles match. Does that prove congruence?", "AAA proves similarity, not equal size.", "no"),
    ),
    ("data_analysis", "Sample inferences from displays"): (
        ("model", "12 of 30 randomly sampled students prefer art. Estimate out of 100.", "Use the sample proportion: 12/30 = 0.4, then 0.4 x 100.", "40"),
        ("guided", "15 of 50 randomly sampled voters support a proposal. Estimate out of 200.", "Scale 15/50 to the population of 200.", "60"),
        ("transfer", "A sports club poll is used to describe all students. Is that justified?", "No; the sampling group is biased toward sports-club members.", "no"),
    ),
}


def pilot_manifest_fields(skill: str, subskill: str, base_id: str) -> dict[str, object] | None:
    target = (skill, subskill)
    if target not in PILOT_TARGETS:
        return None
    misconception_rows = MISCONCEPTIONS[target]
    return {
        "content_status": "ready",
        "worked_example": {
            "title": f"Worked example: {subskill}",
            "steps": [
                {"stage": stage, "prompt": prompt, "explanation": explanation, "expected_answer": answer}
                for stage, prompt, explanation, answer in WORKED_EXAMPLES[target]
            ],
        },
        "misconceptions": [
            {
                "code": code,
                "feedback": feedback,
                "hint": hint,
                "recovery_archetype_id": f"{base_id}.concept" if index == 0 else f"{base_id}.procedure",
            }
            for index, (code, feedback, hint) in enumerate(misconception_rows)
        ],
    }
