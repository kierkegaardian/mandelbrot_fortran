from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Explanation:
    how_short: str
    how_long: str
    why_short: str
    why_long: str
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
    ),
    "add_subtract": Explanation(
        how_short="Set the two numbers and choose add or subtract.",
        how_long="Use the number boxes to set A and B. Choose add or subtract and see the groups combine or shrink.",
        why_short="Adding puts groups together; subtracting takes part away.",
        why_long="Seeing the groups merge or shrink helps your brain feel what the numbers are doing.",
    ),
    "multiply": Explanation(
        how_short="Pick rows and columns to build an array.",
        how_long="Set the number of rows and columns. The total objects show why multiplication is repeated groups.",
        why_short="Multiplication is equal groups repeated.",
        why_long="Arrays make multiplication visible: rows × columns = total.",
    ),
    "divide": Explanation(
        how_short="Choose a total and how many groups to share.",
        how_long="Set the total objects and number of groups. The objects spread out evenly to show division.",
        why_short="Division shares a total into equal groups.",
        why_long="Seeing each group fill up makes the quotient feel like a fair share.",
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
