"""Fractal controls assembled from bounded view and save modules."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event
import tkinter as tk
from tkinter import ttk

from .explanations import FRACTAL_EXPLANATIONS
from .ui_fractal_canvas import FractalCanvas
from .ui_fractal_control_view import FractalControlViewMixin
from .ui_fractal_save import FractalSaveMixin

_SLIDER_DEBOUNCE_MS: int = 200


class FractalPanel(FractalControlViewMixin, FractalSaveMixin):
    """Public fractal panel with the legacy constructor and canvas property."""

    def __init__(self, controls_parent: tk.Widget, view_parent: tk.Widget) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)
        self._ready: bool = False

        self.max_iter: int = 100
        self.fractal_type = tk.StringVar(value="mandelbrot")
        self.palette_var = tk.StringVar(value="rgb")
        self.smooth = tk.BooleanVar(value=True)
        self.cyclic = tk.BooleanVar(value=False)
        self.freq: float = 0.1
        self.power: float = 2.0
        self.julia_cx_var = tk.DoubleVar(value=-0.8)
        self.julia_cy_var = tk.DoubleVar(value=0.156)
        self.julia_cx_display = tk.StringVar(value="-0.800")
        self.julia_cy_display = tk.StringVar(value="0.156")
        self._slider_after_id: str | None = None

        self.fcanvas = FractalCanvas(self.view_frame)
        self.fcanvas.set_nav_callback(self._on_canvas_nav)
        self._save_executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="fractal-save"
        )
        self._save_future: Future[None] | None = None
        self._save_cancel_event: Event | None = None
        self._save_poll_after_id: str | None = None

        self._build_controls()
        self._bind_keyboard()
        self._ready = True

    @property
    def canvas(self) -> tk.Canvas:
        return self.fcanvas.canvas

    def _key_pan(self, dx: int, dy: int) -> None:
        self.fcanvas._shift_center(dx, dy)
        self.render(interaction=True)

    def _key_zoom(self, factor: float) -> None:
        width = self.fcanvas.canvas.winfo_width()
        height = self.fcanvas.canvas.winfo_height()
        self.fcanvas._zoom_at(width // 2, height // 2, factor)
        self.render(interaction=True)

    def _on_type_change(self) -> None:
        self._set_explanation()
        self._sync_julia_controls()
        self.render()

    def _on_palette_change(self) -> None:
        self.render()

    def _on_julia_slider(self, _value: str) -> None:
        self.julia_cx_display.set(f"{self.julia_cx_var.get():.3f}")
        self.julia_cy_display.set(f"{self.julia_cy_var.get():.3f}")
        if self.fractal_type.get() == "julia":
            self.render(interaction=True)

    def _on_slider(self, _value: str) -> None:
        if not self._ready:
            return
        if self._slider_after_id is not None:
            self.controls_frame.after_cancel(self._slider_after_id)
        self._slider_after_id = self.controls_frame.after(
            _SLIDER_DEBOUNCE_MS, self._fire_slider_render
        )

    def _fire_slider_render(self) -> None:
        self._slider_after_id = None
        self.render(interaction=True)

    def _sync_julia_controls(self) -> None:
        if self.fractal_type.get() == "julia":
            self.julia_frame.pack(fill=tk.X, pady=(8, 8))
        else:
            self.julia_frame.pack_forget()

    def _set_explanation(self) -> None:
        explanation = FRACTAL_EXPLANATIONS.get(
            self.fractal_type.get(),
            next(iter(FRACTAL_EXPLANATIONS.values())),
        )
        self.explain.set_explanation(explanation)

    def _on_canvas_nav(self) -> None:
        self.render(interaction=True)

    def _read_sliders(self) -> None:
        self.max_iter = int(self.iter_scale.get())
        self.freq = float(self.freq_scale.get())
        self.power = float(self.power_scale.get())
        self.julia_cx_display.set(f"{self.julia_cx_var.get():.3f}")
        self.julia_cy_display.set(f"{self.julia_cy_var.get():.3f}")

    def render(self, *, interaction: bool = False) -> None:
        if not self._ready:
            return
        self._read_sliders()
        self._update_zoom_label()
        self.fcanvas.render_progressive(
            max_iter=self.max_iter,
            freq=self.freq,
            power=self.power,
            fractal_type=self.fractal_type.get(),
            palette=self.palette_var.get(),
            smooth=self.smooth.get(),
            cyclic=self.cyclic.get(),
            julia_cx=float(self.julia_cx_var.get()),
            julia_cy=float(self.julia_cy_var.get()),
            interaction_mode=interaction,
        )
        self.fcanvas.update_hud(self.max_iter)

    def _update_zoom_label(self) -> None:
        zoom = self.fcanvas.zoom
        if zoom >= 1000:
            text = f"Zoom: {zoom:,.0f}×"
        elif zoom >= 1:
            text = f"Zoom: {zoom:.1f}×"
        else:
            text = f"Zoom: {zoom:.4f}×"
        self.zoom_label.configure(text=text)

    def reset_view(self) -> None:
        self.fcanvas.reset_view()
        self._update_zoom_label()
        self.render()

    def shutdown(self) -> None:
        if self._slider_after_id is not None:
            try:
                self.controls_frame.after_cancel(self._slider_after_id)
            except tk.TclError:
                pass
            self._slider_after_id = None
        if self._save_poll_after_id is not None:
            try:
                self.fcanvas.canvas.after_cancel(self._save_poll_after_id)
            except tk.TclError:
                pass
            self._save_poll_after_id = None
        self.fcanvas.shutdown()
        if self._save_cancel_event is not None:
            self._save_cancel_event.set()
        self._save_executor.shutdown(wait=False, cancel_futures=True)
