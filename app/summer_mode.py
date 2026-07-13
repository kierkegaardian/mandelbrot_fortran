from __future__ import annotations

from .curriculum import BY_SKILL as CURRICULUM_BY_SKILL


GRADE_ORDER: tuple[str, ...] = (
    "K",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
)
GRADE_INDEX = {grade: idx for idx, grade in enumerate(GRADE_ORDER)}
SUMMER_MODE_EXCLUDED_SKILLS: frozenset[str] = frozenset(
    {
        "algebra_2",
        "trig_right_triangle",
        "statistics",
        "calculus_1",
        "calculus_2",
        "calculus_3",
        "sat_math",
        "psat_math",
        "gre_quant",
        "calculus_slope",
    }
)
SUMMER_MODE_EXCLUDED_TRACKS: frozenset[str] = frozenset({"Calculus", "Test Prep"})


def normalize_grade_band(grade_band: str | None, default: str = "K-8") -> str:
    cleaned = (grade_band or "").strip()
    return cleaned or default


def grade_band_bounds(grade_band: str | None) -> tuple[int, int] | None:
    cleaned = normalize_grade_band(grade_band)
    if cleaned.endswith("+"):
        start = cleaned[:-1].strip()
        idx = GRADE_INDEX.get(start)
        if idx is None:
            return None
        return (idx, len(GRADE_ORDER) - 1)

    parts = [part.strip() for part in cleaned.split("-") if part.strip()]
    if len(parts) == 1:
        idx = GRADE_INDEX.get(parts[0])
        if idx is None:
            return None
        return (idx, idx)
    if len(parts) != 2:
        return None
    start = GRADE_INDEX.get(parts[0])
    end = GRADE_INDEX.get(parts[1])
    if start is None or end is None:
        return None
    if start > end:
        start, end = end, start
    return (start, end)


def grade_band_contains(grade_band: str | None, grade: str) -> bool:
    bounds = grade_band_bounds(grade_band)
    idx = GRADE_INDEX.get(grade)
    if bounds is None or idx is None:
        return False
    return bounds[0] <= idx <= bounds[1]


def grade_bands_overlap(left: str | None, right: str | None) -> bool:
    left_bounds = grade_band_bounds(left)
    right_bounds = grade_band_bounds(right)
    if left_bounds is None or right_bounds is None:
        return False
    return left_bounds[0] <= right_bounds[1] and right_bounds[0] <= left_bounds[1]


def skill_matches_grade(skill: str, grade_band: str | None) -> bool:
    entry = CURRICULUM_BY_SKILL.get(skill)
    if entry is None or not entry.grade_band:
        return True
    return grade_bands_overlap(entry.grade_band, grade_band)


def skill_allowed(skill: str, *, grade_band: str | None, summer_mode: bool) -> bool:
    if not skill_matches_grade(skill, grade_band):
        return False
    if summer_mode and skill in SUMMER_MODE_EXCLUDED_SKILLS:
        return False
    return True


def filter_skills(skills: tuple[str, ...] | list[str], *, grade_band: str | None, summer_mode: bool) -> tuple[str, ...]:
    return tuple(skill for skill in skills if skill_allowed(skill, grade_band=grade_band, summer_mode=summer_mode))


def filter_tracks(
    tracks: tuple[str, ...] | list[str],
    skills_for_track,
    *,
    grade_band: str | None,
    summer_mode: bool,
) -> tuple[str, ...]:
    visible: list[str] = []
    for track in tracks:
        if summer_mode and track in SUMMER_MODE_EXCLUDED_TRACKS:
            continue
        skills = filter_skills(tuple(skills_for_track(track)), grade_band=grade_band, summer_mode=summer_mode)
        if skills:
            visible.append(track)
    return tuple(visible)


def preferred_track_for_skill(
    skill: str,
    tracks: tuple[str, ...] | list[str],
    skills_for_track,
    *,
    grade_band: str | None,
    summer_mode: bool,
) -> str:
    for track in filter_tracks(tracks, skills_for_track, grade_band=grade_band, summer_mode=summer_mode):
        if skill in filter_skills(tuple(skills_for_track(track)), grade_band=grade_band, summer_mode=summer_mode):
            return track
    return "All"
