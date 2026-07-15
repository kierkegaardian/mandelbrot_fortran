"""Mouse and keyboard navigation math for the fractal canvas."""

from __future__ import annotations

import tkinter as tk


class FractalNavigationMixin:
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
        if (dx == 0 and dy == 0) or not self._shift_center(dx, dy):
            return
        self._last_drag_x = event.x
        self._last_drag_y = event.y
        self._drag_offset_x += dx
        self._drag_offset_y += dy
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
        if self._fg_item is not None:
            self.canvas.coords(self._fg_item, 0, 0)
        if self._bg_item is not None:
            self.canvas.coords(self._bg_item, 0, 0)
        self._notify_nav()

    def _on_wheel(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        factor = self._zoom_factor(event)
        if factor != 1.0 and self._zoom_at(event.x, event.y, factor):
            self._notify_nav()

    def _zoom_factor(self, event: tk.Event) -> float:  # type: ignore[type-arg]
        if getattr(event, "num", None) in (4, 5):
            return 1.15 if event.num == 4 else 1 / 1.15
        delta = getattr(event, "delta", 0)
        if delta == 0:
            return 1.0
        factor = 1.12 ** (abs(delta) / 120.0)
        return factor if delta > 0 else 1 / factor

    def _zoom_at(self, x: int, y: int, factor: float) -> bool:
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width <= 1 or height <= 1 or factor <= 0:
            return False
        aspect = height / width
        x_range = 3.0 / self.zoom
        y_range = x_range * aspect
        world_x = self.center_x + (x - width / 2) * (x_range / width)
        world_y = self.center_y - (y - height / 2) * (y_range / height)
        self.zoom *= factor
        new_x_range = 3.0 / self.zoom
        new_y_range = new_x_range * aspect
        self.center_x = world_x - (x - width / 2) * (new_x_range / width)
        self.center_y = world_y + (y - height / 2) * (new_y_range / height)
        return True

    def _shift_center(self, dx: float, dy: float) -> bool:
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width <= 1 or height <= 1:
            return False
        aspect = height / width
        x_range = 3.0 / self.zoom
        y_range = x_range * aspect
        self.center_x += -dx * (x_range / width)
        self.center_y += dy * (y_range / height)
        return True
