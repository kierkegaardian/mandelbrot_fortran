from __future__ import annotations

import tkinter as tk


class ToolTip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self._tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event=None) -> None:
        if self._tip is not None:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self._tip = tk.Toplevel(self.widget)
        self._tip.overrideredirect(True)
        self._tip.geometry(f"+{x}+{y}")
        label = tk.Label(
            self._tip,
            text=self.text,
            justify=tk.LEFT,
            background="#f7f7f7",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Helvetica", 9),
        )
        label.pack(ipadx=6, ipady=4)

    def _hide(self, _event=None) -> None:
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None
