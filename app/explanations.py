from __future__ import annotations

from dataclasses import dataclass


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
    ),
    "long_subtraction": Explanation(
        how_short="Type two numbers to see borrowing in columns.",
        how_long="Use the number boxes to build a long subtraction problem and watch the borrow marks appear.",
        why_short="Long subtraction keeps place values aligned.",
        why_long="Borrowing lets you subtract a larger digit from a smaller one by taking 10 from the next column.",
    ),
    "long_multiplication": Explanation(
        how_short="Type two numbers to see the stacked multiplication layout.",
        how_long="The view shows the traditional multiplication format with partial products when needed.",
        why_short="Long multiplication breaks the problem into place-value parts.",
        why_long="Each digit in the bottom number creates a partial product. Adding them gives the final result.",
    ),
    "long_division": Explanation(
        how_short="Type a dividend and divisor to see the long division layout.",
        how_long="The quotient appears above the bar and the remainder is shown below if there is one.",
        why_short="Long division shows how many times a divisor fits into the dividend.",
        why_long="The layout connects repeated subtraction to the quotient and shows leftover as a remainder.",
    ),
    "money": Explanation(
        how_short="Enter dollars and cents to see a money breakdown.",
        how_long="The view shows bills and coins that make the total, using common US denominations.",
        why_short="Money turns numbers into real-world amounts.",
        why_long="Seeing bills and coins helps learners connect arithmetic to shopping and change-making.",
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
    "algebra_linear": Explanation(
        how_short="Set an equation and watch operations isolate x.",
        how_long="Use inverse steps on both sides to keep the equation balanced while removing constants and coefficients.",
        why_short="A balance stays true when both sides change equally.",
        why_long="If every operation is mirrored on both sides, the final x value is mathematically valid.",
        mental_model="Think of a scale: whatever you do to one side, do to the other.",
        common_mistake="Applying an operation to only one side of the equation.",
        try_this="Solve 2x + 5 = 17 with two mirrored steps.",
    ),
    "geometry_area": Explanation(
        how_short="Pick rectangles or right triangles and compare unit area.",
        how_long="Use count-and-block area models to show width × height, and 1/2 × base × height for triangles.",
        why_short="Area is counting square units.",
        why_long="Drawing unit cells or halves of rectangles makes area formulas concrete.",
    ),
    "trig_right_triangle": Explanation(
        how_short="Build a right triangle and read the trig ratio from side labels.",
        how_long="For sine, cosine, and tangent, use opposite/hypotenuse, adjacent/hypotenuse, and opposite/adjacent respectively.",
        why_short="Trig is about fixed side-length relationships.",
        why_long="Consistent labeling prevents common angle and ratio swaps.",
    ),
    "stats_percent": Explanation(
        how_short="Set total and percent to get a rate problem.",
        how_long="Convert the percent to decimal by dividing by 100 and multiply by the base value.",
        why_short="Percent is a scaled whole.",
        why_long="This keeps part-of problems in one multiplication workflow.",
    ),
    "stats_mean": Explanation(
        how_short="Enter a few values and average them.",
        how_long="Add all values, then divide by the count of values to get the mean.",
        why_short="Mean represents the equal-shares value.",
        why_long="The average is where values balance around the center if redistributed equally.",
    ),
    "stats_probability": Explanation(
        how_short="Set successful outcomes and total outcomes.",
        how_long="Probability is successful outcomes divided by equally likely outcomes.",
        why_short="Fractions naturally represent chances.",
        why_long="A numerator and denominator together describe likelihood without approximation.",
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
