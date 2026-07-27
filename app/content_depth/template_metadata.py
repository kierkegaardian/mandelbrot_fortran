from __future__ import annotations

import json

from ..template_engine import validate_numeric_expression


class TemplateMetadataError(ValueError):
    pass


def validate_misconceptions_json(value: str | None) -> str:
    text = value or "[]"
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TemplateMetadataError("Misconceptions must be valid JSON.") from exc
    if not isinstance(raw, list):
        raise TemplateMetadataError("Misconceptions must be a JSON list.")
    seen: set[str] = set()
    normalized: list[dict[str, str]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise TemplateMetadataError(f"Misconception {index + 1} must be an object.")
        code = str(item.get("code", "")).strip()
        answer_expr = str(item.get("answer_expr", "")).strip()
        feedback = str(item.get("feedback", "")).strip()
        hint = str(item.get("hint", "")).strip()
        recovery = str(item.get("recovery_archetype_id", "")).strip()
        if not code or code in seen:
            raise TemplateMetadataError(f"Misconception {index + 1} has an empty or duplicate code.")
        if not answer_expr or not feedback or not hint or not recovery:
            raise TemplateMetadataError(f"Misconception {code} is missing required metadata.")
        try:
            validate_numeric_expression(answer_expr)
        except ValueError as exc:
            raise TemplateMetadataError(f"Misconception {code} has an unsafe answer expression.") from exc
        seen.add(code)
        normalized.append(
            {
                "code": code,
                "answer_expr": answer_expr,
                "feedback": feedback,
                "hint": hint,
                "recovery_archetype_id": recovery,
            }
        )
    return json.dumps(normalized, sort_keys=True, ensure_ascii=True)
