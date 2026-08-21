from __future__ import annotations

from dataclasses import dataclass
import random

from .models import ReasoningKind
from .pilot_problem import PilotProblem


@dataclass(frozen=True)
class SourceCase:
    scenario: str
    answer: str


@dataclass(frozen=True)
class PurposeCase:
    item: str
    context: str
    answer: str


@dataclass(frozen=True)
class RoleSkill:
    role: str
    task: str
    skill: str


SOURCE_CASES: tuple[SourceCase, ...] = (
    SourceCase("Mia earns six dollars for raking leaves", "income"),
    SourceCase("Noah receives ten dollars in a birthday card", "gift"),
    SourceCase("Ari earns money for sorting books at a community sale", "income"),
    SourceCase("Lena receives a book from a grandparent for her birthday", "gift"),
)

PURPOSE_CASES: tuple[PurposeCase, ...] = (
    PurposeCase("umbrella", "Kai must walk to school in heavy rain and has no umbrella", "need"),
    PurposeCase("umbrella", "Kai is indoors on a sunny day and already has an umbrella at home", "want"),
    PurposeCase("water", "Zoe is thirsty after recess and has no drink", "need"),
    PurposeCase("water", "Zoe is not thirsty and asks for an extra flavored water", "want"),
    PurposeCase("school shoes", "Max's school shoes no longer fit and he has no other pair", "need"),
    PurposeCase("school shoes", "Max's school shoes fit and he asks for a second pair in another color", "want"),
    PurposeCase("warm coat", "Ivy must go outside on a cold morning and has no warm coat", "need"),
    PurposeCase("warm coat", "Ivy has a warm coat that fits and asks for another pattern", "want"),
)

ROLE_SKILLS: tuple[RoleSkill, ...] = (
    RoleSkill("classroom helper", "put supplies where the class can find them", "organizing"),
    RoleSkill("baker", "make a recipe in the correct order", "following steps"),
    RoleSkill("librarian", "place books in the correct sections", "sorting"),
    RoleSkill("bus driver", "notice traffic and stops", "careful attention"),
    RoleSkill("animal-care helper", "look after an animal calmly", "gentle handling"),
    RoleSkill("shop helper", "check a small group of items", "careful counting"),
)


def income_gifts_wants_needs(kind: ReasoningKind) -> PilotProblem:
    if kind is ReasoningKind.TRANSFER:
        return _transfer_problem()
    axis = random.choice(("source", "purpose", "skill"))
    if axis == "source":
        return _source_problem(kind)
    if axis == "purpose":
        return _purpose_problem(kind)
    return _skill_problem(kind)


def _source_problem(kind: ReasoningKind) -> PilotProblem:
    case = random.choice(SOURCE_CASES)
    other = "gift" if case.answer == "income" else "income"
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            f"Use a source model: {case.scenario}. Was the money or item earned as income or received as a gift?",
            case.answer,
            "A source model asks whether something was earned for work or received without being earned.",
            (other, "want"),
        )
    if kind is ReasoningKind.APPLICATION:
        return PilotProblem(
            f"{case.scenario}. Select a model for the source and decide. Answer model; result.",
            f"income-or-gift model; {case.answer}",
            "Use the income-or-gift model because the question asks where it came from.",
            (f"income-or-gift model; {other}", "need-want model; want"),
        )
    return PilotProblem(
        f"Use the source routine: {case.scenario}. Name the source as income or gift.",
        case.answer,
        "Ask what is being classified, find whether work earned it, then name the source.",
        (other, "need"),
    )


def _purpose_problem(kind: ReasoningKind) -> PilotProblem:
    case = random.choice(PURPOSE_CASES)
    other = "want" if case.answer == "need" else "need"
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            f"Use a purpose-in-context model: {case.context}. Is the {case.item} a need or a want in this situation?",
            case.answer,
            "A purpose model uses the situation, not the object name alone, to distinguish needs from wants.",
            ("income", other),
        )
    if kind is ReasoningKind.APPLICATION:
        return PilotProblem(
            f"{case.context}. Select a model for the {case.item} choice and decide. Answer model; result.",
            f"need-want model; {case.answer}",
            "Use the stated situation to decide whether the item is necessary or optional here.",
            ("income-or-gift model; income", f"need-want model; {other}"),
        )
    return PilotProblem(
        f"Use the purpose-in-context routine: {case.context}. Classify the {case.item} as need or want.",
        case.answer,
        "Name the purpose question, point to the context clue, then decide whether the item is necessary here.",
        ("gift", other),
    )


def _skill_problem(kind: ReasoningKind) -> PilotProblem:
    case = random.choice(ROLE_SKILLS)
    if kind is ReasoningKind.CONCEPTUAL:
        return PilotProblem(
            f"Use a job-skill model: which skill helps a {case.role} {case.task}?",
            case.skill,
            "A job skill is an ability used to complete the named task safely and carefully.",
            ("income", "want"),
        )
    if kind is ReasoningKind.APPLICATION:
        return PilotProblem(
            f"A {case.role} needs to {case.task}. Select a model and name the useful skill. Answer model; result.",
            f"job-skill model; {case.skill}",
            "Use a job-skill model because the question asks which ability supports the task.",
            ("income-or-gift model; income", "need-want model; want"),
        )
    return PilotProblem(
        f"Use the job-skill routine: a {case.role} must {case.task}. Name the useful skill.",
        case.skill,
        "Name the skill question, point to the task, then choose the ability that supports it.",
        ("gift", "need"),
    )


def _transfer_problem() -> PilotProblem:
    if random.choice((True, False)):
        case = random.choice(tuple(item for item in SOURCE_CASES if item.answer == "gift"))
        return PilotProblem(
            f"A learner says, '{case.scenario}, so it is income.' Correct the gift-as-income error.",
            "gift",
            "The item was received without being earned for work, so its source is a gift.",
            ("income", "want"),
        )
    case = random.choice(PURPOSE_CASES)
    wrong = "want" if case.answer == "need" else "need"
    return PilotProblem(
        f"A learner ignores the situation and calls every {case.item} a {wrong}. Correct the context error: {case.context}.",
        case.answer,
        "Need versus want depends on what is necessary in this stated situation.",
        ("income", wrong),
    )
