from __future__ import annotations

import random
from dataclasses import dataclass


FINANCIAL_LITERACY_SUBSKILLS: tuple[str, ...] = (
    "Income, gifts, wants, and needs",
    "Saving, spending, giving, borrowing, and lending",
    "Scarcity, planned spending, and credit choices",
    "Expenses, profit, savings options, and institutions",
    "Taxes, payments, records, and simple budgets",
    "Accounts, credit reports, and education income",
    "Budget percentages, net worth, interest, and incentives",
)

FINANCIAL_LITERACY_KHAN_URL = "https://www.khanacademy.org/college-careers-more/personal-finance"
_KHAN_URL_BY_SUBSKILL: dict[str, str] = {
    "Income, gifts, wants, and needs": FINANCIAL_LITERACY_KHAN_URL,
    "Saving, spending, giving, borrowing, and lending": (
        "https://www.khanacademy.org/college-careers-more/personal-finance/pf-saving-and-budgeting"
    ),
    "Scarcity, planned spending, and credit choices": FINANCIAL_LITERACY_KHAN_URL,
    "Expenses, profit, savings options, and institutions": FINANCIAL_LITERACY_KHAN_URL,
    "Taxes, payments, records, and simple budgets": (
        "https://www.khanacademy.org/college-careers-more/personal-finance/pf-saving-and-budgeting"
    ),
    "Accounts, credit reports, and education income": FINANCIAL_LITERACY_KHAN_URL,
    "Budget percentages, net worth, interest, and incentives": (
        "https://www.khanacademy.org/college-careers-more/personal-finance/pf-interest-and-debt"
    ),
}


@dataclass(frozen=True)
class FinancialProblem:
    prompt: str
    answer: str
    explanation: str
    subskill: str
    choices: list[str] | None


@dataclass(frozen=True)
class FinancialIntuition:
    mental_model: str
    common_mistake: str
    try_this: str


def _money(value: float) -> str:
    return f"${value:.2f}"


def _selected_subskill(requested: str | None) -> str:
    if requested in FINANCIAL_LITERACY_SUBSKILLS:
        return requested
    return random.choice(FINANCIAL_LITERACY_SUBSKILLS)


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


def _money_choices(correct: float, *, enabled: bool) -> list[str] | None:
    if not enabled:
        return None
    cents = int(round(correct * 100))
    values = {cents}
    for delta in (100, -100, 250, -250, 500, -500, 1000, -1000):
        if len(values) >= 4:
            break
        values.add(max(0, cents + delta))
    ordered = list(values)
    random.shuffle(ordered)
    return [_money(value / 100) for value in ordered]


def _number_choices(correct: int, *, enabled: bool) -> list[str] | None:
    if not enabled:
        return None
    values = {correct}
    for delta in (1, -1, 2, -2, 5, -5, 10, -10):
        if len(values) >= 4:
            break
        values.add(max(0, correct + delta))
    ordered = list(values)
    random.shuffle(ordered)
    return [str(value) for value in ordered]


def build_financial_literacy_problem(
    level: int,
    requested_subskill: str | None,
    *,
    multiple_choice: bool,
) -> FinancialProblem:
    subskill = _selected_subskill(requested_subskill)
    if subskill == "Income, gifts, wants, and needs":
        item, answer = random.choice(
            (
                ("earning 6 dollars for raking leaves", "income"),
                ("getting 10 dollars in a birthday card", "gift"),
                ("new headphones when old ones still work", "want"),
                ("lunch for a school day", "need"),
            )
        )
        return FinancialProblem(
            prompt=f"Classify this: {item}.",
            answer=answer,
            explanation="Income is earned, gifts are received, needs are necessary, and wants are optional.",
            subskill=subskill,
            choices=_text_choices(answer, ("income", "gift", "want", "need"), enabled=multiple_choice),
        )

    if subskill == "Saving, spending, giving, borrowing, and lending":
        weekly = random.randint(2, 9)
        weeks = random.randint(3, 8)
        answer = weekly * weeks
        return FinancialProblem(
            prompt=f"If you save ${weekly} each week for {weeks} weeks, how many dollars will you save?",
            answer=str(answer),
            explanation="Repeated saving accumulates by adding the same amount each week.",
            subskill=subskill,
            choices=_number_choices(answer, enabled=multiple_choice),
        )

    if subskill == "Scarcity, planned spending, and credit choices":
        answer = random.choice(("planned spending", "unplanned spending"))
        event = "saving for a bike before buying it" if answer == "planned spending" else "buying a toy on impulse"
        return FinancialProblem(
            prompt=f"Is this planned or unplanned spending: {event}?",
            answer=answer,
            explanation="Planned spending is decided before purchase; unplanned spending happens without that plan.",
            subskill=subskill,
            choices=_text_choices(
                answer,
                ("planned spending", "unplanned spending", "responsible lending", "income"),
                enabled=multiple_choice,
            ),
        )

    if subskill == "Expenses, profit, savings options, and institutions":
        price = random.randint(8, 18)
        cost = random.randint(2, price - 2)
        sold = random.randint(3, 8)
        profit = (price - cost) * sold
        return FinancialProblem(
            prompt=f"You sell {sold} items for ${price} each. Each item costs ${cost} to make. What is the profit?",
            answer=str(profit),
            explanation="Profit is revenue minus cost. Find profit per item, then multiply by items sold.",
            subskill=subskill,
            choices=_number_choices(profit, enabled=multiple_choice),
        )

    if subskill == "Taxes, payments, records, and simple budgets":
        amount = random.randint(20, 90)
        tax_rate = random.choice((5, 6, 8))
        tax = round(amount * tax_rate / 100, 2)
        return FinancialProblem(
            prompt=f"A purchase costs ${amount}. Sales tax is {tax_rate} percent. How much tax is owed?",
            answer=_money(tax),
            explanation="Sales tax is the purchase amount multiplied by the tax rate as a decimal.",
            subskill=subskill,
            choices=_money_choices(tax, enabled=multiple_choice),
        )

    if subskill == "Accounts, credit reports, and education income":
        start = random.randint(30, 100)
        deposit = random.randint(10, 60)
        withdrawal = random.randint(5, start + deposit - 5)
        balance = start + deposit - withdrawal
        return FinancialProblem(
            prompt=(
                f"A check register starts at ${start}. You deposit ${deposit} and withdraw ${withdrawal}. "
                "What is the new balance?"
            ),
            answer=_money(float(balance)),
            explanation="A register adds deposits and subtracts withdrawals to keep the account balance current.",
            subskill=subskill,
            choices=_money_choices(float(balance), enabled=multiple_choice),
        )

    principal = random.choice((100, 200, 300, 500))
    rate = random.choice((4, 5, 6, 8))
    years = random.randint(1, 4)
    interest = principal * rate * years / 100
    return FinancialProblem(
        prompt=f"What simple interest is earned on ${principal} at {rate} percent for {years} years?",
        answer=_money(interest),
        explanation="Simple interest is principal times rate times time.",
        subskill=subskill,
        choices=_money_choices(interest, enabled=multiple_choice),
    )


_INTUITION_BY_SUBSKILL: dict[str, FinancialIntuition] = {
    "Income, gifts, wants, and needs": FinancialIntuition(
        "First name the question: source, purpose, or job skill. Then use the scenario evidence to decide.",
        "Calling every received dollar income or naming a need or want without checking the situation.",
        "Classify one earned item and one gift, decide one need or want from its context, then name a useful skill for a simple job.",
    ),
    "Saving, spending, giving, borrowing, and lending": FinancialIntuition(
        "Money choices move value across time: spend now, save for later, give away, borrow, or lend.",
        "Treating borrowed money like free money instead of money that must be repaid.",
        "Save the same small amount for four weeks and predict the total before adding.",
    ),
    "Scarcity, planned spending, and credit choices": FinancialIntuition(
        "Scarcity forces choices, so a plan helps compare benefits, costs, and future obligations.",
        "Using credit because something is wanted without checking repayment.",
        "Pick one desired item and write what you would give up to buy it.",
    ),
    "Expenses, profit, savings options, and institutions": FinancialIntuition(
        "A financial decision compares incoming money, outgoing expenses, risk, and where money is kept.",
        "Confusing revenue with profit before subtracting the cost to produce or sell.",
        "For a small sale, compute revenue, cost, and profit as three separate numbers.",
    ),
    "Taxes, payments, records, and simple budgets": FinancialIntuition(
        "Budgets and records tell where money came from, where it went, and what obligations were paid.",
        "Ignoring taxes or fees and thinking the sticker price is the full cost.",
        "Write a three-line budget with income, expenses, and leftover money.",
    ),
    "Accounts, credit reports, and education income": FinancialIntuition(
        "Accounts, credit records, and training choices affect both short-term access and long-term income.",
        "Thinking debit and credit behave the same because both use a card.",
        "Compare one job needing training with one not needing training, then compare long-term income.",
    ),
    "Budget percentages, net worth, interest, and incentives": FinancialIntuition(
        "Advanced finance combines percentages, assets, liabilities, interest, and incentives into decisions.",
        "Comparing interest offers without checking rate, time, and starting amount.",
        "Compute simple interest on the same amount at two rates and compare the difference.",
    ),
}


def intuition_for(subskill: str | None) -> FinancialIntuition | None:
    if subskill is None:
        return None
    return _INTUITION_BY_SUBSKILL.get(subskill)


def khan_url_for(subskill: str | None) -> str:
    if subskill is None:
        return FINANCIAL_LITERACY_KHAN_URL
    return _KHAN_URL_BY_SUBSKILL.get(subskill, FINANCIAL_LITERACY_KHAN_URL)
