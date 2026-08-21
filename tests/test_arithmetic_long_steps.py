from __future__ import annotations

import unittest

from app.arithmetic_long import _division_steps, _multiplication_partials


class ArithmeticLongStepsTests(unittest.TestCase):
    def test_multiplication_partials_include_place_value_shift(self) -> None:
        self.assertEqual(_multiplication_partials(12, 34), [(48, 0), (360, 1)])

    def test_division_steps_capture_subtract_and_bring_down(self) -> None:
        steps = _division_steps(496, 4)
        self.assertEqual(len(steps), 3)
        self.assertEqual((steps[0].segment, steps[0].subtract, steps[0].remainder, steps[0].bring_down), (4, 4, 0, 9))
        self.assertEqual((steps[1].segment, steps[1].subtract, steps[1].remainder, steps[1].bring_down), (9, 8, 1, 6))
        self.assertEqual((steps[2].segment, steps[2].subtract, steps[2].remainder, steps[2].bring_down), (16, 16, 0, None))

    def test_division_steps_empty_when_dividend_smaller_than_divisor(self) -> None:
        self.assertEqual(_division_steps(3, 7), [])


if __name__ == "__main__":
    unittest.main()
