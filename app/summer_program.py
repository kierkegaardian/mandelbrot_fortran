from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json

from . import db, summer_program_schedule
from .learning_engine import build_skill_stats, mastery_label
from .models import (
    SummerAssessmentRun,
    SummerProgram,
    SummerProgramBlockSummary,
    SummerProgramReviewState,
    SummerProgramStatusSummary,
    SummerProgramTask,
)
from .skill_graph import SKILL_ORDER
from .summer_program_defs import (
    EXIT_AFTER_UNIT,
    FOUNDATION_BRIDGE_LANE,
    FOUNDATION_PROFICIENT_SKILLS,
    MIDPOINT_AFTER_UNIT,
    PLACEMENT_REVIEW_ACCEPTED,
    PLACEMENT_REVIEW_OVERRIDDEN,
    PLACEMENT_REVIEW_PENDING,
    PLACEMENT_STRANDS,
    PREALGEBRA_FINISH_LANE,
    PREALGEBRA_GATE_SUBSKILLS,
    TASK_CYCLE,
    TASK_TARGETS,
    bridge_skill_set,
    default_end_date,
    default_minutes_for_lane,
    finish_definition_json,
    is_optional_unit,
    lane_display_name,
    lane_required_subskills,
    lane_units,
    task_kind_label,
    task_schedule_dates,
    unit_label,
)


@dataclass(frozen=True)
class SummerProgramPace:
    label: str
    expected_completed: int
    completed: int
    remaining: int


@dataclass(frozen=True)
class RemediationTaskSpec:
    source: str
    source_key: str
    anchor_task_id: int
    sequence_index: int
    unit_code: str
    skill: str
    subskill: str | None
    scheduled_date: str
    notes: dict[str, object]


_PLACEMENT_REMEDIATION_TARGETS: dict[str, tuple[tuple[str, str], ...]] = {
    "fractions": (
        ("fractions", "Equivalent fractions"),
        ("fractions", "Compare fractions and mixed numbers"),
    ),
    "integer_order_fluency": (
        ("pre_algebra", "Integer and fraction fluency"),
        ("pre_algebra", "Order of operations"),
    ),
    "variables_equations": (
        ("pre_algebra", "Expressions and variables"),
        ("pre_algebra", "One-step equations"),
        ("pre_algebra", "Two-step equations and inequalities"),
    ),
    "ratios_percent": (
        ("pre_algebra", "Ratios, rates, and proportional relationships"),
        ("pre_algebra", "Percent problems"),
    ),
    "exponents_coordinates": (
        ("pre_algebra", "Exponents, roots, and scientific notation"),
        ("pre_algebra", "Coordinate plane and function tables"),
    ),
}

_ASSESSMENT_REMEDIATION_TARGETS: dict[str, tuple[tuple[str, str], ...]] = {
    "fluency": (("pre_algebra", "Integer and fraction fluency"),),
    "order_ops": (("pre_algebra", "Order of operations"), ("order_of_operations", "Parentheses first")),
    "expressions": (("pre_algebra", "Expressions and variables"),),
    "one_step": (("pre_algebra", "One-step equations"),),
    "two_step": (("pre_algebra", "Two-step equations and inequalities"),),
    "ratios": (
        ("pre_algebra", "Ratios, rates, and proportional relationships"),
        ("ratios", "Equivalent ratios"),
    ),
    "percent": (("pre_algebra", "Percent problems"),),
    "exponents": (("pre_algebra", "Exponents, roots, and scientific notation"),),
    "coordinates": (("pre_algebra", "Coordinate plane and function tables"),),
    "place_value": (
        ("place_value", "Expanded form"),
        ("place_value", "Compare numbers by place value"),
    ),
    "add_subtract": (("add_subtract", "Word problems"),),
    "multiply_divide": (("multiply", "Simple product facts"), ("divide", "Inverse thinking")),
    "money_measurement": (
        ("money", "Making change"),
        ("measurement", "Metric and customary conversions"),
    ),
    "geometry_shapes": (
        ("geometry_shapes", "2D shape attributes"),
        ("geometry_shapes", "Equal shares of shapes"),
    ),
    "data_displays": (
        ("data_displays", "Picture and bar graphs"),
        ("data_displays", "Frequency tables"),
        ("data_displays", "Questions from data displays"),
    ),
    "geometry_measurement": (
        ("geometry_area", "Area of triangles and parallelograms"),
        ("geometry_area", "Surface area and volume"),
    ),
    "data_probability": (
        ("data_analysis", "Histograms"),
        ("data_analysis", "Median, range, and IQR"),
        ("data_analysis", "Sample inferences from displays"),
        ("stats_probability", "Probability models"),
    ),
    "financial_literacy": (
        ("financial_literacy", "Income, gifts, wants, and needs"),
        ("financial_literacy", "Saving, spending, giving, borrowing, and lending"),
        ("financial_literacy", "Accounts, credit reports, and education income"),
        ("financial_literacy", "Budget percentages, net worth, interest, and incentives"),
    ),
    "fractions": (
        ("fractions", "Equivalent fractions"),
        ("fractions", "Compare fractions and mixed numbers"),
    ),
}


def create_summer_program(
    *,
    profile_id: int,
    lane: str,
    start_date: str,
    end_date: str | None,
    days_per_week: int,
    minutes_per_session: int | None,
    student_age_years: int | None,
    created_at: str,
) -> SummerProgram:
    start = date.fromisoformat(start_date)
    finish = date.fromisoformat(end_date) if end_date else default_end_date(start)
    db.archive_summer_programs(profile_id, archived_at=created_at)
    program = db.create_summer_program(
        profile_id=profile_id,
        lane=lane,
        start_date=start.isoformat(),
        end_date=finish.isoformat(),
        days_per_week=max(1, min(7, int(days_per_week))),
        minutes_per_session=int(minutes_per_session or default_minutes_for_lane(lane)),
        status="active",
        finish_definition=finish_definition_json(lane),
        placement_recommendation=None,
        placement_review_status=PLACEMENT_REVIEW_ACCEPTED,
        placement_reviewed_at=None,
        student_age_years=student_age_years,
        created_at=created_at,
        updated_at=created_at,
    )
    generate_program_tasks(program.id, updated_at=created_at)
    refresh_program_plan(program.id, today_iso=start.isoformat())
    return db.get_summer_program(program.id) or program


def list_summer_programs(profile_id: int, *, include_inactive: bool = False) -> list[SummerProgram]:
    return db.list_summer_programs(profile_id, include_inactive=include_inactive)


def get_active_summer_program(profile_id: int) -> SummerProgram | None:
    return db.get_active_summer_program(profile_id)


def generate_program_tasks(program_id: int, *, updated_at: str) -> list[SummerProgramTask]:
    program = db.get_summer_program(program_id)
    if program is None:
        return []
    if db.list_summer_program_tasks(program_id):
        return db.list_summer_program_tasks(program_id)
    unit_defs = lane_units(program.lane)
    total_slots = 1 + (len(unit_defs) * len(TASK_CYCLE)) + 2
    scheduled = task_schedule_dates(date.fromisoformat(program.start_date), total_slots, program.days_per_week)
    payloads: list[dict[str, object]] = []
    sequence = 0
    payloads.append(
        {
            "unit_code": "placement",
            "task_kind": "placement_assessment",
            "skill": "pre_algebra",
            "subskill": None,
            "sequence_index": sequence,
            "status": "pending",
            "target_score_pct": TASK_TARGETS["placement_assessment"],
            "scheduled_date": scheduled[sequence].isoformat(),
            "notes_json": "{}",
        }
    )
    sequence += 1
    for unit in unit_defs:
        for task_kind in TASK_CYCLE:
            payloads.append(
                {
                    "unit_code": unit.code,
                    "task_kind": task_kind,
                    "skill": unit.skill,
                    "subskill": unit.subskill,
                    "sequence_index": sequence,
                    "status": "pending",
                    "target_score_pct": TASK_TARGETS[task_kind],
                    "scheduled_date": scheduled[sequence].isoformat(),
                    "notes_json": "{}",
                }
            )
            sequence += 1
        if unit.code == MIDPOINT_AFTER_UNIT.get(program.lane):
            payloads.append(
                {
                    "unit_code": unit.code,
                    "task_kind": "midpoint_assessment",
                    "skill": unit.skill,
                    "subskill": unit.subskill,
                    "sequence_index": sequence,
                    "status": "pending",
                    "target_score_pct": TASK_TARGETS["midpoint_assessment"],
                    "scheduled_date": scheduled[sequence].isoformat(),
                    "notes_json": "{}",
                }
            )
            sequence += 1
        if unit.code == EXIT_AFTER_UNIT.get(program.lane):
            payloads.append(
                {
                    "unit_code": unit.code,
                    "task_kind": "exit_assessment",
                    "skill": unit.skill,
                    "subskill": unit.subskill,
                    "sequence_index": sequence,
                    "status": "pending",
                    "target_score_pct": TASK_TARGETS["exit_assessment"],
                    "scheduled_date": scheduled[sequence].isoformat(),
                    "notes_json": "{}",
                }
            )
            sequence += 1
    db.replace_summer_program_tasks(program_id, payloads, updated_at=updated_at)
    return db.list_summer_program_tasks(program_id)


def next_summer_program_task(program_id: int) -> SummerProgramTask | None:
    return _queued_summer_program_task(program_id)


def launchable_summer_program_task(program_id: int) -> SummerProgramTask | None:
    program = db.get_summer_program(program_id)
    if program is None:
        return None
    review = summer_program_review_state(program_id)
    if _review_pending(program, review):
        return None
    return _queued_summer_program_task(program_id)


def summer_program_pace_status(program_id: int, *, today: str | None = None) -> SummerProgramPace:
    program = db.get_summer_program(program_id)
    if program is None:
        return SummerProgramPace("on_pace", 0, 0, 0)
    tasks = _core_program_tasks(program, db.list_summer_program_tasks(program_id))
    today_iso = today or date.today().isoformat()
    if not tasks:
        return SummerProgramPace("on_pace", 0, 0, 0)
    completed = sum(1 for item in tasks if item.status == "completed")
    blocked = any(item.status == "blocked" for item in tasks)
    expected = sum(1 for item in tasks if item.scheduled_date <= today_iso)
    remaining = sum(1 for item in tasks if item.status != "completed")
    if remaining == 0:
        return SummerProgramPace("completed", expected, completed, 0)
    if blocked:
        return SummerProgramPace("blocked_on_checkpoint", expected, completed, remaining)
    if completed + 1 < expected:
        return SummerProgramPace("behind", expected, completed, remaining)
    if completed > expected:
        return SummerProgramPace("ahead", expected, completed, remaining)
    return SummerProgramPace("on_pace", expected, completed, remaining)


def record_summer_assessment(
    *,
    program_id: int,
    assessment_type: str,
    score_pct: float,
    passed: bool,
    strand_results: dict[str, float],
    completed_at: str,
) -> SummerAssessmentRun:
    return db.record_summer_assessment(
        program_id=program_id,
        assessment_type=assessment_type,
        score_pct=score_pct,
        passed=passed,
        strand_results_json=json.dumps(strand_results, ensure_ascii=True, sort_keys=True),
        completed_at=completed_at,
    )


def update_task_outcome(
    *,
    task_id: int,
    score_pct: float,
    attempt_id: int,
    completed_at: str,
    strand_results: dict[str, float] | None = None,
) -> None:
    task = db.get_summer_program_task(task_id)
    if task is None:
        return
    program = db.get_summer_program(task.program_id)
    if program is None:
        return
    strands = strand_results or {}
    target = task.target_score_pct
    passed = True if target is None else score_pct >= target
    status = "completed" if passed else "blocked"
    notes = _task_notes(task)
    for key in ("attempt_id", "score_pct", "required_score_pct", "strand_results", "block_reason"):
        notes.pop(key, None)
    if task.task_kind != "placement_assessment":
        notes.pop("weak_strands", None)
    if task.task_kind not in {"placement_assessment", "remediation_review"}:
        notes.pop("next_action", None)
    notes.update(_task_attempt_notes(task, score_pct=score_pct, attempt_id=attempt_id, strand_results=strands))
    if not passed:
        notes["block_reason"] = _default_block_reason(task)
        notes["required_score_pct"] = target
        notes["weak_strands"] = list(_weak_strands_from_scores(strands))
        notes["next_action"] = _default_next_action(notes["block_reason"], task)
    elif task.task_kind == "placement_assessment":
        notes["weak_strands"] = list(_weak_strands_from_scores(strands))
        notes["next_action"] = "Parent review needed after placement."
    db.update_summer_program_task(task.id, status=status, notes_json=json.dumps(notes, ensure_ascii=True, sort_keys=True))
    if task.task_kind.endswith("_assessment"):
        assessment_type = task.task_kind.replace("_assessment", "")
        record_summer_assessment(
            program_id=program.id,
            assessment_type=assessment_type,
            score_pct=score_pct,
            passed=passed,
            strand_results=strands,
            completed_at=completed_at,
        )
        if assessment_type == "placement":
            recommendation = recommended_lane(
                overall=score_pct,
                strand_results=strands,
                student_age_years=program.student_age_years,
            )
            db.update_summer_program(
                program.id,
                placement_recommendation=recommendation,
                placement_review_status=PLACEMENT_REVIEW_PENDING,
                placement_reviewed_at=None,
                updated_at=completed_at,
            )
    refresh_program_plan(program.id, today_iso=completed_at[:10])
    finish = finish_status(program.profile_id, program.id)
    db.update_summer_program(program.id, status=finish, updated_at=completed_at)


def finish_status(profile_id: int, program_id: int) -> str:
    program = db.get_summer_program(program_id)
    if program is None:
        return "active"
    task_statuses = db.list_summer_program_tasks(program_id)
    if any(item.status != "completed" for item in _core_program_tasks(program, task_statuses)):
        return "active"
    required = lane_required_subskills(program.lane)
    progress = {(row.skill, row.subskill): row for row in db.list_subskill_progress(profile_id)}
    for skill, subskills in required.items():
        for subskill in subskills:
            stage = _subskill_stage(progress.get((skill, subskill)))
            if program.lane == PREALGEBRA_FINISH_LANE:
                if stage not in {"Proficient", "Mastered"}:
                    return "active"
            elif stage not in {"Developing", "Proficient", "Mastered"}:
                return "active"
    if program.lane == PREALGEBRA_FINISH_LANE:
        for subskill in PREALGEBRA_GATE_SUBSKILLS:
            if _subskill_stage(progress.get(("pre_algebra", subskill))) != "Mastered":
                return "active"
    else:
        for skill in FOUNDATION_PROFICIENT_SKILLS:
            if not _skill_proficient(profile_id, skill):
                return "active"
    exit_runs = [item for item in db.list_summer_assessment_runs(program.id) if item.assessment_type == "exit"]
    return "completed" if exit_runs and exit_runs[-1].passed else "active"


def latest_assessment_reports(program_id: int) -> list[SummerAssessmentRun]:
    return db.list_summer_assessment_runs(program_id)


def refresh_program_plan(program_id: int, *, today_iso: str | None = None) -> None:
    program = db.get_summer_program(program_id)
    if program is None:
        return
    tasks = db.list_summer_program_tasks(program_id)
    if not tasks:
        return
    today = today_iso or date.today().isoformat()
    remediation_plan = _build_remediation_plan(program, tasks)
    if _ensure_remediation_review_task(program, tasks, remediation_plan):
        tasks = db.list_summer_program_tasks(program_id)
    catch_up_plan = _build_catch_up_plan(program, tasks, today)
    for task in tasks:
        notes = _task_notes(task)
        dynamic_keys = (
            "catch_up_note",
            "catch_up_tasks_per_day",
            "catch_up_date_slot",
        )
        if task.task_kind != "remediation_review":
            dynamic_keys = dynamic_keys + (
                "remediation_focus",
                "remediation_label",
                "remediation_message",
                "remediation_source",
                "remediation_source_key",
            )
        for key in dynamic_keys:
            notes.pop(key, None)
        remediation_update = remediation_plan.get(task.id)
        if remediation_update is not None:
            notes.update(remediation_update)
        catch_up_update = catch_up_plan.get(task.id)
        scheduled_date = task.scheduled_date
        if catch_up_update is not None:
            scheduled_date = str(catch_up_update["scheduled_date"])
            notes.update(catch_up_update["notes"])
        payload = json.dumps(notes, ensure_ascii=True, sort_keys=True)
        if payload != task.notes_json or scheduled_date != task.scheduled_date:
            db.update_summer_program_task(task.id, notes_json=payload, scheduled_date=scheduled_date)


def summer_program_review_state(program_id: int) -> SummerProgramReviewState | None:
    program = db.get_summer_program(program_id)
    if program is None:
        return None
    placement = _latest_assessment(program.id, "placement")
    strands = _assessment_strands(placement)
    latest_score = None if placement is None else float(placement.score_pct)
    weak_strands = _weak_strands_from_scores(strands)
    return SummerProgramReviewState(
        current_lane=program.lane,
        recommended_lane=program.placement_recommendation,
        review_status=program.placement_review_status,
        weak_strands=weak_strands,
        age_gate_note=_age_gate_note(program, latest_score, strands),
        latest_placement_score_pct=latest_score,
    )


def summer_program_block_summary(program_id: int) -> SummerProgramBlockSummary:
    program = db.get_summer_program(program_id)
    if program is None:
        return SummerProgramBlockSummary(None, None, None, None, None, None, (), None)
    review = summer_program_review_state(program_id)
    queued = _queued_summer_program_task(program_id)
    if _review_pending(program, review):
        return SummerProgramBlockSummary(
            reason="awaiting_parent_review",
            task_id=queued.id if queued is not None else None,
            unit_code=queued.unit_code if queued is not None else None,
            task_kind=queued.task_kind if queued is not None else None,
            score_pct=review.latest_placement_score_pct if review is not None else None,
            required_score_pct=None,
            weak_strands=review.weak_strands if review is not None else (),
            next_action="Use Recommended Lane or Keep Current Lane in Parent tools.",
        )
    if queued is not None and _is_optional_task(program, queued):
        return SummerProgramBlockSummary(None, queued.id, queued.unit_code, queued.task_kind, None, None, (), None)
    if queued is not None and queued.task_kind == "remediation_review":
        notes = _task_notes(queued)
        source = _string_or_none(notes.get("remediation_source"))
        if source in {"checkpoint_below_target", "midpoint_below_target", "exit_below_target"}:
            weak = tuple(str(item) for item in notes.get("weak_strands") or ())
            return SummerProgramBlockSummary(
                reason=source,
                task_id=queued.id,
                unit_code=queued.unit_code,
                task_kind=queued.task_kind,
                score_pct=_float_or_none(notes.get("score_pct")),
                required_score_pct=_float_or_none(notes.get("required_score_pct")),
                weak_strands=weak,
                next_action=_string_or_none(notes.get("next_action")),
            )
    if queued is None or queued.status != "blocked":
        return SummerProgramBlockSummary(None, None, None, None, None, None, (), None)
    notes = _task_notes(queued)
    weak = tuple(str(item) for item in notes.get("weak_strands") or ())
    if not weak:
        weak = _weak_strands_from_scores(_coerce_strand_results(notes.get("strand_results")))
    reason = _string_or_none(notes.get("block_reason")) or _default_block_reason(queued)
    return SummerProgramBlockSummary(
        reason=reason,
        task_id=queued.id,
        unit_code=queued.unit_code,
        task_kind=queued.task_kind,
        score_pct=_float_or_none(notes.get("score_pct")),
        required_score_pct=_float_or_none(notes.get("required_score_pct")),
        weak_strands=weak,
        next_action=_string_or_none(notes.get("next_action")) or _default_next_action(reason, queued),
    )


def summer_program_status_summary(profile_id: int, program_id: int) -> SummerProgramStatusSummary | None:
    program = db.get_summer_program(program_id)
    if program is None:
        return None
    review = summer_program_review_state(program_id)
    block = summer_program_block_summary(program_id)
    current_task = _queued_summer_program_task(program_id)
    pace = summer_program_pace_status(program_id)
    finish = finish_status(profile_id, program_id)
    projection = summer_program_schedule.projected_finish(
        tasks=_core_program_tasks(program, db.list_summer_program_tasks(program_id)),
        end_date=program.end_date,
        days_per_week=program.days_per_week,
        today_iso=date.today().isoformat(),
    )
    current_notes = _task_notes(current_task) if current_task is not None else {}
    next_action = block.next_action
    if next_action is None and current_task is not None:
        if _is_optional_task(program, current_task):
            next_action = f"Bonus preview available: {unit_label(program.lane, current_task.unit_code)}."
        else:
            next_action = (
                f"Continue with {task_kind_label(current_task.task_kind)} in "
                f"{unit_label(program.lane, current_task.unit_code)}."
            )
    if next_action is None and finish == "completed":
        next_action = "Summer program complete."
    remediation_focus = tuple(str(item) for item in current_notes.get("remediation_label") or ())
    remediation_note = _string_or_none(current_notes.get("remediation_message"))
    catch_up_note = _string_or_none(current_notes.get("catch_up_note"))
    return SummerProgramStatusSummary(
        program_id=program.id,
        current_lane=program.lane,
        recommended_lane=program.placement_recommendation,
        review_status=review.review_status if review is not None else PLACEMENT_REVIEW_ACCEPTED,
        weak_strands=review.weak_strands if review is not None else (),
        current_blocker=block.reason,
        next_action=next_action,
        pace_label=pace.label,
        finish_state=finish,
        launchable=launchable_summer_program_task(program_id) is not None,
        catch_up_note=catch_up_note,
        projected_finish_date=projection.projected_finish_date,
        projected_finish_note=projection.note,
        remediation_note=remediation_note,
        remediation_focus=remediation_focus,
        current_task=current_task,
        review_state=review
        if review is not None
        else SummerProgramReviewState(program.lane, program.placement_recommendation, program.placement_review_status, (), None, None),
        block_summary=block,
    )


def accept_summer_program_recommendation(program_id: int, reviewed_at: str) -> SummerProgram | None:
    program = db.get_summer_program(program_id)
    if program is None:
        return None
    recommendation = program.placement_recommendation or program.lane
    if recommendation == program.lane:
        db.update_summer_program(
            program.id,
            placement_review_status=PLACEMENT_REVIEW_ACCEPTED,
            placement_reviewed_at=reviewed_at,
            updated_at=reviewed_at,
        )
        refresh_program_plan(program.id, today_iso=reviewed_at[:10])
        return db.get_summer_program(program.id)
    return switch_summer_program_lane(program.id, recommendation, reviewed_at)


def override_summer_program_lane(program_id: int, reviewed_at: str) -> SummerProgram | None:
    program = db.get_summer_program(program_id)
    if program is None:
        return None
    db.update_summer_program(
        program.id,
        placement_review_status=PLACEMENT_REVIEW_OVERRIDDEN,
        placement_reviewed_at=reviewed_at,
        updated_at=reviewed_at,
    )
    refresh_program_plan(program.id, today_iso=reviewed_at[:10])
    return db.get_summer_program(program.id)


def switch_summer_program_lane(program_id: int, lane: str, switched_at: str) -> SummerProgram | None:
    program = db.get_summer_program(program_id)
    if program is None:
        return None
    placement_task = _placement_task(program.id)
    placement_report = _latest_assessment(program.id, "placement")
    db.archive_summer_programs(program.profile_id, archived_at=switched_at)
    new_program = db.create_summer_program(
        profile_id=program.profile_id,
        lane=lane,
        start_date=program.start_date,
        end_date=program.end_date,
        days_per_week=program.days_per_week,
        minutes_per_session=program.minutes_per_session,
        status="active",
        finish_definition=finish_definition_json(lane),
        placement_recommendation=program.placement_recommendation,
        placement_review_status=PLACEMENT_REVIEW_ACCEPTED,
        placement_reviewed_at=switched_at,
        student_age_years=program.student_age_years,
        created_at=switched_at,
        updated_at=switched_at,
    )
    generate_program_tasks(new_program.id, updated_at=switched_at)
    new_placement_task = _placement_task(new_program.id)
    if placement_task is not None and new_placement_task is not None and placement_task.status == "completed":
        db.update_summer_program_task(
            new_placement_task.id,
            status="completed",
            notes_json=placement_task.notes_json,
        )
    if placement_report is not None:
        db.record_summer_assessment(
            program_id=new_program.id,
            assessment_type="placement",
            score_pct=placement_report.score_pct,
            passed=placement_report.passed,
            strand_results_json=placement_report.strand_results_json,
            completed_at=placement_report.completed_at,
        )
    db.update_summer_program(
        new_program.id,
        placement_recommendation=program.placement_recommendation,
        placement_review_status=PLACEMENT_REVIEW_ACCEPTED,
        placement_reviewed_at=switched_at,
        updated_at=switched_at,
    )
    refresh_program_plan(new_program.id, today_iso=switched_at[:10])
    return db.get_summer_program(new_program.id)


def rerun_summer_program_placement(program_id: int, rerun_at: str) -> SummerProgram | None:
    program = db.get_summer_program(program_id)
    if program is None:
        return None
    return create_summer_program(
        profile_id=program.profile_id,
        lane=program.lane,
        start_date=program.start_date,
        end_date=program.end_date,
        days_per_week=program.days_per_week,
        minutes_per_session=program.minutes_per_session,
        student_age_years=program.student_age_years,
        created_at=rerun_at,
    )


def recommended_lane(*, overall: float, strand_results: dict[str, float], student_age_years: int | None) -> str:
    if overall >= 70.0 and all(float(strand_results.get(strand, 0.0)) >= 50.0 for strand in PLACEMENT_STRANDS):
        candidate = PREALGEBRA_FINISH_LANE
    else:
        candidate = FOUNDATION_BRIDGE_LANE
    if student_age_years is not None and student_age_years < 8 and overall < 85.0:
        return FOUNDATION_BRIDGE_LANE
    return candidate


def program_finish_summary(profile_id: int, program_id: int) -> str:
    summary = summer_program_status_summary(profile_id, program_id)
    if summary is None:
        return "No program active."
    detail_parts = [summary.next_action] if summary.next_action else []
    if summary.remediation_note:
        detail_parts.append(summary.remediation_note)
    if summary.catch_up_note:
        detail_parts.append(summary.catch_up_note)
    if summary.projected_finish_note:
        detail_parts.append(summary.projected_finish_note)
    detail = " ".join(part for part in detail_parts if part) or "Continue the current program."
    return (
        f"{lane_display_name(summary.current_lane)} • pace {summary.pace_label} • "
        f"finish {summary.finish_state} • {detail}"
    )


def _build_remediation_plan(
    program: SummerProgram,
    tasks: list[SummerProgramTask],
) -> dict[int, dict[str, object]]:
    queued = _queued_summer_program_task(program.id)
    if queued is None:
        return {}
    if _is_optional_task(program, queued):
        return {}
    if queued.task_kind == "remediation_review":
        notes = _task_notes(queued)
        try:
            anchor_task_id = int(notes.get("remediation_anchor_task_id"))
        except (TypeError, ValueError):
            anchor_task_id = None
        if anchor_task_id is not None:
            anchor = next((task for task in tasks if task.id == anchor_task_id), None)
            if anchor is not None:
                return {
                    anchor.id: {
                        "remediation_focus": list(notes.get("remediation_focus") or ()),
                        "remediation_label": list(notes.get("remediation_label") or ()),
                        "remediation_message": _string_or_none(notes.get("remediation_message")) or "",
                        "remediation_source": _string_or_none(notes.get("remediation_source")) or "review",
                        "remediation_source_key": _string_or_none(notes.get("remediation_source_key")) or f"queued:{queued.id}",
                    }
                }
    if queued.status == "blocked":
        notes = _task_notes(queued)
        targets = _focus_targets_from_labels(tuple(str(item) for item in notes.get("weak_strands") or ()))
        if not targets:
            targets = _focus_targets_from_strand_results(_coerce_strand_results(notes.get("strand_results")))
        if not targets:
            return {}
        focus_labels = tuple(subskill for _skill, subskill in targets)
        source = _string_or_none(notes.get("block_reason")) or "retry"
        return {
            queued.id: {
                "remediation_focus": [_focus_target_payload(skill, subskill) for skill, subskill in targets],
                "remediation_label": list(focus_labels),
                "remediation_message": _remediation_message(
                    task=queued,
                    focus_labels=focus_labels,
                    source=source,
                ),
                "remediation_source": source,
                "remediation_source_key": f"task_attempt:{int(notes.get('attempt_id', queued.id))}",
            }
        }
    reports = latest_assessment_reports(program.id)
    if not reports:
        return {}
    latest = reports[-1]
    if latest.assessment_type == "placement" and program.placement_review_status == PLACEMENT_REVIEW_PENDING:
        return {}
    if latest.assessment_type not in {"placement", "midpoint", "exit"}:
        return {}
    if not latest.passed and latest.assessment_type != "placement":
        return {}
    weak_scores = _assessment_strands(latest)
    weak_targets = _focus_targets_from_strand_results(weak_scores)
    if not weak_targets:
        return {}
    anchor = _assessment_anchor_sequence(tasks, latest.assessment_type)
    pending_after_anchor = [
        task
        for task in tasks
        if task.status == "pending" and task.sequence_index > anchor and task.task_kind != "remediation_review"
    ]
    target_tasks = pending_after_anchor[:2]
    if not target_tasks:
        return {}
    focus_labels = tuple(subskill for _skill, subskill in weak_targets)
    payload = {
        "remediation_focus": [_focus_target_payload(skill, subskill) for skill, subskill in weak_targets],
        "remediation_label": list(focus_labels),
        "remediation_message": _remediation_message(
            task=target_tasks[0],
            focus_labels=focus_labels,
            source=f"{latest.assessment_type}_review",
        ),
        "remediation_source": f"{latest.assessment_type}_review",
        "remediation_source_key": f"assessment:{latest.assessment_type}:{latest.id}",
    }
    return {task.id: payload for task in target_tasks}


def _ensure_remediation_review_task(
    program: SummerProgram,
    tasks: list[SummerProgramTask],
    remediation_plan: dict[int, dict[str, object]],
) -> bool:
    spec = _remediation_review_spec(program, tasks, remediation_plan)
    if spec is None:
        return False
    existing = _existing_remediation_review(tasks, spec.source_key)
    if existing is not None:
        if existing.status == "pending":
            payload = json.dumps(spec.notes, ensure_ascii=True, sort_keys=True)
            if existing.notes_json != payload:
                db.update_summer_program_task(existing.id, notes_json=payload)
        return False
    db.shift_summer_program_task_sequences(program.id, starting_from=spec.sequence_index, delta=1)
    db.create_summer_program_task(
        program_id=program.id,
        unit_code=spec.unit_code,
        task_kind="remediation_review",
        skill=spec.skill,
        subskill=spec.subskill,
        sequence_index=spec.sequence_index,
        status="pending",
        target_score_pct=None,
        scheduled_date=spec.scheduled_date,
        notes_json=json.dumps(spec.notes, ensure_ascii=True, sort_keys=True),
    )
    return True


def _remediation_review_spec(
    program: SummerProgram,
    tasks: list[SummerProgramTask],
    remediation_plan: dict[int, dict[str, object]],
) -> RemediationTaskSpec | None:
    if not remediation_plan:
        return None
    candidates = [task for task in tasks if task.id in remediation_plan]
    if not candidates:
        return None
    anchor = min(candidates, key=lambda item: item.sequence_index)
    payload = remediation_plan.get(anchor.id) or {}
    source = _string_or_none(payload.get("remediation_source")) or "review"
    source_key = _string_or_none(payload.get("remediation_source_key")) or f"{source}:{anchor.id}"
    notes = _task_notes(anchor)
    focus = payload.get("remediation_focus")
    if not isinstance(focus, list) or not focus:
        return None
    labels = payload.get("remediation_label")
    focus_labels = [str(item) for item in labels] if isinstance(labels, list) else []
    remediation_notes: dict[str, object] = {
        "remediation_focus": focus,
        "remediation_label": focus_labels,
        "remediation_message": _string_or_none(payload.get("remediation_message")) or _remediation_message(anchor, tuple(focus_labels), source),
        "remediation_source": source,
        "remediation_source_key": source_key,
        "remediation_anchor_task_id": anchor.id,
        "remediation_anchor_task_kind": anchor.task_kind,
        "next_action": _remediation_task_next_action(program, source, anchor),
    }
    weak_strands = tuple(str(item) for item in notes.get("weak_strands") or ())
    if weak_strands:
        remediation_notes["weak_strands"] = list(weak_strands)
    score_pct = _float_or_none(notes.get("score_pct"))
    required_score_pct = _float_or_none(notes.get("required_score_pct"))
    if score_pct is not None:
        remediation_notes["score_pct"] = score_pct
    if required_score_pct is not None:
        remediation_notes["required_score_pct"] = required_score_pct
    first_target = next(
        (
            (item.get("skill"), item.get("subskill"))
            for item in focus
            if isinstance(item, dict) and item.get("skill") and item.get("subskill")
        ),
        (anchor.skill, anchor.subskill),
    )
    task_skill = str(first_target[0] or anchor.skill)
    task_subskill = None if first_target[1] is None else str(first_target[1])
    return RemediationTaskSpec(
        source=source,
        source_key=source_key,
        anchor_task_id=anchor.id,
        sequence_index=anchor.sequence_index,
        unit_code=anchor.unit_code,
        skill=task_skill,
        subskill=task_subskill,
        scheduled_date=anchor.scheduled_date,
        notes=remediation_notes,
    )


def _existing_remediation_review(tasks: list[SummerProgramTask], source_key: str) -> SummerProgramTask | None:
    for task in tasks:
        if task.task_kind != "remediation_review":
            continue
        notes = _task_notes(task)
        if _string_or_none(notes.get("remediation_source_key")) == source_key:
            return task
    return None


def _build_catch_up_plan(
    program: SummerProgram,
    tasks: list[SummerProgramTask],
    today_iso: str,
) -> dict[int, dict[str, object]]:
    return summer_program_schedule.build_catch_up_plan(
        tasks=_core_program_tasks(program, tasks),
        end_date=program.end_date,
        days_per_week=program.days_per_week,
        today_iso=today_iso,
    )


def _is_optional_task(program: SummerProgram, task: SummerProgramTask) -> bool:
    return is_optional_unit(program.lane, task.unit_code)


def _core_program_tasks(program: SummerProgram, tasks: list[SummerProgramTask]) -> list[SummerProgramTask]:
    return [task for task in tasks if not _is_optional_task(program, task)]


def _skill_proficient(profile_id: int, skill: str) -> bool:
    stats = build_skill_stats(db.list_attempts(profile_id), tuple(SKILL_ORDER))
    item = stats.get(skill)
    if item is None:
        return False
    return mastery_label(item.attempts, item.weighted_accuracy, item.recent_accuracy, item.perfect_attempts) in {
        "Proficient",
        "Mastered",
    }


def _subskill_stage(item) -> str:
    if item is None:
        return "Not started"
    if item.mastered:
        return "Mastered"
    if item.current_streak >= 2:
        return "Proficient"
    if item.current_streak >= 1:
        return "Developing"
    return "Needs work"


def _queued_summer_program_task(program_id: int) -> SummerProgramTask | None:
    tasks = db.list_summer_program_tasks(program_id)
    for task in tasks:
        if task.status in {"pending", "blocked"}:
            return task
    return None


def _placement_task(program_id: int) -> SummerProgramTask | None:
    for task in db.list_summer_program_tasks(program_id):
        if task.task_kind == "placement_assessment":
            return task
    return None


def _assessment_anchor_sequence(tasks: list[SummerProgramTask], assessment_type: str) -> int:
    task_kind = f"{assessment_type}_assessment"
    for task in tasks:
        if task.task_kind == task_kind:
            return task.sequence_index
    return -1


def _latest_assessment(program_id: int, assessment_type: str) -> SummerAssessmentRun | None:
    reports = [item for item in db.list_summer_assessment_runs(program_id) if item.assessment_type == assessment_type]
    return reports[-1] if reports else None


def _review_pending(program: SummerProgram, review: SummerProgramReviewState | None) -> bool:
    return bool(
        review is not None
        and program.placement_recommendation
        and review.review_status == PLACEMENT_REVIEW_PENDING
    )


def _task_attempt_notes(
    task: SummerProgramTask,
    *,
    score_pct: float,
    attempt_id: int,
    strand_results: dict[str, float],
) -> dict[str, object]:
    notes: dict[str, object] = {
        "attempt_id": attempt_id,
        "score_pct": round(score_pct, 2),
    }
    if task.target_score_pct is not None:
        notes["required_score_pct"] = float(task.target_score_pct)
    if strand_results:
        notes["strand_results"] = strand_results
    return notes


def _task_notes(task: SummerProgramTask) -> dict[str, object]:
    try:
        raw = json.loads(task.notes_json or "{}")
    except json.JSONDecodeError:
        return {}
    return raw if isinstance(raw, dict) else {}


def _default_block_reason(task: SummerProgramTask) -> str:
    if task.task_kind == "checkpoint":
        return "checkpoint_below_target"
    if task.task_kind == "midpoint_assessment":
        return "midpoint_below_target"
    if task.task_kind == "exit_assessment":
        return "exit_below_target"
    return "checkpoint_below_target"


def _default_next_action(reason: str, task: SummerProgramTask | None) -> str:
    if reason == "awaiting_parent_review":
        return "Parent must review the placement recommendation before the program can continue."
    if task is None:
        return "Review the Summer Program in Parent tools."
    program = db.get_summer_program(task.program_id)
    unit = unit_label(program.lane, task.unit_code) if program is not None else task.unit_code
    if program is not None and _is_optional_task(program, task):
        return f"Optional preview: continue with {task_kind_label(task.task_kind)} in {unit}."
    if reason == "checkpoint_below_target":
        target = f"{task.target_score_pct:.0f}%" if task.target_score_pct is not None else "the target"
        return f"Retry the {task_kind_label(task.task_kind)} for {unit} and reach {target}."
    if reason == "midpoint_below_target":
        target = f"{task.target_score_pct:.0f}%" if task.target_score_pct is not None else "the target"
        return f"Review recent units, then retry the midpoint and reach {target}."
    if reason == "exit_below_target":
        target = f"{task.target_score_pct:.0f}%" if task.target_score_pct is not None else "the target"
        return f"Do targeted review, then retry the exit assessment and reach {target}."
    return f"Continue with {task_kind_label(task.task_kind)} in {unit}."


def _remediation_task_next_action(program: SummerProgram, source: str, anchor_task: SummerProgramTask) -> str:
    unit = unit_label(program.lane, anchor_task.unit_code)
    if source == "placement_review":
        return f"Finish this remediation review, then start {unit}."
    if source == "midpoint_review":
        return f"Finish this remediation review, then continue with {unit}."
    if source == "exit_review":
        return "Finish this remediation review, then decide whether to run another exit attempt."
    if source.endswith("_below_target"):
        return f"Finish this remediation review, then retry the {task_kind_label(anchor_task.task_kind).lower()} in {unit}."
    return f"Finish this remediation review, then continue with {unit}."


def _focus_targets_from_labels(labels: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    out: list[tuple[str, str]] = []
    for label in labels:
        out.extend(_PLACEMENT_REMEDIATION_TARGETS.get(label, ()))
        out.extend(_ASSESSMENT_REMEDIATION_TARGETS.get(label, ()))
    return _dedupe_targets(out)


def _focus_targets_from_strand_results(strand_results: dict[str, float]) -> tuple[tuple[str, str], ...]:
    weak = _weak_strands_from_scores(strand_results)
    return _focus_targets_from_labels(weak)


def _dedupe_targets(targets: list[tuple[str, str]]) -> tuple[tuple[str, str], ...]:
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for target in targets:
        if target in seen:
            continue
        seen.add(target)
        out.append(target)
    return tuple(out[:4])


def _focus_target_payload(skill: str, subskill: str) -> dict[str, str]:
    return {"skill": skill, "subskill": subskill}


def remediation_targets_for_task(task: SummerProgramTask) -> tuple[tuple[str, str], ...]:
    notes = _task_notes(task)
    raw = notes.get("remediation_focus")
    if not isinstance(raw, list):
        return ()
    out: list[tuple[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        skill = _string_or_none(item.get("skill"))
        subskill = _string_or_none(item.get("subskill"))
        if skill and subskill:
            out.append((skill, subskill))
    return tuple(out)


def _remediation_message(task: SummerProgramTask, focus_labels: tuple[str, ...], source: str) -> str:
    if not focus_labels:
        return ""
    focus_text = ", ".join(focus_labels[:2])
    if source == "placement_review":
        return f"Remediation pack: strengthen {focus_text} before the program ramps up."
    if source == "midpoint_review":
        return f"Remediation pack: revisit {focus_text} before the next major check."
    if source == "exit_review":
        return f"Remediation pack: review {focus_text} before another exit attempt."
    if source.endswith("_below_target"):
        return f"Remediation retry: start with {focus_text} before retrying this task."
    return f"Remediation pack: focus on {focus_text}."


def _study_dates_between(start_iso: str, end_iso: str, days_per_week: int) -> list[str]:
    return summer_program_schedule.study_dates_between(start_iso, end_iso, days_per_week)


def _assign_remaining_dates(*, remaining_count: int, available_days: list[str]) -> list[str]:
    return summer_program_schedule.assign_remaining_dates(
        remaining_count=remaining_count,
        available_days=available_days,
    )


def _catch_up_note(remaining_tasks: int, remaining_days: int, tasks_per_day: int) -> str:
    return summer_program_schedule.catch_up_note(remaining_tasks, remaining_days, tasks_per_day)


def _assessment_strands(report: SummerAssessmentRun | None) -> dict[str, float]:
    if report is None:
        return {}
    try:
        raw = json.loads(report.strand_results_json or "{}")
    except json.JSONDecodeError:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in raw.items():
        try:
            out[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return out


def _weak_strands_from_scores(strand_results: dict[str, float], *, threshold: float = 70.0, limit: int = 3) -> tuple[str, ...]:
    weak = [name for name, score in sorted(strand_results.items(), key=lambda item: item[1]) if float(score) < threshold]
    return tuple(weak[:limit])


def _coerce_strand_results(value: object) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, float] = {}
    for key, item in value.items():
        try:
            out[str(key)] = float(item)
        except (TypeError, ValueError):
            continue
    return out


def _age_gate_note(
    program: SummerProgram,
    latest_score: float | None,
    strand_results: dict[str, float],
) -> str | None:
    if program.student_age_years is None or program.student_age_years >= 8:
        return None
    if program.placement_recommendation != FOUNDATION_BRIDGE_LANE or latest_score is None:
        return None
    if latest_score >= 70.0 and all(float(strand_results.get(strand, 0.0)) >= 50.0 for strand in PLACEMENT_STRANDS):
        return "Age guidance kept Foundation Bridge as the default lane for this child."
    return "Foundation Bridge remains the default lane for younger learners."


def _float_or_none(value: object) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
