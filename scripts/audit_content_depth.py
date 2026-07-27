#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.content_depth.audit import build_depth_audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit all Foundations-to-Algebra-1 depth manifests.")
    parser.add_argument("--seeds", type=int, default=100, help="deterministic seeds per archetype/form")
    parser.add_argument("--summary-only", action="store_true", help="print counts without all thin-row details")
    args = parser.parse_args()
    report = build_depth_audit(seeds_per_archetype=max(1, args.seeds))
    print(
        f"rows={len(report.rows)} ready={report.ready_count} "
        f"thin={report.thin_count} missing={report.missing_count} seeds={max(1, args.seeds)}"
    )
    if not args.summary_only:
        for row in report.weakest_rows:
            if row.readiness == "ready":
                continue
            print(f"{row.readiness}: {row.skill}/{row.subskill}: {'; '.join(row.notes)}")
    return 0 if report.depth_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
