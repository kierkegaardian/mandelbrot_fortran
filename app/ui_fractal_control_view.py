"""Widget construction for the fractal controls panel."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .ui_explain import ExplanationPanel
from .ui_tooltip import ToolTip


class FractalControlViewMixin:
    def _build_controls(self) -> None:
        frame = ttk.Frame(self.controls_frame, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Fractal Type").pack(anchor=tk.W)
        type_picker = ttk.Combobox(
            frame,
            textvariable=self.fractal_type,
            values=(
                "mandelbrot",
                "julia",
                "ship",
                "tricorn",
                "multibrot",
                "celtic",
                "perpendicular",
            ),
            state="readonly",
        )
        type_picker.pack(fill=tk.X, pady=(0, 10))
        type_picker.bind("<<ComboboxSelected>>", lambda _e: self._on_type_change())

        ttk.Label(frame, text="Palette").pack(anchor=tk.W)
        palette_picker = ttk.Combobox(
            frame,
            textvariable=self.palette_var,
            values=("rgb", "gray", "sunset", "ice", "fire", "ocean", "neon"),
            state="readonly",
        )
        palette_picker.pack(fill=tk.X, pady=(0, 10))
        palette_picker.bind(
            "<<ComboboxSelected>>", lambda _e: self._on_palette_change()
        )

        ttk.Label(frame, text="Iterations (Detail)").pack(anchor=tk.W)
        self.iter_scale = ttk.Scale(frame, from_=50, to=1000, command=self._on_slider)
        self.iter_scale.set(100)
        self.iter_scale.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame, text="Color Frequency").pack(anchor=tk.W)
        self.freq_scale = ttk.Scale(
            frame, from_=0.01, to=2.0, command=self._on_slider
        )
        self.freq_scale.set(0.1)
        self.freq_scale.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame, text="Multibrot Power").pack(anchor=tk.W)
        self.power_scale = ttk.Scale(
            frame, from_=2.0, to=10.0, command=self._on_slider
        )
        self.power_scale.set(2.0)
        self.power_scale.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            frame, text="Smooth Coloring", variable=self.smooth, command=self.render
        ).pack(anchor=tk.W)
        ttk.Checkbutton(
            frame, text="Cyclic (Psychedelic)", variable=self.cyclic, command=self.render
        ).pack(anchor=tk.W)

        self._build_julia_controls(frame)
        self.zoom_label = ttk.Label(frame, text="Zoom: 1.0×", font=("Helvetica", 9))
        self.zoom_label.pack(anchor=tk.W, pady=(8, 0))
        zoom_tip = ttk.Label(frame, text="Zoom help (?)")
        zoom_tip.pack(anchor=tk.W, pady=(2, 2))
        ToolTip(
            zoom_tip,
            "Scroll to zoom • Drag to pan • Arrow keys pan "
            "• +/- zoom • Home resets",
        )

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X, pady=10)
        ttk.Button(buttons, text="Reset View", command=self.reset_view).pack(
            side=tk.LEFT, expand=True
        )
        self.save_btn = ttk.Button(buttons, text="Save Image", command=self.save_image)
        self.save_btn.pack(side=tk.LEFT, expand=True)

        self.explain = ExplanationPanel(frame)
        self._set_explanation()
        self.explain.frame.pack(fill=tk.X, pady=(12, 0))
        self._sync_julia_controls()

    def _build_julia_controls(self, frame: ttk.Frame) -> None:
        self.julia_frame = ttk.LabelFrame(frame, text="Julia Parameters", padding=8)
        ttk.Label(self.julia_frame, text="Real (cx)").grid(row=0, column=0, sticky=tk.W)
        self.julia_cx_scale = ttk.Scale(
            self.julia_frame,
            from_=-2.0,
            to=2.0,
            variable=self.julia_cx_var,
            command=self._on_julia_slider,
        )
        self.julia_cx_scale.grid(row=0, column=1, sticky=tk.EW, padx=(6, 6))
        ttk.Label(self.julia_frame, textvariable=self.julia_cx_display, width=8).grid(
            row=0, column=2, sticky=tk.E
        )

        ttk.Label(self.julia_frame, text="Imag (cy)").grid(
            row=1, column=0, sticky=tk.W, pady=(6, 0)
        )
        self.julia_cy_scale = ttk.Scale(
            self.julia_frame,
            from_=-2.0,
            to=2.0,
            variable=self.julia_cy_var,
            command=self._on_julia_slider,
        )
        self.julia_cy_scale.grid(
            row=1, column=1, sticky=tk.EW, padx=(6, 6), pady=(6, 0)
        )
        ttk.Label(self.julia_frame, textvariable=self.julia_cy_display, width=8).grid(
            row=1, column=2, sticky=tk.E, pady=(6, 0)
        )
        self.julia_frame.columnconfigure(1, weight=1)

    def _bind_keyboard(self) -> None:
        canvas = self.fcanvas.canvas
        canvas.configure(takefocus=True)
        canvas.bind("<Left>", lambda _e: self._key_pan(-30, 0))
        canvas.bind("<Right>", lambda _e: self._key_pan(30, 0))
        canvas.bind("<Up>", lambda _e: self._key_pan(0, -30))
        canvas.bind("<Down>", lambda _e: self._key_pan(0, 30))
        canvas.bind("<plus>", lambda _e: self._key_zoom(1.25))
        canvas.bind("<equal>", lambda _e: self._key_zoom(1.25))
        canvas.bind("<minus>", lambda _e: self._key_zoom(1 / 1.25))
        canvas.bind("<Home>", lambda _e: self.reset_view())
        canvas.bind("<ButtonPress-1>", lambda _e: canvas.focus_set(), add="+")
