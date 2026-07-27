from __future__ import annotations

from dataclasses import dataclass
import socket
from typing import Sequence

from . import db, summer_program, sync_apply, sync_client, sync_payloads, sync_state, sync_store
from .models import Assignment, Profile, QuizAttempt, QuizSet
from .time_utils import now_iso


@dataclass(frozen=True)
class QuestionResultInput:
    skill: str
    subskill: str | None
    question_label: str
    mode: str
    prompt: str
    correct_answer: str
    user_answer: str
    is_correct: bool
    explanation: str
    archetype_id: str | None = None
    misconception_code: str | None = None
    response_kind: str | None = None
    recovery_corrected_answer: str | None = None
    recovery_transfer_archetype_id: str | None = None
    recovery_transfer_answer: str | None = None
    recovery_transfer_correct: bool | None = None


@dataclass(frozen=True)
class RecordCompletedQuizResult:
    attempt_id: int
    completed_assignments: int
    completed_summer_task: bool
    summer_program_note: str | None


@dataclass(frozen=True)
class SyncRunResult:
    attempted: bool
    ok: bool
    enabled: bool
    pending_count: int
    uploaded_count: int
    applied_count: int
    status: sync_client.SyncStatus | None
    message: str


@dataclass(frozen=True)
class PairingActionResult:
    ok: bool
    family_id: str | None
    pairing_token: str | None
    message: str


def list_profiles() -> list[Profile]:
    return db.list_profiles()


def create_profile(name: str, role: str, created_at: str) -> Profile:
    profile = db.create_profile(name, role, created_at)
    sync_store.enqueue_change(
        entity_type="profiles",
        local_id=profile.id,
        action="upsert",
        occurred_at=created_at,
        extra={"name": name, "role": role},
    )
    return profile


def delete_profile(profile_id: int, deleted_at: str | None = None) -> None:
    occurred_at = deleted_at or now_iso()
    for target in sync_payloads.dependent_delete_targets_for_profile(profile_id):
        sync_store.enqueue_change(
            entity_type=target.entity_type,
            local_id=target.local_id,
            action="delete",
            occurred_at=occurred_at,
            extra={"deleted_at": occurred_at},
            known_sync_id=target.entity_sync_id,
        )
    sync_id = sync_store.entity_sync_id("profiles", profile_id)
    if sync_id:
        sync_store.enqueue_change(
            entity_type="profiles",
            local_id=profile_id,
            action="delete",
            occurred_at=occurred_at,
            extra={"deleted_at": occurred_at},
            known_sync_id=sync_id,
        )
    db.delete_profile(profile_id)


def list_quiz_sets() -> list[QuizSet]:
    return db.list_quiz_sets()


def create_quiz_set(
    name: str,
    skill: str,
    question_type: str,
    num_questions: int,
    level: int,
    created_at: str,
    mode_intuition_pct: int | None = None,
    mode_expression_pct: int | None = None,
    mode_word_pct: int | None = None,
) -> QuizSet:
    quiz_set = db.create_quiz_set(
        name,
        skill,
        question_type,
        num_questions,
        level,
        created_at,
        mode_intuition_pct,
        mode_expression_pct,
        mode_word_pct,
    )
    sync_store.enqueue_change(
        entity_type="quiz_sets",
        local_id=quiz_set.id,
        action="upsert",
        occurred_at=created_at,
        extra={
            "name": name,
            "skill": skill,
            "question_type": question_type,
            "num_questions": int(num_questions),
            "level": int(level),
        },
    )
    return quiz_set


def update_quiz_set(
    quiz_set_id: int,
    name: str,
    skill: str,
    question_type: str,
    num_questions: int,
    level: int,
    mode_intuition_pct: int | None = None,
    mode_expression_pct: int | None = None,
    mode_word_pct: int | None = None,
    updated_at: str | None = None,
) -> None:
    occurred_at = updated_at or now_iso()
    db.update_quiz_set(
        quiz_set_id,
        name,
        skill,
        question_type,
        num_questions,
        level,
        mode_intuition_pct,
        mode_expression_pct,
        mode_word_pct,
        occurred_at,
    )
    sync_store.enqueue_change(
        entity_type="quiz_sets",
        local_id=quiz_set_id,
        action="upsert",
        occurred_at=occurred_at,
        extra={
            "name": name,
            "skill": skill,
            "question_type": question_type,
            "num_questions": int(num_questions),
            "level": int(level),
        },
    )


def delete_quiz_set(quiz_set_id: int, deleted_at: str | None = None) -> None:
    occurred_at = deleted_at or now_iso()
    sync_id = sync_store.entity_sync_id("quiz_sets", quiz_set_id)
    if sync_id:
        sync_store.enqueue_change(
            entity_type="quiz_sets",
            local_id=quiz_set_id,
            action="delete",
            occurred_at=occurred_at,
            extra={"deleted_at": occurred_at},
            known_sync_id=sync_id,
        )
    db.delete_quiz_set(quiz_set_id)


def list_assignments(
    profile_id: int,
    active_only: bool | None = True,
    *,
    skill: str | None = None,
    target_type: str | None = None,
    limit: int | None = None,
) -> list[Assignment]:
    return db.list_assignments(
        profile_id,
        active_only=active_only,
        skill=skill,
        target_type=target_type,
        limit=limit,
    )


def assignment_completion_analytics(profile_id: int, recent_days: int = 30) -> dict[str, object]:
    return db.assignment_completion_analytics(profile_id, recent_days=recent_days)


def get_next_active_assignment(profile_id: int) -> Assignment | None:
    return db.get_next_active_assignment(profile_id)


def create_assignment(
    *,
    profile_id: int,
    skill: str,
    subskill: str | None,
    target_type: str,
    target_value: float,
    level: int,
    num_questions: int,
    question_type: str,
    mode_intuition_pct: int | None,
    mode_expression_pct: int | None,
    mode_word_pct: int | None,
    notes: str,
    created_at: str,
) -> int:
    assignment_id = db.create_assignment(
        profile_id=profile_id,
        skill=skill,
        subskill=subskill,
        target_type=target_type,
        target_value=target_value,
        level=level,
        num_questions=num_questions,
        question_type=question_type,
        mode_intuition_pct=mode_intuition_pct,
        mode_expression_pct=mode_expression_pct,
        mode_word_pct=mode_word_pct,
        notes=notes,
        created_at=created_at,
    )
    sync_store.enqueue_change(
        entity_type="assignments",
        local_id=assignment_id,
        action="upsert",
        occurred_at=created_at,
        extra={
            "profile_id": int(profile_id),
            "skill": skill,
            "subskill": subskill,
            "target_type": target_type,
        },
    )
    return assignment_id


def complete_assignment(assignment_id: int, completed_at: str) -> None:
    db.set_assignment_active(assignment_id, False, completed_at=completed_at)
    sync_store.enqueue_change(
        entity_type="assignments",
        local_id=assignment_id,
        action="upsert",
        occurred_at=completed_at,
        extra={"active": False, "completed_at": completed_at},
    )


def list_attempts(profile_id: int) -> list[QuizAttempt]:
    return db.list_attempts(profile_id)


def record_completed_quiz(
    *,
    profile_id: int,
    quiz_set_id: int | None,
    skill: str,
    question_type: str,
    num_questions: int,
    level: int,
    score: int,
    created_at: str,
    elapsed_seconds: float | None,
    question_results: Sequence[QuestionResultInput],
    record_progress: bool,
    streak_to_master: int,
    record_daily_review: bool,
    summer_program_task_id: int | None = None,
) -> RecordCompletedQuizResult:
    attempt_id = db.create_attempt(
        profile_id=profile_id,
        quiz_set_id=quiz_set_id,
        skill=skill,
        question_type=question_type,
        num_questions=num_questions,
        level=level,
        score=score,
        created_at=created_at,
        elapsed_seconds=elapsed_seconds,
    )
    sync_store.enqueue_change(
        entity_type="quiz_attempts",
        local_id=attempt_id,
        action="upsert",
        occurred_at=created_at,
        extra={
            "profile_id": int(profile_id),
            "quiz_set_id": int(quiz_set_id) if quiz_set_id is not None else None,
            "skill": skill,
            "score": int(score),
        },
    )

    for item in question_results:
        if record_progress and item.subskill is not None:
            db.upsert_subskill_progress(
                profile_id,
                item.skill,
                item.subskill,
                item.is_correct,
                created_at,
                streak_to_master,
            )
        question_id = db.add_question_result(
            attempt_id,
            item.skill,
            item.subskill,
            item.question_label,
            item.mode,
            item.prompt,
            item.correct_answer,
            item.user_answer,
            item.is_correct,
            item.explanation,
            archetype_id=item.archetype_id,
            misconception_code=item.misconception_code,
            response_kind=item.response_kind,
            sync_updated_at=created_at,
        )
        if item.recovery_corrected_answer is not None:
            db.add_quiz_recovery(
                question_id,
                item.misconception_code,
                item.recovery_corrected_answer,
                item.recovery_transfer_archetype_id,
                item.recovery_transfer_answer,
                item.recovery_transfer_correct,
                created_at,
            )
        sync_store.enqueue_change(
            entity_type="quiz_questions",
            local_id=question_id,
            action="upsert",
            occurred_at=created_at,
            extra={
                "attempt_local_id": int(attempt_id),
                "profile_id": int(profile_id),
                "skill": item.skill,
                "subskill": item.subskill,
            },
        )

    completed_assignment_ids = db.evaluate_assignments_for_attempt_ids(profile_id, attempt_id, created_at)
    for assignment_id in completed_assignment_ids:
        sync_store.enqueue_change(
            entity_type="assignments",
            local_id=assignment_id,
            action="upsert",
            occurred_at=created_at,
            extra={"active": False, "completed_at": created_at},
        )

    if record_daily_review or summer_program_task_id is not None:
        db.record_daily_review_completion(profile_id, created_at)

    completed_summer_task = False
    summer_program_note = None
    if summer_program_task_id is not None:
        score_pct = (float(score) / float(max(1, num_questions))) * 100.0
        strand_results = _summer_program_strand_scores(question_results)
        summer_program.update_task_outcome(
            task_id=summer_program_task_id,
            score_pct=score_pct,
            attempt_id=attempt_id,
            completed_at=created_at,
            strand_results=strand_results if strand_results else None,
        )
        task = db.get_summer_program_task(summer_program_task_id)
        completed_summer_task = task is not None
        if task is not None:
            summer_program_note = summer_program.program_finish_summary(profile_id, task.program_id)

    return RecordCompletedQuizResult(
        attempt_id=attempt_id,
        completed_assignments=len(completed_assignment_ids),
        completed_summer_task=completed_summer_task,
        summer_program_note=summer_program_note,
    )


def _summer_program_strand_scores(question_results: Sequence[QuestionResultInput]) -> dict[str, float]:
    buckets: dict[str, list[bool]] = {}
    for item in question_results:
        if "•" not in item.question_label:
            continue
        _prefix, strand = [part.strip() for part in item.question_label.split("•", 1)]
        if not strand:
            continue
        buckets.setdefault(strand, []).append(bool(item.is_correct))
    out: dict[str, float] = {}
    for strand, values in buckets.items():
        if not values:
            continue
        out[strand] = (sum(1 for value in values if value) / float(len(values))) * 100.0
    return out


def sync_now() -> SyncRunResult:
    pending_count = sync_store.count_pending_changes()
    state = sync_state.load_sync_state()
    if not state.sync_enabled:
        return SyncRunResult(
            attempted=False,
            ok=False,
            enabled=False,
            pending_count=pending_count,
            uploaded_count=0,
            applied_count=0,
            status=None,
            message="Family sync is disabled on this device.",
        )

    at_iso = now_iso()
    state = sync_state.ensure_device_id()
    health_status = sync_client.sync_now()
    if not health_status.ok:
        detail = health_status.error_message or health_status.error_code or "Sync probe failed."
        sync_state.save_sync_probe_result(succeeded=False, at_iso=at_iso, error_message=detail)
        return SyncRunResult(
            attempted=True,
            ok=False,
            enabled=True,
            pending_count=pending_count,
            uploaded_count=0,
            applied_count=0,
            status=health_status,
            message=detail,
        )
    if not state.family_id or not state.pairing_token:
        paired = start_family_sync()
        if not paired.ok:
            return SyncRunResult(
                attempted=True,
                ok=False,
                enabled=True,
                pending_count=pending_count,
                uploaded_count=0,
                applied_count=0,
                status=health_status,
                message=paired.message,
            )
        state = sync_state.load_sync_state()

    pending_entries = sync_store.list_pending_changes(limit=2000)
    outbound: list[dict[str, object]] = []
    skipped_ids: list[int] = []
    for entry in pending_entries:
        change = sync_payloads.build_outbound_change(entry)
        if change is None:
            skipped_ids.append(entry.id)
            continue
        change["client_change_id"] = entry.id
        outbound.append(change)

    batch = sync_client.sync_batch(
        family_id=state.family_id or "",
        pairing_token=state.pairing_token or "",
        device_id=state.device_id or "",
        since_cursor=state.server_cursor,
        changes=outbound,
    )
    if not batch.ok:
        detail = batch.error_message or batch.error_code or "Batch sync failed."
        sync_state.save_sync_probe_result(succeeded=False, at_iso=at_iso, error_message=detail)
        return SyncRunResult(
            attempted=True,
            ok=False,
            enabled=True,
            pending_count=pending_count,
            uploaded_count=0,
            applied_count=0,
            status=health_status,
            message=detail,
        )

    if skipped_ids:
        sync_store.mark_changes_synced(skipped_ids, at_iso)
    if batch.accepted_client_change_ids:
        sync_store.mark_changes_synced(batch.accepted_client_change_ids, at_iso)
    applied_count = sync_apply.apply_remote_changes(
        [
            {
                "entity_type": change.entity_type,
                "action": change.action,
                "entity_sync_id": change.entity_sync_id,
                "updated_at": change.updated_at,
                "payload": change.data,
            }
            for change in batch.changes
        ]
    )
    sync_state.save_sync_server_cursor(batch.server_cursor)
    sync_state.save_sync_probe_result(succeeded=True, at_iso=at_iso)
    remaining = sync_store.count_pending_changes()
    message = (
        f"Uploaded {len(batch.accepted_client_change_ids)} change(s), "
        f"applied {applied_count} remote change(s), "
        f"{remaining} still queued locally."
    )
    return SyncRunResult(
        attempted=True,
        ok=True,
        enabled=True,
        pending_count=remaining,
        uploaded_count=len(batch.accepted_client_change_ids),
        applied_count=applied_count,
        status=health_status,
        message=message,
    )


def start_family_sync() -> PairingActionResult:
    state = sync_state.ensure_device_id()
    link = sync_client.bootstrap_family(
        device_id=state.device_id or "",
        device_label=_device_label(),
    )
    if not link.ok or not link.family_id or not link.pairing_token:
        detail = link.error_message or link.error_code or "Could not enroll device for family sync."
        at_iso = now_iso()
        sync_state.save_sync_probe_result(succeeded=False, at_iso=at_iso, error_message=detail)
        return PairingActionResult(ok=False, family_id=None, pairing_token=None, message=detail)
    paired = sync_state.save_sync_pairing(
        family_id=link.family_id,
        pairing_token=link.pairing_token,
    )
    return PairingActionResult(
        ok=True,
        family_id=paired.family_id,
        pairing_token=paired.pairing_token,
        message=f"Family sync started. Pairing code: {link.pairing_token}",
    )


def join_family_sync(pairing_token: str) -> PairingActionResult:
    cleaned = pairing_token.strip()
    if not cleaned:
        return PairingActionResult(ok=False, family_id=None, pairing_token=None, message="Enter a pairing code first.")
    state = sync_state.ensure_device_id()
    link = sync_client.join_family(
        pairing_token=cleaned,
        device_id=state.device_id or "",
        device_label=_device_label(),
    )
    if not link.ok or not link.family_id or not link.pairing_token:
        detail = link.error_message or link.error_code or "Could not join family sync."
        at_iso = now_iso()
        sync_state.save_sync_probe_result(succeeded=False, at_iso=at_iso, error_message=detail)
        return PairingActionResult(ok=False, family_id=None, pairing_token=None, message=detail)
    paired = sync_state.save_sync_pairing(
        family_id=link.family_id,
        pairing_token=link.pairing_token,
    )
    return PairingActionResult(
        ok=True,
        family_id=paired.family_id,
        pairing_token=paired.pairing_token,
        message="Family sync joined for this device.",
    )


def _device_label() -> str:
    label = socket.gethostname().strip()
    return label or "mandelquest-device"
