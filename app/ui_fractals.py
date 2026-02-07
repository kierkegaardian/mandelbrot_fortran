from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .explanations import FRACTAL_EXPLANATIONS
from .fractal_renderer import FractalConfig, render_ppm, save_high_res
from .ui_explain import ExplanationPanel
from .ui_tooltip import ToolTip


class FractalPanel:
    def __init__(self, controls_parent: tk.Widget, view_parent: tk.Widget) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)
        self._ready = False

        self.center_x = -0.5
        self.center_y = 0.0
        self.zoom = 1.0
        self.max_iter = 100
        self.fractal_type = tk.StringVar(value="mandelbrot")
        self.palette = "rgb"
        self.smooth = tk.BooleanVar(value=True)
        self.cyclic = tk.BooleanVar(value=False)
        self.freq = 0.1
        self.power = 2.0
        self.julia_cx = -0.8
        self.julia_cy = 0.156
        self._dragging = False
        self._last_drag_x = 0
        self._last_drag_y = 0
        self._preview_after_id: str | None = None
        self._final_after_id: str | None = None
        self._image_item_id: int | None = None

        self._build_controls()
        self._build_view()
        self._ready = True

    def _build_controls(self) -> None:
        frame = ttk.Frame(self.controls_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Fractal Type").pack(anchor=tk.W)
        types = ["mandelbrot", "julia", "ship", "tricorn", "multibrot", "celtic", "perpendicular"]
        cb = ttk.Combobox(frame, textvariable=self.fractal_type, values=types, state="readonly")
        cb.pack(fill=tk.X, pady=(0, 10))
        cb.bind("<<ComboboxSelected>>", lambda _e: self._on_type_change())

        self.iter_scale = ttk.Scale(frame, from_=50, to=1000, command=self._on_slider)
        self.iter_scale.set(100)
        ttk.Label(frame, text="Iterations (Detail)").pack(anchor=tk.W)
        self.iter_scale.pack(fill=tk.X, pady=(0, 10))

        self.freq_scale = ttk.Scale(frame, from_=0.01, to=2.0, command=self._on_slider)
        self.freq_scale.set(0.1)
        ttk.Label(frame, text="Color Frequency").pack(anchor=tk.W)
        self.freq_scale.pack(fill=tk.X, pady=(0, 10))

        self.power_scale = ttk.Scale(frame, from_=2.0, to=10.0, command=self._on_slider)
        self.power_scale.set(2.0)
        ttk.Label(frame, text="Multibrot Power").pack(anchor=tk.W)
        self.power_scale.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(frame, text="Smooth Coloring", variable=self.smooth, command=self.render).pack(anchor=tk.W)
        ttk.Checkbutton(frame, text="Cyclic (Psychedelic)", variable=self.cyclic, command=self.render).pack(anchor=tk.W)

        zoom_tip = ttk.Label(frame, text="Zoom help (?)")
        zoom_tip.pack(anchor=tk.W, pady=(6, 2))
        ToolTip(zoom_tip, "Scroll up to zoom in, scroll down to zoom out. Drag to pan the view.")

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, pady=10)
        ttk.Button(btns, text="Reset View", command=self.reset_view).pack(side=tk.LEFT, expand=True)
        ttk.Button(btns, text="Save Image", command=self.save_image).pack(side=tk.LEFT, expand=True)

        self.explain = ExplanationPanel(frame)
        self._set_explanation()
        self.explain.frame.pack(fill=tk.X, pady=(12, 0))

    def _build_view(self) -> None:
        self.canvas = tk.Canvas(self.view_frame, bg="#111", cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", self._on_wheel)
        self.canvas.bind("<Button-5>", self._on_wheel)

    def _on_type_change(self) -> None:
        self._set_explanation()
        self.render(scale=1.0)

    def _set_explanation(self) -> None:
        explanation = FRACTAL_EXPLANATIONS.get(self.fractal_type.get(), next(iter(FRACTAL_EXPLANATIONS.values())))
        self.explain.set_explanation(explanation)

    def _current_config(self, width: int, height: int) -> FractalConfig:
        return FractalConfig(
            width=width,
            height=height,
            max_iter=int(self.max_iter),
            center_x=self.center_x,
            center_y=self.center_y,
            zoom=self.zoom,
            fractal_type=self.fractal_type.get(),
            palette=self.palette,
            freq=self.freq,
            power=self.power,
            julia_cx=self.julia_cx,
            julia_cy=self.julia_cy,
            smooth=self.smooth.get(),
            cyclic=self.cyclic.get(),
        )

    def render(self, scale: float = 1.0) -> None:
        if not self._ready:
            return
        self.max_iter = int(self.iter_scale.get())
        self.freq = float(self.freq_scale.get())
        self.power = float(self.power_scale.get())

        w = max(10, int(self.canvas.winfo_width() * scale))
        h = max(10, int(self.canvas.winfo_height() * scale))
        try:
            data = render_ppm(self._current_config(w, h))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Render failed", str(exc))
            return

        try:
            img = tk.PhotoImage(data=data)
            if scale < 1.0:
                factor = int(1.0 / scale)
                img = img.zoom(factor)
            self._img = img
            if self._image_item_id is None:
                self._image_item_id = self.canvas.create_image(0, 0, image=self._img, anchor=tk.NW)
            else:
                self.canvas.itemconfigure(self._image_item_id, image=self._img)
                self.canvas.coords(self._image_item_id, 0, 0)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Display failed", str(exc))

    def reset_view(self) -> None:
        self.center_x = -0.5
        self.center_y = 0.0
        self.zoom = 1.0
        self.render(scale=1.0)

    def save_image(self) -> None:
        config = self._current_config(1920, 1080)
        try:
            save_high_res(config, "saved_fractal.ppm")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Save failed", str(exc))
            return
        messagebox.showinfo("Saved", "High-res image saved to saved_fractal.ppm")

    def _on_slider(self, _val: str) -> None:
        if not self._ready:
            return
        self.render(scale=0.2)

    def _on_click(self, event: tk.Event) -> None:
        self._dragging = True
        self._last_drag_x = event.x
        self._last_drag_y = event.y

    def _on_drag(self, _event: tk.Event) -> None:
        if not self._dragging:
            return
        event = _event
        dx = event.x - self._last_drag_x
        dy = event.y - self._last_drag_y
        if dx == 0 and dy == 0:
            return
        if not self._shift_center(dx, dy):
            return
        self._last_drag_x = event.x
        self._last_drag_y = event.y
        self._queue_preview(scale=0.35)
        self._queue_final(delay_ms=160)

    def _on_release(self, event: tk.Event) -> None:
        if not self._dragging:
            return
        self._dragging = False
        self._cancel_render_queue()
        self.render(scale=1.0)

    def _on_wheel(self, event: tk.Event) -> None:
        factor = self._zoom_factor(event)
        if factor == 1.0:
            return
        if not self._zoom_at(event.x, event.y, factor):
            return
        self._queue_preview(scale=0.35)
        self._queue_final(delay_ms=180)

    def _zoom_factor(self, event: tk.Event) -> float:
        if getattr(event, "num", None) in (4, 5):
            return 1.15 if event.num == 4 else 1 / 1.15
        delta = getattr(event, "delta", 0)
        if delta == 0:
            return 1.0
        step = abs(delta) / 120.0
        base = 1.12
        factor = base**step
        return factor if delta > 0 else 1 / factor

    def _zoom_at(self, x: int, y: int, factor: float) -> bool:
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1 or factor <= 0:
            return False
        aspect = h / w
        x_range = 3.0 / self.zoom
        y_range = x_range * aspect
        world_x = self.center_x + (x - w / 2) * (x_range / w)
        world_y = self.center_y - (y - h / 2) * (y_range / h)
        self.zoom *= factor
        new_x_range = 3.0 / self.zoom
        new_y_range = new_x_range * aspect
        self.center_x = world_x - (x - w / 2) * (new_x_range / w)
        self.center_y = world_y + (y - h / 2) * (new_y_range / h)
        return True

    def _shift_center(self, dx: float, dy: float) -> bool:
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return False
        aspect = h / w
        x_range = 3.0 / self.zoom
        y_range = x_range * aspect
        self.center_x += -dx * (x_range / w)
        self.center_y += dy * (y_range / h)
        return True

    def _queue_preview(self, scale: float) -> None:
        if self._preview_after_id is not None:
            self.canvas.after_cancel(self._preview_after_id)
        self._preview_after_id = self.canvas.after(25, lambda: self._run_preview(scale))

    def _run_preview(self, scale: float) -> None:
        self._preview_after_id = None
        self.render(scale=scale)

    def _queue_final(self, delay_ms: int) -> None:
        if self._final_after_id is not None:
            self.canvas.after_cancel(self._final_after_id)
        self._final_after_id = self.canvas.after(delay_ms, self._run_final)

    def _run_final(self) -> None:
        self._final_after_id = None
        self.render(scale=1.0)

    def _cancel_render_queue(self) -> None:
        if self._preview_after_id is not None:
            self.canvas.after_cancel(self._preview_after_id)
            self._preview_after_id = None
        if self._final_after_id is not None:
            self.canvas.after_cancel(self._final_after_id)
            self._final_after_id = None
