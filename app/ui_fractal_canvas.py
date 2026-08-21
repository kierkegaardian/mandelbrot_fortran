"""Fractal canvas — display, zoom, pan, HUD, and progressive rendering."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
import os
from collections.abc import Callable
from threading import Event
import tkinter as tk
from tkinter import messagebox

from .fractal_renderer import FractalConfig, RenderCancelled, render_ppm
from .theme import COLORS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Tier scale factors (fraction of canvas native resolution).
_TIER1_SCALE: float = 0.15   # ~instant preview
_TIER2_SCALE: float = 0.40   # fast intermediate
_TIER3_SCALE: float = 1.0    # pixel-perfect final

# Debounce / scheduling
_TIER2_DELAY_MS: int = 60
_TIER3_DELAY_MS: int = 300
_POLL_INTERVAL_MS: int = 16   # ~60 fps poll

# HUD styling
_HUD_FONT: tuple[str, int] = ("Courier", 10)
_HUD_FG: str = "#c8d8e8"
_HUD_BG: str = "#10141bcc"
_HUD_PAD: int = 8

# Loading indicator
_PULSE_RADIUS: int = 5
_PULSE_OFFSET: int = 14


class FractalCanvas:
    """Canvas widget with progressive rendering, crossfade, and HUD overlay."""

    def __init__(self, parent: tk.Widget) -> None:
        self.canvas = tk.Canvas(parent, bg=COLORS["fractal_bg"], cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Navigation state
        self.center_x: float = -0.5
        self.center_y: float = 0.0
        self.zoom: float = 1.0

        # Drag state
        self._dragging: bool = False
        self._last_drag_x: int = 0
        self._last_drag_y: int = 0
        self._drag_offset_x: int = 0
        self._drag_offset_y: int = 0

        # Image layers (bottom=old full-res, top=new render)
        self._bg_img: tk.PhotoImage | None = None
        self._fg_img: tk.PhotoImage | None = None
        self._bg_item: int | None = None
        self._fg_item: int | None = None

        # HUD items
        self._hud_bg_item: int | None = None
        self._hud_text_item: int | None = None

        # Loading indicator
        self._loading_item: int | None = None
        self._pulse_after_id: str | None = None
        self._pulse_growing: bool = True

        # Render pipeline
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="fractal-render"
        )
        self._render_future: Future[bytes] | None = None
        self._active_cancel_event: Event | None = None
        self._pending_render: tuple[int, FractalConfig, float] | None = None
        self._latest_request_id: int = 0
        self._active_request_id: int = 0
        self._poll_after_id: str | None = None

        # Tier scheduling after-ids
        self._tier2_after_id: str | None = None
        self._tier3_after_id: str | None = None

        self._threads: int = max(1, os.cpu_count() or 1)

        # Bindings
        self.canvas.bind("<ButtonPress-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", self._on_wheel)
        self.canvas.bind("<Button-5>", self._on_wheel)

    # ------------------------------------------------------------------
    # Public API — called by FractalPanel / controls
    # ------------------------------------------------------------------

    def render_progressive(
        self,
        max_iter: int,
        freq: float,
        power: float,
        fractal_type: str,
        palette: str,
        smooth: bool,
        cyclic: bool,
        julia_cx: float,
        julia_cy: float,
        *,
        interaction_mode: bool = False,
    ) -> None:
        """Kick off a three-tier progressive render.

        If *interaction_mode* is True, iterations are temporarily halved
        for tiers 1-2 to increase responsiveness.
        """
        self._cancel_scheduled_tiers()
        preview_iter = max(20, max_iter // 2) if interaction_mode else max_iter

        # Tier 1 — instant tiny preview
        cfg1 = self._make_config(_TIER1_SCALE, preview_iter, freq, power,
                                 fractal_type, palette, smooth, cyclic,
                                 julia_cx, julia_cy)
        self._enqueue_render(cfg1, _TIER1_SCALE)

        # Tier 2 — schedule medium after short delay
        cfg2 = self._make_config(_TIER2_SCALE, preview_iter, freq, power,
                                 fractal_type, palette, smooth, cyclic,
                                 julia_cx, julia_cy)
        self._tier2_after_id = self.canvas.after(
            _TIER2_DELAY_MS,
            lambda: self._enqueue_render(cfg2, _TIER2_SCALE),
        )

        # Tier 3 — schedule full-res after idle delay
        cfg3 = self._make_config(_TIER3_SCALE, max_iter, freq, power,
                                 fractal_type, palette, smooth, cyclic,
                                 julia_cx, julia_cy)
        self._tier3_after_id = self.canvas.after(
            _TIER3_DELAY_MS,
            lambda: self._enqueue_render(cfg3, _TIER3_SCALE),
        )

    def render_full(
        self,
        max_iter: int,
        freq: float,
        power: float,
        fractal_type: str,
        palette: str,
        smooth: bool,
        cyclic: bool,
        julia_cx: float,
        julia_cy: float,
    ) -> None:
        """Single full-resolution render (used for final pass after drag)."""
        self._cancel_scheduled_tiers()
        cfg = self._make_config(_TIER3_SCALE, max_iter, freq, power,
                                fractal_type, palette, smooth, cyclic,
                                julia_cx, julia_cy)
        self._enqueue_render(cfg, _TIER3_SCALE)

    def reset_view(self) -> None:
        self.center_x = -0.5
        self.center_y = 0.0
        self.zoom = 1.0

    def cancel_all(self) -> None:
        """Cancel every pending / in-flight render."""
        self._cancel_scheduled_tiers()
        if self._active_cancel_event is not None:
            self._active_cancel_event.set()

    # ------------------------------------------------------------------
    # Callbacks for external wiring (set by FractalPanel)
    # ------------------------------------------------------------------

    _on_nav_change: Callable[[], None] | None = None

    def set_nav_callback(self, cb: Callable[[], None]) -> None:
        self._on_nav_change = cb

    def _notify_nav(self) -> None:
        if self._on_nav_change is not None:
            self._on_nav_change()

    # ------------------------------------------------------------------
    # Config builder
    # ------------------------------------------------------------------

    def _make_config(
        self,
        scale: float,
        max_iter: int,
        freq: float,
        power: float,
        fractal_type: str,
        palette: str,
        smooth: bool,
        cyclic: bool,
        julia_cx: float,
        julia_cy: float,
    ) -> FractalConfig:
        w = max(10, int(self.canvas.winfo_width() * scale))
        h = max(10, int(self.canvas.winfo_height() * scale))
        return FractalConfig(
            width=w,
            height=h,
            max_iter=int(max_iter),
            center_x=self.center_x,
            center_y=self.center_y,
            zoom=self.zoom,
            fractal_type=fractal_type,
            palette=palette,
            freq=freq,
            power=power,
            julia_cx=julia_cx,
            julia_cy=julia_cy,
            smooth=smooth,
            cyclic=cyclic,
            threads=self._threads,
        )

    # ------------------------------------------------------------------
    # Render queue (cancel-and-replace)
    # ------------------------------------------------------------------

    def _enqueue_render(self, config: FractalConfig, scale: float) -> None:
        self._latest_request_id += 1
        rid = self._latest_request_id
        if self._render_future is not None and not self._render_future.done():
            self._pending_render = (rid, config, scale)
            if self._active_cancel_event is not None:
                self._active_cancel_event.set()
            return
        self._start_render(rid, config, scale)

    def _start_render(
        self, request_id: int, config: FractalConfig, scale: float
    ) -> None:
        self._active_request_id = request_id
        cancel_event = Event()
        self._active_cancel_event = cancel_event
        self._render_future = self._executor.submit(
            render_ppm, config, cancel_event
        )
        self._show_loading(True)
        self._poll_after_id = self.canvas.after(
            _POLL_INTERVAL_MS,
            lambda: self._poll_render_done(request_id, scale),
        )

    def _poll_render_done(self, request_id: int, scale: float) -> None:
        self._poll_after_id = None
        future = self._render_future
        if future is None:
            return
        if not future.done():
            self._poll_after_id = self.canvas.after(
                _POLL_INTERVAL_MS,
                lambda: self._poll_render_done(request_id, scale),
            )
            return
        self._handle_render_done(request_id, scale, future)

    def _handle_render_done(
        self, request_id: int, scale: float, future: Future[bytes]
    ) -> None:
        self._render_future = None
        self._active_cancel_event = None
        if request_id != self._active_request_id:
            self._start_pending()
            return
        try:
            data = future.result()
        except RenderCancelled:
            self._start_pending()
            return
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Render failed", str(exc))
            self._start_pending()
            return
        self._display_image(data, scale)
        self._start_pending()

    def _start_pending(self) -> None:
        pending = self._pending_render
        self._pending_render = None
        if pending is None:
            self._show_loading(False)
            return
        rid, config, scale = pending
        self._start_render(rid, config, scale)

    # ------------------------------------------------------------------
    # Image display — crossfade + anti-blur
    # ------------------------------------------------------------------

    def _display_image(self, data: bytes, scale: float) -> None:
        try:
            img = tk.PhotoImage(data=data)
            # For sub-1.0 renders, scale up using integer zoom.
            # Integer zoom stays crisp (nearest-neighbour); avoids blur.
            if scale < 1.0 and scale > 0:
                factor = max(1, round(1.0 / scale))
                img = img.zoom(factor)

            # Crossfade: promote current fg → bg, then set new fg.
            if self._fg_img is not None:
                self._bg_img = self._fg_img
                if self._bg_item is not None:
                    self.canvas.itemconfigure(self._bg_item, image=self._bg_img)
                    self.canvas.coords(self._bg_item, 0, 0)
                else:
                    self._bg_item = self.canvas.create_image(
                        0, 0, image=self._bg_img, anchor=tk.NW
                    )

            self._fg_img = img
            if self._fg_item is None:
                self._fg_item = self.canvas.create_image(
                    0, 0, image=self._fg_img, anchor=tk.NW
                )
            else:
                self.canvas.itemconfigure(self._fg_item, image=self._fg_img)
                self.canvas.coords(self._fg_item, 0, 0)

            # Make sure HUD stays on top.
            self._raise_hud()

        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Display failed", str(exc))

    # ------------------------------------------------------------------
    # HUD overlay
    # ------------------------------------------------------------------

    def update_hud(self, max_iter: int) -> None:
        """Redraw the coordinate / zoom HUD."""
        cw = self.canvas.winfo_width()
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

        # Size the background rectangle to fit text.
        bbox = self.canvas.bbox(self._hud_text_item)
        if bbox and self._hud_bg_item is not None:
            x1, y1, x2, y2 = bbox
            self.canvas.coords(
                self._hud_bg_item,
                x1 - 4, y1 - 2, min(x2 + 4, cw), y2 + 2,
            )
        self._raise_hud()

    def _raise_hud(self) -> None:
        if self._hud_bg_item is not None:
            self.canvas.tag_raise(self._hud_bg_item)
        if self._hud_text_item is not None:
            self.canvas.tag_raise(self._hud_text_item)
        if self._loading_item is not None:
            self.canvas.tag_raise(self._loading_item)

    # ------------------------------------------------------------------
    # Loading indicator
    # ------------------------------------------------------------------

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
        else:
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
        r = _PULSE_RADIUS
        if self._pulse_growing:
            r += 2
            self._pulse_growing = False
        else:
            self._pulse_growing = True
        self.canvas.coords(
            self._loading_item,
            _PULSE_OFFSET - r, _PULSE_OFFSET - r,
            _PULSE_OFFSET + r, _PULSE_OFFSET + r,
        )
        self._pulse_after_id = self.canvas.after(400, self._animate_pulse)

    # ------------------------------------------------------------------
    # Mouse navigation
    # ------------------------------------------------------------------

    def _on_click(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        self._dragging = True
        self._last_drag_x = event.x
        self._last_drag_y = event.y
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self.cancel_all()

    def _on_drag(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if not self._dragging:
            return
        dx = event.x - self._last_drag_x
        dy = event.y - self._last_drag_y
        if dx == 0 and dy == 0:
            return
        if not self._shift_center(dx, dy):
            return
        self._last_drag_x = event.x
        self._last_drag_y = event.y
        self._drag_offset_x += dx
        self._drag_offset_y += dy
        # Move both image layers to follow the cursor.
        if self._fg_item is not None:
            self.canvas.move(self._fg_item, dx, dy)
        if self._bg_item is not None:
            self.canvas.move(self._bg_item, dx, dy)

    def _on_release(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        if not self._dragging:
            return
        self._dragging = False
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        # Snap images back to origin; the full render will draw in the right place.
        if self._fg_item is not None:
            self.canvas.coords(self._fg_item, 0, 0)
        if self._bg_item is not None:
            self.canvas.coords(self._bg_item, 0, 0)
        self._notify_nav()

    def _on_wheel(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        factor = self._zoom_factor(event)
        if factor == 1.0:
            return
        if not self._zoom_at(event.x, event.y, factor):
            return
        self._notify_nav()

    # ------------------------------------------------------------------
    # Zoom / pan math
    # ------------------------------------------------------------------

    def _zoom_factor(self, event: tk.Event) -> float:  # type: ignore[type-arg]
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

    # ------------------------------------------------------------------
    # Tier scheduling helpers
    # ------------------------------------------------------------------

    def _cancel_scheduled_tiers(self) -> None:
        for attr in ("_poll_after_id", "_tier2_after_id", "_tier3_after_id"):
            aid = getattr(self, attr, None)
            if aid is not None:
                try:
                    self.canvas.after_cancel(aid)
                except tk.TclError:
                    pass
                setattr(self, attr, None)
        if self._pulse_after_id is not None:
            try:
                self.canvas.after_cancel(self._pulse_after_id)
            except tk.TclError:
                pass
            self._pulse_after_id = None
        if self._active_cancel_event is not None:
            self._active_cancel_event.set()

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    def shutdown(self) -> None:
        self.cancel_all()
        self._executor.shutdown(wait=False, cancel_futures=True)
