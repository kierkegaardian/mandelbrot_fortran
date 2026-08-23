from __future__ import annotations

TEMPLATE_ONLY_SKILLS = frozenset(
    {
        "sat_math",
        "psat_math",
        "gre_quant",
    }
)

TEMPLATE_INTUITION_SKILLS = frozenset(
    {
        "stats_percent",
        "stats_mean",
        "stats_probability",
        "sat_math",
        "psat_math",
        "gre_quant",
    }
)

NATIVE_INTUITION_SKILLS = frozenset(
    {
        "trig_right_triangle",
        "calculus_1",
        "calculus_2",
        "calculus_3",
        "statistics",
    }
)

TEMPLATE_WORD_SKILLS = frozenset(
    {
        "add_subtract",
        "ratios",
        "algebra_linear",
        "geometry_area",
        "stats_percent",
        "stats_probability",
        "algebra_1",
        "algebra_2",
        "statistics",
        "sat_math",
        "psat_math",
        "gre_quant",
        "logic_syllogism",
    }
)


class ContentUnavailableError(ValueError):
    def __init__(self, skill: str, subskill: str | None = None, mode: str | None = None) -> None:
        self.skill = skill
        self.subskill = subskill
        self.mode = mode
        parts = [f"skill '{skill}'"]
        if subskill:
            parts.append(f"subskill '{subskill}'")
        if mode:
            parts.append(f"mode '{mode}'")
        super().__init__("No quiz content is available for " + ", ".join(parts) + ".")


def is_template_only_skill(skill: str) -> bool:
    return skill in TEMPLATE_ONLY_SKILLS


def is_native_intuition_skill(skill: str) -> bool:
    return skill in NATIVE_INTUITION_SKILLS


def supports_real_intuition(skill: str) -> bool:
    return skill in TEMPLATE_INTUITION_SKILLS or skill in NATIVE_INTUITION_SKILLS


def supports_word_mode(skill: str) -> bool:
    return skill in TEMPLATE_WORD_SKILLS
