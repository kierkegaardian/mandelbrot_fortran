from __future__ import annotations


CALCULUS_1_SUBSKILLS = (
    "Limits and continuity",
    "Average rate of change between two points",
    "Derivative rules",
    "Derivative as slope and velocity",
    "Optimization",
)

CALCULUS_2_SUBSKILLS = (
    "Definite integral of a linear function",
    "Accumulation and area under curves",
    "Basic integration techniques",
    "Area between curves",
)

CALCULUS_3_SUBSKILLS = (
    "Partial derivative with respect to x at a point",
    "Gradient and directional change",
    "Multivariable optimization",
)

CALCULUS_SKILL_SUBSKILLS = {
    "calculus_1": CALCULUS_1_SUBSKILLS,
    "calculus_2": CALCULUS_2_SUBSKILLS,
    "calculus_3": CALCULUS_3_SUBSKILLS,
}

DEFAULT_SUBSKILL = {
    "calculus_1": "Average rate of change between two points",
    "calculus_2": "Definite integral of a linear function",
    "calculus_3": "Partial derivative with respect to x at a point",
}

BASE_KHAN_URL = {
    "calculus_1": "https://www.khanacademy.org/math/ap-calculus-ab",
    "calculus_2": "https://www.khanacademy.org/math/ap-calculus-bc",
    "calculus_3": "https://www.khanacademy.org/math/multivariable-calculus",
}

KHAN_URL_BY_SUBSKILL = {
    ("calculus_1", "Limits and continuity"): "https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new",
    ("calculus_1", "Average rate of change between two points"): "https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-1-new/ab-2-1/e/derivative-at-a-point-as-slope-of-tangent-line",
    ("calculus_1", "Derivative rules"): "https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-2-new",
    ("calculus_1", "Derivative as slope and velocity"): "https://www.khanacademy.org/math/ap-calculus-ab/ab-diff-contextual-applications-new",
    ("calculus_1", "Optimization"): "https://www.khanacademy.org/math/ap-calculus-ab/ab-applications-derivatives-new/ab-5-10",
    ("calculus_2", "Definite integral of a linear function"): "https://www.khanacademy.org/math/ap-calculus-ab/ab-integration-new/ab-6-2",
    ("calculus_2", "Accumulation and area under curves"): "https://www.khanacademy.org/math/ap-calculus-ab/ab-applications-integrals-new",
    ("calculus_2", "Basic integration techniques"): "https://www.khanacademy.org/math/ap-calculus-bc/bc-integration-new",
    ("calculus_2", "Area between curves"): "https://www.khanacademy.org/math/ap-calculus-ab/ab-applications-integrals-new/ab-8-4",
    ("calculus_3", "Partial derivative with respect to x at a point"): "https://www.khanacademy.org/math/multivariable-calculus/multivariable-derivatives/partial-derivatives",
    ("calculus_3", "Gradient and directional change"): "https://www.khanacademy.org/math/multivariable-calculus/multivariable-derivatives/gradient-and-directional-derivatives",
    ("calculus_3", "Multivariable optimization"): "https://www.khanacademy.org/math/multivariable-calculus/applications-of-multivariable-derivatives/optimizing-multivariable-functions",
}

INTUITION_BY_SUBSKILL = {
    ("calculus_1", "Limits and continuity"): (
        "A limit asks what value the function approaches as x gets close, even before you think about the exact point.",
        "Substituting blindly when the graph has a hole, jump, or different left/right behavior.",
        "For a continuous line, plug in the target x; then imagine how a hole would change the function value but not the approach.",
    ),
    ("calculus_1", "Average rate of change between two points"): (
        "Average rate of change is secant slope: total output change divided by total input change.",
        "Reading only the vertical change and forgetting to divide by the horizontal change.",
        "Compute the slope from (1, 2) to (4, 11), then describe it as units of y per 1 unit of x.",
    ),
    ("calculus_1", "Derivative rules"): (
        "Derivative rules are shortcuts for the slope you would get by zooming in at every point.",
        "Lowering the exponent but forgetting to multiply by the original exponent first.",
        "Differentiate 5x^3 by saying the power rule out loud: multiply by 3, then lower to x^2.",
    ),
    ("calculus_1", "Derivative as slope and velocity"): (
        "A derivative is an instantaneous rate: graph slope in geometry and velocity when the input is time.",
        "Confusing position with velocity because both are numbers attached to the same time.",
        "For s(t)=t^2, compare average velocity from 2 to 3 with instantaneous velocity at t=2.",
    ),
    ("calculus_1", "Optimization"): (
        "Optimization turns a changing quantity into a function, then finds where the function reaches a best value.",
        "Checking only an endpoint or vertex without confirming whether the problem asks for a maximum or minimum.",
        "For f(x)=-(x-3)^2+10, identify why the vertex gives the maximum value.",
    ),
    ("calculus_2", "Definite integral of a linear function"): (
        "A definite integral adds signed area across an interval and reports total accumulation.",
        "Finding an antiderivative but forgetting upper value minus lower value.",
        "Integrate 2x+3 from 0 to 4 and interpret the result as area under a line.",
    ),
    ("calculus_2", "Accumulation and area under curves"): (
        "Accumulation means total change gathered from a rate graph over time.",
        "Using the final rate as the total instead of multiplying or integrating across the interval.",
        "If water flows at 6 gallons per minute for 5 minutes, explain why the accumulated water is area under the rate graph.",
    ),
    ("calculus_2", "Basic integration techniques"): (
        "Integration reverses differentiation, so each antiderivative must be checked by differentiating it.",
        "Raising the power but forgetting to divide by the new exponent.",
        "Find an antiderivative for 6x^2, then differentiate your answer to check it returns 6x^2.",
    ),
    ("calculus_2", "Area between curves"): (
        "Area between curves adds vertical gaps: upper function minus lower function across the interval.",
        "Subtracting lower from upper in one part and reversing the order somewhere else.",
        "For y=x+5 and y=x+2 from 0 to 4, sketch the constant gap before multiplying by width.",
    ),
    ("calculus_3", "Partial derivative with respect to x at a point"): (
        "A partial derivative freezes every other variable and measures change in one direction.",
        "Letting y change while computing the x-partial derivative.",
        "For f(x,y)=x^2+3xy, hold y constant and compute only how the x terms change.",
    ),
    ("calculus_3", "Gradient and directional change"): (
        "The gradient collects partial derivatives into a vector that points toward steepest increase.",
        "Treating the gradient as a point location instead of a direction-and-rate vector.",
        "For f(x,y)=2x+5y, identify the gradient and explain which direction climbs fastest.",
    ),
    ("calculus_3", "Multivariable optimization"): (
        "Multivariable optimization looks for high or low points on a surface, often where all partial derivatives balance.",
        "Checking only one variable's slice and assuming the whole surface is optimized.",
        "For f(x,y)=-(x-2)^2-(y+1)^2+9, name the peak point and maximum value.",
    ),
}


def khan_url_for(skill: str, subskill: str | None = None) -> str:
    if subskill:
        return KHAN_URL_BY_SUBSKILL.get((skill, subskill), BASE_KHAN_URL.get(skill, ""))
    return BASE_KHAN_URL.get(skill, "")


def intuition_for(skill: str, subskill: str) -> tuple[str, str, str] | None:
    return INTUITION_BY_SUBSKILL.get((skill, subskill))
