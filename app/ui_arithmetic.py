from __future__ import annotations

import socket
import tkinter as tk
from tkinter import ttk
import webbrowser

from .arithmetic_render import render_arithmetic
from .explanations import ARITHMETIC_MODE_EXPLANATIONS
from .skill_graph import ARITHMETIC_SKILLS, track_names
from .ui_explain import ExplanationPanel
from .theme import COLORS, FONTS
from .ui_arithmetic_builders import ArithmeticBuildersMixin
from .ui_arithmetic_interactions import ArithmeticInteractionsMixin
from .ui_settings import load_ui_settings

KHAN_URL_BY_SKILL = {
    "counting": "https://www.khanacademy.org/math/cc-kindergarten-math/cc-kindergarten-counting-and-cardinality",
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
    "integers": "https://www.khanacademy.org/math/pre-algebra/pre-algebra-negative-numbers",
    "order_of_operations": "https://www.khanacademy.org/math/pre-algebra/pre-algebra-exponents-radicals",
    "algebra_linear": "https://www.khanacademy.org/math/algebra-basics/alg-basics-solving-equations-and-inequalities",
    "algebra_2": "https://www.khanacademy.org/math/algebra2",
    "geometry_area": "https://www.khanacademy.org/math/basic-geo/basic-geo-area-and-perimeter",
    "trig_right_triangle": "https://www.khanacademy.org/math/trigonometry/trig-equations-and-identities",
    "stats_percent": "https://www.khanacademy.org/math/pre-algebra/pre-algebra-ratios-rates",
    "stats_mean": "https://www.khanacademy.org/math/statistics-probability/summarizing-quantitative-data",
    "stats_probability": "https://www.khanacademy.org/math/statistics-probability/probability-library",
    "calculus_1": "https://www.khanacademy.org/math/ap-calculus-ab",
    "calculus_2": "https://www.khanacademy.org/math/ap-calculus-bc",
    "calculus_3": "https://www.khanacademy.org/math/multivariable-calculus",
    "calculus_slope": "https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-1-new/ab-2-1/e/derivative-at-a-point-as-slope-of-tangent-line",
}


class ArithmeticPanel(ArithmeticBuildersMixin, ArithmeticInteractionsMixin):
    def __init__(self, controls_parent: tk.Widget, view_parent: tk.Widget) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)

        self.skill_var = tk.StringVar(value="counting")
        self.track_var = tk.StringVar(value="All")
        self.object_style_var = tk.StringVar(value="Circles")
        self.expression_var = tk.StringVar(value="")
        self.practice_var = tk.StringVar(value="You are practicing: Counting")
        self.lesson_var = tk.StringVar(value="")
        self._openmoji_images: dict[str, tk.PhotoImage] = {}
        self._openmoji_scaled: dict[tuple[str, str, int], tk.PhotoImage] = {}

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

        ttk.Label(frame, text="Math Topic").pack(anchor=tk.W)
        self._skill_combo = ttk.Combobox(
            frame,
            textvariable=self.skill_var,
            values=ARITHMETIC_SKILLS,
            state="readonly",
        )
        self._skill_combo.pack(fill=tk.X, pady=(0, 8))
        self._skill_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_skill_change())

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
        self._apply_track_filter()
        self._on_skill_change()

    def _build_view(self) -> None:
        ttk.Label(self.view_frame, textvariable=self.practice_var, font=FONTS["body_bold"]).pack(
            anchor=tk.W, padx=8, pady=(8, 0)
        )
        ttk.Label(self.view_frame, textvariable=self.expression_var, font=FONTS["heading"]).pack(pady=(8, 4))
        self.canvas = tk.Canvas(self.view_frame, bg=COLORS["canvas_bg"])
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def focus_primary_control(self) -> None:
        self._skill_combo.focus_set()

    def on_module_activated(self) -> None:
        self.render()

    def render(self) -> None:
        if self.canvas is None:
            return
        render_arithmetic(self)

    def _update_lesson_link(self, skill: str) -> None:
        settings = load_ui_settings()
        url = KHAN_URL_BY_SKILL.get(skill, "")
        if settings.enforce_offline_mode:
            self.lesson_btn.state(["disabled"])
            self.lesson_var.set("External links are unavailable while offline mode is enforced.")
            return
        if not settings.show_external_links:
            self.lesson_btn.state(["disabled"])
            self.lesson_var.set("External links are disabled in Parent settings.")
            return
        if not url:
            self.lesson_btn.state(["disabled"])
            self.lesson_var.set("No lesson link mapped for this skill yet.")
            return
        self.lesson_btn.state(["!disabled"])
        self.lesson_var.set("Opens a mapped Khan Academy lesson/unit in your browser (requires internet).")

    def _open_lesson(self) -> None:
        settings = load_ui_settings()
        if settings.enforce_offline_mode or not settings.show_external_links:
            self._update_lesson_link(self.skill_var.get())
            return
        skill = self.skill_var.get()
        url = KHAN_URL_BY_SKILL.get(skill, "")
        if not url:
            return
        if not _can_reach_khan():
            self.lesson_var.set("Could not reach khanacademy.org. Check internet and try again.")
            return
        webbrowser.open(url)


def _can_reach_khan(timeout: float = 1.2) -> bool:
    try:
        with socket.create_connection(("www.khanacademy.org", 443), timeout=timeout):
            return True
    except OSError:
        return False
