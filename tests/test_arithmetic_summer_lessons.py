from __future__ import annotations

import unittest

from app.arithmetic_summer_lessons import build_summer_lesson, supports_summer_lesson


class ArithmeticSummerLessonTests(unittest.TestCase):
    def test_new_skills_are_supported_for_summer_lessons(self) -> None:
        for skill in ("place_value", "money", "measurement", "pre_algebra"):
            with self.subTest(skill=skill):
                self.assertTrue(supports_summer_lesson(skill))

    def test_place_value_lesson_uses_digit_value_questions(self) -> None:
        lesson = build_summer_lesson("place_value")

        self.assertEqual(len(lesson), 3)
        self.assertEqual(lesson[1].expected_answer, "80")
        self.assertEqual(lesson[2].expected_answer, "500")
        self.assertEqual(lesson[1].presets["long_a_var"], 482)

    def test_measurement_time_lesson_uses_hour_to_minute_conversion(self) -> None:
        lesson = build_summer_lesson("measurement", subskill="Elapsed time")

        self.assertEqual(lesson[1].expected_answer, "180")
        self.assertEqual(lesson[1].presets["long_b_var"], 60)
        self.assertIn("minutes", lesson[1].prompt)

    def test_money_lesson_converts_currency_to_cents(self) -> None:
        lesson = build_summer_lesson("money")

        self.assertEqual(lesson[1].expected_answer, "420")
        self.assertEqual(lesson[2].expected_answer, "305")
        self.assertEqual(lesson[0].presets["money_cents_var"], 35)

    def test_pre_algebra_percent_subskill_uses_percent_presets(self) -> None:
        lesson = build_summer_lesson("pre_algebra", subskill="Percent problems")

        self.assertEqual(lesson[1].expected_answer, "10")
        self.assertEqual(lesson[0].presets["percent_value_var"], 25)
        self.assertEqual(lesson[2].presets["percent_total_var"], 60)

    def test_pre_algebra_default_lesson_uses_order_of_operations_presets(self) -> None:
        lesson = build_summer_lesson("pre_algebra")

        self.assertEqual(lesson[1].expected_answer, "18")
        self.assertEqual(lesson[2].expected_answer, "2")
        self.assertEqual(lesson[2].presets["order_shape_var"], "a op (b op c)")


if __name__ == "__main__":
    unittest.main()
