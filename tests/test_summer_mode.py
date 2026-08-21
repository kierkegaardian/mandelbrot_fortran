from __future__ import annotations

import unittest

from app.summer_mode import (
    filter_skills,
    filter_tracks,
    grade_band_contains,
    grade_bands_overlap,
    preferred_track_for_skill,
    skill_allowed,
)


def _skills_for_track(track: str) -> tuple[str, ...]:
    mapping = {
        "Arithmetic": ("counting", "add_subtract", "fractions"),
        "Algebra": ("algebra_linear", "algebra_1", "algebra_2"),
        "Calculus": ("calculus_1",),
        "Test Prep": ("sat_math",),
    }
    return mapping.get(track, ())


class SummerModeTests(unittest.TestCase):
    def test_grade_band_contains_single_and_range(self) -> None:
        self.assertTrue(grade_band_contains("K-2", "1"))
        self.assertTrue(grade_band_contains("12+", "12"))
        self.assertFalse(grade_band_contains("6-8", "4"))

    def test_grade_band_overlap_handles_adjacent_ranges(self) -> None:
        self.assertTrue(grade_bands_overlap("3-5", "4-6"))
        self.assertFalse(grade_bands_overlap("K-2", "6-8"))

    def test_skill_allowed_filters_excluded_summer_skills(self) -> None:
        self.assertTrue(skill_allowed("algebra_1", grade_band="8-10", summer_mode=True))
        self.assertFalse(skill_allowed("sat_math", grade_band="10-12", summer_mode=True))

    def test_filter_skills_respects_grade_band_and_summer_mode(self) -> None:
        visible = filter_skills(
            ("counting", "add_subtract", "algebra_2", "sat_math"),
            grade_band="1-2",
            summer_mode=True,
        )
        self.assertEqual(visible, ("counting", "add_subtract"))

    def test_filter_tracks_drops_empty_and_excluded_tracks(self) -> None:
        visible = filter_tracks(
            ("Arithmetic", "Algebra", "Calculus", "Test Prep"),
            _skills_for_track,
            grade_band="6-8",
            summer_mode=True,
        )
        self.assertEqual(visible, ("Algebra",))

    def test_preferred_track_for_skill_uses_filtered_tracks(self) -> None:
        track = preferred_track_for_skill(
            "algebra_1",
            ("Arithmetic", "Algebra", "Test Prep"),
            _skills_for_track,
            grade_band="8-10",
            summer_mode=True,
        )
        self.assertEqual(track, "Algebra")


if __name__ == "__main__":
    unittest.main()
