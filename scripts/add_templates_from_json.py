from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app import db
from app.time_utils import now_iso


def main() -> None:
    parser = argparse.ArgumentParser(description="Load question templates from a JSON manifest.")
    parser.add_argument("--json", required=True, help="Path to JSON manifest")
    parser.add_argument("--book-id", type=int, default=0, help="Optional book_id to attach templates to")
    parser.add_argument(
        "--no-replace",
        action="store_true",
        help="Do not delete existing templates with the same (skill, subskill, label) before inserting.",
    )
    parser.add_argument(
        "--require-external-id",
        action="store_true",
        help="Fail if a manifest item does not include external_id.",
    )
    args = parser.parse_args()

    db.init_db()

    path = Path(args.json).expanduser().resolve()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise SystemExit("Manifest must be a JSON list of templates.")

    created = 0
    replaced = 0
    missing_external_id = 0
    for item in raw:
        external_id = str(item.get("external_id") or "").strip()
        if not external_id:
            missing_external_id += 1
            if args.require_external_id:
                raise SystemExit("Manifest item missing required external_id.")
        if external_id:
            replaced += db.delete_template_by_external_id(external_id)
        elif not args.no_replace:
            replaced += db.delete_templates_by_identity(
                skill=str(item["skill"]),
                subskill=str(item.get("subskill", "core")),
                label=str(item.get("label", "")) or str(item["skill"]),
            )
        template_id = db.create_question_template(
            book_id=(int(args.book_id) if int(args.book_id) > 0 else None),
            external_id=external_id or None,
            skill=str(item["skill"]),
            subskill=str(item.get("subskill", "core")),
            label=str(item.get("label", "")) or str(item["skill"]),
            mode=str(item.get("mode", "expression")),
            prompt_template=str(item["prompt_template"]),
            answer_expr=str(item["answer_expr"]),
            constraint_expr=str(item.get("constraint_expr", "")),
            explanation_template=str(item.get("explanation_template", "Use the standard method.")),
            min_level=int(item.get("min_level", 1)),
            max_level=int(item.get("max_level", 3)),
            choice_spread=float(item.get("choice_spread", 4.0)),
            active=bool(item.get("active", True)),
            created_at=now_iso(),
            archetype_id=str(item.get("archetype_id") or external_id or "") or None,
            reasoning_kind=str(item.get("reasoning_kind", "legacy")),
            misconceptions_json=json.dumps(item.get("misconceptions", []), ensure_ascii=True),
        )
        for var in item.get("vars", []):
            db.add_template_var(
                template_id,
                name=str(var["name"]),
                kind=str(var.get("kind", "int")),
                min_value=float(var["min"]),
                max_value=float(var["max"]),
                step=float(var.get("step", 1)),
            )
        created += 1

    print(
        f"templates_created={created} templates_replaced={replaced} "
        f"missing_external_id={missing_external_id}"
    )


if __name__ == "__main__":
    main()
