"""Track selection and OpenMoji interactions for arithmetic practice."""

from __future__ import annotations

import tkinter as tk

from .arithmetic_draw import cell_positions
from .explanations import ARITHMETIC_MODE_EXPLANATIONS
from .openmoji_assets import openmoji_paths
from .skill_graph import ARITHMETIC_SKILLS, SKILL_LABELS, skills_in_track


class ArithmeticInteractionsMixin:
    def _show_frame(self, frame: tk.Widget) -> None:
        for child in self.stack.winfo_children():
            child.pack_forget()
        frame.pack(fill=tk.X, pady=(0, 8))

    def _apply_track_filter(self) -> None:
        track = self.track_var.get()
        skills = list(skills_in_track(track))
        skills = [skill for skill in skills if skill in ARITHMETIC_SKILLS]
        if not skills:
            skills = list(ARITHMETIC_SKILLS)
        if self.skill_var.get() not in skills:
            self.skill_var.set(skills[0])
        self._skill_combo.config(values=skills)

    def _on_track_change(self) -> None:
        self._apply_track_filter()
        self._on_skill_change()

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
            "calculus_1": self.slope_frame,
            "calculus_slope": self.slope_frame,
        }
        self._show_frame(frames[skill])
        track = self.track_var.get()
        if track == "All":
            self.practice_var.set(f"You are practicing: {SKILL_LABELS.get(skill, skill)}")
        else:
            self.practice_var.set(f"You are practicing: {SKILL_LABELS.get(skill, skill)} ({track})")
        self.explain.set_explanation(ARITHMETIC_MODE_EXPLANATIONS[skill])
        self._update_lesson_link(skill)
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
