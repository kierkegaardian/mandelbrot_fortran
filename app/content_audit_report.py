from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import html
import re

from .content_audit import SummerContentAuditRow, SummerResourceReview, summer_resource_review
from .paths import worksheets_dir
from .summer_program_defs import lane_display_name


@dataclass(frozen=True)
class ResourceReviewReport:
    path: str
    lane: str
    title: str
    ready_count: int
    thin_count: int
    missing_count: int
    row_count: int


def generate_resource_review_report(lane: str) -> ResourceReviewReport:
    review = summer_resource_review(lane)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    title = f"{lane_display_name(lane)} Resource Review"
    filename = f"resource_review_{_safe_filename_part(lane)}_{stamp}.html"
    path = worksheets_dir() / filename
    path.write_text(_render_report_html(title=title, review=review), encoding="utf-8")
    return ResourceReviewReport(
        path=str(path),
        lane=lane,
        title=title,
        ready_count=review.ready_count,
        thin_count=review.thin_count,
        missing_count=review.missing_count,
        row_count=len(review.rows),
    )


def _safe_filename_part(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    return safe.strip("_") or "summer_program"


def _render_report_html(*, title: str, review: SummerResourceReview) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    body = [
        "<html><head><meta charset='utf-8'>",
        f"<title>{html.escape(title)}</title>",
        "<style>",
        "body{font-family:Arial,sans-serif;margin:36px;color:#20242a;line-height:1.35}",
        "h1{color:#2d5d7c;margin-bottom:4px}",
        ".meta{color:#5b6f84;margin:4px 0}",
        ".summary{display:flex;gap:12px;margin:18px 0;flex-wrap:wrap}",
        ".pill{border:1px solid #dfe6ec;border-radius:6px;padding:8px 10px;background:#f7fafc}",
        "table{border-collapse:collapse;width:100%;font-size:13px}",
        "th,td{border:1px solid #dfe6ec;padding:7px;text-align:left;vertical-align:top}",
        "th{background:#eef5f8;color:#2f4858}",
        ".ready{color:#236b3f;font-weight:bold}",
        ".thin{color:#8a5b3c;font-weight:bold}",
        ".missing{color:#9a2f2f;font-weight:bold}",
        ".notes{color:#5b6f84}",
        "@media print{*{print-color-adjust:exact;-webkit-print-color-adjust:exact}body{margin:24px}a{color:#20242a}}",
        "</style></head><body>",
        f"<h1>{html.escape(title)}</h1>",
        f"<div class='meta'>Generated: {html.escape(generated_at)}</div>",
        f"<div class='meta'>Lane: {html.escape(lane_display_name(review.lane))}</div>",
        "<div class='summary'>",
        f"<div class='pill'>Ready: {review.ready_count}</div>",
        f"<div class='pill'>Thin: {review.thin_count}</div>",
        f"<div class='pill'>Missing: {review.missing_count}</div>",
        f"<div class='pill'>Rows: {len(review.rows)}</div>",
        "</div>",
        "<table>",
        "<thead><tr>",
        "<th>Status</th><th>Unit</th><th>Target</th><th>Question Sources</th>",
        "<th>Help</th><th>Notes</th>",
        "</tr></thead><tbody>",
    ]
    for row in review.weakest_rows:
        body.append(_row_html(row))
    if not review.rows:
        body.append("<tr><td colspan='6'>No auditable Summer Program resources for this lane.</td></tr>")
    body.extend(["</tbody></table>", "</body></html>"])
    return "\n".join(body)


def _row_html(row: SummerContentAuditRow) -> str:
    lane_part = "Bonus" if row.optional else "Core"
    question_sources = [
        f"Expression templates: {row.expression_template_count}",
        f"Word templates: {row.word_template_count}",
        f"Scaffold steps: {row.scaffold_step_count}",
        f"Native generator: {'yes' if row.native_question_available else 'no'}",
    ]
    help_parts = [
        _link_or_status("Khan", row.khan_url),
        _link_or_status("Open resource", row.open_resource_url),
        f"Intuition: {'yes' if row.has_intuition else 'no'}",
    ]
    notes = "; ".join(row.notes) if row.notes else "Ready"
    return (
        "<tr>"
        f"<td class='{html.escape(row.readiness)}'>{html.escape(row.readiness.title())}</td>"
        f"<td>{html.escape(lane_part)}<br>{html.escape(row.unit_label)}</td>"
        f"<td>{html.escape(row.skill)}<br>{html.escape(row.subskill)}</td>"
        f"<td>{'<br>'.join(html.escape(part) for part in question_sources)}</td>"
        f"<td>{'<br>'.join(help_parts)}</td>"
        f"<td class='notes'>{html.escape(notes)}</td>"
        "</tr>"
    )


def _link_or_status(label: str, url: str) -> str:
    if not url:
        return f"{html.escape(label)}: missing"
    safe_url = html.escape(url, quote=True)
    return f"{html.escape(label)}: <a href='{safe_url}'>{safe_url}</a>"
