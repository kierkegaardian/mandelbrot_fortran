from __future__ import annotations

from dataclasses import dataclass

from . import db
from .early_math_catalog import khan_url_for, spec_for
from .explanations import ARITHMETIC_MODE_EXPLANATIONS
from .quiz_engine import ContentUnavailableError, generate_question
from .summer_program_defs import SummerUnitDefinition, lane_units
from .summer_program_quiz import scaffold_step_count_for_target, summer_unit_targets
from .summer_program_template_seed import EXPRESSION_TARGETS, WORD_TARGETS

Readiness = str

READY: Readiness = "ready"
THIN: Readiness = "thin"
MISSING: Readiness = "missing"

_READINESS_ORDER: dict[Readiness, int] = {MISSING: 0, THIN: 1, READY: 2}

_OPEN_RESOURCE_BY_SOURCE_ID: dict[str, str] = {
    "ray_new_practical_arithmetic_1897": "https://archive.org/details/newpracticalarit00rayj",
    "basic_arithmetic_student_workbook_2013": "",
    "elementary_algebra_openstax_2e": "https://openstax.org/details/books/elementary-algebra-2e",
    "college_algebra_stitz_zeager_2013": "https://www.stitz-zeager.com/",
    "school_geometry_1921_hs21": "https://math.libretexts.org/Bookshelves/Geometry",
}

_PREVIEW_KHAN_URLS: dict[tuple[str, str], str] = {
    ("algebra_linear", "Slope from points"): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:slope/e/slope-table",
    ("algebra_linear", "Slope-intercept interpretation"): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:slope-intercept-form/e/graph-from-slope-intercept-equation",
    ("algebra_linear", "Direct variation"): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:direct-and-inverse-variation/e/direct_variation",
    ("algebra_linear", "Rate and unit-rate modeling"): "https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-ratio-proportion/cc-7th-proportional-rel/e/analyzing-and-identifying-proportional-relationships",
    ("algebra_linear", "Word problems with linear models"): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:writing-slope-intercept-equations/e/writing_slope_intercept_equations",
    ("algebra_1", "Slope from points"): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:slope/e/slope-from-two-points",
    ("algebra_1", "Slope-intercept form"): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:forms-of-linear-equations/x2f8bb11595b61c86:intro-to-slope-intercept-form/e/slope-from-an-equation-in-slope-intercept-form",
    ("algebra_1", "Graphing linear inequalities"): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:inequalities-systems-graphs/x2f8bb11595b61c86:graphing-two-variable-inequalities/e/graphing_inequalities_2",
    ("algebra_1", "Functions"): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:functions/x2f8bb11595b61c86:function-inputs-and-outputs/e/inputs-and-outputs-of-a-function",
    ("algebra_1", "Sequences"): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:sequences/x2f8bb11595b61c86:constructing-arithmetic-sequences/e/sequences_1",
    ("algebra_1", "Linear equations & graphs"): "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs",
    ("algebra_1", "Solving equations & inequalities"): "https://www.khanacademy.org/math/algebra-basics/alg-basics-solving-equations-and-inequalities",
    ("geometry_area", "Perimeter and missing sides"): "https://www.khanacademy.org/math/basic-geo/basic-geo-area-and-perimeter",
    ("geometry_area", "Area of triangles and parallelograms"): "https://www.khanacademy.org/math/basic-geo/basic-geo-area-and-perimeter/area-triangle/e/area_of_triangles_1",
    ("geometry_area", "Circumference and area of circles"): "https://www.khanacademy.org/math/basic-geo/basic-geo-area-and-perimeter/circum-area-circles",
    ("geometry_area", "Surface area and volume"): "https://www.khanacademy.org/math/basic-geo/basic-geo-volume-sa",
    ("geometry_area", "Pythagorean theorem"): "https://www.khanacademy.org/math/basic-geo/basic-geo-pythagorean-topic/basic-geometry-pythagorean-theorem/e/pythagorean_theorem_1",
    ("geometry_area", "Coordinate geometry distance and midpoint"): "https://www.khanacademy.org/math/geometry/hs-geo-analytic-geometry/hs-geo-dist-problems/e/coordinate-plane-word-problems-with-polygons",
    ("geometry_area", "Transformations and congruence"): "https://www.khanacademy.org/math/geometry/hs-geo-transformations",
    ("geometry_area", "Similarity and scale factor"): "https://www.khanacademy.org/math/geometry/hs-geo-similarity/hs-geo-similarity-definitions/e/exploring-angle-preserving-transformations-and-similarity",
    ("geometry_area", "Analytic geometry and coordinate proofs"): "https://www.khanacademy.org/math/geometry/hs-geo-analytic-geometry",
}

_OPEN_RESOURCE_BY_SKILL: dict[str, str] = {
    "algebra_linear": "https://openstax.org/details/books/elementary-algebra-2e",
    "algebra_1": "https://openstax.org/details/books/elementary-algebra-2e",
    "geometry_area": "https://math.libretexts.org/Bookshelves/Geometry",
}


@dataclass(frozen=True)
class SummerContentAuditRow:
    lane: str
    unit_code: str
    unit_label: str
    optional: bool
    skill: str
    subskill: str
    expression_template_count: int
    word_template_count: int
    scaffold_step_count: int
    native_question_available: bool
    has_intuition: bool
    khan_url: str
    open_resource_url: str
    readiness: Readiness
    notes: tuple[str, ...]

    @property
    def active_question_count(self) -> int:
        native_count = 1 if self.native_question_available else 0
        scaffold_count = 1 if self.scaffold_step_count > 0 else 0
        return self.expression_template_count + self.word_template_count + scaffold_count + native_count

    @property
    def has_khan_link(self) -> bool:
        return bool(self.khan_url)

    @property
    def has_open_resource(self) -> bool:
        return bool(self.open_resource_url)


@dataclass(frozen=True)
class SummerResourceReview:
    lane: str
    rows: tuple[SummerContentAuditRow, ...]

    @property
    def ready_count(self) -> int:
        return _count_readiness(self.rows, READY)

    @property
    def thin_count(self) -> int:
        return _count_readiness(self.rows, THIN)

    @property
    def missing_count(self) -> int:
        return _count_readiness(self.rows, MISSING)

    @property
    def weakest_rows(self) -> tuple[SummerContentAuditRow, ...]:
        return tuple(
            sorted(
                self.rows,
                key=lambda row: (
                    _READINESS_ORDER.get(row.readiness, 99),
                    0 if not row.has_khan_link else 1,
                    0 if row.active_question_count == 0 else 1,
                    row.unit_label,
                    row.subskill,
                ),
            )
        )


def summer_resource_review(lane: str) -> SummerResourceReview:
    rows: list[SummerContentAuditRow] = []
    for unit in lane_units(lane):
        rows.extend(_audit_unit(lane, unit))
    return SummerResourceReview(lane=lane, rows=tuple(rows))


def _audit_unit(lane: str, unit: SummerUnitDefinition) -> tuple[SummerContentAuditRow, ...]:
    rows: list[SummerContentAuditRow] = []
    for skill, subskill in summer_unit_targets(unit.code, unit.skill, unit.subskill):
        if subskill is None:
            continue
        expression_count = _template_count(skill, subskill, "expression")
        word_count = _template_count(skill, subskill, "word")
        scaffold_count = scaffold_step_count_for_target(skill, subskill)
        native_available = _native_question_available(skill, subskill, unit.optional)
        khan_url = _khan_url(skill, subskill)
        open_resource_url = _open_resource_url(skill, subskill)
        has_intuition = _has_intuition(skill, subskill)
        readiness, notes = _readiness(
            skill,
            subskill,
            expression_count=expression_count,
            word_count=word_count,
            scaffold_count=scaffold_count,
            native_question_available=native_available,
            has_intuition=has_intuition,
            khan_url=khan_url,
            open_resource_url=open_resource_url,
        )
        rows.append(
            SummerContentAuditRow(
                lane=lane,
                unit_code=unit.code,
                unit_label=unit.label,
                optional=unit.optional,
                skill=skill,
                subskill=subskill,
                expression_template_count=expression_count,
                word_template_count=word_count,
                scaffold_step_count=scaffold_count,
                native_question_available=native_available,
                has_intuition=has_intuition,
                khan_url=khan_url,
                open_resource_url=open_resource_url,
                readiness=readiness,
                notes=notes,
            )
        )
    return tuple(rows)


def _template_count(skill: str, subskill: str, mode: str) -> int:
    with db.managed_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*)
            FROM question_templates
            WHERE active = 1 AND skill = ? AND subskill = ? AND mode = ?
            """,
            (skill, subskill, mode),
        ).fetchone()
    return int(row[0]) if row is not None else 0


def _native_question_available(skill: str, subskill: str, optional_unit: bool) -> bool:
    level = 2 if optional_unit or skill in {"pre_algebra", "algebra_linear", "algebra_1", "geometry_area"} else 1
    try:
        question = generate_question(skill, level, "typed", subskill=subskill)
    except (ContentUnavailableError, ValueError, ZeroDivisionError):
        return False
    return question.subskill in {None, subskill}


def _khan_url(skill: str, subskill: str) -> str:
    mapped = khan_url_for(skill, subskill)
    if mapped:
        return mapped
    return _PREVIEW_KHAN_URLS.get((skill, subskill), "")


def _open_resource_url(skill: str, subskill: str) -> str:
    spec = spec_for(skill, subskill)
    if spec is not None:
        for source_id in spec.source_ids:
            url = _OPEN_RESOURCE_BY_SOURCE_ID.get(source_id, "")
            if url:
                return url
    return _OPEN_RESOURCE_BY_SKILL.get(skill, "")


def _has_intuition(skill: str, subskill: str) -> bool:
    spec = spec_for(skill, subskill)
    if spec is not None:
        pack = spec.intuition
        return bool(pack.mental_model and pack.common_mistake and pack.try_this)
    explanation = ARITHMETIC_MODE_EXPLANATIONS.get(skill)
    if explanation is None:
        return False
    return bool(explanation.mental_model and explanation.common_mistake and explanation.try_this)


def _readiness(
    skill: str,
    subskill: str,
    *,
    expression_count: int,
    word_count: int,
    scaffold_count: int,
    native_question_available: bool,
    has_intuition: bool,
    khan_url: str,
    open_resource_url: str,
) -> tuple[Readiness, tuple[str, ...]]:
    missing: list[str] = []
    thin: list[str] = []
    if expression_count + word_count + scaffold_count == 0 and not native_question_available:
        missing.append("no active question source")
    if not khan_url:
        missing.append("missing Khan link")
    expression_target = EXPRESSION_TARGETS.get((skill, subskill), 1)
    if expression_count < expression_target:
        thin.append(f"expression templates {expression_count}/{expression_target}")
    word_target = WORD_TARGETS.get((skill, subskill), 0)
    if word_target > 0 and word_count < word_target:
        thin.append(f"word templates {word_count}/{word_target}")
    if not has_intuition:
        thin.append("missing intuition pack")
    if not open_resource_url:
        thin.append("missing open resource link")
    if scaffold_count == 0 and skill in {"pre_algebra", "algebra_linear", "algebra_1", "geometry_area"}:
        thin.append("no scaffolded lesson steps")
    if missing:
        return MISSING, tuple(missing + thin)
    if thin:
        return THIN, tuple(thin)
    return READY, ()


def _count_readiness(rows: tuple[SummerContentAuditRow, ...], readiness: Readiness) -> int:
    return sum(1 for row in rows if row.readiness == readiness)
