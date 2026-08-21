from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import html

from .paths import worksheets_dir
from .quiz_content import ContentUnavailableError
from .quiz_engine import Question, generate_question
from .texas_grade_goals import TexasGoal, texas_grade_plan
from .content_depth.printable import blank_proof_table, completed_proof_table
from .content_depth.generation import generate_depth_question
from .content_depth.models import ContentStatus, QuestionRequest, ReasoningKind
from .content_depth.registry import depth_spec_for
from .ui_settings import load_ui_settings


@dataclass(frozen=True)
class AssessmentItem:
    goal: TexasGoal
    subskill: str
    question: Question


@dataclass(frozen=True)
class SchoolYearAssessmentPacket:
    path: str
    grade: int
    title: str
    items: tuple[AssessmentItem, ...]
    skipped: tuple[str, ...]


def generate_texas_grade_assessment(
    grade: int,
    *,
    include_stretch: bool,
    questions_per_subskill: int = 1,
) -> SchoolYearAssessmentPacket:
    plan = texas_grade_plan(grade)
    items: list[AssessmentItem] = []
    skipped: list[str] = []
    for goal in plan.goals:
        if not goal.quiz_ready or goal.skill is None:
            skipped.append(f"{goal.label}: content gap")
            continue
        if goal.stretch and not include_stretch:
            skipped.append(f"{goal.label}: stretch goal paused")
            continue
        for subskill in goal.subskills:
            for _idx in range(max(1, int(questions_per_subskill))):
                try:
                    question = _assessment_question(goal, subskill)
                except (ContentUnavailableError, ValueError, ZeroDivisionError) as exc:
                    skipped.append(f"{goal.label} / {subskill}: {exc}")
                    continue
                items.append(AssessmentItem(goal=goal, subskill=subskill, question=question))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    title = f"Texas Grade {grade} Math Assessment"
    filename = f"texas_grade_{grade}_assessment_{stamp}.html"
    path = worksheets_dir() / filename
    path.write_text(
        _render_packet_html(
            title=title,
            grade=grade,
            include_stretch=include_stretch,
            items=tuple(items),
            skipped=tuple(skipped),
        ),
        encoding="utf-8",
    )
    return SchoolYearAssessmentPacket(
        path=str(path),
        grade=grade,
        title=title,
        items=tuple(items),
        skipped=tuple(skipped),
    )


def _assessment_question(goal: TexasGoal, subskill: str) -> Question:
    assert goal.skill is not None
    spec = depth_spec_for(goal.skill, subskill)
    if (
        load_ui_settings().curriculum_depth_beta
        and spec is not None
        and spec.content_status is ContentStatus.READY
    ):
        proof_id = next(
            (item.archetype_id for item in spec.archetypes if item.reasoning_kind is ReasoningKind.PROOF),
            None,
        )
        if proof_id is not None:
            return generate_depth_question(
                QuestionRequest(
                    goal.skill,
                    goal.quiz_level,
                    "typed",
                    subskill,
                    preferred_archetype_id=proof_id,
                )
            )
    return generate_question(goal.skill, goal.quiz_level, "typed", subskill=subskill)


def _render_packet_html(
    *,
    title: str,
    grade: int,
    include_stretch: bool,
    items: tuple[AssessmentItem, ...],
    skipped: tuple[str, ...],
) -> str:
    plan = texas_grade_plan(grade)
    body = [
        "<html><head><meta charset='utf-8'>",
        "<style>",
        "body{font-family:Arial,sans-serif;margin:40px;color:#20242a;line-height:1.35}",
        "h1{color:#2d5d7c;margin-bottom:4px}",
        "h2{margin-top:24px;color:#2f4858}",
        ".meta{color:#5b6f84;margin:4px 0}",
        ".question{margin:14px 0;padding:12px;border:1px solid #dfe6ec;border-radius:6px;break-inside:avoid}",
        ".goal{font-weight:bold;color:#2f4858}",
        ".subskill{color:#5b6f84;font-size:0.94em}",
        ".answer{margin-top:8px}",
        ".proof-table{border-collapse:collapse;width:100%;margin-top:8px}.proof-table th,.proof-table td{border:1px solid #777;padding:8px;height:24px}",
        ".skipped{color:#8a5b3c}",
        "@media print{*{print-color-adjust:exact;-webkit-print-color-adjust:exact}.answer-key{break-before:page}}",
        "</style></head><body>",
        f"<h1>{html.escape(title)}</h1>",
        f"<div class='meta'>TEKS source: {html.escape(plan.tac_section)} • {html.escape(plan.source_url)}</div>",
        f"<div class='meta'>Stretch goals: {'included' if include_stretch else 'paused'}</div>",
        f"<div class='meta'>Focal areas: {html.escape(' | '.join(plan.focal_areas))}</div>",
        "<h2>Questions</h2>",
    ]
    for index, item in enumerate(items, start=1):
        refs = ", ".join(item.goal.standard_refs)
        body.append("<div class='question'>")
        body.append(f"<div class='goal'>{index}. {html.escape(item.goal.label)} ({html.escape(refs)})</div>")
        body.append(f"<div class='subskill'>{html.escape(item.subskill)}</div>")
        body.append(f"<p>{html.escape(item.question.prompt)}</p>")
        if item.question.proof_spec is not None:
            body.append(blank_proof_table(item.question.proof_spec))
        else:
            body.append("<div class='answer'>Answer: ______________________________</div>")
        body.append("</div>")
    if not items:
        body.append("<p>No quiz-ready questions could be generated for this grade target.</p>")

    body.append("<div class='answer-key'>")
    body.append("<h2>Answer Key</h2>")
    for index, item in enumerate(items, start=1):
        if item.question.proof_spec is not None:
            body.append(f"<div>{index}. <span class='subskill'>({html.escape(item.subskill)})</span></div>")
            body.append(completed_proof_table(item.question.proof_spec))
        else:
            body.append(
                f"<div>{index}. {html.escape(str(item.question.correct_answer))} "
                f"<span class='subskill'>({html.escape(item.subskill)})</span></div>"
            )
    if skipped:
        body.append("<h2>Coverage Notes</h2>")
        body.append("<ul class='skipped'>")
        for note in skipped:
            body.append(f"<li>{html.escape(note)}</li>")
        body.append("</ul>")
    body.append("</div>")
    body.append("</body></html>")
    return "\n".join(body)
