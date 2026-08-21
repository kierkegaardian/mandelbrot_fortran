from __future__ import annotations

from .models import WorkedExample


_STAGE_LABELS = {
    "model": "1. Model",
    "guided": "2. Guided check",
    "guided_check": "2. Guided check",
    "transfer": "3. Independent transfer",
    "independent_transfer": "3. Independent transfer",
}


def worked_example_text(example: WorkedExample | None) -> str:
    if example is None:
        return "No worked example is available for this question yet."
    lines = [example.title]
    for step in example.steps:
        label = _STAGE_LABELS.get(step.stage, step.stage.replace("_", " ").title())
        lines.extend(("", f"{label}: {step.prompt}", step.explanation))
        if step.expected_answer:
            lines.append(f"Check: {step.expected_answer}")
    return "\n".join(lines)
