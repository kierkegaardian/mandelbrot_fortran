from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app import db  # noqa: E402


def _infer_year(text: str) -> int | None:
    match = re.search(r"(19|20)\d{2}", text)
    if not match:
        return None
    year = int(match.group(0))
    if 1900 <= year <= 2100:
        return year
    return None


def _year_for_test(test) -> int | None:
    if test.year is not None:
        return int(test.year)
    for value in (test.exam_code, test.title, test.pdf_path):
        year = _infer_year(str(value))
        if year is not None:
            return year
    return None


def _missing_years(start: int, end: int, present: set[int]) -> list[int]:
    return [y for y in range(start, end + 1) if y not in present]


def main() -> int:
    parser = argparse.ArgumentParser(description="Report SAT/GRE historical coverage and missing year gaps.")
    parser.add_argument("--start-year", type=int, default=1980, help="Coverage start year")
    parser.add_argument(
        "--end-year",
        type=int,
        default=datetime.now(timezone.utc).year,
        help="Coverage end year (default: current year UTC)",
    )
    parser.add_argument(
        "--out",
        default="reviews/historical_coverage_report.md",
        help="Output markdown file path",
    )
    args = parser.parse_args()

    db.init_db()
    tests = db.list_historical_tests(exam_type="all")
    by_type: dict[str, list[int]] = {"sat": [], "gre": []}
    unknown_year: dict[str, int] = {"sat": 0, "gre": 0}

    for test in tests:
        exam_type = str(test.exam_type).lower()
        if exam_type not in {"sat", "gre"}:
            continue
        year = _year_for_test(test)
        if year is None:
            unknown_year[exam_type] += 1
            continue
        by_type[exam_type].append(year)

    sat_present = set(y for y in by_type["sat"] if args.start_year <= y <= args.end_year)
    gre_present = set(y for y in by_type["gre"] if args.start_year <= y <= args.end_year)
    sat_missing = _missing_years(args.start_year, args.end_year, sat_present)
    gre_missing = _missing_years(args.start_year, args.end_year, gre_present)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Historical Coverage Report",
        "",
        f"Range: {args.start_year}-{args.end_year}",
        "",
        "## SAT",
        f"- tests with known year in range: {len(sat_present)}",
        f"- tests with unknown year metadata: {unknown_year['sat']}",
        f"- missing years ({len(sat_missing)}): {', '.join(str(y) for y in sat_missing) if sat_missing else 'none'}",
        "",
        "## GRE",
        f"- tests with known year in range: {len(gre_present)}",
        f"- tests with unknown year metadata: {unknown_year['gre']}",
        f"- missing years ({len(gre_missing)}): {', '.join(str(y) for y in gre_missing) if gre_missing else 'none'}",
        "",
        "## Notes",
        "- Years are inferred from explicit `year` column first, then exam code/title/pdf filename.",
        "- Unknown-year tests should be renamed/tagged with year to improve gap detection.",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
