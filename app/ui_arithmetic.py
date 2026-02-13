from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .arithmetic_render import render_arithmetic
from .arithmetic_draw import cell_positions
from .explanations import ARITHMETIC_MODE_EXPLANATIONS
from .openmoji_assets import openmoji_paths
from .ui_explain import ExplanationPanel
from .ui_widgets import int_spinbox


ARITHMETIC_SKILLS = [
    "counting",
    "add_subtract",
    "multiply",
    "divide",
    "ratios",
    "fractions",
    "long_addition",
    "long_subtraction",
    "long_multiplication",
    "long_division",
    "money",
    "integers",
    "order_of_operations",
    "algebra_linear",
    "geometry_area",
    "trig_right_triangle",
    "stats_percent",
    "stats_mean",
    "stats_probability",
    "calculus_slope",
]


class ArithmeticPanel:
    def __init__(self, controls_parent: tk.Widget, view_parent: tk.Widget) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)

        self.skill_var = tk.StringVar(value="counting")
        self.object_style_var = tk.StringVar(value="Circles")
        self.expression_var = tk.StringVar(value="")
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

        self._build_controls()
        self._build_view()
        self._load_openmoji()
        self.render()

    def _build_controls(self) -> None:
        frame = ttk.Frame(self.controls_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Arithmetic Skill").pack(anchor=tk.W)
        skill_cb = ttk.Combobox(
            frame,
            textvariable=self.skill_var,
            values=ARITHMETIC_SKILLS,
            state="readonly",
        )
        skill_cb.pack(fill=tk.X, pady=(0, 8))
        skill_cb.bind("<<ComboboxSelected>>", lambda _e: self._on_skill_change())

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

    def _build_view(self) -> None:
        ttk.Label(self.view_frame, textvariable=self.expression_var, font=("Helvetica", 13, "bold")).pack(pady=(8, 4))
        self.canvas = tk.Canvas(self.view_frame, bg="#f7f7f7")
        self.canvas.pack(fill=tk.BOTH, expand=True)

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

    def _on_skill_change(self) -> None:
        skill = self.skill_var.get()
        frames = {
            "counting": self.counting_frame,
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
            "integers": self.integer_frame,
            "order_of_operations": self.order_frame,
            "algebra_linear": self.algebra_frame,
            "geometry_area": self.geometry_frame,
            "trig_right_triangle": self.trig_frame,
            "stats_percent": self.percent_frame,
            "stats_mean": self.mean_frame,
            "stats_probability": self.prob_frame,
            "calculus_slope": self.slope_frame,
        }
        self._show_frame(frames[skill])
        self.explain.set_explanation(ARITHMETIC_MODE_EXPLANATIONS[skill])
        self.render()

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
        render_arithmetic(self)
