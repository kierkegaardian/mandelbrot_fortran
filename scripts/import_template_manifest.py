from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import db  # noqa: E402


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def import_manifest(path: Path) -> tuple[int, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Manifest must be a JSON array")

    inserted = 0
    replaced = 0
    for item in payload:
        external_id = item.get("external_id")
        if external_id:
            replaced += db.delete_template_by_external_id(str(external_id))

        template_id = db.create_question_template(
            book_id=item.get("book_id"),
            external_id=external_id,
            skill=str(item["skill"]),
            subskill=str(item.get("subskill", "General")),
            label=str(item.get("label", "Template item")),
            mode=str(item.get("mode", "expression")),
            prompt_template=str(item["prompt_template"]),
            answer_expr=str(item["answer_expr"]),
            constraint_expr=str(item.get("constraint_expr", "")),
            explanation_template=str(item.get("explanation_template", "Solve using the modeled relationship.")),
            min_level=int(item.get("min_level", 1)),
            max_level=int(item.get("max_level", 3)),
            choice_spread=float(item.get("choice_spread", 4.0)),
            active=bool(item.get("active", True)),
            created_at=_now_iso(),
            archetype_id=str(item.get("archetype_id") or external_id or "") or None,
            reasoning_kind=str(item.get("reasoning_kind", "legacy")),
            misconceptions_json=json.dumps(item.get("misconceptions", []), ensure_ascii=True),
        )
        for var in item.get("vars", []):
            db.add_template_var(
                template_id=template_id,
                name=str(var["name"]),
                kind=str(var.get("kind", "int")),
                min_value=float(var["min"]),
                max_value=float(var["max"]),
                step=float(var.get("step", 1)),
            )
        inserted += 1

    return inserted, replaced


def main() -> int:
    parser = argparse.ArgumentParser(description="Import template manifest JSON into app.db.")
    parser.add_argument("manifest", help="Path to template manifest JSON file")
    args = parser.parse_args()

    path = Path(args.manifest)
    if not path.exists():
        raise SystemExit(f"manifest does not exist: {path}")

    inserted, replaced = import_manifest(path)
    print(f"manifest={path} inserted={inserted} replaced={replaced}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
