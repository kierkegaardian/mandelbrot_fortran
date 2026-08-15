from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .models import SummerProgramTask


@dataclass(frozen=True)
class ProjectedFinish:
    projected_finish_date: str | None
    note: str | None
    slips_past_end: bool


def study_dates_between(start_iso: str, end_iso: str, days_per_week: int) -> list[str]:
    start = date.fromisoformat(start_iso)
    end = date.fromisoformat(end_iso)
    if end < start:
        end = start
    scheduled: list[str] = []
    cursor = start
    while cursor <= end:
        day_index = (cursor - start).days % 7
        if day_index < _normalized_days_per_week(days_per_week):
            scheduled.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return scheduled


def assign_remaining_dates(*, remaining_count: int, available_days: list[str]) -> list[str]:
    if remaining_count <= 0:
        return []
    if not available_days:
        return [date.today().isoformat()] * remaining_count
    if remaining_count <= len(available_days):
        return available_days[:remaining_count]
    assigned: list[str] = []
    slots = len(available_days)
    for idx in range(remaining_count):
        day_idx = min(slots - 1, (idx * slots) // remaining_count)
        assigned.append(available_days[day_idx])
    return assigned


def build_catch_up_plan(
    *,
    tasks: list[SummerProgramTask],
    end_date: str,
    days_per_week: int,
    today_iso: str,
) -> dict[int, dict[str, object]]:
    remaining = [task for task in tasks if task.status in {"pending", "blocked"}]
    if not remaining:
        return {}
    overdue = [task for task in remaining if task.scheduled_date < today_iso]
    if not overdue and not any(task.status == "blocked" for task in remaining):
        return {}
    available_days = study_dates_between(today_iso, end_date, days_per_week)
    if not available_days:
        available_days = [today_iso]
    assigned_dates = assign_remaining_dates(remaining_count=len(remaining), available_days=available_days)
    tasks_per_day = max(assigned_dates.count(day) for day in set(assigned_dates))
    note = catch_up_note(len(remaining), len(available_days), tasks_per_day)
    out: dict[int, dict[str, object]] = {}
    for task, scheduled_date in zip(remaining, assigned_dates, strict=False):
        out[task.id] = {
            "scheduled_date": scheduled_date,
            "notes": {
                "catch_up_note": note,
                "catch_up_tasks_per_day": tasks_per_day,
                "catch_up_date_slot": scheduled_date,
            },
        }
    return out


def projected_finish(
    *,
    tasks: list[SummerProgramTask],
    end_date: str,
    days_per_week: int,
    today_iso: str,
) -> ProjectedFinish:
    remaining = [task for task in tasks if task.status in {"pending", "blocked"}]
    if not remaining:
        return ProjectedFinish(today_iso, "Projected finish: complete.", False)
    start_iso = max(today_iso, min(task.scheduled_date for task in remaining))
    projected_dates = future_study_dates(start_iso, len(remaining), days_per_week)
    projected_date = projected_dates[-1] if projected_dates else today_iso
    slips = projected_date > end_date
    if slips:
        note = (
            f"Projected finish slips past {_format_short_date(end_date)} "
            f"to {_format_short_date(projected_date)}."
        )
    else:
        note = f"Projected finish: {_format_short_date(projected_date)}."
    return ProjectedFinish(projected_date, note, slips)


def future_study_dates(start_iso: str, count: int, days_per_week: int) -> list[str]:
    if count <= 0:
        return []
    start = date.fromisoformat(start_iso)
    out: list[str] = []
    cursor = start
    normalized = _normalized_days_per_week(days_per_week)
    while len(out) < count:
        day_index = (cursor - start).days % 7
        if day_index < normalized:
            out.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return out


def catch_up_note(remaining_tasks: int, remaining_days: int, tasks_per_day: int) -> str:
    if tasks_per_day <= 1:
        return f"Catch-up plan: {remaining_tasks} tasks over {remaining_days} study days."
    return (
        f"Catch-up plan: {remaining_tasks} tasks over {remaining_days} study days. "
        f"Expect up to {tasks_per_day} tasks on catch-up days."
    )


def _normalized_days_per_week(days_per_week: int) -> int:
    return max(1, min(7, int(days_per_week)))


def _format_short_date(day_iso: str) -> str:
    day = date.fromisoformat(day_iso)
    return f"{day.strftime('%b')} {day.day}"
