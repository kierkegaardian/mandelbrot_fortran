from __future__ import annotations

import random
from dataclasses import dataclass


GEOMETRY_SHAPES_SUBSKILLS: tuple[str, ...] = (
    "2D shape attributes",
    "3D solid attributes",
    "Compose 2D shapes",
    "Equal shares of shapes",
)

DATA_DISPLAYS_SUBSKILLS: tuple[str, ...] = (
    "Sort data into categories",
    "Picture and bar graphs",
    "Dot plots",
    "Frequency tables",
    "Stem-and-leaf plots",
    "Scatterplots and paired data",
    "Questions from data displays",
)


@dataclass(frozen=True)
class ElementaryProblem:
    prompt: str
    answer: str
    explanation: str
    subskill: str
    choices: list[str] | None


def _selected_subskill(requested: str | None, options: tuple[str, ...]) -> str:
    if requested in options:
        return requested
    return random.choice(options)


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


def _number_choices(correct: int, *, enabled: bool, spread: int = 3) -> list[str] | None:
    if not enabled:
        return None
    values = {correct}
    for delta in range(1, max(2, spread) + 4):
        if len(values) >= 4:
            break
        values.add(max(0, correct + delta))
        if len(values) >= 4:
            break
        values.add(max(0, correct - delta))
    ordered = list(values)
    random.shuffle(ordered)
    return [str(value) for value in ordered]


def build_geometry_shapes_problem(level: int, requested_subskill: str | None, *, multiple_choice: bool) -> ElementaryProblem:
    subskill = _selected_subskill(requested_subskill, GEOMETRY_SHAPES_SUBSKILLS)
    if subskill == "2D shape attributes":
        shape, sides, vertices = random.choice(
            (
                ("triangle", 3, 3),
                ("rectangle", 4, 4),
                ("square", 4, 4),
                ("hexagon", 6, 6),
                ("rhombus", 4, 4),
            )
        )
        ask_sides = random.choice([True, False])
        answer = sides if ask_sides else vertices
        word = "sides" if ask_sides else "vertices"
        return ElementaryProblem(
            prompt=f"How many {word} does a {shape} have?",
            answer=str(answer),
            explanation=f"A {shape} has {sides} sides and {vertices} vertices. Count defining attributes only.",
            subskill=subskill,
            choices=_number_choices(answer, enabled=multiple_choice),
        )

    if subskill == "3D solid attributes":
        solid, faces, curved = random.choice(
            (
                ("cube", 6, "no"),
                ("rectangular prism", 6, "no"),
                ("triangular prism", 5, "no"),
                ("cylinder", 2, "yes"),
                ("cone", 1, "yes"),
            )
        )
        if level <= 1 or random.choice([True, False]):
            return ElementaryProblem(
                prompt=f"How many flat faces does a {solid} have?",
                answer=str(faces),
                explanation=f"Count only flat faces. A {solid} has {faces} flat face(s).",
                subskill=subskill,
                choices=_number_choices(faces, enabled=multiple_choice),
            )
        return ElementaryProblem(
            prompt=f"Does a {solid} have a curved surface? Answer yes or no.",
            answer=curved,
            explanation=f"A {solid} {'does' if curved == 'yes' else 'does not'} have a curved surface.",
            subskill=subskill,
            choices=_text_choices(curved, ("yes", "no"), enabled=multiple_choice),
        )

    if subskill == "Compose 2D shapes":
        target, pieces, count = random.choice(
            (
                ("rectangle", "two squares side by side", 2),
                ("larger triangle", "two same-size triangles touching along a side", 2),
                ("hexagon", "six same-size triangles meeting at the center", 6),
                ("square", "two same-size rectangles stacked evenly", 2),
            )
        )
        return ElementaryProblem(
            prompt=f"{pieces.capitalize()} can compose what target shape?",
            answer=target,
            explanation=f"Joined without gaps or overlaps, the {count} pieces make a {target}.",
            subskill=subskill,
            choices=_text_choices(target, ("triangle", "rectangle", "square", "hexagon"), enabled=multiple_choice),
        )

    part_names = {2: "halves", 4: "fourths", 8: "eighths"}
    parts = random.choice(tuple(part_names))
    term = part_names[parts]
    return ElementaryProblem(
        prompt=f"A rectangle is split into {parts} equal parts. What word names the parts?",
        answer=term,
        explanation=f"{parts} fair shares are called {term}; each part must be the same size.",
        subskill="Equal shares of shapes",
        choices=_text_choices(term, ("halves", "fourths", "eighths", "unequal parts"), enabled=multiple_choice),
    )


def build_data_display_problem(level: int, requested_subskill: str | None, *, multiple_choice: bool) -> ElementaryProblem:
    subskill = _selected_subskill(requested_subskill, DATA_DISPLAYS_SUBSKILLS)
    categories = ("apples", "bananas", "oranges")
    counts = {
        "apples": random.randint(2, 8),
        "bananas": random.randint(1, 7),
        "oranges": random.randint(1, 7),
    }
    display = ", ".join(f"{name}: {count}" for name, count in counts.items())

    if subskill == "Sort data into categories":
        chosen = random.choice(categories)
        return ElementaryProblem(
            prompt=f"A T-chart shows {display}. How many {chosen} are in the chart?",
            answer=str(counts[chosen]),
            explanation="A category count tells how many items belong in that sorted group.",
            subskill=subskill,
            choices=_number_choices(counts[chosen], enabled=multiple_choice),
        )

    if subskill == "Picture and bar graphs":
        chosen = max(counts, key=counts.get)
        return ElementaryProblem(
            prompt=f"A bar graph shows {display}. Which category has the most?",
            answer=chosen,
            explanation="The tallest bar or largest picture count has the most items.",
            subskill=subskill,
            choices=_text_choices(chosen, categories, enabled=multiple_choice),
        )

    if subskill == "Dot plots":
        chosen = random.choice(categories)
        return ElementaryProblem(
            prompt=f"A dot plot has {counts[chosen]} dots above {chosen}. How many {chosen} were counted?",
            answer=str(counts[chosen]),
            explanation="Each dot stands for one item, so the number of dots is the count.",
            subskill=subskill,
            choices=_number_choices(counts[chosen], enabled=multiple_choice),
        )

    if subskill == "Frequency tables":
        chosen = random.choice(categories)
        if level <= 1 or random.choice([True, False]):
            return ElementaryProblem(
                prompt=f"A frequency table shows {display}. What is the frequency for {chosen}?",
                answer=str(counts[chosen]),
                explanation="The frequency is the count listed beside a category or value.",
                subskill=subskill,
                choices=_number_choices(counts[chosen], enabled=multiple_choice),
            )
        total = sum(counts.values())
        return ElementaryProblem(
            prompt=f"A frequency table shows {display}. How many items are in the data set?",
            answer=str(total),
            explanation="Add all frequencies to find how many data values were collected.",
            subskill=subskill,
            choices=_number_choices(total, enabled=multiple_choice),
        )

    if subskill == "Stem-and-leaf plots":
        stem = random.randint(2, 8)
        leaves = sorted(random.sample(range(10), 3))
        values = [stem * 10 + leaf for leaf in leaves]
        leaves_text = ", ".join(str(leaf) for leaf in leaves)
        return ElementaryProblem(
            prompt=f"In a stem-and-leaf plot, stem {stem} has leaves {leaves_text}. What is the greatest value?",
            answer=str(max(values)),
            explanation=f"The stem gives the tens digit. The largest leaf {max(leaves)} makes {max(values)}.",
            subskill=subskill,
            choices=_number_choices(max(values), enabled=multiple_choice, spread=8),
        )

    if subskill == "Scatterplots and paired data":
        rate = random.randint(2, 8)
        x_value = random.randint(4, 9)
        answer = rate * x_value
        return ElementaryProblem(
            prompt=(
                f"Paired data on a scatterplot follows y = {rate}x. "
                f"What y-value pairs with x = {x_value}?"
            ),
            answer=str(answer),
            explanation="A paired-data point uses an x-value and its matching y-value from the rule.",
            subskill=subskill,
            choices=_number_choices(answer, enabled=multiple_choice, spread=10),
        )

    high = max(counts, key=counts.get)
    low = min(counts, key=counts.get)
    difference = counts[high] - counts[low]
    if level <= 1:
        return ElementaryProblem(
            prompt=f"A picture graph shows {display}. Which category has the fewest?",
            answer=low,
            explanation="The fewest category has the smallest picture or bar count.",
            subskill="Questions from data displays",
            choices=_text_choices(low, categories, enabled=multiple_choice),
        )
    return ElementaryProblem(
        prompt=f"A graph shows {display}. How many more {high} are there than {low}?",
        answer=str(difference),
        explanation="Compare graph counts by subtracting the smaller count from the larger count.",
        subskill="Questions from data displays",
        choices=_number_choices(difference, enabled=multiple_choice),
    )
