from __future__ import annotations


STATISTICS_SUBSKILLS = (
    "Integrated descriptive statistics and probability",
    "Data collection and study design",
    "Distributions and standard deviation",
    "Probability rules",
    "Combinatorics",
    "Expected value",
    "Sampling and margin of error",
    "Confidence intervals",
    "Hypothesis tests",
    "Correlation and regression",
)

STATISTICS_KHAN_URL = "https://www.khanacademy.org/math/statistics-probability"

KHAN_URL_BY_SUBSKILL = {
    "Integrated descriptive statistics and probability": "https://www.khanacademy.org/math/statistics-probability",
    "Data collection and study design": "https://www.khanacademy.org/math/statistics-probability/designing-studies",
    "Distributions and standard deviation": "https://www.khanacademy.org/math/statistics-probability/summarizing-quantitative-data",
    "Probability rules": "https://www.khanacademy.org/math/statistics-probability/probability-library",
    "Combinatorics": "https://www.khanacademy.org/math/statistics-probability/counting-permutations-and-combinations",
    "Expected value": "https://www.khanacademy.org/math/statistics-probability/random-variables-stats-library/random-variables-discrete/e/mean-expected-value-discrete-random-variable",
    "Sampling and margin of error": "https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:sampling-distribution-confidence-intervals",
    "Confidence intervals": "https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:confidence-intervals-one-sample",
    "Hypothesis tests": "https://www.khanacademy.org/math/ap-statistics/tests-significance-ap",
    "Correlation and regression": "https://www.khanacademy.org/math/statistics-probability/describing-relationships-quantitative-data",
}

INTUITION_BY_SUBSKILL = {
    "Integrated descriptive statistics and probability": (
        "Statistics connects data summaries, probability, and uncertainty into one evidence chain.",
        "Jumping to a conclusion from a percent without checking sample size or variability.",
        "Take one sample table and state the total, one percent, and what uncertainty remains.",
    ),
    "Data collection and study design": (
        "Good statistics starts before arithmetic: who was sampled and how they were selected controls what claims are fair.",
        "Treating a convenience sample as if it represented the whole population.",
        "Compare a voluntary online poll with a random sample and decide which claim is more trustworthy.",
    ),
    "Distributions and standard deviation": (
        "A distribution shows shape; standard deviation measures typical distance from the center.",
        "Using the range as if it described every value's typical distance from the mean.",
        "Compare an all-equal data set to a spread-out data set and predict which standard deviation is larger.",
    ),
    "Probability rules": (
        "Probability rules track how events combine: and usually multiplies independent chances, or usually adds disjoint chances.",
        "Adding probabilities for an and event or multiplying probabilities for an either/or event.",
        "Write one independent and event, then multiply the two probabilities before simplifying.",
    ),
    "Combinatorics": (
        "Combinatorics counts choices systematically so you do not have to list every outcome by hand.",
        "Adding choices from independent stages instead of multiplying the stages.",
        "Count outfits from 4 shirts and 3 pants using a tree or multiplication.",
    ),
    "Expected value": (
        "Expected value is a long-run average: each outcome is weighted by its probability.",
        "Choosing the biggest prize instead of averaging the prize by its chance.",
        "For a 1-in-4 chance at 20 points, compute the long-run average points per play.",
    ),
    "Sampling and margin of error": (
        "A sample estimate has uncertainty; larger random samples usually shrink that uncertainty.",
        "Thinking a sample percent is exact because it was calculated precisely.",
        "Compare samples of 25 and 400 people and predict which has the smaller margin of error.",
    ),
    "Confidence intervals": (
        "A confidence interval gives a plausible range for a population value based on sample evidence.",
        "Reading a 95% confidence interval as a guarantee about one individual.",
        "For interval 42% to 50%, find the center and margin of error.",
    ),
    "Hypothesis tests": (
        "A hypothesis test asks whether observed data would be surprising if the null claim were true.",
        "Treating a small p-value as the size of the effect instead of evidence against the null.",
        "Compare p=0.03 with alpha=0.05 and decide whether the result is statistically significant.",
    ),
    "Correlation and regression": (
        "Correlation describes direction and strength; regression gives a prediction rule with slope and intercept.",
        "Assuming correlation proves one variable caused the other.",
        "For a regression slope of 4, explain what one more unit of x predicts for y.",
    ),
}


def khan_url_for(subskill: str | None = None) -> str:
    if subskill:
        return KHAN_URL_BY_SUBSKILL.get(subskill, STATISTICS_KHAN_URL)
    return STATISTICS_KHAN_URL


def intuition_for(subskill: str | None) -> tuple[str, str, str] | None:
    if subskill is None:
        return None
    return INTUITION_BY_SUBSKILL.get(subskill)
