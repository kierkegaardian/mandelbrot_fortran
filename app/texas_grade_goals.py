from __future__ import annotations

from dataclasses import dataclass


TEA_MATH_TEKS_URL = "https://tea.texas.gov/laws-and-rules/texas-administrative-code/19-tac-chapter-111"
ELEMENTARY_TEKS_URL = "https://tea.texas.gov/laws-and-rules/sboe-rules-tac/sboe-tac-currently-effect/ch111a-0.pdf"
MIDDLE_SCHOOL_TEKS_URL = "https://tea.texas.gov/laws-and-rules/sboe-rules-tac/sboe-tac-currently-effect/ch111b.pdf"


@dataclass(frozen=True)
class TexasGoal:
    code: str
    label: str
    standard_refs: tuple[str, ...]
    skill: str | None
    subskills: tuple[str, ...]
    mental_model: str
    quiz_level: int = 1
    stretch: bool = False

    @property
    def quiz_ready(self) -> bool:
        return self.skill is not None


@dataclass(frozen=True)
class TexasGradePlan:
    grade: int
    tac_section: str
    source_url: str
    focal_areas: tuple[str, ...]
    goals: tuple[TexasGoal, ...]

    @property
    def label(self) -> str:
        return f"Grade {self.grade}"

    @property
    def quiz_ready_count(self) -> int:
        return sum(1 for goal in self.goals if goal.quiz_ready)

    @property
    def gap_count(self) -> int:
        return sum(1 for goal in self.goals if not goal.quiz_ready)


def _g(
    code: str,
    label: str,
    refs: tuple[str, ...],
    skill: str | None,
    subskills: tuple[str, ...],
    mental_model: str,
    *,
    quiz_level: int = 1,
    stretch: bool = False,
) -> TexasGoal:
    return TexasGoal(code, label, refs, skill, subskills, mental_model, quiz_level, stretch)


TEXAS_GRADE_PLANS: tuple[TexasGradePlan, ...] = (
    TexasGradePlan(
        grade=1,
        tac_section="19 TAC 111.3",
        source_url=ELEMENTARY_TEKS_URL,
        focal_areas=("Place value", "Addition and subtraction", "Geometry and data", "Personal finance"),
        goals=(
            _g("g1_place_value", "Read, compare, and order numbers to 120", ("1.2", "1.5A-C"), "place_value", ("Ones, tens, and hundreds identification", "Compare numbers by place value"), "Numbers are built from groups of tens and leftover ones."),
            _g("g1_add_subtract", "Solve addition and subtraction problems within 20", ("1.3B-F", "1.5D"), "add_subtract", ("Single-digit addition", "Single-digit subtraction", "Missing addends", "Word problems"), "Addition joins or compares groups; subtraction finds what changed or what is missing."),
            _g("g1_money", "Identify coins and basic values", ("1.4",), "money", ("Dollar-coin values",), "Coins are named units that can be counted like other groups."),
            _g("g1_personal_finance", "Identify income, gifts, job skills, wants, and needs", ("1.9",), "financial_literacy", ("Income, gifts, wants, and needs",), "Money choices start by naming where money came from and whether a purchase is needed or wanted."),
            _g("g1_shapes", "Compose and describe two- and three-dimensional shapes", ("1.6", "1.7"), "geometry_shapes", ("2D shape attributes", "3D solid attributes", "Compose 2D shapes", "Equal shares of shapes"), "Shapes can be built, split, named, and compared by their attributes."),
            _g("g1_data", "Collect, sort, and interpret simple data displays", ("1.8",), "data_displays", ("Sort data into categories", "Picture and bar graphs", "Questions from data displays"), "Data displays turn sorted counts into pictures and bars that answer questions."),
        ),
    ),
    TexasGradePlan(
        grade=2,
        tac_section="19 TAC 111.4",
        source_url=ELEMENTARY_TEKS_URL,
        focal_areas=("Base-10 comparisons", "Addition/subtraction and multiplication foundations", "Geometry, measurement, and data", "Personal finance"),
        goals=(
            _g("g2_place_value", "Represent and compare numbers to 1,200", ("2.2", "2.7B"), "place_value", ("Ones, tens, and hundreds identification", "Expanded form", "Compare numbers by place value"), "A digit changes value when it moves to a different place."),
            _g("g2_fraction_units", "Partition objects into halves, fourths, and eighths", ("2.3",), "geometry_shapes", ("Equal shares of shapes",), "Fractions begin as equal shares: more same-size parts make each part smaller."),
            _g("g2_add_subtract", "Add and subtract within 1,000", ("2.4A-D", "2.7C"), "add_subtract", ("Borrowing and carrying basics", "Multi-digit regrouping", "Word problems"), "Regrouping keeps the same amount while trading between ones, tens, and hundreds."),
            _g("g2_multiply_foundation", "Model equal groups and repeated addition", ("2.6",), "multiply", ("Repeated addition", "Array and grid models"), "Equal-size groups are the bridge from counting to multiplication."),
            _g("g2_money", "Count coin collections up to one dollar", ("2.5",), "money", ("Dollar-coin values", "Making change"), "Coins are named units that can be counted and compared by value."),
            _g("g2_personal_finance", "Reason about saving, spending, borrowing, lending, and simple production costs", ("2.11",), "financial_literacy", ("Saving, spending, giving, borrowing, and lending", "Expenses, profit, savings options, and institutions"), "Saving, borrowing, lending, and producing all compare benefits with costs over time."),
            _g("g2_geometry", "Classify, compose, and decompose shapes and solids", ("2.8",), "geometry_shapes", ("2D shape attributes", "3D solid attributes", "Compose 2D shapes", "Equal shares of shapes"), "Shape attributes stay true even when a shape is turned, built, or split."),
            _g("g2_measurement", "Measure length and read time to the minute", ("2.9A-E", "2.9G"), "measurement", ("Length unit conversion", "Time reading and arithmetic"), "Measurement turns length and time into number lines with named units."),
            _g("g2_area_intro", "Cover rectangles with square units", ("2.9F",), "geometry_area", ("Area of rectangles and squares",), "Area counts the same-size squares that cover a surface without gaps."),
            _g("g2_data", "Use pictographs and bar graphs to solve problems", ("2.10",), "data_displays", ("Picture and bar graphs", "Questions from data displays"), "Graphs show category counts so questions can be answered from evidence."),
        ),
    ),
    TexasGradePlan(
        grade=3,
        tac_section="19 TAC 111.5",
        source_url=ELEMENTARY_TEKS_URL,
        focal_areas=("Place value", "Whole-number operations", "Fractions, measurement, and data", "Personal finance"),
        goals=(
            _g("g3_place_value", "Represent, compare, and order numbers to 100,000", ("3.2",), "place_value", ("Ones, tens, and hundreds identification", "Expanded form", "Compare numbers by place value"), "Large numbers are still built from place-value units that can be composed, decomposed, and compared."),
            _g("g3_operations", "Represent and solve multiplication and division within 100", ("3.4", "3.5B"), "multiply", ("Repeated addition", "Times tables", "Array and grid models"), "Multiplication and division describe the same equal-group structure from opposite directions."),
            _g("g3_fractions", "Represent, compare, and reason about fractions", ("3.3",), "fractions", ("Unit fractions", "Equivalent fractions", "Shaded region meaning", "Compare fractions and mixed numbers"), "A fraction names equal-size parts of one whole."),
            _g("g3_add_subtract", "Use place value for multi-step addition/subtraction problems", ("3.4A-B", "3.5A"), "add_subtract", ("Multi-digit regrouping", "Word problems"), "A multi-step problem is several smaller actions in sequence."),
            _g("g3_area_perimeter", "Use area and perimeter to solve geometry problems", ("3.6", "3.7A-B"), "geometry_area", ("Area of rectangles and squares", "Perimeter and missing sides"), "Area covers a surface; perimeter walks around its edge."),
            _g("g3_measurement", "Solve elapsed-time, capacity, and weight problems", ("3.7C-E",), "measurement", ("Elapsed time", "Capacity and weight units"), "Measurement questions start by naming the unit and then operating on the quantity."),
            _g("g3_data", "Represent and interpret scaled displays", ("3.8",), "data_displays", ("Picture and bar graphs", "Dot plots", "Frequency tables", "Questions from data displays"), "Scaled displays organize counts so comparisons and summaries are visible."),
            _g("g3_personal_finance", "Connect labor, scarcity, spending plans, credit, saving, and giving", ("3.9",), "financial_literacy", ("Income, gifts, wants, and needs", "Scarcity, planned spending, and credit choices", "Saving, spending, giving, borrowing, and lending"), "A financial choice has a source of income, a tradeoff, and sometimes a future repayment or saving goal."),
        ),
    ),
    TexasGradePlan(
        grade=4,
        tac_section="19 TAC 111.6",
        source_url=ELEMENTARY_TEKS_URL,
        focal_areas=("Operations", "Fractions and decimals", "Geometry, measurement, and data", "Personal finance"),
        goals=(
            _g("g4_rational_numbers", "Compare fractions and decimals with place-value models", ("4.2", "4.3"), "fractions", ("Equivalent fractions", "Fraction to decimal", "Compare fractions and mixed numbers"), "Fractions and decimals can name the same point on a number line."),
            _g("g4_multi_digit", "Use all four operations in multi-step problems", ("4.4", "4.5A"), "long_multiplication", ("Partial products", "Place-value breakdown", "Two-digit multiplies"), "Multi-digit operations work when every place value keeps its job."),
            _g("g4_measurement", "Convert units and solve measurement problems", ("4.8",), "measurement", ("Length unit conversion", "Metric and customary conversions", "Elapsed time", "Capacity and weight units"), "Measurement compares a quantity to a chosen unit."),
            _g("g4_geometry", "Classify figures and analyze area, perimeter, and angles", ("4.5C-D", "4.6", "4.7"), "geometry_area", ("Area of rectangles and squares", "Perimeter and missing sides", "Angles in lines and triangles"), "Geometry is a way to organize space by attributes and measures."),
            _g("g4_data", "Use frequency tables, dot plots, and stem-and-leaf plots", ("4.9",), "data_displays", ("Frequency tables", "Dot plots", "Stem-and-leaf plots", "Questions from data displays"), "Data displays keep counts and measurements organized for one- and two-step questions."),
            _g("g4_personal_finance", "Compare expenses, profit, savings choices, allowances, and financial institutions", ("4.10",), "financial_literacy", ("Expenses, profit, savings options, and institutions", "Saving, spending, giving, borrowing, and lending"), "Financial institutions and budgets help keep money safe, divide it by purpose, and compare profit with expense."),
        ),
    ),
    TexasGradePlan(
        grade=5,
        tac_section="19 TAC 111.7",
        source_url=ELEMENTARY_TEKS_URL,
        focal_areas=("Positive rational operations", "Expressions and formulas", "Area, volume, and data", "Personal finance"),
        goals=(
            _g("g5_rational_operations", "Compute with whole numbers, decimals, and fractions", ("5.2", "5.3"), "long_division", ("Division layout", "Quotient estimation", "Remainder handling"), "Operations on larger numbers still follow place-value and equal-group meaning."),
            _g("g5_expressions", "Generate and evaluate expressions and simple formulas", ("5.4",), "order_of_operations", ("Parentheses first", "Expression grouping", "Multiplication vs addition/subtraction"), "An expression is a reusable recipe for a number."),
            _g("g5_geometry_classify", "Classify two-dimensional figures by attributes", ("5.5",), "geometry_shapes", ("2D shape attributes",), "A figure can belong to nested groups when it shares defining attributes."),
            _g("g5_volume", "Use formulas for area, perimeter, and volume", ("5.4G-H", "5.6"), "geometry_area", ("Area of rectangles and squares", "Perimeter and missing sides", "Surface area and volume"), "Formulas organize repeated measurement into a reliable shortcut."),
            _g("g5_measurement", "Convert within customary and metric systems", ("5.7",), "measurement", ("Metric and customary conversions",), "A conversion factor tells how many smaller units match one larger unit."),
            _g("g5_coordinate_plane", "Graph first-quadrant ordered pairs from patterns", ("5.8",), "pre_algebra", ("Coordinate plane and function tables",), "Coordinates locate a paired input and output on perpendicular number lines."),
            _g("g5_data", "Represent and solve problems from grade-level data displays", ("5.9",), "data_displays", ("Frequency tables", "Dot plots", "Stem-and-leaf plots", "Scatterplots and paired data", "Questions from data displays"), "Different displays answer different data questions, but every answer must come from the represented values."),
            _g("g5_personal_finance", "Use taxes, payment methods, financial records, and simple budgets", ("5.10",), "financial_literacy", ("Taxes, payments, records, and simple budgets",), "A budget is a record-backed plan for balancing income, spending, taxes, and payment choices."),
            _g("g5_pre_algebra_stretch", "Preview ratios, rates, and algebraic structure", ("5.4",), "pre_algebra", ("Expressions and variables", "Ratios, rates, and proportional relationships"), "Patterns become algebra when the relationship is written clearly.", quiz_level=2, stretch=True),
        ),
    ),
    TexasGradePlan(
        grade=6,
        tac_section="19 TAC 111.26",
        source_url=MIDDLE_SCHOOL_TEKS_URL,
        focal_areas=("Number and operations", "Proportionality", "Expressions/equations", "Measurement/data and finance"),
        goals=(
            _g("g6_rational_numbers", "Use integers and rational numbers fluently", ("6.2", "6.3"), "integers", ("Signed numbers", "Negative arithmetic", "Absolute value"), "Rational numbers are points on a number line that can be compared and operated on."),
            _g("g6_proportionality", "Model ratios, rates, percents, and unit conversions", ("6.4", "6.5"), "pre_algebra", ("Ratios, rates, and proportional relationships", "Percent problems"), "A proportion says two changing quantities keep the same multiplicative relationship."),
            _g("g6_expressions", "Connect tables, graphs, equations, and inequalities", ("6.6", "6.7", "6.9", "6.10"), "pre_algebra", ("Expressions and variables", "One-step equations", "Coordinate plane and function tables"), "Algebra is a translation layer between words, tables, graphs, and symbols."),
            _g("g6_geometry_measurement", "Solve area and volume problems with rational dimensions", ("6.8",), "geometry_area", ("Area of triangles and parallelograms", "Area of trapezoids and composite figures", "Surface area and volume"), "Geometry measurement turns shapes into equations about area and volume."),
            _g("g6_coordinate_plane", "Graph ordered pairs in all four quadrants", ("6.11",), "pre_algebra", ("Coordinate plane and function tables",), "A coordinate pair names horizontal and vertical movement from the origin."),
            _g("g6_data_displays", "Represent and interpret numeric data displays", ("6.12A-B", "6.13A-B"), "data_analysis", ("Histograms", "Box plots", "Center, spread, and shape", "Variability in data"), "Data displays reveal center, spread, shape, and variability when read carefully."),
            _g("g6_data_summaries", "Summarize numeric and categorical data", ("6.12C-D",), "stats_mean", ("Mean", "Mean from display"), "Numerical summaries compress a data set while preserving its center and spread."),
            _g("g6_median_iqr", "Use median, range, and IQR to describe data spread", ("6.12C",), "data_analysis", ("Median, range, and IQR",), "Median and IQR describe the center and middle spread of an ordered data set."),
            _g("g6_categorical_percent", "Use relative frequency and percent summaries", ("6.12D",), "stats_percent", ("Percent word problems",), "Categorical summaries compare each category to the whole sample."),
            _g("g6_personal_finance", "Compare accounts, credit reports, college-payment options, and education-linked income", ("6.14",), "financial_literacy", ("Accounts, credit reports, and education income",), "Accounts and credit records connect today's transactions to future access, cost, and income choices."),
        ),
    ),
    TexasGradePlan(
        grade=7,
        tac_section="19 TAC 111.27",
        source_url=MIDDLE_SCHOOL_TEKS_URL,
        focal_areas=("Number and operations", "Proportionality", "Expressions/equations", "Measurement/data and finance"),
        goals=(
            _g("g7_rational_operations", "Add, subtract, multiply, and divide rational numbers fluently", ("7.2", "7.3"), "pre_algebra", ("Integer and fraction fluency",), "Signed fractions and decimals follow the same operation meanings as whole numbers."),
            _g("g7_proportionality", "Solve proportional relationships, percents, and unit-rate problems", ("7.4", "7.5"), "algebra_linear", ("Direct variation", "Rate and unit-rate modeling", "Word problems with linear models"), "The constant of proportionality is the steady multiplier linking two quantities."),
            _g("g7_linear_relationships", "Represent linear relationships with tables, graphs, and equations", ("7.7", "7.10", "7.11"), "algebra_linear", ("Slope from points", "Slope-intercept interpretation", "Systems of linear equations"), "A line shows a steady change: each step in x creates a predictable step in y."),
            _g("g7_similarity_circles", "Use similarity, scale drawings, and circle relationships", ("7.5", "7.8C", "7.9B-C"), "geometry_area", ("Similarity and scale factor", "Circumference and area of circles", "Area of trapezoids and composite figures"), "Scale and circle formulas compare parts of shapes through stable ratios.", quiz_level=2),
            _g("g7_volume_surface_area", "Solve volume and surface-area problems", ("7.8A-B", "7.9A", "7.9D"), "geometry_area", ("Surface area and volume",), "Three-dimensional measurement tracks how much space a solid holds and how much area covers it.", quiz_level=2),
            _g("g7_probability", "Model simple and compound probability", ("7.6A-E", "7.6H-I"), "stats_probability", ("Probability models",), "Probability compares favorable outcomes to all possible outcomes, then uses that ratio to predict.", quiz_level=2),
            _g("g7_data_comparisons", "Use samples and comparative displays to make inferences", ("7.6F-G", "7.12"), "data_analysis", ("Comparative dot and box plots", "Sample inferences from displays", "Part-to-whole display comparisons"), "A sample can support a claim only when its display, center, spread, and source are interpreted together.", quiz_level=2),
            _g("g7_personal_finance", "Calculate taxes, budget shares, net worth, interest, and incentives", ("7.13",), "financial_literacy", ("Taxes, payments, records, and simple budgets", "Budget percentages, net worth, interest, and incentives"), "Financial comparisons use percent, assets, liabilities, interest, and incentives to choose responsibly.", quiz_level=2),
            _g("g7_algebra1_stretch", "Preview Algebra 1 functions and sequences", ("7.7", "7.11"), "algebra_1", ("Functions", "Sequences", "Linear equations & graphs"), "A function is a rule that assigns exactly one output to each input.", quiz_level=2, stretch=True),
        ),
    ),
)

_PLAN_BY_GRADE = {plan.grade: plan for plan in TEXAS_GRADE_PLANS}


def texas_grade_plans() -> tuple[TexasGradePlan, ...]:
    return TEXAS_GRADE_PLANS


def texas_grade_plan(grade: int) -> TexasGradePlan:
    try:
        return _PLAN_BY_GRADE[int(grade)]
    except KeyError as exc:
        raise ValueError(f"Texas grade plan is only available for grades 1-7: {grade}") from exc


def quiz_ready_goals(grade: int) -> tuple[TexasGoal, ...]:
    return tuple(goal for goal in texas_grade_plan(grade).goals if goal.quiz_ready)


def content_gap_goals(grade: int) -> tuple[TexasGoal, ...]:
    return tuple(goal for goal in texas_grade_plan(grade).goals if not goal.quiz_ready)
