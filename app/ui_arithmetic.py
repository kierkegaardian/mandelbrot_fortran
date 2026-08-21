from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
import socket
import tkinter as tk
from tkinter import ttk
import webbrowser

from .arithmetic_summer_lessons import build_summer_lesson, supports_summer_lesson
from .arithmetic_render import render_arithmetic
from .arithmetic_draw import cell_positions
from .algebra_1_generators import khan_url_for as algebra_1_khan_url_for
from .algebra_2_generators import khan_url_for as algebra_2_khan_url_for
from .calculus_catalog import khan_url_for as calculus_khan_url_for
from .data_analysis import khan_url_for as data_analysis_khan_url_for
from .early_math_catalog import khan_url_for as catalog_khan_url_for
from .explanations import ARITHMETIC_MODE_EXPLANATIONS, explanation_for
from .financial_literacy import khan_url_for as financial_khan_url_for
from .openmoji_assets import openmoji_paths
from .quiz_answers import is_correct_answer
from .skill_graph import ARITHMETIC_SKILLS, SKILL_LABELS, skills_in_track, subskills_for, track_names
from .statistics_catalog import khan_url_for as statistics_khan_url_for
from .summer_mode import filter_skills, filter_tracks
from .theme import COLORS, FONTS
from .ui_explain import ExplanationPanel
from .ui_settings import UiSettings, load_ui_settings
from .ui_widgets import int_spinbox

KHAN_URL_BY_SKILL = {
    "counting": "https://www.khanacademy.org/math/cc-kindergarten-math/cc-kindergarten-counting-and-cardinality",
    "place_value": "https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-place-value",
    "add_subtract": "https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-add-subtract-100",
    "multiply": "https://www.khanacademy.org/math/cc-third-grade-math/imp-mult-div",
    "divide": "https://www.khanacademy.org/math/cc-third-grade-math/imp-mult-div",
    "ratios": "https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-ratios-proportional-relationships",
    "fractions": "https://www.khanacademy.org/math/cc-fourth-grade-math/imp-fractions-2",
    "long_addition": "https://www.khanacademy.org/math/cc-fourth-grade-math/imp-add-sub-multi-digit",
    "long_subtraction": "https://www.khanacademy.org/math/cc-fourth-grade-math/imp-add-sub-multi-digit",
    "long_multiplication": "https://www.khanacademy.org/math/cc-fifth-grade-math/imp-multi-digit-arithmetic",
    "long_division": "https://www.khanacademy.org/math/cc-fifth-grade-math/imp-multi-digit-arithmetic",
    "money": "https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-money",
    "financial_literacy": "https://www.khanacademy.org/college-careers-more/personal-finance",
    "measurement": "https://www.khanacademy.org/math/cc-4th-grade-math/imp-measurement-and-data-2",
    "geometry_shapes": "https://www.khanacademy.org/math/cc-1st-grade-math/cc-1st-measurement-geometry",
    "data_displays": "https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:data",
    "data_analysis": "https://www.khanacademy.org/math/statistics-probability/displaying-describing-data",
    "integers": "https://www.khanacademy.org/math/pre-algebra/pre-algebra-negative-numbers",
    "order_of_operations": "https://www.khanacademy.org/math/pre-algebra/pre-algebra-exponents-radicals",
    "pre_algebra": "https://www.khanacademy.org/math/pre-algebra",
    "algebra_linear": "https://www.khanacademy.org/math/algebra-basics/alg-basics-solving-equations-and-inequalities",
    "algebra_1": "https://www.khanacademy.org/math/algebra",
    "algebra_2": "https://www.khanacademy.org/math/algebra2",
    "geometry_area": "https://www.khanacademy.org/math/geometry",
    "trig_right_triangle": "https://www.khanacademy.org/math/precalculus",
    "stats_percent": "https://www.khanacademy.org/math/pre-algebra/pre-algebra-ratios-rates",
    "stats_mean": "https://www.khanacademy.org/math/statistics-probability/summarizing-quantitative-data",
    "stats_probability": "https://www.khanacademy.org/math/statistics-probability/probability-library",
    "statistics": "https://www.khanacademy.org/math/statistics-probability",
    "calculus_1": "https://www.khanacademy.org/math/ap-calculus-ab",
    "calculus_2": "https://www.khanacademy.org/math/ap-calculus-bc",
    "calculus_3": "https://www.khanacademy.org/math/multivariable-calculus",
    "sat_math": "https://www.khanacademy.org/digital-sat/start",
    "psat_math": "https://www.khanacademy.org/digital-sat/start",
    "gre_quant": "https://www.khanacademy.org/math/algebra2",
    "calculus_slope": "https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-1-new/ab-2-1/e/derivative-at-a-point-as-slope-of-tangent-line",
}

GEOMETRY_KHAN_URL_BY_SUBSKILL = {
    "Area of rectangles and squares": "https://www.khanacademy.org/math/basic-geo/basic-geo-area-and-perimeter/area-rectangles",
    "Area of triangles and parallelograms": "https://www.khanacademy.org/math/basic-geo/basic-geo-area-and-perimeter/area-triangle/e/area_of_triangles_1",
    "Area of trapezoids and composite figures": "https://www.khanacademy.org/math/basic-geo/basic-geo-area-and-perimeter/area-trap-composite",
    "Perimeter and missing sides": "https://www.khanacademy.org/math/basic-geo/basic-geo-area-and-perimeter",
    "Circumference and area of circles": "https://www.khanacademy.org/math/basic-geo/basic-geo-area-and-perimeter/circum-area-circles",
    "Surface area and volume": "https://www.khanacademy.org/math/basic-geo/basic-geo-volume-sa",
    "Pythagorean theorem": "https://www.khanacademy.org/math/basic-geo/basic-geo-pythagorean-topic/basic-geometry-pythagorean-theorem/e/pythagorean_theorem_1",
    "Coordinate geometry distance and midpoint": "https://www.khanacademy.org/math/geometry/hs-geo-analytic-geometry/hs-geo-dist-problems/e/coordinate-plane-word-problems-with-polygons",
    "Angles in lines and triangles": "https://www.khanacademy.org/math/geometry/hs-geo-foundations/hs-geo-angles",
    "Triangle congruence criteria": "https://www.khanacademy.org/math/geometry/hs-geo-congruence/hs-geo-triangle-congruence",
    "Transformations and congruence": "https://www.khanacademy.org/math/geometry/xff63fac4:hs-geo-transformation-properties-and-proofs/hs-geo-transformations-definitions/e/qualitatively-defining-rigid-transformations",
    "Similarity and scale factor": "https://www.khanacademy.org/math/geometry/hs-geo-similarity/hs-geo-similarity-definitions/e/exploring-angle-preserving-transformations-and-similarity",
    "Analytic geometry and coordinate proofs": "https://www.khanacademy.org/math/geometry/hs-geo-analytic-geometry/hs-geo-dist-problems/e/coordinate-plane-word-problems-with-polygons",
}

TRIG_KHAN_URL_BY_SUBSKILL = {
    "Right-triangle trig ratios": "https://www.khanacademy.org/math/precalculus",
    "Unit circle trig values": "https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:trig/x9e81a4f98389efdf:unit-circle-trig",
    "Trig functions and graphs": "https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:trig/x9e81a4f98389efdf:sinus-models",
    "Trig identities": "https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:trig/x9e81a4f98389efdf:trig-identities",
    "Inverse trig": "https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:trig/x9e81a4f98389efdf:inverse-trig-functions",
    "Vectors": "https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:vectors",
    "Matrices and linear transformations": "https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:matrices/x9e81a4f98389efdf:using-matrices-to-transform-the-plane/e/use-matrices-to-transform-the-plane",
    "Polar coordinates": "https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:parametric-equations-polar-coordinates-and-vector-valued-functions/x9e81a4f98389efdf:polar-coordinates",
}


@dataclass(frozen=True)
class LessonLinkState:
    enabled: bool
    url: str
    message: str


def khan_url_for_selection(skill: str, subskill: str | None = None) -> str:
    cleaned = (subskill or "").strip()
    if skill == "algebra_1":
        return algebra_1_khan_url_for(None if cleaned == "Any" else cleaned or None)
    if skill == "algebra_2":
        return algebra_2_khan_url_for(None if cleaned == "Any" else cleaned or None)
    if skill in {"calculus_1", "calculus_2", "calculus_3"}:
        return calculus_khan_url_for(skill, None if cleaned == "Any" else cleaned or None)
    if skill == "geometry_area" and cleaned and cleaned != "Any":
        return GEOMETRY_KHAN_URL_BY_SUBSKILL.get(cleaned, KHAN_URL_BY_SKILL["geometry_area"])
    if skill == "trig_right_triangle" and cleaned and cleaned != "Any":
        return TRIG_KHAN_URL_BY_SUBSKILL.get(cleaned, KHAN_URL_BY_SKILL["trig_right_triangle"])
    if skill == "data_analysis":
        return data_analysis_khan_url_for(None if cleaned == "Any" else cleaned or None)
    if skill == "financial_literacy":
        return financial_khan_url_for(None if cleaned == "Any" else cleaned or None)
    if skill == "statistics":
        return statistics_khan_url_for(None if cleaned == "Any" else cleaned or None)
    if cleaned and cleaned != "Any":
        url = catalog_khan_url_for(skill, cleaned)
        if url:
            return url
    return KHAN_URL_BY_SKILL.get(skill, "")


def lesson_link_state(skill: str, subskill: str | None, settings: UiSettings) -> LessonLinkState:
    if settings.enforce_offline_mode:
        return LessonLinkState(False, "", "Offline mode is enforced in Parent settings.")
    if not settings.show_external_links:
        return LessonLinkState(False, "", "External links are disabled in Parent settings.")
    url = khan_url_for_selection(skill, subskill=subskill)
    if not url:
        return LessonLinkState(False, "", "No lesson link mapped for this topic yet.")
    return LessonLinkState(True, url, "Opens a mapped Khan Academy practice or lesson in your browser.")


class ArithmeticPanel:
    def __init__(self, controls_parent: tk.Widget, view_parent: tk.Widget) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)

        self.skill_var = tk.StringVar(value="counting")
        self.track_var = tk.StringVar(value="All")
        self.subskill_var = tk.StringVar(value="Any")
        self.object_style_var = tk.StringVar(value="Circles")
        self.expression_var = tk.StringVar(value="")
        self.practice_var = tk.StringVar(value="You are practicing: Counting")
        self.lesson_var = tk.StringVar(value="")
        self.guided_status_var = tk.StringVar(value="")
        self.guided_title_var = tk.StringVar(value="")
        self.guided_prompt_var = tk.StringVar(value="")
        self.guided_hint_var = tk.StringVar(value="")
        self.guided_feedback_var = tk.StringVar(value="")
        self.guided_answer_var = tk.StringVar(value="")
        self._openmoji_images: dict[str, tk.PhotoImage] = {}
        self._openmoji_scaled: dict[tuple[str, str, int], tk.PhotoImage] = {}
        self._khan_check_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="khan-check")
        self._khan_check_future: Future[bool] | None = None
        self._lesson_steps = []
        self._lesson_index = 0
        self._lesson_skill: str | None = None
        self.guided_frame: ttk.LabelFrame | None = None

        self.count_var = tk.IntVar(value=6)
        self.a_var = tk.IntVar(value=6)
        self.b_var = tk.IntVar(value=4)
        self.op_var = tk.StringVar(value="add")
        self.rows_var = tk.IntVar(value=3)
        self.cols_var = tk.IntVar(value=4)
        self.total_var = tk.IntVar(value=12)
        self.groups_var = tk.IntVar(value=3)
        self.ratio_a_var = tk.IntVar(value=2)
        self.ratio_b_var = tk.IntVar(value=3)
        self.frac_num_var = tk.IntVar(value=3)
        self.frac_den_var = tk.IntVar(value=4)
        self.long_a_var = tk.IntVar(value=124)
        self.long_b_var = tk.IntVar(value=37)
        self.money_dollars_var = tk.IntVar(value=12)
        self.money_cents_var = tk.IntVar(value=50)
        self.int_a_var = tk.IntVar(value=-8)
        self.int_b_var = tk.IntVar(value=5)
        self.int_c_var = tk.IntVar(value=4)
        self.int_op1_var = tk.StringVar(value="*")
        self.int_op2_var = tk.StringVar(value="+")
        self.order_shape_var = tk.StringVar(value="(a op b) op c")
        self.algebra_a_var = tk.IntVar(value=3)
        self.algebra_b_var = tk.IntVar(value=7)
        self.algebra_c_var = tk.IntVar(value=28)
        self.geom_shape_var = tk.StringVar(value="rectangle")
        self.geom_width_var = tk.IntVar(value=8)
        self.geom_height_var = tk.IntVar(value=5)
        self.geom_side_var = tk.IntVar(value=6)
        self.trig_opp_var = tk.IntVar(value=4)
        self.trig_adj_var = tk.IntVar(value=3)
        self.trig_hyp_var = tk.IntVar(value=5)
        self.trig_func_var = tk.StringVar(value="sin")
        self.percent_value_var = tk.IntVar(value=40)
        self.percent_total_var = tk.IntVar(value=120)
        self.mean_count_var = tk.IntVar(value=3)
        self.mean_a_var = tk.IntVar(value=12)
        self.mean_b_var = tk.IntVar(value=18)
        self.mean_c_var = tk.IntVar(value=21)
        self.mean_d_var = tk.IntVar(value=9)
        self.mean_e_var = tk.IntVar(value=15)
        self.prob_success_var = tk.IntVar(value=3)
        self.prob_total_var = tk.IntVar(value=9)
        self.slope_x1_var = tk.IntVar(value=1)
        self.slope_y1_var = tk.IntVar(value=2)
        self.slope_x2_var = tk.IntVar(value=5)
        self.slope_y2_var = tk.IntVar(value=6)
        self.canvas: tk.Canvas | None = None

        self._build_controls()
        self._build_view()
        self._load_openmoji()
        self.render()

    def _build_controls(self) -> None:
        frame = ttk.Frame(self.controls_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Math Track").pack(anchor=tk.W)
        track_cb = ttk.Combobox(
            frame,
            textvariable=self.track_var,
            values=["All", *track_names()],
            state="readonly",
        )
        track_cb.pack(fill=tk.X, pady=(0, 8))
        track_cb.bind("<<ComboboxSelected>>", lambda _e: self._on_track_change())
        self.track_cb = track_cb

        ttk.Label(frame, text="Math Topic").pack(anchor=tk.W)
        self._skill_combo = ttk.Combobox(
            frame,
            textvariable=self.skill_var,
            values=ARITHMETIC_SKILLS,
            state="readonly",
        )
        self._skill_combo.pack(fill=tk.X, pady=(0, 8))
        self._skill_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_skill_change())
        ttk.Label(frame, text="Subskill").pack(anchor=tk.W)
        self._subskill_combo = ttk.Combobox(
            frame,
            textvariable=self.subskill_var,
            values=["Any"],
            state="readonly",
        )
        self._subskill_combo.pack(fill=tk.X, pady=(0, 8))
        self._subskill_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_subskill_change())

        ttk.Label(frame, text="Object Style").pack(anchor=tk.W)
        self.style_cb = ttk.Combobox(
            frame,
            textvariable=self.object_style_var,
            values=[
                "Circles",
                "Squares",
                "Triangles",
                "Stars",
                "Hearts",
                "Apples",
                "Fish",
                "Black Dog",
                "Avocados",
                "Trucks",
            ],
            state="readonly",
        )
        self.style_cb.pack(fill=tk.X, pady=(0, 12))
        self.style_cb.bind("<<ComboboxSelected>>", lambda _e: self.render())

        self.stack = ttk.Frame(frame)
        self.stack.pack(fill=tk.X)
        self._build_counting(self.stack)
        self._build_add_subtract(self.stack)
        self._build_multiply(self.stack)
        self._build_divide(self.stack)
        self._build_ratios(self.stack)
        self._build_fractions(self.stack)
        self._build_long(self.stack)
        self._build_money(self.stack)
        self._build_integer_like(self.stack)
        self._build_algebra(self.stack)
        self._build_geometry(self.stack)
        self._build_trig(self.stack)
        self._build_stats(self.stack)
        self._build_slope(self.stack)
        self._show_frame(self.counting_frame)

        self.explain = ExplanationPanel(frame)
        self.explain.set_explanation(ARITHMETIC_MODE_EXPLANATIONS["counting"])
        self.explain.frame.pack(fill=tk.X, pady=(12, 0))
        self.lesson_btn = ttk.Button(frame, text="Watch lesson (online)", command=self._open_lesson)
        self.lesson_btn.pack(anchor=tk.W, pady=(10, 2))
        ttk.Label(frame, textvariable=self.lesson_var, wraplength=260, foreground=COLORS["text_secondary"]).pack(anchor=tk.W)
        self.guided_btn = ttk.Button(frame, text="Start Guided Lesson", command=self._start_guided_lesson)
        self.guided_btn.pack(anchor=tk.W, pady=(10, 2))
        ttk.Label(frame, textvariable=self.guided_status_var, wraplength=260, foreground=COLORS["text_secondary"]).pack(
            anchor=tk.W
        )
        self._apply_track_filter()
        self._on_skill_change()

    def _build_view(self) -> None:
        ttk.Label(self.view_frame, textvariable=self.practice_var, font=FONTS["body_bold"]).pack(
            anchor=tk.W, padx=8, pady=(8, 0)
        )
        ttk.Label(self.view_frame, textvariable=self.expression_var, font=("Helvetica", 13, "bold")).pack(pady=(8, 4))
        self.canvas = tk.Canvas(self.view_frame, bg=COLORS["canvas_bg"])
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.guided_frame = ttk.LabelFrame(self.view_frame, text="Guided Lesson")
        ttk.Label(self.guided_frame, textvariable=self.guided_title_var, font=FONTS["body_bold"]).pack(
            anchor=tk.W, padx=12, pady=(10, 2)
        )
        ttk.Label(self.guided_frame, textvariable=self.guided_prompt_var, wraplength=760).pack(
            anchor=tk.W, padx=12, pady=(0, 4)
        )
        ttk.Label(self.guided_frame, textvariable=self.guided_hint_var, wraplength=760, foreground=COLORS["text_secondary"]).pack(
            anchor=tk.W, padx=12, pady=(0, 6)
        )
        answer_row = ttk.Frame(self.guided_frame)
        answer_row.pack(fill=tk.X, padx=12, pady=(0, 6))
        ttk.Label(answer_row, text="Answer").pack(side=tk.LEFT)
        self.guided_entry = ttk.Entry(answer_row, textvariable=self.guided_answer_var)
        self.guided_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        self.guided_entry.bind("<Return>", lambda _e: self._submit_guided_lesson())
        btn_row = ttk.Frame(self.guided_frame)
        btn_row.pack(anchor=tk.W, padx=12, pady=(0, 10))
        self.guided_submit_btn = ttk.Button(btn_row, text="Check", command=self._submit_guided_lesson)
        self.guided_submit_btn.pack(side=tk.LEFT)
        self.guided_next_btn = ttk.Button(btn_row, text="Next Step", command=self._next_guided_lesson)
        self.guided_next_btn.pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(self.guided_frame, textvariable=self.guided_feedback_var, foreground=COLORS["accent_strong"], wraplength=760).pack(
            anchor=tk.W, padx=12, pady=(0, 12)
        )

    def _build_counting(self, parent: tk.Widget) -> None:
        self.counting_frame = ttk.Frame(parent)
        ttk.Label(self.counting_frame, text="Count").grid(row=0, column=0, sticky=tk.W)
        int_spinbox(self.counting_frame, self.count_var, 0, 40, command=self.render).grid(
            row=0, column=1, padx=4, pady=4
        )
        ttk.Button(self.counting_frame, text="+", command=lambda: self._nudge(self.count_var, 1)).grid(
            row=0, column=2, padx=2
        )
        ttk.Button(self.counting_frame, text="-", command=lambda: self._nudge(self.count_var, -1)).grid(
            row=0, column=3, padx=2
        )

    def _build_add_subtract(self, parent: tk.Widget) -> None:
        self.addsub_frame = ttk.Frame(parent)
        ttk.Label(self.addsub_frame, text="A").grid(row=0, column=0, sticky=tk.W)
        int_spinbox(self.addsub_frame, self.a_var, 0, 30, command=self.render).grid(
            row=0, column=1, padx=4, pady=4
        )
        ttk.Label(self.addsub_frame, text="B").grid(row=1, column=0, sticky=tk.W)
        int_spinbox(self.addsub_frame, self.b_var, 0, 30, command=self.render).grid(
            row=1, column=1, padx=4, pady=4
        )
        ttk.Radiobutton(self.addsub_frame, text="Add", variable=self.op_var, value="add", command=self.render).grid(
            row=2, column=0, sticky=tk.W
        )
        ttk.Radiobutton(
            self.addsub_frame, text="Subtract", variable=self.op_var, value="subtract", command=self.render
        ).grid(row=2, column=1, sticky=tk.W)

    def _build_multiply(self, parent: tk.Widget) -> None:
        self.multiply_frame = ttk.Frame(parent)
        ttk.Label(self.multiply_frame, text="Rows").grid(row=0, column=0, sticky=tk.W)
        int_spinbox(self.multiply_frame, self.rows_var, 1, 12, command=self.render).grid(
            row=0, column=1, padx=4, pady=4
        )
        ttk.Label(self.multiply_frame, text="Columns").grid(row=1, column=0, sticky=tk.W)
        int_spinbox(self.multiply_frame, self.cols_var, 1, 12, command=self.render).grid(
            row=1, column=1, padx=4, pady=4
        )

    def _build_divide(self, parent: tk.Widget) -> None:
        self.divide_frame = ttk.Frame(parent)
        ttk.Label(self.divide_frame, text="Total").grid(row=0, column=0, sticky=tk.W)
        int_spinbox(self.divide_frame, self.total_var, 1, 40, command=self.render).grid(
            row=0, column=1, padx=4, pady=4
        )
        ttk.Label(self.divide_frame, text="Groups").grid(row=1, column=0, sticky=tk.W)
        int_spinbox(self.divide_frame, self.groups_var, 1, 12, command=self.render).grid(
            row=1, column=1, padx=4, pady=4
        )

    def _build_ratios(self, parent: tk.Widget) -> None:
        self.ratios_frame = ttk.Frame(parent)
        ttk.Label(self.ratios_frame, text="A").grid(row=0, column=0, sticky=tk.W)
        int_spinbox(self.ratios_frame, self.ratio_a_var, 1, 20, command=self.render).grid(
            row=0, column=1, padx=4, pady=4
        )
        ttk.Label(self.ratios_frame, text="B").grid(row=1, column=0, sticky=tk.W)
        int_spinbox(self.ratios_frame, self.ratio_b_var, 1, 20, command=self.render).grid(
            row=1, column=1, padx=4, pady=4
        )

    def _build_fractions(self, parent: tk.Widget) -> None:
        self.fractions_frame = ttk.Frame(parent)
        ttk.Label(self.fractions_frame, text="Numerator").grid(row=0, column=0, sticky=tk.W)
        int_spinbox(self.fractions_frame, self.frac_num_var, 0, 36, command=self.render).grid(
            row=0, column=1, padx=4, pady=4
        )
        ttk.Label(self.fractions_frame, text="Denominator").grid(row=1, column=0, sticky=tk.W)
        int_spinbox(self.fractions_frame, self.frac_den_var, 1, 12, command=self.render).grid(
            row=1, column=1, padx=4, pady=4
        )

    def _build_long(self, parent: tk.Widget) -> None:
        self.long_frame = ttk.Frame(parent)
        ttk.Label(self.long_frame, text="Number A").grid(row=0, column=0, sticky=tk.W)
        int_spinbox(self.long_frame, self.long_a_var, 0, 9999, command=self.render).grid(
            row=0, column=1, padx=4, pady=4
        )
        ttk.Label(self.long_frame, text="Number B").grid(row=1, column=0, sticky=tk.W)
        int_spinbox(self.long_frame, self.long_b_var, 1, 9999, command=self.render).grid(
            row=1, column=1, padx=4, pady=4
        )

    def _build_money(self, parent: tk.Widget) -> None:
        self.money_frame = ttk.Frame(parent)
        ttk.Label(self.money_frame, text="Dollars").grid(row=0, column=0, sticky=tk.W)
        int_spinbox(self.money_frame, self.money_dollars_var, 0, 500, command=self.render).grid(
            row=0, column=1, padx=4, pady=4
        )
        ttk.Label(self.money_frame, text="Cents").grid(row=1, column=0, sticky=tk.W)
        int_spinbox(self.money_frame, self.money_cents_var, 0, 99, command=self.render).grid(
            row=1, column=1, padx=4, pady=4
        )

    def _build_integer_like(self, parent: tk.Widget) -> None:
        self.integer_frame = ttk.Frame(parent)
        self.order_frame = ttk.Frame(parent)
        ttk.Label(self.integer_frame, text="A").grid(row=0, column=0, sticky=tk.W)
        int_spinbox(self.integer_frame, self.int_a_var, -20, 20, command=self.render).grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(self.integer_frame, text="Operation 1").grid(row=0, column=2, sticky=tk.W)
        ttk.Combobox(
            self.integer_frame,
            textvariable=self.int_op1_var,
            values=["+", "-", "*"],
            width=6,
            state="readonly",
        ).grid(row=0, column=3, padx=4, pady=4)
        self.int_op1_var.trace_add("write", lambda *_: self.render())

        ttk.Label(self.integer_frame, text="B").grid(row=1, column=0, sticky=tk.W)
        int_spinbox(self.integer_frame, self.int_b_var, -20, 20, command=self.render).grid(row=1, column=1, padx=4, pady=4)
        ttk.Label(self.integer_frame, text="Operation 2").grid(row=1, column=2, sticky=tk.W)
        ttk.Combobox(
            self.integer_frame,
            textvariable=self.int_op2_var,
            values=["+", "-", "*"],
            width=6,
            state="readonly",
        ).grid(row=1, column=3, padx=4, pady=4)
        self.int_op2_var.trace_add("write", lambda *_: self.render())
        ttk.Label(self.integer_frame, text="C").grid(row=2, column=0, sticky=tk.W)
        int_spinbox(self.integer_frame, self.int_c_var, -20, 20, command=self.render).grid(row=2, column=1, padx=4, pady=4)

        self.order_frame = ttk.Frame(parent)
        ttk.Label(self.order_frame, text="Expression style").grid(row=0, column=0, sticky=tk.W)
        ttk.Combobox(
            self.order_frame,
            textvariable=self.order_shape_var,
            values=["(a op b) op c", "a op (b op c)"],
            state="readonly",
            width=16,
        ).grid(row=0, column=1, sticky=tk.W, padx=4, pady=4)
        self.order_shape_var.trace_add("write", lambda *_: self.render())

    def _build_algebra(self, parent: tk.Widget) -> None:
        self.algebra_frame = ttk.Frame(parent)
        ttk.Label(self.algebra_frame, text="a").grid(row=0, column=0, sticky=tk.W)
        int_spinbox(self.algebra_frame, self.algebra_a_var, -12, 12, command=self.render).grid(
            row=0, column=1, padx=4, pady=4
        )
        ttk.Label(self.algebra_frame, text="b").grid(row=0, column=2, sticky=tk.W, padx=(6, 0))
        int_spinbox(self.algebra_frame, self.algebra_b_var, -40, 40, command=self.render).grid(
            row=0, column=3, padx=4, pady=4
        )
        ttk.Label(self.algebra_frame, text="right side").grid(row=1, column=0, sticky=tk.W)
        int_spinbox(self.algebra_frame, self.algebra_c_var, -100, 100, command=self.render).grid(
            row=1, column=1, padx=4, pady=4
        )

    def _build_geometry(self, parent: tk.Widget) -> None:
        self.geometry_frame = ttk.Frame(parent)
        ttk.Label(self.geometry_frame, text="Shape").grid(row=0, column=0, sticky=tk.W)
        shape_cb = ttk.Combobox(
            self.geometry_frame,
            textvariable=self.geom_shape_var,
            values=["rectangle", "square", "triangle"],
            state="readonly",
            width=12,
        )
        shape_cb.grid(row=0, column=1, sticky=tk.W)
        shape_cb.bind("<<ComboboxSelected>>", lambda _e: self._on_shape_change())
        ttk.Label(self.geometry_frame, text="Length").grid(row=1, column=0, sticky=tk.W)
        int_spinbox(self.geometry_frame, self.geom_width_var, 1, 18, command=self.render).grid(row=1, column=1, padx=4, pady=4)
        ttk.Label(self.geometry_frame, text="Width/Height").grid(row=1, column=2, sticky=tk.W, padx=(6, 0))
        int_spinbox(self.geometry_frame, self.geom_height_var, 1, 18, command=self.render).grid(row=1, column=3, padx=4, pady=4)
        ttk.Label(self.geometry_frame, text="Side").grid(row=2, column=0, sticky=tk.W)
        int_spinbox(self.geometry_frame, self.geom_side_var, 1, 18, command=self.render).grid(row=2, column=1, padx=4, pady=4)
        self._on_shape_change()

    def _on_shape_change(self) -> None:
        if self.geom_shape_var.get() == "triangle":
            self.geom_side_var.set(max(1, min(self.geom_side_var.get(), 16)))
            if self.geom_height_var.get() == self.geom_side_var.get():
                self.geom_height_var.set(max(2, self.geom_width_var.get()))
        elif self.geom_shape_var.get() == "square":
            self.geom_height_var.set(self.geom_width_var.get())
        self.render()

    def _build_trig(self, parent: tk.Widget) -> None:
        self.trig_frame = ttk.Frame(parent)
        ttk.Label(self.trig_frame, text="Opposite").grid(row=0, column=0, sticky=tk.W)
        int_spinbox(self.trig_frame, self.trig_opp_var, 1, 16, command=self.render).grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(self.trig_frame, text="Adjacent").grid(row=1, column=0, sticky=tk.W)
        int_spinbox(self.trig_frame, self.trig_adj_var, 1, 16, command=self.render).grid(row=1, column=1, padx=4, pady=4)
        ttk.Label(self.trig_frame, text="Hypotenuse").grid(row=2, column=0, sticky=tk.W)
        int_spinbox(self.trig_frame, self.trig_hyp_var, 1, 24, command=self.render).grid(row=2, column=1, padx=4, pady=4)
        ttk.Label(self.trig_frame, text="Ratio").grid(row=3, column=0, sticky=tk.W)
        ttk.Combobox(
            self.trig_frame,
            textvariable=self.trig_func_var,
            values=["sin", "cos", "tan"],
            state="readonly",
            width=6,
        ).grid(row=3, column=1, padx=4, pady=4)
        self.trig_func_var.trace_add("write", lambda *_: self.render())

    def _build_stats(self, parent: tk.Widget) -> None:
        self.percent_frame = ttk.Frame(parent)
        ttk.Label(self.percent_frame, text="Percent").grid(row=0, column=0, sticky=tk.W)
        int_spinbox(self.percent_frame, self.percent_value_var, 0, 100, command=self.render).grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(self.percent_frame, text="Of").grid(row=0, column=2, sticky=tk.W)
        int_spinbox(self.percent_frame, self.percent_total_var, 1, 500, command=self.render).grid(row=0, column=3, padx=4, pady=4)

        self.mean_frame = ttk.Frame(parent)
        ttk.Label(self.mean_frame, text="Count").grid(row=0, column=0, sticky=tk.W)
        int_spinbox(self.mean_frame, self.mean_count_var, 2, 5, command=self.render).grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(self.mean_frame, text="Values:").grid(row=1, column=0, sticky=tk.W, pady=(4, 0))
        int_spinbox(self.mean_frame, self.mean_a_var, 0, 100, command=self.render).grid(row=1, column=1, padx=4, pady=2)
        int_spinbox(self.mean_frame, self.mean_b_var, 0, 100, command=self.render).grid(row=1, column=2, padx=4, pady=2)
        int_spinbox(self.mean_frame, self.mean_c_var, 0, 100, command=self.render).grid(row=1, column=3, padx=4, pady=2)
        int_spinbox(self.mean_frame, self.mean_d_var, 0, 100, command=self.render).grid(row=2, column=1, padx=4, pady=2)
        int_spinbox(self.mean_frame, self.mean_e_var, 0, 100, command=self.render).grid(row=2, column=2, padx=4, pady=2)

        self.prob_frame = ttk.Frame(parent)
        ttk.Label(self.prob_frame, text="Successes").grid(row=0, column=0, sticky=tk.W)
        int_spinbox(self.prob_frame, self.prob_success_var, 0, 20, command=self.render).grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(self.prob_frame, text="Total").grid(row=0, column=2, sticky=tk.W, padx=(6, 0))
        int_spinbox(self.prob_frame, self.prob_total_var, 1, 30, command=self.render).grid(row=0, column=3, padx=4, pady=4)

    def _build_slope(self, parent: tk.Widget) -> None:
        self.slope_frame = ttk.Frame(parent)
        ttk.Label(self.slope_frame, text="x₁").grid(row=0, column=0, sticky=tk.W)
        int_spinbox(self.slope_frame, self.slope_x1_var, -10, 20, command=self.render).grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(self.slope_frame, text="y₁").grid(row=0, column=2, sticky=tk.W, padx=(6, 0))
        int_spinbox(self.slope_frame, self.slope_y1_var, -20, 40, command=self.render).grid(row=0, column=3, padx=4, pady=4)
        ttk.Label(self.slope_frame, text="x₂").grid(row=1, column=0, sticky=tk.W)
        int_spinbox(self.slope_frame, self.slope_x2_var, -10, 20, command=self.render).grid(row=1, column=1, padx=4, pady=4)
        ttk.Label(self.slope_frame, text="y₂").grid(row=1, column=2, sticky=tk.W, padx=(6, 0))
        int_spinbox(self.slope_frame, self.slope_y2_var, -20, 40, command=self.render).grid(row=1, column=3, padx=4, pady=4)

    def _show_frame(self, frame: tk.Widget) -> None:
        for child in self.stack.winfo_children():
            child.pack_forget()
        frame.pack(fill=tk.X, pady=(0, 8))

    def _apply_track_filter(self) -> None:
        settings = load_ui_settings()
        visible_tracks = list(
            filter_tracks(track_names(), skills_in_track, grade_band=settings.default_grade_band, summer_mode=settings.summer_mode)
        )
        track_values = visible_tracks if settings.summer_mode else ["All", *visible_tracks]
        if not track_values:
            track_values = ["All"]
        if self.track_var.get() not in track_values:
            self.track_var.set(track_values[0])
        self.track_cb.config(values=track_values)
        track = self.track_var.get()
        base_skills = ARITHMETIC_SKILLS if track == "All" else skills_in_track(track)
        skills = [
            skill
            for skill in filter_skills(base_skills, grade_band=settings.default_grade_band, summer_mode=settings.summer_mode)
            if skill in ARITHMETIC_SKILLS
        ]
        if not skills:
            skills = list(ARITHMETIC_SKILLS)
        if self.skill_var.get() not in skills:
            self.skill_var.set(skills[0])
        self._skill_combo.config(values=skills)
        self._refresh_subskills()

    def _on_track_change(self) -> None:
        self._apply_track_filter()
        self._on_skill_change()

    def _on_skill_change(self) -> None:
        self._stop_guided_lesson()
        skill = self.skill_var.get()
        self._refresh_subskills()
        selected_subskill = self.subskill_var.get()
        pre_algebra_frame = self.order_frame
        if selected_subskill == "Ratios, rates, and proportional relationships":
            pre_algebra_frame = self.ratios_frame
        elif selected_subskill == "Integer and fraction fluency":
            pre_algebra_frame = self.integer_frame
        elif selected_subskill == "Percent problems":
            pre_algebra_frame = self.percent_frame
        elif selected_subskill in {
            "One-step equations",
            "Two-step equations and inequalities",
            "Coordinate plane and function tables",
        }:
            pre_algebra_frame = self.algebra_frame
        frames = {
            "counting": self.counting_frame,
            "place_value": self.long_frame,
            "add_subtract": self.addsub_frame,
            "multiply": self.multiply_frame,
            "divide": self.divide_frame,
            "ratios": self.ratios_frame,
            "fractions": self.fractions_frame,
            "long_addition": self.long_frame,
            "long_subtraction": self.long_frame,
            "long_multiplication": self.long_frame,
            "long_division": self.long_frame,
            "money": self.money_frame,
            "measurement": self.long_frame,
            "integers": self.integer_frame,
            "order_of_operations": self.order_frame,
            "pre_algebra": pre_algebra_frame,
            "algebra_linear": self.algebra_frame,
            "algebra_1": self.algebra_frame,
            "algebra_2": self.algebra_frame,
            "geometry_area": self.geometry_frame,
            "trig_right_triangle": self.trig_frame,
            "stats_percent": self.percent_frame,
            "stats_mean": self.mean_frame,
            "stats_probability": self.prob_frame,
            "calculus_1": self.slope_frame,
            "calculus_slope": self.slope_frame,
        }
        self._show_frame(frames[skill])
        track = self.track_var.get()
        subskill = self.subskill_var.get()
        suffix = f" • {subskill}" if subskill != "Any" else ""
        if track == "All":
            self.practice_var.set(f"You are practicing: {SKILL_LABELS.get(skill, skill)}{suffix}")
        else:
            self.practice_var.set(f"You are practicing: {SKILL_LABELS.get(skill, skill)} ({track}){suffix}")
        explanation = explanation_for(skill, None if subskill == "Any" else subskill)
        self.explain.set_explanation(explanation)
        self._update_lesson_link(skill)
        self._refresh_guided_lesson_controls()
        self.render()

    def _refresh_subskills(self) -> None:
        skill = self.skill_var.get()
        options = ["Any", *subskills_for(skill)]
        if self.subskill_var.get() not in options:
            self.subskill_var.set("Any")
        self._subskill_combo.config(values=options)

    def _on_subskill_change(self) -> None:
        self._on_skill_change()

    def _nudge(self, var: tk.IntVar, delta: int) -> None:
        var.set(max(0, var.get() + delta))
        self.render()

    def _load_openmoji(self) -> None:
        for name, path in openmoji_paths().items():
            if not path.exists():
                continue
            try:
                self._openmoji_images[name] = tk.PhotoImage(file=str(path))
            except tk.TclError:
                continue

        if self._openmoji_images:
            base_styles = list(self.style_cb.cget("values"))
            extra = list(self._openmoji_images.keys())
            self.style_cb.configure(values=base_styles + extra)

    def _scaled_image(self, style: str, base: tk.PhotoImage, target: int) -> tk.PhotoImage:
        if target <= 0:
            return base
        if target >= base.width():
            factor = max(1, int(target / base.width()))
            key = (style, "zoom", factor)
            if key not in self._openmoji_scaled:
                self._openmoji_scaled[key] = base.zoom(factor)
            return self._openmoji_scaled[key]

        factor = max(1, int(base.width() / target))
        key = (style, "sub", factor)
        if key not in self._openmoji_scaled:
            self._openmoji_scaled[key] = base.subsample(factor)
        return self._openmoji_scaled[key]

    def _openmoji_for(self, style: str, count: int, bounds: tuple[int, int, int, int]) -> tk.PhotoImage | None:
        base = self._openmoji_images.get(style)
        if base is None:
            return None
        x, y, width, height = bounds
        safe_bounds = (x, y, max(20, width), max(20, height))
        positions = cell_positions(count, safe_bounds)
        size = int(positions[0][2]) if positions else 24
        return self._scaled_image(style, base, size)

    def render(self) -> None:
        if self.canvas is None:
            return
        render_arithmetic(self)

    def _refresh_guided_lesson_controls(self) -> None:
        settings = load_ui_settings()
        skill = self.skill_var.get()
        if settings.summer_mode and supports_summer_lesson(skill):
            self.guided_btn.state(["!disabled"])
            self.guided_status_var.set("Use Guided Lesson for a short teach-then-try summer session.")
            return
        self.guided_btn.state(["disabled"])
        self.guided_status_var.set("Guided lessons are available for core summer skills when Summer Mode is on.")
        if self.guided_frame is not None:
            self.guided_frame.pack_forget()

    def _start_guided_lesson(self) -> None:
        settings = load_ui_settings()
        skill = self.skill_var.get()
        if self.guided_frame is None or not settings.summer_mode or not supports_summer_lesson(skill):
            return
        subskill = None if self.subskill_var.get() == "Any" else self.subskill_var.get()
        self._lesson_steps = build_summer_lesson(skill, subskill=subskill)
        self._lesson_index = 0
        self._lesson_skill = skill
        self.guided_frame.pack(fill=tk.X, padx=8, pady=(8, 10))
        self._show_guided_lesson_step()

    def _show_guided_lesson_step(self) -> None:
        step = self._lesson_steps[self._lesson_index]
        for attr, value in step.presets.items():
            getattr(self, attr).set(value)
        self.guided_title_var.set(f"{step.title} ({self._lesson_index + 1}/{len(self._lesson_steps)})")
        self.guided_prompt_var.set(step.prompt)
        self.guided_hint_var.set(f"Hint: {step.hint}")
        self.guided_feedback_var.set("")
        self.guided_answer_var.set("")
        self.render()
        expects_answer = step.expected_answer is not None
        if expects_answer:
            self.guided_entry.state(["!disabled"])
            self.guided_submit_btn.state(["!disabled"])
            self.guided_next_btn.state(["disabled"])
            self.guided_entry.focus_set()
        else:
            self.guided_entry.state(["disabled"])
            self.guided_submit_btn.state(["disabled"])
            self.guided_next_btn.state(["!disabled"])

    def _submit_guided_lesson(self) -> None:
        if not self._lesson_steps:
            return
        step = self._lesson_steps[self._lesson_index]
        if step.expected_answer is None:
            return
        answer = self.guided_answer_var.get().strip()
        if not answer:
            self.guided_feedback_var.set("Type an answer first.")
            return
        if is_correct_answer(step.expected_answer, answer):
            self.guided_feedback_var.set("Correct. Move to the next step.")
            self.guided_submit_btn.state(["disabled"])
            self.guided_next_btn.state(["!disabled"])
            return
        self.guided_feedback_var.set(f"Not yet. {step.hint}")

    def _next_guided_lesson(self) -> None:
        if not self._lesson_steps:
            return
        if self._lesson_index + 1 >= len(self._lesson_steps):
            self.guided_title_var.set("Lesson complete")
            self.guided_prompt_var.set("Nice work. Start a quiz next to lock in the idea.")
            self.guided_hint_var.set("Tip: keep the picture in your head while you answer.")
            self.guided_feedback_var.set("Lesson finished.")
            self.guided_submit_btn.state(["disabled"])
            self.guided_next_btn.state(["disabled"])
            return
        self._lesson_index += 1
        self._show_guided_lesson_step()

    def _stop_guided_lesson(self) -> None:
        self._lesson_steps = []
        self._lesson_index = 0
        self._lesson_skill = None
        self.guided_title_var.set("")
        self.guided_prompt_var.set("")
        self.guided_hint_var.set("")
        self.guided_feedback_var.set("")
        self.guided_answer_var.set("")
        if self.guided_frame is not None:
            self.guided_frame.pack_forget()

    def _update_lesson_link(self, skill: str) -> None:
        settings = load_ui_settings()
        state = lesson_link_state(skill, self.subskill_var.get(), settings)
        if state.enabled:
            self.lesson_btn.state(["!disabled"])
        else:
            self.lesson_btn.state(["disabled"])
        self.lesson_var.set(state.message)

    def _open_lesson(self) -> None:
        settings = load_ui_settings()
        state = lesson_link_state(self.skill_var.get(), self.subskill_var.get(), settings)
        if not state.enabled:
            self.lesson_btn.state(["disabled"])
            self.lesson_var.set(state.message)
            return
        if self._khan_check_future is not None and not self._khan_check_future.done():
            self.lesson_var.set("Checking reachability…")
            return
        self.lesson_btn.state(["disabled"])
        self.lesson_var.set("Checking…")
        self._khan_check_future = self._khan_check_executor.submit(_can_reach_khan)
        self.controls_frame.after(40, lambda: self._poll_khan_check(state.url))

    def _poll_khan_check(self, url: str) -> None:
        future = self._khan_check_future
        if future is None:
            self.lesson_btn.state(["!disabled"])
            return
        if not future.done():
            self.controls_frame.after(40, lambda: self._poll_khan_check(url))
            return

        self._khan_check_future = None
        self._update_lesson_link(self.skill_var.get())
        reachable = False
        try:
            reachable = bool(future.result())
        except Exception:  # noqa: BLE001
            reachable = False
        if not reachable:
            self.lesson_var.set("Could not reach khanacademy.org. Check internet and try again.")
            return
        webbrowser.open(url)

    def shutdown(self) -> None:
        self._khan_check_executor.shutdown(wait=False, cancel_futures=True)


def _can_reach_khan(timeout: float = 1.2) -> bool:
    try:
        with socket.create_connection(("www.khanacademy.org", 443), timeout=timeout):
            return True
    except OSError:
        return False
