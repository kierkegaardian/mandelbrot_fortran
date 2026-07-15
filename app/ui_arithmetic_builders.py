"""Skill-specific arithmetic control builders."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .ui_widgets import int_spinbox


class ArithmeticBuildersMixin:
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
