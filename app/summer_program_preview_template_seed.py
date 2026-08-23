from __future__ import annotations

from .summer_program_seed_types import SeedPattern


def _v(name: str, kind: str, min_value: int, max_value: int, step: int = 1) -> dict[str, object]:
    return {"name": name, "kind": kind, "min": min_value, "max": max_value, "step": step}


PREVIEW_EXPRESSION_TARGETS: dict[tuple[str, str], int] = {
    ("algebra_linear", "Slope from points"): 1,
    ("algebra_linear", "Slope-intercept interpretation"): 1,
    ("algebra_linear", "Direct variation"): 1,
    ("algebra_linear", "Rate and unit-rate modeling"): 1,
    ("algebra_linear", "Word problems with linear models"): 1,
    ("algebra_1", "Slope from points"): 1,
    ("algebra_1", "Slope-intercept form"): 1,
    ("algebra_1", "Graphing linear inequalities"): 1,
    ("algebra_1", "Functions"): 1,
    ("algebra_1", "Sequences"): 1,
    ("algebra_1", "Linear equations & graphs"): 1,
    ("algebra_1", "Solving equations & inequalities"): 1,
    ("geometry_area", "Perimeter and missing sides"): 1,
    ("geometry_area", "Area of triangles and parallelograms"): 1,
    ("geometry_area", "Circumference and area of circles"): 1,
    ("geometry_area", "Surface area and volume"): 1,
    ("geometry_area", "Pythagorean theorem"): 1,
    ("geometry_area", "Coordinate geometry distance and midpoint"): 1,
    ("geometry_area", "Transformations and congruence"): 1,
    ("geometry_area", "Similarity and scale factor"): 1,
    ("geometry_area", "Analytic geometry and coordinate proofs"): 1,
}

PREVIEW_WORD_TARGETS: dict[tuple[str, str], int] = {
    ("algebra_linear", "Slope from points"): 1,
    ("algebra_linear", "Word problems with linear models"): 1,
    ("algebra_1", "Slope from points"): 1,
    ("algebra_1", "Slope-intercept form"): 1,
    ("algebra_1", "Graphing linear inequalities"): 1,
    ("algebra_1", "Functions"): 1,
    ("algebra_1", "Sequences"): 1,
    ("algebra_1", "Linear equations & graphs"): 1,
    ("algebra_1", "Solving equations & inequalities"): 1,
    ("geometry_area", "Perimeter and missing sides"): 1,
    ("geometry_area", "Area of triangles and parallelograms"): 1,
    ("geometry_area", "Circumference and area of circles"): 1,
    ("geometry_area", "Surface area and volume"): 1,
    ("geometry_area", "Pythagorean theorem"): 1,
    ("geometry_area", "Coordinate geometry distance and midpoint"): 1,
    ("geometry_area", "Transformations and congruence"): 1,
    ("geometry_area", "Similarity and scale factor"): 1,
    ("geometry_area", "Analytic geometry and coordinate proofs"): 1,
}

PREVIEW_SEED_PATTERNS: dict[tuple[str, str, str], tuple[SeedPattern, ...]] = {
    ("algebra_linear", "Slope from points", "expression"): (
        SeedPattern("Find the slope through ({x1}, {y1}) and ({x2}, {y2}).", "(y2 - y1) / (x2 - x1)", "x2 > x1 and y2 > y1 and (y2 - y1) % (x2 - x1) == 0", "Slope is rise divided by run: change in y over change in x.", (_v("x1", "int", 0, 8), _v("y1", "int", 0, 20), _v("x2", "int", 1, 10), _v("y2", "int", 1, 30)), 6.0),
    ),
    ("algebra_linear", "Slope from points", "word"): (
        SeedPattern("A ramp line goes from ({x1}, {y1}) to ({x2}, {y2}). What is its slope?", "(y2 - y1) / (x2 - x1)", "x2 > x1 and y2 > y1 and (y2 - y1) % (x2 - x1) == 0", "A coordinate story still uses rise divided by run.", (_v("x1", "int", 0, 8), _v("y1", "int", 0, 20), _v("x2", "int", 1, 10), _v("y2", "int", 1, 30)), 6.0),
    ),
    ("algebra_linear", "Slope-intercept interpretation", "expression"): (
        SeedPattern("In y = {m}x + {b}, what is the slope?", "m", "m != 0", "In slope-intercept form y = mx + b, m is the slope and b is the starting value.", (_v("m", "int", -6, 6), _v("b", "int", -12, 12)), 6.0),
    ),
    ("algebra_linear", "Direct variation", "expression"): (
        SeedPattern("A direct variation has y = {k}x. What is y when x = {x}?", "k * x", "k != 0", "Direct variation keeps the same multiplier from x to y.", (_v("k", "int", 2, 9), _v("x", "int", 2, 12)), 16.0),
    ),
    ("algebra_linear", "Rate and unit-rate modeling", "expression"): (
        SeedPattern("A pack of {items} notebooks costs ${cost}. What is the unit cost per notebook?", "cost / items", "cost % items == 0", "Unit rate means one item's share of the total cost.", (_v("items", "int", 2, 8), _v("cost", "int", 8, 64)), 8.0),
    ),
    ("algebra_linear", "Word problems with linear models", "expression"): (
        SeedPattern("A club starts with ${b} and adds ${m} each week. How many dollars after {x} weeks?", "b + m * x", "", "A linear model adds the same rate for each step after the starting amount.", (_v("b", "int", 3, 25), _v("m", "int", 2, 12), _v("x", "int", 2, 12)), 18.0),
    ),
    ("algebra_linear", "Word problems with linear models", "word"): (
        SeedPattern("A music app charges a ${b} signup fee plus ${m} per month. What is the total after {x} months?", "b + m * x", "", "Translate the story into total = starting fee + rate times number of months.", (_v("b", "int", 4, 30), _v("m", "int", 2, 15), _v("x", "int", 2, 12)), 20.0),
    ),
    ("algebra_1", "Slope from points", "expression"): (
        SeedPattern("Find the slope through ({x1}, {y1}) and ({x2}, {y2}).", "(y2 - y1) / (x2 - x1)", "x2 > x1 and y2 != y1 and (y2 - y1) % (x2 - x1) == 0", "Slope is rise divided by run: change in y over change in x.", (_v("x1", "int", -8, 4), _v("y1", "int", -12, 12), _v("x2", "int", -2, 10), _v("y2", "int", -18, 18)), 8.0),
    ),
    ("algebra_1", "Slope from points", "word"): (
        SeedPattern("A grid trail goes from ({x1}, {y1}) to ({x2}, {y2}). What is its slope?", "(y2 - y1) / (x2 - x1)", "x2 > x1 and y2 != y1 and (y2 - y1) % (x2 - x1) == 0", "A real path on a coordinate grid still uses rise divided by run.", (_v("x1", "int", -8, 4), _v("y1", "int", -12, 12), _v("x2", "int", -2, 10), _v("y2", "int", -18, 18)), 8.0),
    ),
    ("algebra_1", "Slope-intercept form", "expression"): (
        SeedPattern("In y = {m}x + {b}, what is the y-intercept?", "b", "m != 0", "In y = mx + b, b is the output when x is 0.", (_v("m", "int", -8, 8), _v("b", "int", -15, 15)), 8.0),
    ),
    ("algebra_1", "Slope-intercept form", "word"): (
        SeedPattern("A line rule is y = {m}x + {b}. What starting output does the rule show?", "b", "m != 0", "The starting output is the y-intercept, the value left when x is 0.", (_v("m", "int", -8, 8), _v("b", "int", -15, 15)), 8.0),
    ),
    ("algebra_1", "Graphing linear inequalities", "expression"): (
        SeedPattern("For y > {m}x + {b}, at x = {x}, what boundary y-value should you compare against?", "m * x + b", "m != 0", "Graph the boundary line first, then shade above it for greater-than.", (_v("m", "int", -5, 5), _v("b", "int", -12, 12), _v("x", "int", -6, 6)), 12.0),
    ),
    ("algebra_1", "Graphing linear inequalities", "word"): (
        SeedPattern("A shaded region uses y < {m}x + {b}. At x = {x}, what boundary value separates above from below?", "m * x + b", "m != 0", "The inequality compares y-values to the boundary line value.", (_v("m", "int", -5, 5), _v("b", "int", -12, 12), _v("x", "int", -6, 6)), 12.0),
    ),
    ("algebra_1", "Functions", "expression"): (
        SeedPattern("If f(x) = {a}x + {b}, what is f({x})?", "a * x + b", "", "A function rule takes one input and produces one output.", (_v("a", "int", 2, 8), _v("b", "int", 0, 20), _v("x", "int", 2, 12)), 12.0),
    ),
    ("algebra_1", "Functions", "word"): (
        SeedPattern("A score rule is score = {a} x level + {b}. What score is level {x}?", "a * x + b", "a != 0", "Treat the level as the function input and follow the rule.", (_v("a", "int", 2, 8), _v("b", "int", 0, 20), _v("x", "int", 2, 12)), 16.0),
    ),
    ("algebra_1", "Sequences", "expression"): (
        SeedPattern("An arithmetic sequence starts at {first} and changes by {step}. What is term {n}?", "first + (n - 1) * step", "step > 0", "For term n, make n - 1 jumps from the first term.", (_v("first", "int", 0, 20), _v("step", "int", 2, 9), _v("n", "int", 4, 12)), 18.0),
    ),
    ("algebra_1", "Sequences", "word"): (
        SeedPattern("A reading streak starts with {first} pages and adds {step} more pages each day. How many pages on day {n}?", "first + (n - 1) * step", "step > 0", "Each new day adds one more common-difference jump.", (_v("first", "int", 4, 20), _v("step", "int", 2, 9), _v("n", "int", 4, 12)), 18.0),
    ),
    ("algebra_1", "Linear equations & graphs", "expression"): (
        SeedPattern("For y = {m}x + {b}, find y when x = {x}.", "m * x + b", "", "A line rule maps each x-value to a y-value.", (_v("m", "int", 1, 6), _v("b", "int", 0, 15), _v("x", "int", 1, 10)), 12.0),
    ),
    ("algebra_1", "Linear equations & graphs", "word"): (
        SeedPattern("A line starts at {b} and changes by {m} for each x-step. What is y when x = {x}?", "b + m * x", "", "The graph follows starting value plus rate times input.", (_v("b", "int", 0, 15), _v("m", "int", 1, 6), _v("x", "int", 1, 10)), 14.0),
    ),
    ("algebra_1", "Solving equations & inequalities", "expression"): (
        SeedPattern("Solve for x: {m}x + {b} = {rhs}", "(rhs - b) / m", "(rhs - b) % m == 0", "Undo the constant first, then divide by the coefficient.", (_v("m", "int", 2, 9), _v("b", "int", 0, 18), _v("rhs", "int", 20, 120)), 14.0),
    ),
    ("algebra_1", "Solving equations & inequalities", "word"): (
        SeedPattern("A number is multiplied by {m}, then {b} is added, giving {rhs}. What was the number?", "(rhs - b) / m", "(rhs - b) % m == 0", "Translate the story to mx + b = rhs, then undo the operations.", (_v("m", "int", 2, 9), _v("b", "int", 0, 18), _v("rhs", "int", 20, 120)), 14.0),
    ),
    ("geometry_area", "Perimeter and missing sides", "expression"): (
        SeedPattern("A rectangle has perimeter {p} and width {w}. What is its length?", "p / 2 - w", "p % 2 == 0 and p / 2 > w", "Half the perimeter is length plus width, so subtract the width.", (_v("p", "int", 20, 100, 2), _v("w", "int", 2, 20)), 14.0),
    ),
    ("geometry_area", "Perimeter and missing sides", "word"): (
        SeedPattern("A garden is {l} ft long and {w} ft wide. What is its perimeter?", "2 * (l + w)", "", "Perimeter is the distance around: two lengths plus two widths.", (_v("l", "int", 4, 30), _v("w", "int", 3, 18)), 20.0),
    ),
    ("geometry_area", "Area of triangles and parallelograms", "expression"): (
        SeedPattern("What is the area of a triangle with base {b} and height {h}?", "b * h / 2", "(b * h) % 2 == 0", "A triangle has half the area of a matching parallelogram.", (_v("b", "int", 4, 24), _v("h", "int", 3, 18)), 20.0),
    ),
    ("geometry_area", "Area of triangles and parallelograms", "word"): (
        SeedPattern("A parallelogram has base {b} and height {h}. What is its area?", "b * h", "", "Parallelogram area is base times height.", (_v("b", "int", 4, 24), _v("h", "int", 3, 18)), 20.0),
    ),
    ("geometry_area", "Circumference and area of circles", "expression"): (
        SeedPattern("Using pi = 3.14, what is the circumference of a circle with radius {r}?", "2 * 3.14 * r", "", "Circumference is the distance around: 2 times pi times radius.", (_v("r", "int", 2, 12),), 30.0),
    ),
    ("geometry_area", "Circumference and area of circles", "word"): (
        SeedPattern("A circular rug has diameter {d}. Using pi = 3.14, what is its circumference?", "3.14 * d", "", "When diameter is known, circumference is pi times diameter.", (_v("d", "int", 4, 24),), 30.0),
    ),
    ("geometry_area", "Surface area and volume", "expression"): (
        SeedPattern("What is the volume of a rectangular prism with length {l}, width {w}, and height {h}?", "l * w * h", "", "Volume counts cubic units: length times width times height.", (_v("l", "int", 2, 12), _v("w", "int", 2, 10), _v("h", "int", 2, 8)), 40.0),
    ),
    ("geometry_area", "Surface area and volume", "word"): (
        SeedPattern("A box is {l} by {w} by {h}. What is its surface area?", "2 * (l * w + l * h + w * h)", "", "Surface area adds the areas of all six faces.", (_v("l", "int", 2, 10), _v("w", "int", 2, 8), _v("h", "int", 2, 6)), 50.0),
    ),
    ("geometry_area", "Pythagorean theorem", "expression"): (
        SeedPattern("A 3-4-5 right triangle is scaled by {k}. What is the hypotenuse?", "5 * k", "", "Scaling a 3-4-5 triangle multiplies every side by the same factor.", (_v("k", "int", 2, 10),), 20.0),
    ),
    ("geometry_area", "Pythagorean theorem", "word"): (
        SeedPattern("A ladder problem forms a 3-4-5 right triangle scaled by {k}. How long is the ladder?", "5 * k", "", "The ladder is the hypotenuse, the longest side in the scaled 3-4-5 triangle.", (_v("k", "int", 2, 10),), 20.0),
    ),
    ("geometry_area", "Coordinate geometry distance and midpoint", "expression"): (
        SeedPattern("Find the midpoint y-coordinate for the segment from ({x1}, {y1}) to ({x2}, {y2}).", "(y1 + y2) / 2", "(y1 + y2) % 2 == 0", "A midpoint averages the endpoint coordinates.", (_v("x1", "int", 0, 12), _v("y1", "int", 0, 12), _v("x2", "int", 2, 18), _v("y2", "int", 2, 18)), 10.0),
    ),
    ("geometry_area", "Coordinate geometry distance and midpoint", "word"): (
        SeedPattern("A map path starts at ({x1}, {y1}) and ends at ({x2}, {y2}). What is the midpoint x-coordinate?", "(x1 + x2) / 2", "(x1 + x2) % 2 == 0", "The midpoint's x-coordinate is the average of the endpoint x-values.", (_v("x1", "int", 0, 12), _v("y1", "int", 0, 12), _v("x2", "int", 2, 18), _v("y2", "int", 2, 18)), 10.0),
    ),
    ("geometry_area", "Transformations and congruence", "expression"): (
        SeedPattern("Point ({x}, {y}) is translated right {dx} and up {dy}. What is the new x-coordinate?", "x + dx", "", "A translation slides every point the same amount without changing the shape.", (_v("x", "int", 0, 12), _v("y", "int", 0, 12), _v("dx", "int", 1, 8), _v("dy", "int", 1, 8)), 10.0),
    ),
    ("geometry_area", "Transformations and congruence", "word"): (
        SeedPattern("A triangle vertex starts at ({x}, {y}) and slides right {dx}, up {dy}. What is the new y-coordinate?", "y + dy", "", "Congruent translated shapes keep their size; only coordinates shift.", (_v("x", "int", 0, 12), _v("y", "int", 0, 12), _v("dx", "int", 1, 8), _v("dy", "int", 1, 8)), 10.0),
    ),
    ("geometry_area", "Similarity and scale factor", "expression"): (
        SeedPattern("A side length {side} is scaled by factor {scale}. What is the new side length?", "side * scale", "", "Similar figures multiply corresponding lengths by the same scale factor.", (_v("side", "int", 2, 18), _v("scale", "int", 2, 5)), 16.0),
    ),
    ("geometry_area", "Similarity and scale factor", "word"): (
        SeedPattern("A model side is {side} cm. The real object is scale factor {scale}. What is the real side length?", "side * scale", "", "A scale factor turns model lengths into matching real lengths.", (_v("side", "int", 2, 18), _v("scale", "int", 2, 5)), 16.0),
    ),
    ("geometry_area", "Analytic geometry and coordinate proofs", "expression"): (
        SeedPattern("A horizontal segment goes from ({x1}, {y}) to ({x2}, {y}). What is its length?", "x2 - x1", "x2 > x1", "A horizontal segment's length is the change in x when y stays the same.", (_v("x1", "int", 0, 12), _v("x2", "int", 2, 20), _v("y", "int", 0, 12)), 14.0),
    ),
    ("geometry_area", "Analytic geometry and coordinate proofs", "word"): (
        SeedPattern("Two rectangle vertices are ({x1}, {y}) and ({x2}, {y}). What is the horizontal side length?", "x2 - x1", "x2 > x1", "Coordinate proofs often prove side lengths by comparing matching coordinates.", (_v("x1", "int", 0, 12), _v("x2", "int", 2, 20), _v("y", "int", 0, 12)), 14.0),
    ),
}
