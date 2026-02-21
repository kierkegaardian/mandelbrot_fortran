from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app import db  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="List template catalog with external IDs.")
    parser.add_argument("--skill", default="", help="Optional skill filter")
    parser.add_argument("--external-id-prefix", default="", help="Optional external_id prefix filter")
    parser.add_argument("--include-inactive", action="store_true", help="Include inactive templates")
    parser.add_argument("--limit", type=int, default=200, help="Maximum rows to print")
    args = parser.parse_args()

    db.init_db()
    rows = db.list_all_question_templates(active_only=not args.include_inactive)
    if args.skill:
        rows = [row for row in rows if row.skill == args.skill]
    if args.external_id_prefix:
        prefix = str(args.external_id_prefix)
        rows = [row for row in rows if row.external_id and str(row.external_id).startswith(prefix)]
    rows = rows[: max(1, int(args.limit))]

    print("id\texternal_id\tskill\tsubskill\tmode\tactive\tlabel")
    for row in rows:
        external_id = row.external_id or ""
        print(
            f"{row.id}\t{external_id}\t{row.skill}\t{row.subskill}\t"
            f"{row.mode}\t{int(row.active)}\t{row.label}"
        )


if __name__ == "__main__":
    main()
