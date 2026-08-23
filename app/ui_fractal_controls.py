"""Fractal controls panel — sliders, dropdowns, save, and keyboard shortcuts."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event
import tkinter as tk
from tkinter import messagebox, ttk

from .explanations import FRACTAL_EXPLANATIONS
from .fractal_renderer import FractalConfig, RenderCancelled, save_high_res
from .theme import COLORS
from .ui_explain import ExplanationPanel
from .ui_fractal_canvas import FractalCanvas
from .ui_tooltip import ToolTip

# Slider debounce (ms). Prevents render storms while dragging sliders.
_SLIDER_DEBOUNCE_MS: int = 200


class FractalPanel:
    """Reassembled fractal viewer: controls on the left, canvas on the right."""

    def __init__(
        self, controls_parent: tk.Widget, view_parent: tk.Widget
    ) -> None:
        self.controls_frame = ttk.Frame(controls_parent)
        self.view_frame = ttk.Frame(view_parent)
        self._ready: bool = False

        # Shared render parameters
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

        # Slider debounce
        self._slider_after_id: str | None = None

        # Canvas (owns nav state + rendering)
        self.fcanvas = FractalCanvas(self.view_frame)
        self.fcanvas.set_nav_callback(self._on_canvas_nav)

        # Save executor
        self._save_executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="fractal-save"
        )
        self._save_future: Future[None] | None = None
        self._save_cancel_event: Event | None = None
        self._save_poll_after_id: str | None = None

        self._build_controls()
        self._bind_keyboard()
        self._ready = True

    # ------------------------------------------------------------------
    # Expose canvas on .canvas for backward compat (ui_root reads it)
    # ------------------------------------------------------------------

    @property
    def canvas(self) -> tk.Canvas:
        return self.fcanvas.canvas

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def _build_controls(self) -> None:
        frame = ttk.Frame(self.controls_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Fractal Type").pack(anchor=tk.W)
        types = [
            "mandelbrot", "julia", "ship", "tricorn",
            "multibrot", "celtic", "perpendicular",
        ]
        cb = ttk.Combobox(
            frame, textvariable=self.fractal_type,
            values=types, state="readonly",
        )
        cb.pack(fill=tk.X, pady=(0, 10))
        cb.bind("<<ComboboxSelected>>", lambda _e: self._on_type_change())

        ttk.Label(frame, text="Palette").pack(anchor=tk.W)
        palette_cb = ttk.Combobox(
            frame,
            textvariable=self.palette_var,
            values=["rgb", "gray", "sunset", "ice", "fire", "ocean", "neon"],
            state="readonly",
        )
        palette_cb.pack(fill=tk.X, pady=(0, 10))
        palette_cb.bind(
            "<<ComboboxSelected>>", lambda _e: self._on_palette_change()
        )

        self.iter_scale = ttk.Scale(
            frame, from_=50, to=1000, command=self._on_slider
        )
        self.iter_scale.set(100)
        ttk.Label(frame, text="Iterations (Detail)").pack(anchor=tk.W)
        self.iter_scale.pack(fill=tk.X, pady=(0, 10))

        self.freq_scale = ttk.Scale(
            frame, from_=0.01, to=2.0, command=self._on_slider
        )
        self.freq_scale.set(0.1)
        ttk.Label(frame, text="Color Frequency").pack(anchor=tk.W)
        self.freq_scale.pack(fill=tk.X, pady=(0, 10))

        self.power_scale = ttk.Scale(
            frame, from_=2.0, to=10.0, command=self._on_slider
        )
        self.power_scale.set(2.0)
        ttk.Label(frame, text="Multibrot Power").pack(anchor=tk.W)
        self.power_scale.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            frame, text="Smooth Coloring",
            variable=self.smooth, command=self.render,
        ).pack(anchor=tk.W)
        ttk.Checkbutton(
            frame, text="Cyclic (Psychedelic)",
            variable=self.cyclic, command=self.render,
        ).pack(anchor=tk.W)

        # Julia parameters
        self.julia_frame = ttk.LabelFrame(
            frame, text="Julia Parameters", padding=8
        )
        ttk.Label(self.julia_frame, text="Real (cx)").grid(
            row=0, column=0, sticky=tk.W
        )
        self.julia_cx_scale = ttk.Scale(
            self.julia_frame, from_=-2.0, to=2.0,
            variable=self.julia_cx_var, command=self._on_julia_slider,
        )
        self.julia_cx_scale.grid(
            row=0, column=1, sticky=tk.EW, padx=(6, 6)
        )
        ttk.Label(
            self.julia_frame, textvariable=self.julia_cx_display, width=8
        ).grid(row=0, column=2, sticky=tk.E)

        ttk.Label(self.julia_frame, text="Imag (cy)").grid(
            row=1, column=0, sticky=tk.W, pady=(6, 0)
        )
        self.julia_cy_scale = ttk.Scale(
            self.julia_frame, from_=-2.0, to=2.0,
            variable=self.julia_cy_var, command=self._on_julia_slider,
        )
        self.julia_cy_scale.grid(
            row=1, column=1, sticky=tk.EW, padx=(6, 6), pady=(6, 0)
        )
        ttk.Label(
            self.julia_frame, textvariable=self.julia_cy_display, width=8
        ).grid(row=1, column=2, sticky=tk.E, pady=(6, 0))
        self.julia_frame.columnconfigure(1, weight=1)

        # Zoom label
        self.zoom_label = ttk.Label(
            frame, text="Zoom: 1.0×", font=("Helvetica", 9),
        )
        self.zoom_label.pack(anchor=tk.W, pady=(8, 0))

        zoom_tip = ttk.Label(frame, text="Zoom help (?)")
        zoom_tip.pack(anchor=tk.W, pady=(2, 2))
        ToolTip(
            zoom_tip,
            "Scroll to zoom • Drag to pan • Arrow keys pan "
            "• +/- zoom • Home resets",
        )

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, pady=10)
        ttk.Button(
            btns, text="Reset View", command=self.reset_view
        ).pack(side=tk.LEFT, expand=True)
        self.save_btn = ttk.Button(
            btns, text="Save Image", command=self.save_image
        )
        self.save_btn.pack(side=tk.LEFT, expand=True)

        self.explain = ExplanationPanel(frame)
        self._set_explanation()
        self.explain.frame.pack(fill=tk.X, pady=(12, 0))
        self._sync_julia_controls()

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def _bind_keyboard(self) -> None:
        c = self.fcanvas.canvas
        # Make canvas focusable for key events.
        c.configure(takefocus=True)
        c.bind("<Left>", lambda _e: self._key_pan(-30, 0))
        c.bind("<Right>", lambda _e: self._key_pan(30, 0))
        c.bind("<Up>", lambda _e: self._key_pan(0, -30))
        c.bind("<Down>", lambda _e: self._key_pan(0, 30))
        c.bind("<plus>", lambda _e: self._key_zoom(1.25))
        c.bind("<equal>", lambda _e: self._key_zoom(1.25))
        c.bind("<minus>", lambda _e: self._key_zoom(1 / 1.25))
        c.bind("<Home>", lambda _e: self.reset_view())
        # Focus canvas on click so key bindings work.
        c.bind("<ButtonPress-1>", lambda e: c.focus_set(), add="+")

    def _key_pan(self, dx: int, dy: int) -> None:
        self.fcanvas._shift_center(dx, dy)
        self.render(interaction=True)

    def _key_zoom(self, factor: float) -> None:
        w = self.fcanvas.canvas.winfo_width()
        h = self.fcanvas.canvas.winfo_height()
        self.fcanvas._zoom_at(w // 2, h // 2, factor)
        self.render(interaction=True)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_type_change(self) -> None:
        self._set_explanation()
        self._sync_julia_controls()
        self.render()

    def _on_palette_change(self) -> None:
        self.render()

    def _on_julia_slider(self, _val: str) -> None:
        self.julia_cx_display.set(f"{self.julia_cx_var.get():.3f}")
        self.julia_cy_display.set(f"{self.julia_cy_var.get():.3f}")
        if self.fractal_type.get() == "julia":
            self.render(interaction=True)

    def _on_slider(self, _val: str) -> None:
        if not self._ready:
            return
        # Debounce: cancel any pending slider render, schedule a new one.
        if self._slider_after_id is not None:
            self.controls_frame.after_cancel(self._slider_after_id)
        self._slider_after_id = self.controls_frame.after(
            _SLIDER_DEBOUNCE_MS, lambda: self._fire_slider_render()
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
        """Called by the canvas after a zoom or drag-release."""
        self.render(interaction=True)

    # ------------------------------------------------------------------
    # Render dispatch
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Zoom label
    # ------------------------------------------------------------------

    def _update_zoom_label(self) -> None:
        z = self.fcanvas.zoom
        if z >= 1000:
            txt = f"Zoom: {z:,.0f}×"
        elif z >= 1:
            txt = f"Zoom: {z:.1f}×"
        else:
            txt = f"Zoom: {z:.4f}×"
        self.zoom_label.configure(text=txt)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset_view(self) -> None:
        self.fcanvas.reset_view()
        self._update_zoom_label()
        self.render()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save_image(self) -> None:
        if self._save_future is not None and not self._save_future.done():
            messagebox.showinfo(
                "Save in progress",
                "Please wait for the current save to finish.",
            )
            return
        config = FractalConfig(
            width=1920,
            height=1080,
            max_iter=int(self.max_iter),
            center_x=self.fcanvas.center_x,
            center_y=self.fcanvas.center_y,
            zoom=self.fcanvas.zoom,
            fractal_type=self.fractal_type.get(),
            palette=self.palette_var.get(),
            freq=self.freq,
            power=self.power,
            julia_cx=float(self.julia_cx_var.get()),
            julia_cy=float(self.julia_cy_var.get()),
            smooth=self.smooth.get(),
            cyclic=self.cyclic.get(),
            threads=self.fcanvas._threads,
        )
        self.save_btn.state(["disabled"])
        cancel_event = Event()
        self._save_cancel_event = cancel_event
        self._save_future = self._save_executor.submit(
            save_high_res, config, "saved_fractal.ppm", cancel_event
        )
        self._schedule_save_poll()

    def _schedule_save_poll(self) -> None:
        self._save_poll_after_id = self.fcanvas.canvas.after(40, self._poll_save_done)

    def _poll_save_done(self) -> None:
        self._save_poll_after_id = None
        future = self._save_future
        if future is None:
            self.save_btn.state(["!disabled"])
            return
        if not future.done():
            self._schedule_save_poll()
            return
        self._save_future = None
        self._save_cancel_event = None
        self.save_btn.state(["!disabled"])
        try:
            future.result()
        except RenderCancelled:
            return
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Save failed", str(exc))
            return
        messagebox.showinfo(
            "Saved", "High-res image saved to saved_fractal.ppm"
        )

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

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
