from __future__ import annotations

from datetime import datetime
import html
from pathlib import Path

from ..paths import worksheets_dir
from .audit import DepthAuditReport, build_depth_audit


def render_depth_review_html(report: DepthAuditReport) -> str:
    rows: list[str] = []
    for row in report.weakest_rows:
        counts = ", ".join(f"{kind}={count}" for kind, count in row.reasoning_counts)
        notes = "; ".join(row.notes) or "Depth contract satisfied."
        rows.append(
            "<tr>"
            f"<td>{html.escape(row.skill)}</td>"
            f"<td>{html.escape(row.subskill)}</td>"
            f"<td>{html.escape(row.readiness)}</td>"
            f"<td>{html.escape(counts)}</td>"
            f"<td>{row.worked_example_steps}</td>"
            f"<td>{row.misconception_count}</td>"
            f"<td>{'yes' if row.has_proof else 'n/a'}</td>"
            f"<td>{html.escape(notes)}</td>"
            f"<td>{html.escape(row.sample_prompt)}</td>"
            "</tr>"
        )
    return """<!doctype html>
<html><head><meta charset="utf-8"><title>MandelQuest Depth Review</title>
<style>body{font-family:sans-serif;margin:2rem;color:#20242a}table{border-collapse:collapse;width:100%%;font-size:12px}
th,td{border:1px solid #bbb;padding:6px;vertical-align:top}th{background:#eef2f6}.ready{color:#176b31}</style></head>
<body><h1>Foundations-to-Algebra-1 Depth Review</h1>
<p>Ready: %d &nbsp; Thin: %d &nbsp; Missing: %d &nbsp; Total: %d</p>
<table><thead><tr><th>Skill</th><th>Subskill</th><th>Status</th><th>Archetypes</th><th>Example steps</th>
<th>Misconceptions</th><th>Proof</th><th>Notes</th><th>Sample</th></tr></thead><tbody>%s</tbody></table></body></html>""" % (
        report.ready_count, report.thin_count, report.missing_count, len(report.rows), "".join(rows)
    )


def generate_depth_review_report(
    output_dir: Path | None = None, *, seeds_per_archetype: int = 25
) -> Path:
    report = build_depth_audit(seeds_per_archetype=seeds_per_archetype)
    target_dir = output_dir or worksheets_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = target_dir / f"curriculum_depth_review_{stamp}.html"
    path.write_text(render_depth_review_html(report), encoding="utf-8")
    return path
