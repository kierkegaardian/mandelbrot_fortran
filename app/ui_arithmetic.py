from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .arithmetic_render import render_arithmetic
from .arithmetic_draw import cell_positions
from .explanations import ARITHMETIC_MODE_EXPLANATIONS
from .openmoji_assets import openmoji_paths
from .ui_explain import ExplanationPanel
from .ui_widgets import int_spinbox


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
            values=[
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
            ],
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
