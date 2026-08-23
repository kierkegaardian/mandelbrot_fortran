from __future__ import annotations

from dataclasses import dataclass, replace

from .calculus_catalog import intuition_for as calculus_intuition_for
from .data_analysis import intuition_for as data_analysis_intuition_for
from .early_math_catalog import intuition_for as catalog_intuition_for
from .financial_literacy import intuition_for as financial_intuition_for
from .statistics_catalog import intuition_for as statistics_intuition_for


@dataclass(frozen=True)
class Explanation:
    how_short: str
    how_long: str
    why_short: str
    why_long: str
    mental_model: str = ""
    common_mistake: str = ""
    try_this: str = ""
    history: str = ""


FRACTAL_CONTROLS = (
    "Controls: Center (x,y) moves the view. Zoom narrows the window. "
    "Iterations add detail but take longer. Color frequency changes band spacing. "
    "Smooth blends bands. Cyclic repeats the palette."
)

FRACTAL_EXPLANATIONS = {
    "mandelbrot": Explanation(
        how_short="Drag to pan, scroll to zoom. Iterations add detail.",
        how_long=(
            "Equation: z_{n+1} = z_n^2 + c with z0 = 0, where c = x + i*y from each pixel. "
            "A point is in the set if |z| stays <= 2. "
            + FRACTAL_CONTROLS
        ),
        why_short="The image shows which points escape vs stay bounded.",
        why_long=(
            "Black points stay bounded; colored points escape, and the color shows how fast. "
            "The edge is the boundary between stable and escaping behavior, so tiny c changes "
            "flip the outcome. More iterations sharpen that boundary, and deeper zoom reveals "
            "self-similar spirals and filaments."
        ),
        history=(
            "Roots of this set trace back to early 1900s complex dynamics (Fatou and Julia). "
            "It was first drawn in 1978 by Robert W. Brooks and Peter Matelski, and Benoit "
            "Mandelbrot produced high-quality visualizations in 1980 at IBM, sparking wide interest."
        ),
    ),
    "julia": Explanation(
        how_short="Explore with zoom and pan; Julia uses a fixed c value.",
        how_long=(
            "Equation: z_{n+1} = z_n^2 + c, but c is fixed and each pixel is z0. "
            "This app uses c = -0.8 + 0.156i for now. "
            + FRACTAL_CONTROLS
        ),
        why_short="A Julia set maps stability for one fixed rule.",
        why_long=(
            "Each pixel is a starting value z0. If the orbit stays bounded, it is in the set; "
            "if it escapes, it is outside. Some c values make connected shapes; others produce "
            "dust-like islands, showing how sensitive the rule is. "
            "Changing c would reshape the whole picture."
        ),
        history=(
            "Named after Gaston Julia, who studied iteration of complex functions in 1918, "
            "alongside Pierre Fatou's early 1900s work on complex dynamics. "
            "Computer graphics later made Julia sets famous for their rich patterns."
        ),
    ),
    "ship": Explanation(
        how_short="Use iterations to sharpen the flame-like edges.",
        how_long=(
            "Equation: z_{n+1} = (|Re(z_n)| + i*|Im(z_n)|)^2 + c. "
            "The absolute values fold the plane each step. "
            + FRACTAL_CONTROLS
        ),
        why_short="Folding the plane makes sharp, symmetrical flames.",
        why_long=(
            "The absolute value step forces symmetry and sharp corners. "
            "Tiny changes in c create dramatic spikes and ridges, so the boundary is rich with detail. "
            "Higher iterations sharpen the flame ridges."
        ),
        history=(
            "First described and created by Michael Michelitsch and Otto E. Rossler in 1992. "
            "It became a popular example of how a small rule change creates a new fractal family."
        ),
    ),
    "tricorn": Explanation(
        how_short="Pan slowly; the patterns twist more than Mandelbrot.",
        how_long=(
            "Equation: z_{n+1} = conj(z_n)^2 + c. "
            "Conjugation flips rotation and creates mirrored spirals. "
            + FRACTAL_CONTROLS
        ),
        why_short="Conjugation flips the math, so spirals mirror and twist.",
        why_long=(
            "Replacing z with its conjugate changes rotation direction. "
            "The result is a three-cornered shape with strong symmetry and spiral arms. "
            "Zooming reveals repeated twists that differ from Mandelbrot."
        ),
        history=(
            "Sometimes called the Mandelbar set. It was introduced by W. D. Crowe, "
            "R. Hasson, P. J. Rippon, and P. E. D. Strain-Clark; their 1989 paper "
            "studied its structure."
        ),
    ),
    "multibrot": Explanation(
        how_short="Change the power slider to add more arms or petals.",
        how_long=(
            "Equation: z_{n+1} = z_n^p + c, where p is the power slider. "
            "Higher powers create more petals and sharper cusps. "
            + FRACTAL_CONTROLS
        ),
        why_short="Higher powers add more symmetry arms.",
        why_long=(
            "Power changes how quickly points rotate around the origin. "
            "That rotation shows up as extra arms and rotational symmetry. "
            "Lower powers look closer to Mandelbrot; higher powers add more lobes."
        ),
        history=(
            "A generalization of the Mandelbrot set using z^d + c with d >= 2. "
            "The name blends multiple and Mandelbrot, reflecting the family of powers."
        ),
    ),
    "celtic": Explanation(
        how_short="Zoom into the bright seams to find repeating knots.",
        how_long=(
            "Equation: z_{n+1} = (|Re(z_n^2)| + i*Im(z_n^2)) + c. "
            "Taking the absolute value of the real part folds one side. "
            + FRACTAL_CONTROLS
        ),
        why_short="Absolute value creates knot-like symmetry.",
        why_long=(
            "The folding step creates mirrored ridges that look like knots or woven lines. "
            "It's a small rule change with a big visual effect. "
            "More iterations sharpen the knot seams."
        ),
        history=(
            "A named variant in fractal art community formula collections, "
            "built from an absolute-value tweak to z^2 + c."
        ),
    ),
    "perpendicular": Explanation(
        how_short="Look for tall, upright structures when you zoom in.",
        how_long=(
            "Equation: z_{n+1} = (Re(z_n) + i*|Im(z_n)|)^2 + c. "
            "Keeping the imaginary part non-negative forces upright symmetry. "
            + FRACTAL_CONTROLS
        ),
        why_short="Forcing the imaginary part positive builds upright symmetry.",
        why_long=(
            "By keeping the imaginary side non-negative, the set stacks upward. "
            "That makes vertical towers and repeated ridges. "
            "Higher iterations bring out the stacked layers."
        ),
        history=(
            "Another named Mandelbrot variant in fractal art community formula collections, "
            "created by applying an absolute-value fold before squaring."
        ),
    ),
}


ARITHMETIC_MODE_EXPLANATIONS = {
    "counting": Explanation(
        how_short="Type a number or use +/− to change how many objects you see.",
        how_long="Pick an object style, then use the buttons or the number box to add or remove objects.",
        why_short="Counting matches a number to a group of objects.",
        why_long="When you can see the group, the number stops being just a symbol and starts meaning something real.",
        mental_model="Each object is one count. Touch each once, then stop when every object is matched.",
        common_mistake="Skipping objects or counting one object twice.",
        try_this="Show 7 objects, then hide 2. How many are still visible without recounting from 1?",
    ),
    "place_value": Explanation(
        how_short="Identify the value of each digit by its position in a number.",
        how_long="Every digit in a number has a place value: ones, tens, hundreds, thousands, and so on. The same digit means different amounts depending on where it sits.",
        why_short="Place value is the foundation for multi-digit arithmetic.",
        why_long="Understanding place value lets you parse big numbers, compare them, and perform operations like carrying and borrowing correctly.",
        mental_model="Think of each place as a bucket that can hold 0–9 items. When a bucket overflows past 9, it sends 1 to the next bucket on the left.",
        common_mistake="Confusing the digit itself with its place value (e.g., the 3 in 345 means 300, not 3).",
        try_this="Write 527 in expanded form: 500 + 20 + 7. Now swap the digits of 527 to make 725. How does each place value change?",
    ),
    "add_subtract": Explanation(
        how_short="Set the two numbers and choose add or subtract.",
        how_long="Use the number boxes to set A and B. Choose add or subtract and see the groups combine or shrink.",
        why_short="Adding puts groups together; subtracting takes part away.",
        why_long="Seeing the groups merge or shrink helps your brain feel what the numbers are doing.",
        mental_model="Addition grows a collection; subtraction removes from a collection.",
        common_mistake="Switching subtraction order and expecting the same result.",
        try_this="Start at 13 and subtract 5 by counting back. What number do you land on?",
    ),
    "multiply": Explanation(
        how_short="Pick rows and columns to build an array.",
        how_long="Set the number of rows and columns. The total objects show why multiplication is repeated groups.",
        why_short="Multiplication is equal groups repeated.",
        why_long="Arrays make multiplication visible: rows × columns = total.",
        mental_model="Rows are groups, columns are items per group.",
        common_mistake="Mixing unequal groups and still calling it multiplication.",
        try_this="Build 4 rows of 6. Now rotate it. Why is the total unchanged?",
    ),
    "divide": Explanation(
        how_short="Choose a total and how many groups to share.",
        how_long="Set the total objects and number of groups. The objects spread out evenly to show division.",
        why_short="Division shares a total into equal groups.",
        why_long="Seeing each group fill up makes the quotient feel like a fair share.",
        mental_model="Division asks: if we share fairly, how much per group?",
        common_mistake="Forgetting remainders when totals do not split evenly.",
        try_this="Share 14 into 4 groups. What is equal, and what is leftover?",
    ),
    "ratios": Explanation(
        how_short="Set A and B to compare two amounts.",
        how_long="Change A and B to see the ratio as bars or groups. This shows how two quantities compare.",
        why_short="A ratio compares two amounts side by side.",
        why_long="Ratios are about comparison, not just size. Seeing two bars makes that comparison clear.",
        mental_model="A ratio is a recipe, not a difference: 2:3 means every 2 of one thing travel with 3 of the other.",
        common_mistake="Comparing by subtraction when the situation depends on scaling.",
        try_this="Draw 2 blue and 3 red, then double both counts. Why do 2:3 and 4:6 tell the same story?",
    ),
    "fractions": Explanation(
        how_short="Pick a numerator and denominator to shade a circle.",
        how_long=(
            "The denominator tells how many equal slices each circle has. The numerator tells how many slices "
            "are shaded. If the numerator is larger than the denominator, extra circles appear to show the "
            "whole parts plus the remainder."
        ),
        why_short="Fractions describe parts of a whole.",
        why_long="Circles make it easy to see how much of the whole is shaded, even for improper fractions.",
        mental_model="Denominator sets the slice size; numerator counts selected slices.",
        common_mistake="Comparing numerators alone when denominators differ.",
        try_this="Which is larger: 3/8 or 1/2? Explain using equal-size slices.",
    ),
    "long_addition": Explanation(
        how_short="Type two numbers to see them stacked with carries.",
        how_long="Use the number boxes to build a long addition problem and watch the carry marks appear.",
        why_short="Long addition lines up place values.",
        why_long="Stacking digits keeps ones with ones and tens with tens. Carries show when a column reaches 10.",
        mental_model="Each column is a place-value bucket. When a bucket reaches 10, trade 10 ones for 1 ten, 10 tens for 1 hundred, and so on.",
        common_mistake="Carrying a digit mechanically without noticing it represents a regrouped ten or hundred.",
        try_this="Add 278 + 156 and say out loud when you trade 10 ones for 1 ten.",
    ),
    "long_subtraction": Explanation(
        how_short="Type two numbers to see borrowing in columns.",
        how_long="Use the number boxes to build a long subtraction problem and watch the borrow marks appear.",
        why_short="Long subtraction keeps place values aligned.",
        why_long="Borrowing lets you subtract a larger digit from a smaller one by taking 10 from the next column.",
        mental_model="Borrowing is regrouping: one ten becomes 10 ones, one hundred becomes 10 tens.",
        common_mistake="Crossing out digits without tracking which place value was actually changed.",
        try_this="Subtract 402 - 187 and explain how the 0 tens can still become 9 tens after regrouping.",
    ),
    "long_multiplication": Explanation(
        how_short="Type two numbers to see the stacked multiplication layout.",
        how_long="The view shows the traditional multiplication format with partial products when needed.",
        why_short="Long multiplication breaks the problem into place-value parts.",
        why_long="Each digit in the bottom number creates a partial product. Adding them gives the final result.",
        mental_model="Multiply by place value, not just digits: the 3 in 34 means 30, so its row must represent tens.",
        common_mistake="Forgetting the place-value shift for tens or hundreds in a partial product row.",
        try_this="Compute 23 x 14 as 23 x 4 plus 23 x 10. Where do those two rows show up in the algorithm?",
    ),
    "long_division": Explanation(
        how_short="Type a dividend and divisor to see the long division layout.",
        how_long="The quotient appears above the bar and the remainder is shown below if there is one.",
        why_short="Long division shows how many times a divisor fits into the dividend.",
        why_long="The layout connects repeated subtraction to the quotient and shows leftover as a remainder.",
        mental_model="Long division is repeated fitting: at each place, ask how many groups fit here, record it above, then subtract what you used.",
        common_mistake="Placing a quotient digit in the wrong place-value column.",
        try_this="Work 156 ÷ 12 and explain why the first quotient digit belongs in the tens place, not the ones place.",
    ),
    "money": Explanation(
        how_short="Enter dollars and cents to see a money breakdown.",
        how_long="The view shows bills and coins that make the total, using common US denominations.",
        why_short="Money turns numbers into real-world amounts.",
        why_long="Seeing bills and coins helps learners connect arithmetic to shopping and change-making.",
        mental_model="Money is place value with units attached: dollars are wholes and cents are hundredths of a dollar.",
        common_mistake="Mixing dollars and cents as if they were the same unit.",
        try_this="Compare $3.45 and 345 cents. Why are they equal, and what does the 45 mean in coin units?",
    ),
    "financial_literacy": Explanation(
        how_short="Practice money decisions such as saving, budgeting, credit, tax, and interest.",
        how_long=(
            "Financial literacy connects arithmetic and percent reasoning to personal decisions: income, gifts, "
            "needs, wants, saving, giving, borrowing, lending, budgets, accounts, credit, tax, and incentives."
        ),
        why_short="Personal finance turns math into daily choices.",
        why_long=(
            "Students need to reason about costs, tradeoffs, records, and future obligations so money choices are "
            "not just guesses or reactions."
        ),
        mental_model="Track where money comes from, where it goes, and what future promise or tradeoff is attached.",
        common_mistake="Treating all money events as simple spending without naming income, savings, debt, or records.",
        try_this="For one purchase, name the income source, tax or fee, payment method, and what you give up by buying it.",
    ),
    "measurement": Explanation(
        how_short="Convert between units and solve real-world measurement problems.",
        how_long="Practice converting lengths (inches/feet, cm/m), work with time (hours and minutes), and understand temperature scales.",
        why_short="Measurement connects numbers to the physical world.",
        why_long="Being fluent with measurement units means you can estimate distances, plan schedules, and understand weather reports without confusion.",
        mental_model="Each conversion factor is a multiplier: 12 inches per foot, 100 cm per meter, 60 minutes per hour. Multiply to go to smaller units, divide for larger.",
        common_mistake="Multiplying when you should divide (or vice versa) — always check whether you're going to a smaller or larger unit.",
        try_this="Convert 3 feet 6 inches to just inches. Then convert 150 cm to meters. Which direction did you multiply each time?",
    ),
    "geometry_shapes": Explanation(
        how_short="Name, sort, build, and split simple shapes.",
        how_long="Practice two-dimensional shape attributes, three-dimensional solids, composing shapes from smaller pieces, and fair shares.",
        why_short="Shape work builds spatial reasoning before formulas.",
        why_long="Young learners need to see that shapes are defined by attributes, can be combined into larger shapes, and can be partitioned into equal parts.",
        mental_model="A shape is a set of attributes: sides, vertices, faces, curves, and equal parts tell the story.",
        common_mistake="Sorting by color or size when the math question asks for defining attributes.",
        try_this="Make a rectangle from two squares, then name which attributes changed and which stayed true.",
    ),
    "data_displays": Explanation(
        how_short="Sort, graph, and answer questions from small data sets.",
        how_long="Use category counts, picture graphs, bar graphs, dot plots, and comparison questions to turn data into useful information.",
        why_short="Graphs help numbers tell a clear story.",
        why_long="Students learn to organize information, read counts from displays, and answer questions like most, fewest, total, and how many more.",
        mental_model="A data display is a counted story: first sort, then count, then compare what the display shows.",
        common_mistake="Answering from memory or preference instead of reading the graph carefully.",
        try_this="Ask three people their favorite fruit, make one mark for each answer, then point to the category with the most marks.",
    ),
    "data_analysis": Explanation(
        how_short="Analyze middle-school data displays such as histograms, box plots, and samples.",
        how_long=(
            "Practice histograms, box plots, center, spread, shape, variability, comparative displays, "
            "sample inference, and part-to-whole graph comparisons."
        ),
        why_short="Data analysis turns displays into justified conclusions.",
        why_long=(
            "Middle-school statistics asks students to read more than a count: they compare distributions, "
            "summarize center and spread, and decide what a sample can reasonably say about a population."
        ),
        mental_model="Read the display as a distribution: first find the center, then spread, then shape, then compare.",
        common_mistake="Answering from one high or low value instead of using the whole distribution.",
        try_this="For one box plot, name the median, IQR, and range before making a claim.",
    ),
    "integers": Explanation(
        how_short="Use negative numbers and see them move a point across a number line.",
        how_long="Build signed arithmetic expressions and watch values on a number line, where values left are negative and right are positive.",
        why_short="Negative values are the same arithmetic rules with values below zero.",
        why_long="Keeping sign and magnitude explicit prevents confusion and helps students reason with subtraction and addition.",
        mental_model="Use a number line: right is greater, left is smaller.",
        common_mistake="Treating minus sign as decoration instead of direction.",
        try_this="Start at -3 and add +7. Where do you end up on the line?",
    ),
    "order_of_operations": Explanation(
        how_short="Change the expression and see the operation order visually.",
        how_long="Parentheses are resolved first, then multiplication and division, then addition and subtraction.",
        why_short="Operator precedence makes answers consistent.",
        why_long="A clear order keeps students from getting different answers for the same expression.",
        mental_model="Resolve chunks: parentheses first, then multiply/divide, then add/subtract.",
        common_mistake="Computing strictly left-to-right for every expression.",
        try_this="Evaluate 3 + 2 * 5 two ways and explain why only one is valid.",
    ),
    "pre_algebra": Explanation(
        how_short="Blend arithmetic fluency with early equations, percent reasoning, and function-table habits.",
        how_long=(
            "Pre-algebra combines signed arithmetic, expressions, one- and two-step equations, "
            "proportional reasoning, percent work, scientific notation, and simple coordinate/function-table ideas."
        ),
        why_short="Pre-algebra is the bridge from arithmetic routines to algebraic thinking.",
        why_long=(
            "When learners can manage signs, operation order, percent structure, and variable rules reliably, "
            "later algebra feels like organized reasoning instead of memorized tricks."
        ),
        mental_model="Translate each problem into structure first: what is grouped, what is unknown, and what relationship stays constant.",
        common_mistake="Mixing arithmetic rules, variable rules, and percent/proportion setup in the same line of work.",
        try_this="Solve one equation, one percent problem, and one function-table rule, then explain what stayed the same in your setup.",
    ),
    "algebra_linear": Explanation(
        how_short="Set an equation and watch operations isolate x.",
        how_long="Use inverse steps on both sides to keep the equation balanced while removing constants and coefficients.",
        why_short="A balance stays true when both sides change equally.",
        why_long="If every operation is mirrored on both sides, the final x value is mathematically valid.",
        mental_model="Think of a scale: whatever you do to one side, do to the other.",
        common_mistake="Applying an operation to only one side of the equation.",
        try_this="Solve 2x + 5 = 17 with two mirrored steps.",
    ),
    "algebra_1": Explanation(
        how_short="Practice Algebra 1 modeling and equation habits with guided visuals.",
        how_long="Use the algebra workspace to rehearse balancing, linear structure, and symbolic manipulation used throughout Algebra 1.",
        why_short="Algebra 1 builds translation from words, tables, and graphs to equations.",
        why_long="When symbolic steps are consistent, students can solve unfamiliar word problems by modeling relationships instead of guessing.",
        mental_model="Represent a relationship first, then apply inverse operations and checks.",
        common_mistake="Treating each equation as a new trick instead of the same balancing rules.",
        try_this="Write one equation for a fixed fee plus per-item cost, then solve for the unknown quantity.",
    ),
    "algebra_2": Explanation(
        how_short="Extend to Algebra 2 structures: quadratics, exponentials, and function behavior.",
        how_long="Use the same symbolic discipline while tackling higher-order expressions and multi-step function reasoning.",
        why_short="Algebra 2 generalizes linear thinking to richer function families.",
        why_long="Mastering these patterns supports precalculus, data modeling, and standardized-test problem solving.",
        mental_model="Every new form is still a function with inputs, outputs, and transformation rules.",
        common_mistake="Manipulating symbols without checking domain restrictions or structure.",
        try_this="Compare a linear and exponential model for the same starting value and growth context.",
    ),
    "geometry_area": Explanation(
        how_short="Use shapes, coordinates, and measures to reason about geometry.",
        how_long=(
            "Practice geometry through transformations, similarity, circles, coordinate distance/slope, and "
            "measurement problems (area, perimeter, surface area, volume). Use diagrams first, then symbolic steps."
        ),
        why_short="Geometry connects visual structure to algebraic reasoning.",
        why_long=(
            "When you combine diagrams with equations, you can prove relationships, model real spaces, "
            "and solve coordinate-based problems with fewer mistakes."
        ),
        mental_model="Treat each figure as constraints: lengths, angles, and parallel/perpendicular relationships.",
        common_mistake="Jumping straight to formulas without labeling known relationships in the diagram.",
        try_this="Sketch a triangle pair, mark equal angles/sides first, then justify one similarity ratio.",
    ),
    "trig_right_triangle": Explanation(
        how_short="Start with right-triangle trig, then extend to full precalculus ideas.",
        how_long=(
            "Use opposite/adjacent/hypotenuse ratios as the foundation, then build toward unit-circle trig, "
            "identities, equations, vectors, matrices, conics, and modeling."
        ),
        why_short="Precalculus unifies functions, trig, algebra, and modeling tools.",
        why_long=(
            "Right-triangle ratios are the entry point; from there you can analyze periodic behavior, "
            "transformations, and advanced function relationships used before calculus."
        ),
        mental_model="Every trig expression is a function transformation or geometric relationship in disguise.",
        common_mistake="Memorizing identities without checking domain, period, or angle interpretation.",
        try_this="Convert a trig model to words: identify amplitude, midline, period, and phase shift.",
    ),
    "stats_percent": Explanation(
        how_short="Set total and percent to get a rate problem.",
        how_long="Convert the percent to decimal by dividing by 100 and multiply by the base value.",
        why_short="Percent is a scaled whole.",
        why_long="This keeps part-of problems in one multiplication workflow.",
        mental_model="Percent means per 100. Once you know the out-of-100 version, you can scale it to any total.",
        common_mistake="Moving the decimal or dropping the percent sign without changing the value correctly.",
        try_this="Find 15% of 80 by splitting it into 10% and 5%. Why does that mental shortcut work?",
    ),
    "stats_mean": Explanation(
        how_short="Enter a few values and average them.",
        how_long="Add all values, then divide by the count of values to get the mean.",
        why_short="Mean represents the equal-shares value.",
        why_long="The average is where values balance around the center if redistributed equally.",
        mental_model="The mean is the fair-share value: combine all the data, then redistribute it evenly.",
        common_mistake="Using the mean as the whole story when one extreme value is pulling it away from the typical case.",
        try_this="For 4, 6, and 20, compute the mean and then decide whether it feels representative of the set.",
    ),
    "stats_probability": Explanation(
        how_short="Set successful outcomes and total outcomes.",
        how_long="Probability is successful outcomes divided by equally likely outcomes.",
        why_short="Fractions naturally represent chances.",
        why_long="A numerator and denominator together describe likelihood without approximation.",
        mental_model="Probability is a fraction of the sample space: favorable outcomes over total equally likely outcomes.",
        common_mistake="Confusing one observed result with the long-run likelihood of that result.",
        try_this="A spinner has 3 blue, 1 red, and 2 green sections. What is P(not red), and how do you know?",
    ),
    "statistics": Explanation(
        how_short="Work from data collection to inference and uncertainty.",
        how_long="Use distributions, regression, probability, sampling distributions, and inference to answer questions with data instead of guesswork.",
        why_short="Statistics turns messy data into justified conclusions.",
        why_long="It helps learners separate signal from noise, evaluate claims, and quantify uncertainty instead of relying on anecdotes.",
        mental_model="Statistics is the story of data from three angles: how it was collected, what pattern it shows, and how confident you are the pattern is real.",
        common_mistake="Treating a graph, correlation, or p-value as proof without checking sampling method or variability.",
        try_this="Take a survey claim and ask three questions: who was sampled, what pattern do you see, and how strong is the evidence?",
    ),
    "calculus_1": Explanation(
        how_short="Move from average slope to instantaneous rate of change.",
        how_long="Compute slopes over intervals, then use derivative rules to evaluate rate of change at a point.",
        why_short="Calculus I explains how quantities change moment by moment.",
        why_long="Derivatives connect graphs, formulas, and real behavior like speed, optimization, and local approximation.",
        mental_model="Zoom in on a curve until it behaves like a line; that line's slope is the derivative.",
        common_mistake="Mixing average rate over an interval with derivative at a point.",
        try_this="Compare secant slope on [1,2] with derivative at x=1.5 for f(x)=x^2.",
    ),
    "calculus_2": Explanation(
        how_short="Accumulate change with integrals and series.",
        how_long="Build antiderivatives, evaluate definite integrals by bounds, and reason about sequence/series convergence.",
        why_short="Calculus II turns local rates into total accumulated change.",
        why_long="Integration and series power area, volume, probability accumulations, and approximation methods.",
        mental_model="Derivative is local slope; integral is total area/accumulation from those tiny changes.",
        common_mistake="Forgetting that definite integrals are upper-minus-lower after finding an antiderivative.",
        try_this="Integrate f(x)=2x+3 from x=0 to x=4 and interpret the result as accumulated quantity.",
    ),
    "calculus_3": Explanation(
        how_short="Extend calculus to multivariable and vector settings.",
        how_long="Use partial derivatives, gradients, and multivariable integrals to model surfaces and 3D fields.",
        why_short="Calculus III handles systems where outputs depend on several inputs.",
        why_long="It provides the tools for optimization on surfaces, flux, and geometry in higher dimensions.",
        mental_model="A gradient points in steepest ascent; partial derivatives are directional slices of a surface.",
        common_mistake="Treating other variables as changing while taking a partial derivative.",
        try_this="For f(x,y)=x^2+3xy, compute ∂f/∂x and ∂f/∂y at (1,2).",
    ),
    "sat_math": Explanation(
        how_short="Practice translating fast, mixed-domain problems into a solvable model.",
        how_long="SAT math rewards rapid structure recognition: identify the tested domain, represent the condition cleanly, and use answer choices or estimation when that is faster than brute-force algebra.",
        why_short="SAT Math is as much about decision-making as computation.",
        why_long="Strong students gain points by choosing efficient setups, spotting trap answers, and checking reasonableness under time pressure.",
        mental_model="Treat each problem like triage: classify it, build the smallest correct model, and choose the fastest reliable path.",
        common_mistake="Doing full algebra on every question when estimation, plugging in, or answer-choice elimination would be safer and faster.",
        try_this="Take one word problem and solve it two ways: full algebra and answer-choice elimination. Which method is better under a two-minute clock?",
    ),
    "psat_math": Explanation(
        how_short="Use PSAT-style algebra, geometry, and data reasoning with a setup-first approach.",
        how_long="PSAT math is mostly about translating cleanly from words or diagrams into equations, expressions, and proportional relationships without giving away points to careless mistakes.",
        why_short="PSAT Math rewards steady structure and accuracy.",
        why_long="Learners improve fastest when they slow down enough to define variables, track units, and use core algebra and geometry reliably.",
        mental_model="PSAT math is foundation work under light pressure: turn words into structure, then execute with calm, consistent steps.",
        common_mistake="Rushing because a problem looks easy and dropping a sign, label, or constraint.",
        try_this="Rewrite one word problem into an equation before computing anything. What becomes clearer once the structure is written down?",
    ),
    "gre_quant": Explanation(
        how_short="Blend arithmetic, algebra, geometry, and data reasoning with GRE-style comparison logic.",
        how_long="GRE Quant often rewards bounding, case analysis, estimation, and structural comparison more than long symbolic manipulation.",
        why_short="GRE Quant tests precision under ambiguity.",
        why_long="Many questions become easier when you compare cases, test assumptions, and decide what must be true before trying to compute an exact number.",
        mental_model="Start by asking what kind of claim the question is making, then use bounds, test cases, or comparison structure before doing heavy algebra.",
        common_mistake="Assuming a relationship is always true after checking only one convenient example.",
        try_this="For a comparison question, invent a positive, negative, and fractional test case. Does the relationship stay the same each time?",
    ),
    "calculus_slope": Explanation(
        how_short="Legacy alias for Calculus I slope/rate foundations.",
        how_long="This older label maps to Calculus I where slope is (y2 - y1)/(x2 - x1) and rates are derivatives.",
        why_short="Keeps older quiz/history data compatible.",
        why_long="Existing records using the old skill name still route to the same foundational calculus concepts.",
        mental_model="Treat this as Calculus I rate-of-change practice.",
        common_mistake="Assuming this is separate from Calculus I.",
        try_this="Use Calculus I presets for any new slope/rate practice.",
    ),
}

_GEOMETRY_SUBSKILL_INTUITION: dict[str, tuple[str, str, str]] = {
    "Area of rectangles and squares": (
        "Area counts equal-size square units covering a flat surface with no gaps or overlaps.",
        "Counting only the outside edge, which is perimeter, instead of the whole covered surface.",
        "Draw a 4 by 6 rectangle as rows and columns, then count why 4 * 6 gives the area.",
    ),
    "Area of triangles and parallelograms": (
        "Triangles and parallelograms both use base and perpendicular height; a triangle is half of its matching rectangle or parallelogram.",
        "Using the slanted side as height instead of the perpendicular distance to the base.",
        "Sketch a parallelogram, cut off one triangle, and slide it to make a rectangle with the same area.",
    ),
    "Area of trapezoids and composite figures": (
        "Composite area comes from decomposing a figure into known pieces, and trapezoids average the two bases before multiplying by height.",
        "Adding every side length when the problem asks for area, or forgetting to divide the trapezoid formula by 2.",
        "Split an L-shaped figure into two rectangles and write the two area products before adding.",
    ),
    "Perimeter and missing sides": (
        "Perimeter is the walking distance around the boundary; missing sides can be recovered from the total path length.",
        "Using area multiplication when the problem gives a perimeter total.",
        "For a rectangle with perimeter 30 and length 10, subtract the two lengths first, then split what remains.",
    ),
    "Circumference and area of circles": (
        "A circle has two linked measures: circumference wraps around it, while area covers the inside disk.",
        "Using radius and diameter interchangeably without doubling or halving first.",
        "For radius 5, compute 2*pi*r and pi*r^2 and explain which answer is around versus inside.",
    ),
    "Surface area and volume": (
        "Volume fills a 3D solid, while surface area wraps all outside faces.",
        "Giving a volume formula when the question asks for outside covering, or missing one pair of faces.",
        "For a 2 by 3 by 4 box, name the three face-pair areas before adding surface area.",
    ),
    "Pythagorean theorem": (
        "Right-triangle side lengths obey a square relationship: leg square plus leg square equals hypotenuse square.",
        "Putting the hypotenuse in the wrong place or adding the side lengths instead of their squares.",
        "Check the 3-4-5 triangle by comparing 3^2 + 4^2 with 5^2.",
    ),
    "Coordinate geometry distance and midpoint": (
        "Coordinate geometry turns a diagram into arithmetic: distance uses horizontal and vertical changes, midpoint averages endpoints.",
        "Averaging all four coordinates together instead of averaging x-values and y-values separately.",
        "Find the midpoint of (2, 5) and (8, 1), then explain which average gives the x-coordinate.",
    ),
    "Angles in lines and triangles": (
        "Angle facts are conservation rules: a straight line has 180 degrees, and a triangle's angles total 180 degrees.",
        "Adding known angles without first deciding whether they form a line, a triangle, or a vertical-angle pair.",
        "Draw a triangle with two known angles 50 and 65; use the 180-degree total to find the third.",
    ),
    "Triangle congruence criteria": (
        "Congruence criteria are proof shortcuts: enough matching sides and angles prove the whole triangles match.",
        "Using SSA as if it were a valid congruence shortcut, or naming parts that do not correspond.",
        "Compare SSS, SAS, ASA, AAS, and HL; say what information each shortcut needs before writing a proof.",
    ),
    "Transformations and congruence": (
        "Rigid transformations move a figure without changing size or shape, so corresponding lengths and angles stay equal.",
        "Changing the coordinates but forgetting that reflection flips orientation while preserving distance.",
        "Reflect point (4, -2) over the y-axis, then explain why the new point is still the same distance from the y-axis.",
    ),
    "Similarity and scale factor": (
        "Similar figures keep angle measures and multiply every corresponding length by the same scale factor.",
        "Adding the scale factor to side lengths instead of multiplying each corresponding length.",
        "If a triangle is scaled by 3, multiply two different side lengths and check that both ratios match.",
    ),
    "Analytic geometry and coordinate proofs": (
        "Coordinate proofs replace visual claims with slope, distance, midpoint, and shift calculations.",
        "Relying on how a diagram looks instead of proving a side length, slope, or midpoint from coordinates.",
        "Use coordinates to show opposite sides of a translated quadrilateral moved by the same horizontal and vertical shifts.",
    ),
}

_TRIG_SUBSKILL_INTUITION: dict[str, tuple[str, str, str]] = {
    "Right-triangle trig ratios": (
        "Sine, cosine, and tangent are side-ratio names tied to one acute angle in a right triangle.",
        "Choosing opposite or adjacent from the wrong angle's point of view.",
        "Label one acute angle, mark opposite/adjacent/hypotenuse, then write sin, cos, and tan before calculating.",
    ),
    "Unit circle trig values": (
        "The unit circle stores trig values as coordinates: cos(theta) is x and sin(theta) is y.",
        "Swapping sine and cosine, or forgetting that signs change by quadrant.",
        "Place 30, 45, and 60 degrees in quadrant I, then reflect them to predict signs in another quadrant.",
    ),
    "Trig functions and graphs": (
        "A trig graph repeats a wave; amplitude, period, midline, and phase shift describe how the wave was transformed.",
        "Mixing up amplitude with period because both affect the shape of the graph.",
        "For y = 3sin(2x), identify the amplitude first, then explain how the 2 changes the period.",
    ),
    "Trig identities": (
        "A trig identity is a reusable equivalence; it changes the form without changing the value.",
        "Applying an identity to an expression that does not actually match the identity's structure.",
        "Simplify sin^2(theta) + cos^2(theta), then check it with theta = 30 degrees.",
    ),
    "Inverse trig": (
        "Inverse trig returns an angle whose trig value matches the input inside a restricted output range.",
        "Ignoring the restricted range and choosing another angle with the same sine, cosine, or tangent.",
        "Find arcsin(1/2), then name a second angle with sine 1/2 that arcsin does not return.",
    ),
    "Vectors": (
        "A vector combines horizontal and vertical components into one directed move.",
        "Adding components to find magnitude instead of using the Pythagorean theorem.",
        "Draw vector <3, 4>, then explain why its length is 5 and not 7.",
    ),
    "Matrices and linear transformations": (
        "A transformation matrix is a coordinate rule that moves, scales, rotates, or shears every point consistently.",
        "Multiplying the wrong coordinate or treating matrix order as interchangeable.",
        "Apply a diagonal scale matrix to (2, -3) and say which coordinate each diagonal entry changes.",
    ),
    "Polar coordinates": (
        "Polar form locates a point by distance from the origin and angle from the positive x-axis.",
        "Using x or y as the radius instead of measuring distance from the origin.",
        "Convert (3, 4) to polar radius first, then estimate which quadrant the angle belongs in.",
    ),
}

_ALGEBRA_2_SUBSKILL_INTUITION: dict[str, tuple[str, str, str]] = {
    "Polynomial arithmetic": (
        "A polynomial is organized by powers of x; evaluation means substituting first, then simplifying power by power.",
        "Dropping signs or combining terms before matching the same power of x.",
        "Evaluate 2x^2 - 3x + 1 at x = -2 and track each term separately.",
    ),
    "Complex numbers": (
        "The imaginary unit repeats in a four-step cycle, so powers of i are pattern questions.",
        "Treating i like an ordinary variable instead of using i^2 = -1.",
        "Write i, i^2, i^3, and i^4, then predict i^10 from the cycle.",
    ),
    "Polynomial factorization": (
        "Factoring turns a polynomial into roots and building blocks; roots are the x-values that make the product zero.",
        "Finding numbers with the right product but the wrong sum for the middle coefficient.",
        "For x^2 - 5x + 6, name the two roots and check both make the polynomial zero.",
    ),
    "Polynomial division": (
        "Polynomial division removes a factor and leaves the quotient that behaves the same away from excluded inputs.",
        "Cancelling terms instead of cancelling common factors.",
        "Rewrite x^2 - 9 as a difference of squares before dividing by x - 3.",
    ),
    "Polynomial graphs": (
        "A polynomial graph's intercepts and end behavior come from its constant term, degree, and leading coefficient.",
        "Reading the y-intercept from a coefficient other than the value when x = 0.",
        "Set x = 0 in y = -2x^3 + 7 and explain why only the constant remains.",
    ),
    "Domain and range": (
        "Domain is the set of allowed inputs; denominators, even roots, and context can remove inputs.",
        "Solving the numerator equal to zero when the restriction actually comes from the denominator.",
        "For f(x) = 1/(x - 4), set the denominator equal to zero to find the excluded input.",
    ),
    "Inverse and composition": (
        "Composition chains functions, while an inverse reverses a function's input-output relationship.",
        "Composing in the wrong order or treating f^-1 as a reciprocal instead of a reverse rule.",
        "If f(x) = 2x + 3, find f(5), then use the inverse idea to get back to 5.",
    ),
    "Rational exponents and radicals": (
        "Rational exponents rewrite roots and powers in one notation: the denominator names the root.",
        "Multiplying by the fractional exponent instead of interpreting it as a root or power instruction.",
        "Rewrite 27^(1/3) as a cube-root question before evaluating.",
    ),
    "Exponential models": (
        "Exponential models use repeated multiplication by a fixed factor, so equal time steps have equal ratios.",
        "Adding the rate each step instead of multiplying by the growth or decay factor.",
        "Start at 80 and multiply by 1.25 twice; compare that with adding 25 percent twice.",
    ),
    "Logarithms": (
        "A logarithm asks for the exponent needed to build a number from a base.",
        "Treating log_b(x) like division by b instead of an exponent question.",
        "Translate log base 3 of 81 into the question: 3 to what power is 81?",
    ),
    "Transformations of functions": (
        "Function transformations move or stretch a parent graph by changing inputs and outputs in a predictable order.",
        "Applying outside shifts before handling the changed input inside parentheses.",
        "Compare f(x)=x^2 and g(x)=2(x-1)^2+3 at x=1 and x=2.",
    ),
    "Equations": (
        "Advanced equations still use inverse operations, but each move must preserve the solution set.",
        "Creating extraneous answers and not checking them in the original equation.",
        "Solve 4x - 7 = 17, then substitute your answer back into the original equation.",
    ),
    "Trigonometry": (
        "Algebra 2 trig connects side ratios and function values, using angle relationships as equations.",
        "Choosing a ratio before identifying opposite, adjacent, and hypotenuse from the angle.",
        "In a 3-4-5 triangle, write tan(theta) from opposite over adjacent before decimalizing.",
    ),
    "Modeling": (
        "A model is a function with a context; evaluating it means answering the context's question at a chosen input.",
        "Ignoring what the input and output units represent after doing the algebra.",
        "For R(x) = -2x^2 + 30x + 100, say what R(5) means before computing it.",
    ),
    "Rational expressions": (
        "Rational expressions are fractions made from algebraic factors; simplification cancels factors, not loose terms.",
        "Cancelling a piece of a sum instead of a full common factor.",
        "Factor (x+2)(x+5)/(x+2), cancel the matching factor, and name the restriction.",
    ),
    "Rational functions": (
        "A rational function behaves like an algebraic fraction, so the denominator controls holes and excluded inputs.",
        "Substituting into a denominator that becomes zero or forgetting to state that restriction.",
        "For f(x) = (2x+1)/(x-3), check the denominator before evaluating at x = 4.",
    ),
    "Sequences and series": (
        "Sequences list terms by position; series add those terms into an accumulated total.",
        "Using n instead of n - 1 for an arithmetic sequence that starts at term 1.",
        "List the first four terms of 5, 8, 11, ... and then add them as a short series.",
    ),
}

_ALGEBRA_1_SUBSKILL_INTUITION: dict[str, tuple[str, str, str]] = {
    "Algebra foundations": (
        "Algebra starts by treating expressions as number machines: simplify the machine before feeding in a value.",
        "Substituting a value before combining like terms, which makes the arithmetic longer and easier to misread.",
        "Simplify 4x - x + 6 first, then evaluate it at x = 3.",
    ),
    "Solving equations & inequalities": (
        "Solving means undoing operations in reverse while keeping both sides balanced.",
        "Changing one side of an equation or inequality without making the same legal move on the other side.",
        "Solve 3x - 5 = 16 by naming the last operation and undoing it first.",
    ),
    "Working with units": (
        "Units are labels that must travel with the numbers; conversion rewrites the same amount in a different unit.",
        "Dividing when the conversion calls for multiplying, or dropping units before checking whether they cancel.",
        "Convert 45 miles in 1.5 hours into miles per hour by writing distance divided by time.",
    ),
    "Linear equations & graphs": (
        "A linear equation has a steady step: each 1-step change in x changes y by the same amount.",
        "Treating the intercept as another step instead of the starting output when x is zero.",
        "For y = 2x + 3, make a tiny table for x = 0, 1, and 2 and look for the steady change.",
    ),
    "Forms of linear equations": (
        "Different line forms store the same line information in different places: slope, point, or intercept.",
        "Trying to read y = mx + b shortcuts from point-slope form before rewriting or substituting carefully.",
        "Use y - 4 = 3(x - 2) to find y when x = 2, then explain why that point is on the line.",
    ),
    "Slope from points": (
        "Slope measures how much y changes for each 1-step change in x; it is rise divided by run.",
        "Subtracting the coordinates in a different order for y than for x, which flips the sign.",
        "Use points (1, 2) and (4, 8); compute change in y and change in x before dividing.",
    ),
    "Slope-intercept form": (
        "In y = mx + b, m is the constant rate of change and b is where the line starts on the y-axis.",
        "Mixing up slope and y-intercept, or treating b as the x-intercept.",
        "For y = 3x - 5, name the slope and then say where the graph crosses the y-axis.",
    ),
    "Graphing linear inequalities": (
        "A linear inequality starts with a boundary line, then shades every point above or below that line.",
        "Shading before checking whether the inequality says greater-than or less-than.",
        "Graph y = 2x + 1 lightly, then test one point above it and one point below it.",
    ),
    "Systems of equations": (
        "A system is a set of clues that must all be true at the same time.",
        "Finding a value that satisfies one equation and stopping before checking the other equation.",
        "Test x = 2, y = 5 in x + y = 7 and x - y = -3 to see both clues agree.",
    ),
    "Systems by substitution": (
        "A substitution system gives two clues about the same point; replace one variable with its matching expression so only one unknown remains.",
        "Substituting into the wrong equation or forgetting that both equations must share the same x and y.",
        "If y = 2x + 1 and y = -x + 7, set the right sides equal before solving.",
    ),
    "Systems by elimination": (
        "Elimination combines two equations so one variable disappears, leaving a simpler one-variable equation.",
        "Adding or subtracting only one side of the equations, or missing that opposite coefficients cancel.",
        "For 3x + 2y = 14 and -3x + 5y = 7, add the equations and watch x disappear.",
    ),
    "Graphing systems and intersections": (
        "A graphed system is two lines on the same plane; the solution is the point where both lines pass through the same x and y.",
        "Reading where one line crosses an axis instead of where the two lines cross each other.",
        "Sketch y = x + 1 and y = -x + 5, then mark the point where the lines meet.",
    ),
    "Inequalities (systems & graphs)": (
        "Inequalities describe regions of possible answers; a system keeps only the overlap of all regions.",
        "Using the boundary line as the whole answer instead of checking which side or overlap is allowed.",
        "Sketch x > 1 and x <= 4 on one number line, then name the smallest integer in the overlap.",
    ),
    "Functions": (
        "A function is a rule that gives exactly one output for each input.",
        "Forgetting to substitute the input everywhere it appears before simplifying.",
        "Evaluate f(x) = 2x^2 - 1 at x = -3 and underline every place x was replaced.",
    ),
    "Sequences": (
        "A sequence is a function with step numbers as inputs; arithmetic sequences add the same difference each step.",
        "Multiplying the common difference by n instead of by n - 1 when starting from the first term.",
        "Start at 5, add 3 each time, and compare term 1, term 2, and term 5.",
    ),
    "Absolute value & piecewise functions": (
        "Absolute value measures distance, while piecewise rules choose different instructions in different zones.",
        "Keeping a negative sign inside absolute value even though distance cannot be negative.",
        "Evaluate |x - 4| at x = 1 and x = 7, then compare the two distances from 4.",
    ),
    "Function transformations": (
        "Transformations move or reshape a parent function: inside changes move the input side-to-side, outside changes move the output up or down.",
        "Treating (x - h)^2 as x^2 - h^2 instead of substituting the full shifted input first.",
        "Compare f(x) = x^2 and g(x) = (x - 3)^2 + 2 at x = 3; explain what moved.",
    ),
    "Exponents & radicals": (
        "Exponents build powers by repeated multiplication; radicals ask for the base that made a power.",
        "Treating sqrt(a + b) like sqrt(a) + sqrt(b), which is not a valid shortcut.",
        "Square 7, then take the square root of the result and explain why you returned to 7.",
    ),
    "Radicals and rational exponents": (
        "A rational exponent rewrites a root: x^(1/n) asks which number multiplied by itself n times gives x.",
        "Multiplying the base by the fraction instead of treating the denominator as the root index.",
        "Rewrite 64^(1/3) as a cube-root question, then name the number whose cube is 64.",
    ),
    "Exponential growth & decay": (
        "Exponential models multiply by the same factor each step instead of adding the same amount.",
        "Adding the percent rate each year instead of multiplying by the growth or decay factor.",
        "Start with 100 and grow by 10 percent twice; compare adding 10 twice with multiplying by 1.1 twice.",
    ),
    "Polynomial arithmetic": (
        "Polynomials are sums of terms; arithmetic works by lining up matching powers, like x^2 with x^2 and x with x.",
        "Combining unlike terms, such as adding an x^2 coefficient directly to an x coefficient.",
        "Add (3x^2 + 2x - 1) and (5x^2 - 7x + 4), then circle each pair of like terms.",
    ),
    "Factoring basics": (
        "Factoring reverses multiplication: look for pieces that multiply to the constant term and add to the middle coefficient.",
        "Only checking multiplication and forgetting the same two numbers must also add to the x-coefficient.",
        "For x^2 + 7x + 12, list factor pairs of 12 and find the pair whose sum is 7.",
    ),
    "Quadratics: Multiplying & factoring": (
        "Multiplying binomials builds a quadratic; the middle x-term comes from both cross-products working together.",
        "Multiplying only the first and last terms and missing the two middle products.",
        "Expand (x + 3)(x + 5), then point to the two products that create the 8x term.",
    ),
    "Quadratic factoring by grouping": (
        "Grouping is the ac method made visible: split the middle term so pairs of terms share common factors.",
        "Finding two numbers that multiply to ac but forgetting they must also add to the middle coefficient.",
        "For 2x^2 + 7x + 3, split 7x as 6x + x, then factor the two groups.",
    ),
    "Difference of squares": (
        "A difference of squares is one square minus another square; it factors into matching plus and minus binomials.",
        "Trying to use the pattern on a sum of squares or on terms that are not both perfect squares.",
        "Rewrite 9x^2 - 25 as (3x)^2 - 5^2 before factoring.",
    ),
    "Quadratic functions & equations": (
        "A quadratic makes a U-shaped relationship; solving asks where that curve reaches zero.",
        "Factoring with numbers that multiply to c but do not add to the middle coefficient.",
        "For x^2 - 7x + 12 = 0, list factor pairs of 12 and find the pair with sum 7.",
    ),
    "Quadratic formula": (
        "The quadratic formula is a universal root-finder for ax^2 + bx + c = 0: plug in a, b, and c, then simplify carefully.",
        "Forgetting that the entire numerator -b +/- sqrt(b^2 - 4ac) sits over 2a, or losing the sign of b.",
        "For x^2 - 5x + 6 = 0, identify a, b, and c before doing any arithmetic.",
    ),
    "Completing the square": (
        "Completing the square turns x^2 + bx into a perfect-square pattern by adding the same balanced amount to both sides.",
        "Adding (b/2)^2 to one side only, or using b^2/2 instead of (b/2)^2.",
        "For x^2 + 8x = 9, find half of 8, square it, then rewrite the left side as a square.",
    ),
    "Irrational numbers": (
        "Irrational numbers fill number-line locations that cannot be written as repeating or terminating fractions.",
        "Rounding too early and treating the decimal estimate as the exact value.",
        "Place sqrt(10) between two whole numbers by comparing 10 with nearby perfect squares.",
    ),
}


def explanation_for(skill: str, subskill: str | None = None) -> Explanation:
    explanation = ARITHMETIC_MODE_EXPLANATIONS.get(skill, ARITHMETIC_MODE_EXPLANATIONS["algebra_linear"])
    if skill == "geometry_area" and subskill in _GEOMETRY_SUBSKILL_INTUITION:
        mental_model, common_mistake, try_this = _GEOMETRY_SUBSKILL_INTUITION[subskill]
        return replace(
            explanation,
            mental_model=mental_model,
            common_mistake=common_mistake,
            try_this=try_this,
        )
    if skill == "trig_right_triangle" and subskill in _TRIG_SUBSKILL_INTUITION:
        mental_model, common_mistake, try_this = _TRIG_SUBSKILL_INTUITION[subskill]
        return replace(
            explanation,
            mental_model=mental_model,
            common_mistake=common_mistake,
            try_this=try_this,
        )
    if skill == "algebra_2" and subskill in _ALGEBRA_2_SUBSKILL_INTUITION:
        mental_model, common_mistake, try_this = _ALGEBRA_2_SUBSKILL_INTUITION[subskill]
        return replace(
            explanation,
            mental_model=mental_model,
            common_mistake=common_mistake,
            try_this=try_this,
        )
    if skill == "algebra_1" and subskill in _ALGEBRA_1_SUBSKILL_INTUITION:
        mental_model, common_mistake, try_this = _ALGEBRA_1_SUBSKILL_INTUITION[subskill]
        return replace(
            explanation,
            mental_model=mental_model,
            common_mistake=common_mistake,
            try_this=try_this,
        )
    if skill in {"calculus_1", "calculus_2", "calculus_3"} and subskill:
        intuition = calculus_intuition_for(skill, subskill)
        if intuition is not None:
            mental_model, common_mistake, try_this = intuition
            return replace(
                explanation,
                mental_model=mental_model,
                common_mistake=common_mistake,
                try_this=try_this,
            )
    if skill == "data_analysis":
        intuition = data_analysis_intuition_for(subskill)
        if intuition is None:
            return explanation
        return replace(
            explanation,
            mental_model=intuition.mental_model,
            common_mistake=intuition.common_mistake,
            try_this=intuition.try_this,
        )
    if skill == "financial_literacy":
        intuition = financial_intuition_for(subskill)
        if intuition is None:
            return explanation
        return replace(
            explanation,
            mental_model=intuition.mental_model,
            common_mistake=intuition.common_mistake,
            try_this=intuition.try_this,
        )
    if skill == "statistics":
        intuition = statistics_intuition_for(subskill)
        if intuition is None:
            return explanation
        mental_model, common_mistake, try_this = intuition
        return replace(
            explanation,
            mental_model=mental_model,
            common_mistake=common_mistake,
            try_this=try_this,
        )
    intuition = catalog_intuition_for(skill, subskill)
    if intuition is None:
        return explanation
    return replace(
        explanation,
        mental_model=intuition.mental_model,
        common_mistake=intuition.common_mistake,
        try_this=intuition.try_this,
    )

QUIZ_EXPLANATION = Explanation(
    how_short="Pick a skill and start a quiz. Answer with choices or typing.",
    how_long=(
        "Choose a skill (or mixed), a level, and how many questions. "
        "Answer each question, then review your score with explanations."
    ),
    why_short="Practice helps ideas stick.",
    why_long="Quizzes make you recall ideas on your own, which strengthens memory and understanding.",
)

PARENT_EXPLANATION = Explanation(
    how_short="Manage profiles, quizzes, grades, and worksheets.",
    how_long="Create or edit profiles, build quiz sets, review grades, and generate printable worksheets.",
    why_short="Parents keep learning organized.",
    why_long="Having one place to manage accounts and progress keeps learning smooth and consistent.",
)
