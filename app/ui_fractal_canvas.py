"""Fractal canvas display composed with render-queue and navigation mixins."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
import os
from threading import Event
import tkinter as tk
from tkinter import messagebox

from .fractal_renderer import FractalConfig
from .theme import COLORS
from .ui_fractal_navigation import FractalNavigationMixin
from .ui_fractal_render_queue import FractalRenderQueueMixin

_HUD_FONT: tuple[str, int] = ("Courier", 10)
_HUD_FG: str = "#c8d8e8"
_HUD_PAD: int = 8
_PULSE_RADIUS: int = 5
_PULSE_OFFSET: int = 14


class FractalCanvas(FractalRenderQueueMixin, FractalNavigationMixin):
    """Canvas widget with progressive rendering, navigation, and a HUD."""

    def __init__(self, parent: tk.Widget) -> None:
        self.canvas = tk.Canvas(parent, bg=COLORS["fractal_bg"], cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.center_x: float = -0.5
        self.center_y: float = 0.0
        self.zoom: float = 1.0
        self._dragging: bool = False
        self._last_drag_x: int = 0
        self._last_drag_y: int = 0
        self._drag_offset_x: int = 0
        self._drag_offset_y: int = 0

        self._bg_img: tk.PhotoImage | None = None
        self._fg_img: tk.PhotoImage | None = None
        self._bg_item: int | None = None
        self._fg_item: int | None = None
        self._hud_bg_item: int | None = None
        self._hud_text_item: int | None = None
        self._loading_item: int | None = None
        self._pulse_after_id: str | None = None
        self._pulse_growing: bool = True

        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="fractal-render"
        )
        self._render_future: Future[bytes] | None = None
        self._active_cancel_event: Event | None = None
        self._pending_render: tuple[int, FractalConfig, float] | None = None
        self._latest_request_id: int = 0
        self._active_request_id: int = 0
        self._poll_after_id: str | None = None
        self._tier2_after_id: str | None = None
        self._tier3_after_id: str | None = None
        self._threads: int = max(1, os.cpu_count() or 1)
        self._on_nav_change: Callable[[], None] | None = None

        self.canvas.bind("<ButtonPress-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", self._on_wheel)
        self.canvas.bind("<Button-5>", self._on_wheel)

    def reset_view(self) -> None:
        self.center_x = -0.5
        self.center_y = 0.0
        self.zoom = 1.0

    def set_nav_callback(self, callback: Callable[[], None]) -> None:
        self._on_nav_change = callback

    def _notify_nav(self) -> None:
        if self._on_nav_change is not None:
            self._on_nav_change()

    def _display_image(self, data: bytes, scale: float) -> None:
        try:
            image = tk.PhotoImage(data=data)
            if 0 < scale < 1.0:
                image = image.zoom(max(1, round(1.0 / scale)))
            if self._fg_img is not None:
                self._bg_img = self._fg_img
                if self._bg_item is None:
                    self._bg_item = self.canvas.create_image(
                        0, 0, image=self._bg_img, anchor=tk.NW
                    )
                else:
                    self.canvas.itemconfigure(self._bg_item, image=self._bg_img)
                    self.canvas.coords(self._bg_item, 0, 0)
            self._fg_img = image
            if self._fg_item is None:
                self._fg_item = self.canvas.create_image(
                    0, 0, image=self._fg_img, anchor=tk.NW
                )
            else:
                self.canvas.itemconfigure(self._fg_item, image=self._fg_img)
                self.canvas.coords(self._fg_item, 0, 0)
            self._raise_hud()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Display failed", str(exc))

    def update_hud(self, max_iter: int) -> None:
        width = self.canvas.winfo_width()
        text = (
            f"center ({self.center_x:+.10g}, {self.center_y:+.10g})  "
            f"zoom {self.zoom:.4g}×  iter {max_iter}"
        )
        if self._hud_text_item is None:
            self._hud_bg_item = self.canvas.create_rectangle(
                0, 0, 1, 1, fill="#10141b", stipple="gray50", outline=""
            )
            self._hud_text_item = self.canvas.create_text(
                _HUD_PAD,
                _HUD_PAD,
                text=text,
                anchor=tk.NW,
                fill=_HUD_FG,
                font=_HUD_FONT,
            )
        else:
            self.canvas.itemconfigure(self._hud_text_item, text=text)
        bbox = self.canvas.bbox(self._hud_text_item)
        if bbox and self._hud_bg_item is not None:
            x1, y1, x2, y2 = bbox
            self.canvas.coords(
                self._hud_bg_item,
                x1 - 4,
                y1 - 2,
                min(x2 + 4, width),
                y2 + 2,
            )
        self._raise_hud()

    def _raise_hud(self) -> None:
        for item in (self._hud_bg_item, self._hud_text_item, self._loading_item):
            if item is not None:
                self.canvas.tag_raise(item)

    def _show_loading(self, show: bool) -> None:
        if show:
            if self._loading_item is None:
                self._loading_item = self.canvas.create_oval(
                    _PULSE_OFFSET - _PULSE_RADIUS,
                    _PULSE_OFFSET - _PULSE_RADIUS,
                    _PULSE_OFFSET + _PULSE_RADIUS,
                    _PULSE_OFFSET + _PULSE_RADIUS,
                    fill="#5b8def",
                    outline="",
                )
            if self._pulse_after_id is None:
                self._animate_pulse()
            return
        if self._loading_item is not None:
            self.canvas.delete(self._loading_item)
            self._loading_item = None
        if self._pulse_after_id is not None:
            self.canvas.after_cancel(self._pulse_after_id)
            self._pulse_after_id = None

    def _animate_pulse(self) -> None:
        if self._loading_item is None:
            self._pulse_after_id = None
            return
        radius = _PULSE_RADIUS + (2 if self._pulse_growing else 0)
        self._pulse_growing = not self._pulse_growing
        self.canvas.coords(
            self._loading_item,
            _PULSE_OFFSET - radius,
            _PULSE_OFFSET - radius,
            _PULSE_OFFSET + radius,
            _PULSE_OFFSET + radius,
        )
        self._pulse_after_id = self.canvas.after(400, self._animate_pulse)

    def shutdown(self) -> None:
        self.cancel_all()
        self._executor.shutdown(wait=False, cancel_futures=True)
