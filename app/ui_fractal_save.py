"""Asynchronous high-resolution export for the fractal panel."""

from __future__ import annotations

from threading import Event
from tkinter import messagebox

from .fractal_renderer import FractalConfig, RenderCancelled, save_high_res


class FractalSaveMixin:
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
        self._save_poll_after_id = self.fcanvas.canvas.after(
            40, self._poll_save_done
        )

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
        messagebox.showinfo("Saved", "High-res image saved to saved_fractal.ppm")
