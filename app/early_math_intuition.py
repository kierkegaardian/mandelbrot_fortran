from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntuitionPack:
    mental_model: str
    common_mistake: str
    try_this: str


def _pack(mental_model: str, common_mistake: str, try_this: str) -> IntuitionPack:
    return IntuitionPack(mental_model=mental_model, common_mistake=common_mistake, try_this=try_this)


_INTUITION_BY_SKILL_SUBSKILL: dict[tuple[str, str], IntuitionPack] = {
    ("counting", "Number recognition"): _pack(
        "A numeral is a label for how many objects are in the set.",
        "Reading the symbol without connecting it to an actual quantity.",
        "Show 7 objects, hide the digit, then decide which numeral matches.",
    ),
    ("counting", "Skip-counting"): _pack(
        "Skip-counting is taking equal jumps instead of one-step counts.",
        "Changing jump size in the middle of the count.",
        "Count by 5s on your fingers: 5, 10, 15, 20.",
    ),
    ("counting", "Count-to-number matching"): _pack(
        "Each object gets one count word, and the last word tells the total.",
        "Double-counting one object or skipping one entirely.",
        "Touch each object once while saying the count out loud.",
    ),
    ("place_value", "Ones, tens, and hundreds identification"): _pack(
        "Digits change value because of where they sit, not just what they are.",
        "Thinking the 3 in 345 means 3 instead of 300.",
        "Say 482 as 4 hundreds, 8 tens, and 2 ones.",
    ),
    ("place_value", "Expanded form"): _pack(
        "Expanded form breaks a number into place-value pieces that add back together.",
        "Dropping a zero place and changing the total by accident.",
        "Rewrite 507 as 500 + 7, then rebuild the original number.",
    ),
    ("place_value", "Compare numbers by place value"): _pack(
        "Compare from the leftmost place where the numbers differ.",
        "Comparing the last digit first instead of the highest-value place.",
        "Compare 482 and 472 by checking hundreds, then tens.",
    ),
    ("place_value", "Decimal place value and comparison"): _pack(
        "Tenths and hundredths are smaller place-value buckets to the right of the decimal.",
        "Treating 0.5 as bigger than 0.45 just because 5 is bigger than 45.",
        "Rename 0.45 as 45 hundredths and compare it to 50 hundredths.",
    ),
    ("add_subtract", "Single-digit addition"): _pack(
        "Addition joins two small counts into one total.",
        "Counting the first group again instead of counting on from it.",
        "Start at 8 and count on 3 more: 9, 10, 11.",
    ),
    ("add_subtract", "Single-digit subtraction"): _pack(
        "Subtraction asks how much is left after some part is removed.",
        "Swapping the numbers because addition feels more familiar.",
        "Start at 9 and count back 4 steps on a number line.",
    ),
    ("add_subtract", "Borrowing and carrying basics"): _pack(
        "Carrying and borrowing are trades between place-value buckets.",
        "Moving a digit without noticing what value was regrouped.",
        "Explain why 10 ones can become 1 ten and back again.",
    ),
    ("add_subtract", "Word problems"): _pack(
        "The story tells whether quantities are being joined, compared, or separated.",
        "Grabbing numbers and operating before naming the relationship.",
        "Circle who has more, less, or how many altogether before solving.",
    ),
    ("add_subtract", "Missing addends"): _pack(
        "A missing addend is the part you need to reach the target total.",
        "Adding every number you see, even when one number is the whole.",
        "Ask, 'What do I add to 9 to make 14?'",
    ),
    ("add_subtract", "Multi-digit regrouping"): _pack(
        "Regrouping keeps the total the same while moving value between places.",
        "Forgetting that 1 ten equals 10 ones during the trade.",
        "Write 312 + 98 as 312 + 100 - 2 to see the regrouping idea.",
    ),
    ("multiply", "Repeated addition"): _pack(
        "Multiplication compresses equal additions into one rule.",
        "Using multiplication when the groups are not equal in size.",
        "Read 4 x 3 as 4 groups of 3, then list the repeated sum.",
    ),
    ("multiply", "Times tables"): _pack(
        "A fact family is a fast recall shortcut for equal groups.",
        "Memorizing digits without linking them to a group picture.",
        "Use 6 x 7 as 5 x 7 plus 1 x 7.",
    ),
    ("multiply", "Array and grid models"): _pack(
        "Rows and columns make equal groups visible all at once.",
        "Counting one row twice when reading the grid.",
        "Rotate a 3-by-4 array and notice the total stays 12.",
    ),
    ("multiply", "Simple product facts"): _pack(
        "A product is the total number of items in equal groups.",
        "Mixing up factors and the product in a fact family.",
        "Say which numbers are groups, items per group, and total.",
    ),
    ("multiply", "Multiplicative comparison and estimation"): _pack(
        "Times-as-many compares scaling, not just adding the same difference.",
        "Treating '3 times as many' like '3 more'.",
        "If one box has 6 and another has 3 times as many, picture 3 boxes of 6.",
    ),
    ("divide", "Equal sharing"): _pack(
        "Division answers how much each group gets in a fair share.",
        "Stopping before all the items are distributed.",
        "Share 12 counters into 3 bowls until every bowl matches.",
    ),
    ("divide", "Division as repeated subtraction"): _pack(
        "Each subtraction removes one full group of the divisor.",
        "Subtracting different-sized groups and still calling it division.",
        "Take away 4s from 20 until nothing is left.",
    ),
    ("divide", "Remainders"): _pack(
        "A remainder is what cannot make another full equal group.",
        "Forcing leftovers into a full group when they do not fit.",
        "Divide 14 by 3 and explain why 2 is leftover.",
    ),
    ("divide", "Inverse thinking"): _pack(
        "Division can be checked by asking what multiplication rebuilds the total.",
        "Forgetting to multiply back to see if the answer fits.",
        "Solve 24 ÷ 6, then ask what times 6 makes 24.",
    ),
    ("divide", "Remainder interpretation and estimation"): _pack(
        "A remainder changes meaning depending on the story: leftover, extra trip, or partial group.",
        "Reporting only the raw remainder without deciding what the context means.",
        "Ask whether the leftover gets ignored, kept, or forces one more group.",
    ),
    ("ratios", "Ratio language (to:of)"): _pack(
        "A ratio is a comparison recipe: for every this, there are that many of those.",
        "Treating a ratio like a subtraction sentence.",
        "Read 2:3 as '2 to 3' and say what each part counts.",
    ),
    ("ratios", "Equivalent ratios"): _pack(
        "Equivalent ratios tell the same story at a different scale.",
        "Changing only one side of the ratio and calling it equivalent.",
        "Double both parts of 3:5 and check that the comparison stays the same.",
    ),
    ("ratios", "Fractional comparison"): _pack(
        "A ratio can be read as a fraction when you want one part compared to another.",
        "Forgetting which quantity belongs in the numerator.",
        "Turn 4 girls to 6 boys into 4/6 and explain what it means.",
    ),
    ("ratios", "Unit rates and proportional relationships"): _pack(
        "A unit rate shrinks the comparison down to 'per 1' so scaling is easier.",
        "Comparing totals without first finding the per-1 amount.",
        "If 18 miles takes 3 hours, find the miles in 1 hour first.",
    ),
    ("fractions", "Unit fractions"): _pack(
        "A unit fraction names one equal piece of a whole.",
        "Using unequal pieces and still calling them fractional parts.",
        "Cut a bar into 5 equal parts and name one part as 1/5.",
    ),
    ("fractions", "Equivalent fractions"): _pack(
        "Equivalent fractions rename the same amount with different-sized pieces.",
        "Thinking a bigger denominator always means a bigger fraction.",
        "Shade 1/2 and 2/4 and check that the shaded amount matches.",
    ),
    ("fractions", "Shaded region meaning"): _pack(
        "The denominator sets the slice count; the numerator counts chosen slices.",
        "Counting shaded pieces when the whole is not split evenly.",
        "State the whole first, then count shaded equal pieces.",
    ),
    ("fractions", "Fraction to decimal"): _pack(
        "A decimal is another way to write a fraction using place value.",
        "Reading 0.25 as 25 wholes instead of 25 hundredths.",
        "Rename 1/4 as 25/100, then write 0.25.",
    ),
    ("fractions", "Compare fractions and mixed numbers"): _pack(
        "Compare using common piece sizes, common numerators, or benchmark values like 1/2 and 1.",
        "Comparing only numerators when denominators differ.",
        "Decide whether 5/8 is above or below 1/2 before comparing it further.",
    ),
    ("long_addition", "Column alignment"): _pack(
        "Long addition works because ones stay with ones and tens stay with tens.",
        "Sliding digits out of their place-value columns.",
        "Line up the rightmost digits before adding anything.",
    ),
    ("long_addition", "Carry handling"): _pack(
        "A carry is a regrouped ten, hundred, or thousand written in the next column.",
        "Writing the carry but forgetting to add it into the next place.",
        "Add the ones column and explain why 13 ones becomes 1 ten and 3 ones.",
    ),
    ("long_addition", "Multi-digit accuracy"): _pack(
        "Work one column at a time so each place-value decision stays clear.",
        "Rushing across the row and mixing column values together.",
        "Cover the finished columns and focus on one place at a time.",
    ),
    ("long_addition", "Place-value structure"): _pack(
        "The written algorithm is a place-value trade system, not a digit trick.",
        "Treating 300 + 40 + 7 like separate unrelated digits.",
        "Say each addend in expanded form before adding.",
    ),
    ("long_subtraction", "Borrowing"): _pack(
        "Borrowing is regrouping one larger place into 10 of the next smaller place.",
        "Crossing out digits without stating what value changed.",
        "Explain why 1 hundred can become 10 tens before subtracting.",
    ),
    ("long_subtraction", "Column alignment"): _pack(
        "Digits must stay in matching place columns for subtraction to mean anything.",
        "Subtracting tens from ones because the numbers were not lined up.",
        "Write both numbers with the ones place stacked on the right edge.",
    ),
    ("long_subtraction", "Crossing zero safely"): _pack(
        "Zeros can still lend value by borrowing from the next nonzero place to the left.",
        "Stopping when a zero cannot lend immediately.",
        "Work through 402 - 187 and say each regrouping trade out loud.",
    ),
    ("long_multiplication", "Partial products"): _pack(
        "Each row is one factor multiplied by one place of the other factor.",
        "Adding a row without noticing what place value it represents.",
        "Read 23 x 14 as 23 x 4 plus 23 x 10.",
    ),
    ("long_multiplication", "Place-value breakdown"): _pack(
        "Two-digit multiplication is multiplying tens and ones, then combining the parts.",
        "Forgetting the zero placeholder for a tens row.",
        "Split 34 into 30 and 4 before starting the algorithm.",
    ),
    ("long_multiplication", "Two-digit multiplies"): _pack(
        "The algorithm is a compact way to organize repeated place-value products.",
        "Treating the second digit as if it were ones when it is really tens.",
        "Estimate first so you know roughly where the final product should land.",
    ),
    ("long_division", "Division layout"): _pack(
        "The quotient goes above the place you are currently dividing.",
        "Dropping a quotient digit into the wrong column.",
        "Ask which place of the dividend you are working with before you write above it.",
    ),
    ("long_division", "Quotient estimation"): _pack(
        "Estimate how many divisor-sized groups fit before subtracting exactly.",
        "Guessing a quotient digit with no size check.",
        "Round 84 ÷ 6 to nearby easy facts before writing the digit.",
    ),
    ("long_division", "Remainder handling"): _pack(
        "A remainder is what stays after the largest possible full groups have been removed.",
        "Subtracting past zero because the quotient digit was too large.",
        "After each subtraction, check that the remainder is smaller than the divisor.",
    ),
    ("money", "Dollar-coin values"): _pack(
        "Money uses place value with units: dollars, dimes, nickels, pennies.",
        "Mixing coin names with their values.",
        "Make $1.37 with bills and coins in two different ways.",
    ),
    ("money", "Making change"): _pack(
        "Change is the difference between the cost and what was paid.",
        "Subtracting in the wrong direction and getting a negative change amount.",
        "Count up from the price to the amount paid instead of only subtracting.",
    ),
    ("money", "Budget-style totals"): _pack(
        "A budget total is just several small costs joined into one amount.",
        "Dropping cents when adding dollar amounts.",
        "Add two prices and say the cents total before converting past 100 cents.",
    ),
    ("money", "Place-value in currency"): _pack(
        "Cents are hundredths of a dollar, so 45 cents means 45/100 of a dollar.",
        "Treating $3.45 like 345 whole dollars.",
        "Rewrite $2.08 as 2 dollars and 8 hundredths of a dollar.",
    ),
    ("measurement", "Length unit conversion"): _pack(
        "Unit conversion is a scale change, not a new quantity.",
        "Multiplying when moving to a larger unit or dividing when moving smaller.",
        "Ask whether the answer should be more units or fewer units before computing.",
    ),
    ("measurement", "Time reading and arithmetic"): _pack(
        "Time uses base-60, so hours and minutes trade differently than place value.",
        "Adding minutes like base-10 digits and missing the 60-minute regroup.",
        "Convert the hours to minutes first, then combine.",
    ),
    ("measurement", "Capacity and weight units"): _pack(
        "Capacity and weight compare real quantities by choosing a unit such as cups, quarts, ounces, or pounds.",
        "Mixing the object being measured with the unit used to measure it.",
        "Name the unit first, then decide how many smaller units fit in one larger unit.",
    ),
    ("measurement", "Temperature basics"): _pack(
        "Temperature compares how hot or cold something is on a scale.",
        "Treating negative temperatures like impossible values.",
        "Decide whether -3 degrees is warmer or colder than 2 degrees.",
    ),
    ("measurement", "Metric and customary conversions"): _pack(
        "A conversion factor tells how many smaller units fit inside one larger unit.",
        "Using the wrong factor because the units sound similar.",
        "Say '12 inches in 1 foot' or '100 cm in 1 meter' before calculating.",
    ),
    ("measurement", "Elapsed time"): _pack(
        "Elapsed time is the distance between two clock times.",
        "Subtracting the hour numbers and ignoring the minutes.",
        "Jump to the next friendly time like the next hour, then finish the difference.",
    ),
    ("geometry_shapes", "2D shape attributes"): _pack(
        "A shape's defining attributes are the features that must stay true, such as sides and vertices.",
        "Sorting by size or color when the question asks what makes the shape itself.",
        "Pick a triangle in two sizes and explain why both are still triangles.",
    ),
    ("geometry_shapes", "3D solid attributes"): _pack(
        "A solid can be described by flat faces, curved surfaces, edges, and vertices.",
        "Counting a curved surface as a flat face.",
        "Hold a can, a box, and a ball; name which parts are flat and which are curved.",
    ),
    ("geometry_shapes", "Compose 2D shapes"): _pack(
        "Composing shapes means joining smaller shapes without gaps or overlaps to make a target shape.",
        "Leaving a gap between pieces and still counting it as the composed target.",
        "Use two squares to make a rectangle, then try another way to make a rectangle.",
    ),
    ("geometry_shapes", "Equal shares of shapes"): _pack(
        "Fair shares are equal-size parts of the same whole.",
        "Calling any two pieces halves even when one piece is larger.",
        "Fold a paper into two equal parts and then four equal parts; name the shares.",
    ),
    ("data_displays", "Sort data into categories"): _pack(
        "Data becomes useful when each item is placed in the right category before counting.",
        "Counting an item twice or putting it in the wrong category.",
        "Sort ten toys by color, then count how many are in each group.",
    ),
    ("data_displays", "Picture and bar graphs"): _pack(
        "A graph turns category counts into pictures or bars so differences are easier to see.",
        "Reading the tallest bar as the answer before checking what the question asks.",
        "Make a quick bar graph of three snack choices and point to the most popular one.",
    ),
    ("data_displays", "Dot plots"): _pack(
        "Each dot stands for one data value, stacked above its matching label or number.",
        "Counting the labels instead of counting the dots.",
        "Put one dot for each book read this week, then count the dots above each number.",
    ),
    ("data_displays", "Frequency tables"): _pack(
        "A frequency table pairs each category or value with how often it appeared.",
        "Adding labels instead of adding the frequency counts.",
        "Make a table of three snack choices and add the frequencies to check the total.",
    ),
    ("data_displays", "Stem-and-leaf plots"): _pack(
        "A stem-and-leaf plot keeps place value visible while listing many numbers compactly.",
        "Reading the stem or leaf alone instead of joining them into one number.",
        "Read stem 4 with leaves 2, 5, 8 as 42, 45, and 48.",
    ),
    ("data_displays", "Scatterplots and paired data"): _pack(
        "A scatterplot shows paired values, so each point answers both x and y at once.",
        "Reading only one coordinate and forgetting the pair.",
        "Plot (2, 6) and say what the 2 measures and what the 6 measures.",
    ),
    ("data_displays", "Questions from data displays"): _pack(
        "Graph questions ask you to read, compare, or combine the counts shown in the display.",
        "Answering from a favorite category instead of from the data.",
        "Ask 'how many more?' about two bars and solve by comparing their heights.",
    ),
    ("integers", "Signed numbers"): _pack(
        "The sign tells direction or side of zero, not just size.",
        "Ignoring the sign and comparing only the digits.",
        "Place -4 and 3 on a number line and say which is greater.",
    ),
    ("integers", "Negative arithmetic"): _pack(
        "Adding and subtracting signed numbers is movement on the number line.",
        "Treating minus signs as decoration instead of direction.",
        "Start at -2 and add 5 by moving right five steps.",
    ),
    ("integers", "Order-dependent operations"): _pack(
        "With negatives, operation order matters because each step changes the next input.",
        "Assuming subtraction and division behave like commutative operations.",
        "Compare 6 - (-2) with (-2) - 6 and explain the difference.",
    ),
    ("integers", "Absolute value"): _pack(
        "Absolute value is distance from zero, so it is always nonnegative.",
        "Thinking absolute value keeps the original sign.",
        "Explain why |-7| and |7| are both 7.",
    ),
    ("order_of_operations", "Parentheses first"): _pack(
        "Parentheses make a chunk that must be finished before the rest.",
        "Ignoring the grouped chunk and working left to right anyway.",
        "Evaluate (3 + 4) x 2 and say why the addition happens first.",
    ),
    ("order_of_operations", "Multiplication vs addition/subtraction"): _pack(
        "Multiplication and division build pieces before addition combines them.",
        "Adding first because it appears earlier in the line.",
        "Compare 3 + 2 x 5 with (3 + 2) x 5.",
    ),
    ("order_of_operations", "Expression grouping"): _pack(
        "A long expression is solved by simplifying one sensible chunk at a time.",
        "Trying to do every operation at once.",
        "Underline one chunk, simplify it, then rewrite the shorter expression.",
    ),
    ("order_of_operations", "Exponents in expressions"): _pack(
        "An exponent is repeated multiplication that belongs to its base before other operations.",
        "Reading 3^2 as 3 x 2 instead of 3 x 3.",
        "Evaluate 2 + 3^2 and explain why the square happens before addition.",
    ),
    ("pre_algebra", "Integer and fraction fluency"): _pack(
        "Pre-algebra fluency means small numeric skills stop blocking bigger ideas.",
        "Getting stuck on arithmetic details and losing the structure of the problem.",
        "Simplify one signed-number step and one fraction step before solving the full problem.",
    ),
    ("pre_algebra", "Order of operations"): _pack(
        "The order of operations keeps one expression from having many answers.",
        "Working left to right even when grouping changes the value.",
        "Rewrite the expression after each completed chunk.",
    ),
    ("pre_algebra", "Expressions and variables"): _pack(
        "A variable stands for a value, and the expression tells how to transform it.",
        "Plugging in the value before combining obvious like terms.",
        "Say what each part of 3x + 5 does to the input.",
    ),
    ("pre_algebra", "One-step equations"): _pack(
        "One-step equations are balances solved by one inverse move.",
        "Doing a move to only one side of the equation.",
        "Ask what single operation is trapping the variable.",
    ),
    ("pre_algebra", "Two-step equations and inequalities"): _pack(
        "Two-step problems untangle by undoing the outside operation before the inside one.",
        "Dividing first when a constant still needs to be removed.",
        "For 3x + 5 = 20, remove the 5 before dividing by 3.",
    ),
    ("pre_algebra", "Ratios, rates, and proportional relationships"): _pack(
        "Proportional relationships keep the same multiplier or same unit rate every time.",
        "Comparing totals instead of comparing per-1 amounts.",
        "Find the unit rate first, then scale to the new situation.",
    ),
    ("pre_algebra", "Percent problems"): _pack(
        "Percent means out of 100, so convert it to a decimal or fraction before solving.",
        "Moving the decimal without saying what percent means.",
        "Find 15% of 80 as 10% plus 5%.",
    ),
    ("pre_algebra", "Exponents, roots, and scientific notation"): _pack(
        "These ideas all track size changes efficiently: repeated factors, undoing squares, or powers of 10.",
        "Mixing the exponent with the coefficient or ignoring place value in scientific notation.",
        "Explain how 4^3, sqrt(16), and 3.2 x 10^4 each describe size.",
    ),
    ("pre_algebra", "Coordinate plane and function tables"): _pack(
        "Coordinates and tables show a rule pairing each input with one output.",
        "Reading x and y in the wrong order or changing the rule mid-table.",
        "Plot (2, 5), then say what happens when x increases by 1.",
    ),
}


def intuition_for(skill: str, subskill: str | None) -> IntuitionPack | None:
    if subskill is None:
        return None
    return _INTUITION_BY_SKILL_SUBSKILL.get((skill, subskill))
