"""Progressive render scheduling for the fractal canvas."""

from __future__ import annotations

from concurrent.futures import Future
from threading import Event
import tkinter as tk
from tkinter import messagebox

from .fractal_renderer import FractalConfig, RenderCancelled, render_ppm

_TIER1_SCALE: float = 0.15
_TIER2_SCALE: float = 0.40
_TIER3_SCALE: float = 1.0
_TIER2_DELAY_MS: int = 60
_TIER3_DELAY_MS: int = 300
_POLL_INTERVAL_MS: int = 16


class FractalRenderQueueMixin:
    """Cancel-and-replace render queue shared by ``FractalCanvas``."""

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
        self._cancel_scheduled_tiers()
        preview_iter = max(20, max_iter // 2) if interaction_mode else max_iter
        common = (
            freq, power, fractal_type, palette, smooth, cyclic, julia_cx, julia_cy
        )
        cfg1 = self._make_config(_TIER1_SCALE, preview_iter, *common)
        self._enqueue_render(cfg1, _TIER1_SCALE)
        cfg2 = self._make_config(_TIER2_SCALE, preview_iter, *common)
        self._tier2_after_id = self.canvas.after(
            _TIER2_DELAY_MS,
            lambda: self._enqueue_render(cfg2, _TIER2_SCALE),
        )
        cfg3 = self._make_config(_TIER3_SCALE, max_iter, *common)
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
        self._cancel_scheduled_tiers()
        config = self._make_config(
            _TIER3_SCALE,
            max_iter,
            freq,
            power,
            fractal_type,
            palette,
            smooth,
            cyclic,
            julia_cx,
            julia_cy,
        )
        self._enqueue_render(config, _TIER3_SCALE)

    def cancel_all(self) -> None:
        self._cancel_scheduled_tiers()
        if self._active_cancel_event is not None:
            self._active_cancel_event.set()

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
        return FractalConfig(
            width=max(10, int(self.canvas.winfo_width() * scale)),
            height=max(10, int(self.canvas.winfo_height() * scale)),
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

    def _enqueue_render(self, config: FractalConfig, scale: float) -> None:
        self._latest_request_id += 1
        request_id = self._latest_request_id
        if self._render_future is not None and not self._render_future.done():
            self._pending_render = (request_id, config, scale)
            if self._active_cancel_event is not None:
                self._active_cancel_event.set()
            return
        self._start_render(request_id, config, scale)

    def _start_render(
        self, request_id: int, config: FractalConfig, scale: float
    ) -> None:
        self._active_request_id = request_id
        cancel_event = Event()
        self._active_cancel_event = cancel_event
        self._render_future = self._executor.submit(render_ppm, config, cancel_event)
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
        request_id, config, scale = pending
        self._start_render(request_id, config, scale)

    def _cancel_scheduled_tiers(self) -> None:
        for attr in ("_poll_after_id", "_tier2_after_id", "_tier3_after_id"):
            after_id = getattr(self, attr, None)
            if after_id is not None:
                try:
                    self.canvas.after_cancel(after_id)
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
