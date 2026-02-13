from __future__ import annotations

import argparse
import sys
from pathlib import Path
import random

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app import db  # noqa: E402
from app.template_engine import instantiate_template, mc_choices  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry-run all question templates for errors.")
    parser.add_argument("--samples", type=int, default=50, help="Number of instantiations per template")
    parser.add_argument("--skill", default="", help="Optional skill filter")
    parser.add_argument("--include-inactive", action="store_true", help="Include inactive templates")
    parser.add_argument("--mc", action="store_true", help="Also dry-run MC distractor generation")
    args = parser.parse_args()

    db.init_db()
    templates = db.list_all_question_templates(active_only=not args.include_inactive)
    if args.skill:
        templates = [t for t in templates if t.skill == args.skill]

    rng = random.Random(0)
    total = 0
    failures: list[str] = []
    for template in templates:
        vars_spec = db.list_template_vars(template.id)
        for i in range(int(args.samples)):
            total += 1
            try:
                inst = instantiate_template(template, vars_spec, rng=rng)
                if args.mc and inst.numeric_answer is not None:
                    choices = mc_choices(inst.numeric_answer, spread=template.choice_spread, rng=rng)
                    if len(set(choices)) != 4:
                        raise ValueError("choices not unique")
            except Exception as exc:
                failures.append(
                    f"template_id={template.id} skill={template.skill} subskill={template.subskill} "
                    f"label={template.label!r} sample={i+1} error={type(exc).__name__}: {exc}"
                )
                break

    print(f"templates={len(templates)} samples_per={int(args.samples)} total_runs={total} failures={len(failures)}")
    if failures:
        print("\n".join(failures[:50]))
        raise SystemExit(1)


if __name__ == "__main__":
    main()

