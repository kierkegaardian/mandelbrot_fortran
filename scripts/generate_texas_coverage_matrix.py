from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.texas_coverage_matrix import build_texas_coverage_report, render_texas_coverage_markdown  # noqa: E402


DEFAULT_OUTPUT = REPO_ROOT / "docs" / "texas-teks-coverage-matrix.md"


def main(argv: list[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    output = Path(args[0]) if args else DEFAULT_OUTPUT
    report = build_texas_coverage_report()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_texas_coverage_markdown(report), encoding="utf-8")
    print(f"Wrote {output}")
    print(f"Rows={len(report.rows)} missing={len(report.missing_rows)} weak={len(report.weak_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
