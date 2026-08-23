from __future__ import annotations

import random
from dataclasses import dataclass


DATA_ANALYSIS_SUBSKILLS: tuple[str, ...] = (
    "Histograms",
    "Box plots",
    "Center, spread, and shape",
    "Median, range, and IQR",
    "Variability in data",
    "Comparative dot and box plots",
    "Sample inferences from displays",
    "Part-to-whole display comparisons",
)

DATA_ANALYSIS_KHAN_URL = "https://www.khanacademy.org/math/statistics-probability/displaying-describing-data"
_KHAN_URL_BY_SUBSKILL: dict[str, str] = {
    "Histograms": "https://www.khanacademy.org/math/statistics-probability/displaying-describing-data/quantitative-data-graphs",
    "Box plots": "https://www.khanacademy.org/math/statistics-probability/displaying-describing-data/box-whisker-plots",
    "Center, spread, and shape": "https://www.khanacademy.org/math/statistics-probability/summarizing-quantitative-data",
    "Median, range, and IQR": "https://www.khanacademy.org/math/statistics-probability/summarizing-quantitative-data",
    "Variability in data": "https://www.khanacademy.org/math/statistics-probability/summarizing-quantitative-data",
    "Comparative dot and box plots": "https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-data-statistics",
    "Sample inferences from displays": "https://www.khanacademy.org/math/statistics-probability/designing-studies",
    "Part-to-whole display comparisons": "https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-probability-statistics",
}


@dataclass(frozen=True)
class DataAnalysisProblem:
    prompt: str
    answer: str
    explanation: str
    subskill: str
    choices: list[str] | None


@dataclass(frozen=True)
class DataAnalysisIntuition:
    mental_model: str
    common_mistake: str
    try_this: str


def _selected_subskill(requested: str | None) -> str:
    if requested in DATA_ANALYSIS_SUBSKILLS:
        return requested
    return random.choice(DATA_ANALYSIS_SUBSKILLS)


def _number_choices(correct: int, *, enabled: bool, spread: int = 6) -> list[str] | None:
    if not enabled:
        return None
    values = {correct}
    for delta in range(1, spread + 5):
        if len(values) >= 4:
            break
        values.add(max(0, correct + delta))
        if len(values) >= 4:
            break
        values.add(max(0, correct - delta))
    ordered = list(values)
    random.shuffle(ordered)
    return [str(value) for value in ordered]


def _text_choices(correct: str, distractors: tuple[str, ...], *, enabled: bool) -> list[str] | None:
    if not enabled:
        return None
    choices = [correct]
    for item in distractors:
        if item != correct and item not in choices:
            choices.append(item)
        if len(choices) == 4:
            break
    random.shuffle(choices)
    return choices


def _quartile_values() -> tuple[int, int, int, int, int]:
    minimum = random.randint(2, 12)
    q1 = minimum + random.randint(2, 6)
    median = q1 + random.randint(2, 6)
    q3 = median + random.randint(2, 6)
    maximum = q3 + random.randint(2, 8)
    return minimum, q1, median, q3, maximum


def build_data_analysis_problem(
    level: int,
    requested_subskill: str | None,
    *,
    multiple_choice: bool,
) -> DataAnalysisProblem:
    subskill = _selected_subskill(requested_subskill)

    if subskill == "Histograms":
        intervals = ("0-9", "10-19", "20-29", "30-39")
        counts = [random.randint(2, 9) for _ in intervals]
        winner = max(range(len(counts)), key=counts.__getitem__)
        display = ", ".join(f"{interval}: {count}" for interval, count in zip(intervals, counts))
        return DataAnalysisProblem(
            prompt=f"A histogram has bin frequencies {display}. Which interval has the greatest frequency?",
            answer=intervals[winner],
            explanation="A histogram groups numeric values into intervals; compare the bar heights.",
            subskill=subskill,
            choices=_text_choices(intervals[winner], intervals, enabled=multiple_choice),
        )

    if subskill == "Box plots":
        minimum, q1, median, q3, maximum = _quartile_values()
        ask_iqr = random.choice([True, False])
        answer = q3 - q1 if ask_iqr else median
        measure = "IQR" if ask_iqr else "median"
        return DataAnalysisProblem(
            prompt=f"A box plot has min {minimum}, Q1 {q1}, median {median}, Q3 {q3}, max {maximum}. Find the {measure}.",
            answer=str(answer),
            explanation="The median is the middle marker. The IQR is Q3 minus Q1.",
            subskill=subskill,
            choices=_number_choices(answer, enabled=multiple_choice),
        )

    if subskill == "Center, spread, and shape":
        data = [random.randint(3, 10), random.randint(11, 18), random.randint(19, 26)]
        answer = max(data) - min(data)
        return DataAnalysisProblem(
            prompt=f"For the data values {', '.join(map(str, data))}, what is the range?",
            answer=str(answer),
            explanation="Range measures spread by subtracting the smallest value from the largest value.",
            subskill=subskill,
            choices=_number_choices(answer, enabled=multiple_choice),
        )

    if subskill == "Median, range, and IQR":
        data = sorted(random.sample(range(10, 55), 7))
        median = data[3]
        lower = data[:3]
        upper = data[4:]
        iqr = upper[1] - lower[1]
        answer = median if level <= 1 else iqr
        measure = "median" if answer == median else "IQR"
        return DataAnalysisProblem(
            prompt=f"For the ordered data {', '.join(map(str, data))}, find the {measure}.",
            answer=str(answer),
            explanation="The median is the middle value. The IQR is the upper-half median minus the lower-half median.",
            subskill=subskill,
            choices=_number_choices(answer, enabled=multiple_choice, spread=8),
        )

    if subskill == "Variability in data":
        varied = (4, 7, 9, 12)
        constant = (8, 8, 8, 8)
        answer = "Set A" if random.choice([True, False]) else "Set B"
        set_a = varied if answer == "Set A" else constant
        set_b = constant if answer == "Set A" else varied
        return DataAnalysisProblem(
            prompt=f"Set A: {set_a}. Set B: {set_b}. Which set has variability?",
            answer=answer,
            explanation="A data set has variability when its values are not all the same.",
            subskill=subskill,
            choices=_text_choices(answer, ("Set A", "Set B", "both", "neither"), enabled=multiple_choice),
        )

    if subskill == "Comparative dot and box plots":
        median_a = random.randint(12, 25)
        median_b = median_a + random.choice((-5, -3, 4, 6))
        answer = "Group A" if median_a > median_b else "Group B"
        return DataAnalysisProblem(
            prompt=f"Two box plots have medians: Group A {median_a}, Group B {median_b}. Which group has the greater median?",
            answer=answer,
            explanation="Compare the center markers of the two displays to decide which group is greater.",
            subskill=subskill,
            choices=_text_choices(answer, ("Group A", "Group B", "same median", "cannot tell"), enabled=multiple_choice),
        )

    if subskill == "Sample inferences from displays":
        sample_size = random.choice((20, 25, 30, 40))
        success = random.randint(sample_size // 4, sample_size // 2)
        population = random.choice((100, 150, 200))
        estimate = round(population * success / sample_size)
        return DataAnalysisProblem(
            prompt=f"In a random sample, {success} of {sample_size} students chose art. Estimate how many of {population} students would choose art.",
            answer=str(estimate),
            explanation="Use the sample fraction as a rate, then scale it to the population size.",
            subskill=subskill,
            choices=_number_choices(estimate, enabled=multiple_choice, spread=12),
        )

    part = random.randint(6, 18)
    whole = part + random.randint(10, 24)
    percent = round(part * 100 / whole)
    return DataAnalysisProblem(
        prompt=f"A circle graph category has {part} out of {whole} responses. About what percent of the whole is that?",
        answer=f"{percent}%",
        explanation="A part-to-whole comparison divides the category by the total and scales to 100.",
        subskill=subskill,
        choices=_text_choices(f"{percent}%", (f"{max(0, percent - 10)}%", f"{percent + 10}%", f"{whole}%"), enabled=multiple_choice),
    )


_INTUITION_BY_SUBSKILL: dict[str, DataAnalysisIntuition] = {
    "Histograms": DataAnalysisIntuition("Histograms group numeric values into intervals so distribution shape becomes visible.", "Reading a bin label as one exact value instead of an interval.", "Name the interval with the tallest bar before doing any arithmetic."),
    "Box plots": DataAnalysisIntuition("A box plot compresses data into five landmarks: min, Q1, median, Q3, and max.", "Using max minus min when the question asks for IQR.", "Point to Q1, median, and Q3, then compute Q3 - Q1."),
    "Center, spread, and shape": DataAnalysisIntuition("Center, spread, and shape describe what is typical, how variable values are, and how values are distributed.", "Naming only the largest value and missing the distribution.", "For one data set, state its median, range, and whether values cluster or spread out."),
    "Median, range, and IQR": DataAnalysisIntuition("Median and IQR use ordered data to describe center and middle spread.", "Finding quartiles before sorting the data.", "Sort seven numbers, circle the median, then find the middle of each half."),
    "Variability in data": DataAnalysisIntuition("Variability means the data values change; no variability means all values match.", "Assuming every data set has spread just because it has several values.", "Compare 5,5,5,5 with 3,5,7,9 and say which has variability."),
    "Comparative dot and box plots": DataAnalysisIntuition("Comparative displays let two groups be judged by center, spread, and shape side by side.", "Declaring a winner from one extreme value instead of comparing the whole display.", "Compare two groups by median first, then compare spread."),
    "Sample inferences from displays": DataAnalysisIntuition("A random sample can estimate a larger population when the sample rate is scaled carefully.", "Treating a sample count as the population count.", "Use 6 out of 20 as a rate, then estimate out of 100."),
    "Part-to-whole display comparisons": DataAnalysisIntuition("Circle graphs and bar graphs often compare each part to the whole or to another part.", "Comparing parts without first finding the whole.", "Write one part-to-whole fraction from a graph, then convert it to a percent."),
}


def intuition_for(subskill: str | None) -> DataAnalysisIntuition | None:
    if subskill is None:
        return None
    return _INTUITION_BY_SUBSKILL.get(subskill)


def khan_url_for(subskill: str | None) -> str:
    if subskill is None:
        return DATA_ANALYSIS_KHAN_URL
    return _KHAN_URL_BY_SUBSKILL.get(subskill, DATA_ANALYSIS_KHAN_URL)
