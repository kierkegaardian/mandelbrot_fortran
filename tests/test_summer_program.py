from __future__ import annotations

import json
import tempfile
import unittest
from types import SimpleNamespace

from app import db, summer_program, sync_service
from app.models import ScaffoldStep
from app.quiz_engine import Question
from app.skill_graph import subskills_for
from app.summer_program_quiz import SummerProgramLaunch, build_task_quiz_plan
from app.ui_quiz import QuizPanel


class _Var:
    def __init__(self, value) -> None:
        self._value = value

    def get(self):
        return self._value


class SummerProgramTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        tmp_path = self._tmp.name

        def _tmp_config() -> db.DbConfig:
            return db.DbConfig(path=f"{tmp_path}/test_app.db")

        self.enterContext(db.override_db_config(_tmp_config))
        db.init_db()
        self.child = db.create_profile("Child", "child", "2026-04-22T00:00:00+00:00")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_create_program_generates_placement_first_and_fixed_cycle(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="prealgebra_finish",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=35,
            student_age_years=9,
            created_at="2026-04-22T10:00:00+00:00",
        )

        tasks = db.list_summer_program_tasks(program.id)
        self.assertGreater(len(tasks), 10)
        self.assertEqual("placement_assessment", tasks[0].task_kind)
        self.assertEqual(["lesson", "practice_a", "practice_b", "mixed_review", "checkpoint"], [task.task_kind for task in tasks[1:6]])

    def test_foundation_bridge_tasks_do_not_surface_prealgebra_units(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="foundation_bridge",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=4,
            minutes_per_session=20,
            student_age_years=6,
            created_at="2026-04-22T10:00:00+00:00",
        )

        tasks = db.list_summer_program_tasks(program.id)
        leaked = [task for task in tasks if task.task_kind != "placement_assessment" and task.skill == "pre_algebra"]
        self.assertEqual(leaked, [])

    def test_prealgebra_finish_appends_optional_preview_units_after_exit(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="prealgebra_finish",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=35,
            student_age_years=9,
            created_at="2026-04-22T10:00:00+00:00",
        )

        tasks = db.list_summer_program_tasks(program.id)
        exit_task = next(task for task in tasks if task.task_kind == "exit_assessment")
        preview_units = {
            "linear_relationships_preview",
            "functions_patterns_preview",
            "algebra_1_preview_capstone",
            "geometry_measurement_preview",
            "coordinate_geometry_preview",
            "geometry_preview_capstone",
        }
        preview_tasks = [task for task in tasks if task.unit_code in preview_units]

        self.assertTrue(preview_tasks)
        self.assertTrue(all(task.sequence_index > exit_task.sequence_index for task in preview_tasks))
        self.assertTrue(any(task.skill == "algebra_linear" for task in preview_tasks))
        self.assertTrue(any(task.skill == "algebra_1" for task in preview_tasks))
        self.assertTrue(any(task.skill == "geometry_area" for task in preview_tasks))

    def test_recommended_lane_honors_score_floor_and_under_eight_gate(self) -> None:
        strong = summer_program.recommended_lane(
            overall=82.0,
            strand_results={
                "fractions": 80.0,
                "integer_order_fluency": 72.0,
                "variables_equations": 78.0,
                "ratios_percent": 74.0,
                "exponents_coordinates": 71.0,
            },
            student_age_years=9,
        )
        young = summer_program.recommended_lane(
            overall=82.0,
            strand_results={
                "fractions": 80.0,
                "integer_order_fluency": 72.0,
                "variables_equations": 78.0,
                "ratios_percent": 74.0,
                "exponents_coordinates": 71.0,
            },
            student_age_years=6,
        )

        self.assertEqual(strong, "prealgebra_finish")
        self.assertEqual(young, "foundation_bridge")

    def test_pace_status_reports_blocked_when_a_task_is_blocked(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="prealgebra_finish",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=35,
            student_age_years=9,
            created_at="2026-04-22T10:00:00+00:00",
        )
        first_task = summer_program.next_summer_program_task(program.id)
        assert first_task is not None
        db.update_summer_program_task(first_task.id, status="blocked", notes_json='{"score_pct": 55}')

        pace = summer_program.summer_program_pace_status(program.id, today="2026-06-02")
        self.assertEqual(pace.label, "blocked_on_checkpoint")

    def test_record_completed_quiz_updates_summer_program_task(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="foundation_bridge",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=20,
            student_age_years=6,
            created_at="2026-04-22T10:00:00+00:00",
        )
        task = summer_program.next_summer_program_task(program.id)
        assert task is not None

        result = sync_service.record_completed_quiz(
            profile_id=self.child.id,
            quiz_set_id=None,
            skill="pre_algebra",
            question_type="typed",
            num_questions=2,
            level=2,
            score=2,
            created_at="2026-06-01T10:00:00+00:00",
            elapsed_seconds=12.0,
            question_results=[
                sync_service.QuestionResultInput(
                    skill="fractions",
                    subskill="Equivalent fractions",
                    question_label="Placement • fractions",
                    mode="expression",
                    prompt="1/2 = ?/4",
                    correct_answer="2",
                    user_answer="2",
                    is_correct=True,
                    explanation="Scale both parts.",
                ),
                sync_service.QuestionResultInput(
                    skill="pre_algebra",
                    subskill="One-step equations",
                    question_label="Placement • variables_equations",
                    mode="expression",
                    prompt="x + 3 = 8",
                    correct_answer="5",
                    user_answer="5",
                    is_correct=True,
                    explanation="Subtract 3.",
                ),
            ],
            record_progress=True,
            streak_to_master=3,
            record_daily_review=False,
            summer_program_task_id=task.id,
        )

        updated_task = db.get_summer_program_task(task.id)
        self.assertTrue(result.completed_summer_task)
        self.assertIsNotNone(result.summer_program_note)
        self.assertIsNotNone(updated_task)
        assert updated_task is not None
        self.assertEqual(updated_task.status, "completed")

    def test_placement_completion_sets_pending_review_and_blocks_launch(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="prealgebra_finish",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=35,
            student_age_years=9,
            created_at="2026-04-22T10:00:00+00:00",
        )
        placement = summer_program.next_summer_program_task(program.id)
        assert placement is not None

        summer_program.update_task_outcome(
            task_id=placement.id,
            score_pct=62.0,
            attempt_id=17,
            completed_at="2026-06-01T10:05:00+00:00",
            strand_results={
                "fractions": 65.0,
                "integer_order_fluency": 62.0,
                "variables_equations": 58.0,
                "ratios_percent": 55.0,
                "exponents_coordinates": 52.0,
            },
        )

        updated = db.get_summer_program(program.id)
        summary = summer_program.summer_program_status_summary(self.child.id, program.id)
        self.assertIsNotNone(updated)
        self.assertIsNotNone(summary)
        assert updated is not None
        assert summary is not None
        self.assertEqual("foundation_bridge", updated.placement_recommendation)
        self.assertEqual("pending_review", updated.placement_review_status)
        self.assertIsNone(summer_program.launchable_summer_program_task(program.id))
        self.assertEqual("awaiting_parent_review", summary.current_blocker)

    def test_accepting_matching_recommendation_keeps_program_and_resumes_units(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="foundation_bridge",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=20,
            student_age_years=6,
            created_at="2026-04-22T10:00:00+00:00",
        )
        placement = summer_program.next_summer_program_task(program.id)
        assert placement is not None
        summer_program.update_task_outcome(
            task_id=placement.id,
            score_pct=61.0,
            attempt_id=18,
            completed_at="2026-06-01T10:05:00+00:00",
            strand_results={
                "fractions": 60.0,
                "integer_order_fluency": 62.0,
                "variables_equations": 58.0,
                "ratios_percent": 57.0,
                "exponents_coordinates": 55.0,
            },
        )

        accepted = summer_program.accept_summer_program_recommendation(program.id, "2026-06-01T10:06:00+00:00")
        launch_task = summer_program.launchable_summer_program_task(program.id)
        self.assertIsNotNone(accepted)
        assert accepted is not None
        self.assertEqual(program.id, accepted.id)
        self.assertEqual("accepted", accepted.placement_review_status)
        self.assertIsNotNone(launch_task)
        assert launch_task is not None
        self.assertNotEqual("placement_assessment", launch_task.task_kind)

    def test_overriding_lane_keeps_program_and_resumes_units(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="prealgebra_finish",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=35,
            student_age_years=9,
            created_at="2026-04-22T10:00:00+00:00",
        )
        placement = summer_program.next_summer_program_task(program.id)
        assert placement is not None
        summer_program.update_task_outcome(
            task_id=placement.id,
            score_pct=60.0,
            attempt_id=19,
            completed_at="2026-06-01T10:05:00+00:00",
            strand_results={
                "fractions": 60.0,
                "integer_order_fluency": 61.0,
                "variables_equations": 59.0,
                "ratios_percent": 58.0,
                "exponents_coordinates": 57.0,
            },
        )

        overridden = summer_program.override_summer_program_lane(program.id, "2026-06-01T10:06:00+00:00")
        launch_task = summer_program.launchable_summer_program_task(program.id)
        self.assertIsNotNone(overridden)
        assert overridden is not None
        self.assertEqual(program.id, overridden.id)
        self.assertEqual("overridden", overridden.placement_review_status)
        self.assertIsNotNone(launch_task)
        assert launch_task is not None
        self.assertNotEqual("placement_assessment", launch_task.task_kind)

    def test_accepting_mismatched_recommendation_switches_lane_and_preserves_placement(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="prealgebra_finish",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=35,
            student_age_years=9,
            created_at="2026-04-22T10:00:00+00:00",
        )
        placement = summer_program.next_summer_program_task(program.id)
        assert placement is not None
        summer_program.update_task_outcome(
            task_id=placement.id,
            score_pct=58.0,
            attempt_id=20,
            completed_at="2026-06-01T10:05:00+00:00",
            strand_results={
                "fractions": 60.0,
                "integer_order_fluency": 57.0,
                "variables_equations": 52.0,
                "ratios_percent": 49.0,
                "exponents_coordinates": 45.0,
            },
        )

        switched = summer_program.accept_summer_program_recommendation(program.id, "2026-06-01T10:06:00+00:00")
        active = summer_program.get_active_summer_program(self.child.id)
        archived = db.get_summer_program(program.id)
        self.assertIsNotNone(switched)
        self.assertIsNotNone(active)
        assert switched is not None
        assert active is not None
        assert archived is not None
        self.assertNotEqual(program.id, switched.id)
        self.assertEqual(switched.id, active.id)
        self.assertEqual("foundation_bridge", switched.lane)
        self.assertEqual("accepted", switched.placement_review_status)
        self.assertEqual("archived", archived.status)
        placement_copy = db.list_summer_program_tasks(switched.id)[0]
        self.assertEqual("placement_assessment", placement_copy.task_kind)
        self.assertEqual("completed", placement_copy.status)
        self.assertTrue(summer_program.latest_assessment_reports(switched.id))
        next_task = summer_program.launchable_summer_program_task(switched.id)
        self.assertIsNotNone(next_task)
        assert next_task is not None
        self.assertNotEqual("placement_assessment", next_task.task_kind)

    def test_rerunning_placement_creates_fresh_program(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="foundation_bridge",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=4,
            minutes_per_session=20,
            student_age_years=6,
            created_at="2026-04-22T10:00:00+00:00",
        )
        fresh = summer_program.rerun_summer_program_placement(program.id, "2026-06-05T09:00:00+00:00")
        active = summer_program.get_active_summer_program(self.child.id)
        archived = db.get_summer_program(program.id)
        self.assertIsNotNone(fresh)
        self.assertIsNotNone(active)
        assert fresh is not None
        assert active is not None
        assert archived is not None
        self.assertNotEqual(program.id, fresh.id)
        self.assertEqual("archived", archived.status)
        self.assertEqual(active.id, fresh.id)
        first_task = db.list_summer_program_tasks(fresh.id)[0]
        self.assertEqual("placement_assessment", first_task.task_kind)
        self.assertEqual("pending", first_task.status)

    def test_failed_program_tasks_store_block_reason_and_next_action(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="prealgebra_finish",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=35,
            student_age_years=9,
            created_at="2026-04-22T10:00:00+00:00",
        )
        tasks = db.list_summer_program_tasks(program.id)
        checkpoint = next(task for task in tasks if task.task_kind == "checkpoint")
        midpoint = next(task for task in tasks if task.task_kind == "midpoint_assessment")
        exit_task = next(task for task in tasks if task.task_kind == "exit_assessment")

        for attempt_id, task, reason in (
            (30, checkpoint, "checkpoint_below_target"),
            (31, midpoint, "midpoint_below_target"),
            (32, exit_task, "exit_below_target"),
        ):
            summer_program.update_task_outcome(
                task_id=task.id,
                score_pct=60.0,
                attempt_id=attempt_id,
                completed_at=f"2026-06-02T10:{attempt_id:02d}:00+00:00",
                strand_results={
                    "fractions": 62.0,
                    "variables_equations": 58.0,
                    "ratios_percent": 54.0,
                },
            )
            updated = db.get_summer_program_task(task.id)
            self.assertIsNotNone(updated)
            assert updated is not None
            notes = json.loads(updated.notes_json)
            self.assertEqual("blocked", updated.status)
            self.assertEqual(reason, notes["block_reason"])
            self.assertEqual(60.0, notes["score_pct"])
            self.assertEqual(task.target_score_pct, notes["required_score_pct"])
            self.assertTrue(notes["weak_strands"])
            self.assertTrue(notes["next_action"])

    def test_refresh_program_plan_builds_catch_up_schedule_when_work_is_overdue(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="foundation_bridge",
            start_date="2026-06-01",
            end_date="2026-06-08",
            days_per_week=2,
            minutes_per_session=20,
            student_age_years=6,
            created_at="2026-04-22T10:00:00+00:00",
        )

        summer_program.refresh_program_plan(program.id, today_iso="2026-06-07")
        summary = summer_program.summer_program_status_summary(self.child.id, program.id)
        remaining = [task for task in db.list_summer_program_tasks(program.id) if task.status in {"pending", "blocked"}]

        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertIsNotNone(summary.catch_up_note)
        self.assertTrue(all(task.scheduled_date >= "2026-06-07" for task in remaining))
        self.assertTrue(any(json.loads(task.notes_json).get("catch_up_note") for task in remaining))

    def test_accepting_placement_creates_short_remediation_pack_for_next_tasks(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="prealgebra_finish",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=35,
            student_age_years=9,
            created_at="2026-04-22T10:00:00+00:00",
        )
        placement = summer_program.next_summer_program_task(program.id)
        assert placement is not None
        summer_program.update_task_outcome(
            task_id=placement.id,
            score_pct=83.0,
            attempt_id=50,
            completed_at="2026-06-01T10:05:00+00:00",
            strand_results={
                "fractions": 82.0,
                "integer_order_fluency": 84.0,
                "variables_equations": 61.0,
                "ratios_percent": 80.0,
                "exponents_coordinates": 78.0,
            },
        )

        accepted = summer_program.accept_summer_program_recommendation(program.id, "2026-06-01T10:06:00+00:00")
        self.assertIsNotNone(accepted)
        launch_task = summer_program.launchable_summer_program_task(program.id)
        self.assertIsNotNone(launch_task)
        assert launch_task is not None
        self.assertEqual("remediation_review", launch_task.task_kind)
        notes = json.loads(launch_task.notes_json)
        focus = notes.get("remediation_label") or []
        self.assertTrue(focus)
        self.assertIn("Expressions and variables", focus)
        plan = build_task_quiz_plan(SummerProgramLaunch(profile_id=self.child.id, program_id=program.id, task_id=launch_task.id))
        self.assertIn("Remediation", plan.meta)
        self.assertTrue(any(question.subskill in focus for question in plan.questions if question.subskill))
        summer_program.update_task_outcome(
            task_id=launch_task.id,
            score_pct=80.0,
            attempt_id=51,
            completed_at="2026-06-01T10:10:00+00:00",
        )
        next_task = summer_program.launchable_summer_program_task(program.id)
        self.assertIsNotNone(next_task)
        assert next_task is not None
        self.assertEqual("lesson", next_task.task_kind)

    def test_blocked_retry_uses_remediation_focus(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="prealgebra_finish",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=35,
            student_age_years=9,
            created_at="2026-04-22T10:00:00+00:00",
        )
        placement = summer_program.next_summer_program_task(program.id)
        assert placement is not None
        summer_program.update_task_outcome(
            task_id=placement.id,
            score_pct=84.0,
            attempt_id=60,
            completed_at="2026-06-01T09:00:00+00:00",
            strand_results={
                "fractions": 82.0,
                "integer_order_fluency": 84.0,
                "variables_equations": 81.0,
                "ratios_percent": 79.0,
                "exponents_coordinates": 78.0,
            },
        )
        summer_program.accept_summer_program_recommendation(program.id, "2026-06-01T09:05:00+00:00")
        ordered = db.list_summer_program_tasks(program.id)
        prefix = [task for task in ordered if task.task_kind in {"lesson", "practice_a", "practice_b", "mixed_review"}][:4]
        for offset, task in enumerate(prefix, start=61):
            summer_program.update_task_outcome(
                task_id=task.id,
                score_pct=100.0,
                attempt_id=offset,
                completed_at=f"2026-06-01T09:{offset:02d}:00+00:00",
            )
        checkpoint = next(task for task in db.list_summer_program_tasks(program.id) if task.task_kind == "checkpoint")
        summer_program.update_task_outcome(
            task_id=checkpoint.id,
            score_pct=60.0,
            attempt_id=70,
            completed_at="2026-06-10T09:00:00+00:00",
            strand_results={
                "variables_equations": 55.0,
                "ratios_percent": 58.0,
                "percent": 62.0,
            },
        )

        blocked = db.get_summer_program_task(checkpoint.id)
        summary = summer_program.summer_program_status_summary(self.child.id, program.id)
        launch_task = summer_program.launchable_summer_program_task(program.id)
        self.assertIsNotNone(blocked)
        self.assertIsNotNone(summary)
        self.assertIsNotNone(launch_task)
        assert blocked is not None
        assert summary is not None
        assert launch_task is not None
        notes = json.loads(blocked.notes_json)
        self.assertTrue(notes.get("remediation_label"))
        self.assertIsNotNone(summary.remediation_note)
        self.assertEqual("remediation_review", launch_task.task_kind)
        self.assertEqual("checkpoint_below_target", summary.current_blocker)
        plan = build_task_quiz_plan(SummerProgramLaunch(profile_id=self.child.id, program_id=program.id, task_id=launch_task.id))
        focus = set(notes["remediation_label"])
        self.assertIn("Remediation", plan.meta)
        self.assertTrue(any(question.subskill in focus for question in plan.questions if question.subskill))
        summer_program.update_task_outcome(
            task_id=launch_task.id,
            score_pct=80.0,
            attempt_id=71,
            completed_at="2026-06-10T09:05:00+00:00",
        )
        retry_task = summer_program.launchable_summer_program_task(program.id)
        self.assertIsNotNone(retry_task)
        assert retry_task is not None
        self.assertEqual(checkpoint.id, retry_task.id)

    def test_projected_finish_note_reports_when_plan_slips_past_end(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="prealgebra_finish",
            start_date="2026-06-01",
            end_date="2026-06-08",
            days_per_week=1,
            minutes_per_session=35,
            student_age_years=9,
            created_at="2026-04-22T10:00:00+00:00",
        )

        summary = summer_program.summer_program_status_summary(self.child.id, program.id)

        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertIsNotNone(summary.projected_finish_date)
        self.assertIsNotNone(summary.projected_finish_note)
        assert summary.projected_finish_note is not None
        self.assertIn("Projected finish slips past", summary.projected_finish_note)

    def test_core_finish_can_complete_with_preview_tasks_pending(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="prealgebra_finish",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=35,
            student_age_years=9,
            created_at="2026-04-22T10:00:00+00:00",
        )

        preview_units = {
            "linear_relationships_preview",
            "functions_patterns_preview",
            "algebra_1_preview_capstone",
            "geometry_measurement_preview",
            "coordinate_geometry_preview",
            "geometry_preview_capstone",
        }
        for task in db.list_summer_program_tasks(program.id):
            if task.unit_code in preview_units:
                continue
            db.update_summer_program_task(task.id, status="completed")

        for subskill in subskills_for("pre_algebra"):
            repetitions = 3 if subskill in {
                "Expressions and variables",
                "One-step equations",
                "Two-step equations and inequalities",
                "Ratios, rates, and proportional relationships",
                "Percent problems",
            } else 2
            for idx in range(repetitions):
                db.upsert_subskill_progress(
                    self.child.id,
                    "pre_algebra",
                    subskill,
                    True,
                    f"2026-06-02T10:0{idx}:00+00:00",
                    3,
                )

        db.record_summer_assessment(
            program_id=program.id,
            assessment_type="exit",
            score_pct=91.0,
            passed=True,
            strand_results_json=json.dumps({"review": 91.0}),
            completed_at="2026-06-30T12:00:00+00:00",
        )

        self.assertEqual("completed", summer_program.finish_status(self.child.id, program.id))
        summary = summer_program.summer_program_status_summary(self.child.id, program.id)
        launch_task = summer_program.launchable_summer_program_task(program.id)
        self.assertIsNotNone(summary)
        self.assertIsNotNone(launch_task)
        assert summary is not None
        assert launch_task is not None
        self.assertEqual("completed", summary.finish_state)
        self.assertEqual("completed", summary.pace_label)
        self.assertIn("Bonus preview available", summary.next_action or "")
        self.assertEqual("linear_relationships_preview", launch_task.unit_code)

    def test_preview_unit_quiz_plan_uses_algebra_and_geometry_questions(self) -> None:
        program = summer_program.create_summer_program(
            profile_id=self.child.id,
            lane="prealgebra_finish",
            start_date="2026-06-01",
            end_date="2026-08-31",
            days_per_week=5,
            minutes_per_session=35,
            student_age_years=9,
            created_at="2026-04-22T10:00:00+00:00",
        )

        linear_task = next(
            task
            for task in db.list_summer_program_tasks(program.id)
            if task.unit_code == "linear_relationships_preview" and task.task_kind == "lesson"
        )
        geometry_task = next(
            task
            for task in db.list_summer_program_tasks(program.id)
            if task.unit_code == "coordinate_geometry_preview" and task.task_kind == "lesson"
        )
        capstone_task = next(
            task
            for task in db.list_summer_program_tasks(program.id)
            if task.unit_code == "algebra_1_preview_capstone" and task.task_kind == "checkpoint"
        )
        geometry_capstone_task = next(
            task
            for task in db.list_summer_program_tasks(program.id)
            if task.unit_code == "geometry_preview_capstone" and task.task_kind == "checkpoint"
        )

        linear_plan = build_task_quiz_plan(
            SummerProgramLaunch(profile_id=self.child.id, program_id=program.id, task_id=linear_task.id)
        )
        geometry_plan = build_task_quiz_plan(
            SummerProgramLaunch(profile_id=self.child.id, program_id=program.id, task_id=geometry_task.id)
        )
        capstone_plan = build_task_quiz_plan(
            SummerProgramLaunch(profile_id=self.child.id, program_id=program.id, task_id=capstone_task.id)
        )
        geometry_capstone_plan = build_task_quiz_plan(
            SummerProgramLaunch(profile_id=self.child.id, program_id=program.id, task_id=geometry_capstone_task.id)
        )

        self.assertTrue(all(question.skill == "algebra_linear" for question in linear_plan.questions))
        self.assertTrue(any(question.scaffold_steps for question in linear_plan.questions))
        self.assertTrue(any(question.skill == "geometry_area" for question in geometry_plan.questions))
        self.assertTrue(any(question.scaffold_steps for question in geometry_plan.questions))
        self.assertTrue(all(question.skill == "algebra_1" for question in capstone_plan.questions))
        self.assertTrue(any(question.subskill == "Slope from points" for question in capstone_plan.questions))
        self.assertTrue(any(question.subskill == "Sequences" for question in capstone_plan.questions))
        self.assertTrue(any(question.subskill == "Graphing linear inequalities" for question in capstone_plan.questions))
        self.assertTrue(any(question.scaffold_steps for question in capstone_plan.questions))
        self.assertTrue(all(question.skill == "geometry_area" for question in geometry_capstone_plan.questions))
        self.assertTrue(any(question.subskill == "Circumference and area of circles" for question in geometry_capstone_plan.questions))
        self.assertTrue(any(question.subskill == "Pythagorean theorem" for question in geometry_capstone_plan.questions))
        self.assertTrue(any(question.subskill == "Similarity and scale factor" for question in geometry_capstone_plan.questions))
        self.assertTrue(any(question.scaffold_steps for question in geometry_capstone_plan.questions))

    def test_quiz_payload_roundtrip_keeps_scaffold_steps_and_progress(self) -> None:
        panel = QuizPanel.__new__(QuizPanel)
        question = Question(
            skill="pre_algebra",
            prompt="Solve for x: x + 5 = 11",
            correct_answer="6",
            explanation="Subtract 5.",
            choices=None,
            visual=None,
            subskill="One-step equations",
            scaffold_steps=[
                ScaffoldStep(prompt="What is 11 - 5?", expected_answer="6", hint="Undo the +5."),
                ScaffoldStep(prompt="Now what is x?", expected_answer="6", hint="The remaining number is x."),
            ],
        )
        panel.track_var = _Var("Pre-Algebra")
        panel.skill_var = _Var("pre_algebra")
        panel.subskill_var = _Var("One-step equations")
        panel.type_var = _Var("typed")
        panel.strategy_var = _Var("focused")
        panel.num_var = _Var(3)
        panel.level_var = _Var(2)
        panel.meta_var = _Var("Summer Program")
        panel._attempt_skill = "pre_algebra"
        panel._record_attempt = True
        panel._record_progress = True
        panel._launch_context = "summer_program"
        panel._profile_override = SimpleNamespace(id=self.child.id)
        panel._summer_program_launch = SummerProgramLaunch(profile_id=self.child.id, program_id=7, task_id=9)
        panel._index = 0
        panel._score = 0
        panel._correct_streak = 0
        panel._scaffold_question_index = 0
        panel._scaffold_step_index = 1
        panel._scaffold_step_answers = ["6"]
        panel._questions = [question]
        panel._answers = []
        panel._mistake_recovery = None

        payload = json.loads(panel._build_progress_state())
        rebuilt = QuizPanel.__new__(QuizPanel)._question_from_payload(payload["questions"][0])

        self.assertEqual(payload["scaffold_state"]["step_index"], 1)
        self.assertEqual(payload["scaffold_state"]["answers"], ["6"])
        self.assertEqual(payload["summer_program_launch"]["task_id"], 9)
        self.assertIsNotNone(rebuilt.scaffold_steps)
        assert rebuilt.scaffold_steps is not None
        self.assertEqual(rebuilt.scaffold_steps[0].expected_answer, "6")


if __name__ == "__main__":
    unittest.main()
