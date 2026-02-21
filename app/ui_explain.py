from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk

from .explanations import Explanation
from .ui_settings import load_ui_settings, save_detail_geometry


class ExplanationPanel:
    def __init__(self, parent: tk.Widget) -> None:
        self.frame = ttk.Frame(parent)
        self._how_short = tk.StringVar(value="")
        self._why_short = tk.StringVar(value="")
        self._how_long = ""
        self._why_long = ""
        self._mental_model = ""
        self._common_mistake = ""
        self._try_this = ""
        self._history = ""
        self._show_more = tk.BooleanVar(value=False)
        self._detail_window: tk.Toplevel | None = None
        self._detail_box: tk.Text | None = None
        self._detail_geometry: str | None = None
        self._build()

    def _build(self) -> None:
        ttk.Label(self.frame, text="How to use", font=("Helvetica", 11, "bold")).pack(anchor=tk.W)
        ttk.Label(self.frame, textvariable=self._how_short, wraplength=260).pack(anchor=tk.W, pady=(0, 8))

        ttk.Label(self.frame, text="Why it works", font=("Helvetica", 11, "bold")).pack(anchor=tk.W)
        ttk.Label(self.frame, textvariable=self._why_short, wraplength=260).pack(anchor=tk.W, pady=(0, 8))

        toggle_row = ttk.Frame(self.frame)
        toggle_row.pack(anchor=tk.W, pady=(4, 4))
        ttk.Checkbutton(
            toggle_row,
            text="Tell me more",
            variable=self._show_more,
            command=self._toggle,
        ).pack(side=tk.LEFT)
        ttk.Button(toggle_row, text="Open in window", command=self._open_detail_window).pack(side=tk.LEFT, padx=(8, 0))

        self._more_frame = ttk.Frame(self.frame)
        self._more_box = tk.Text(self._more_frame, height=14, wrap=tk.WORD, font=("Helvetica", 10))
        self._more_scroll = ttk.Scrollbar(self._more_frame, orient=tk.VERTICAL, command=self._more_box.yview)
        self._more_box.configure(yscrollcommand=self._more_scroll.set)
        self._configure_readonly_text(self._more_box)
        self._more_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._more_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._more_frame.pack(fill=tk.BOTH, expand=True)
        self._more_frame.pack_forget()

    def set_explanation(self, explanation: Explanation) -> None:
        self._how_short.set(explanation.how_short)
        self._why_short.set(explanation.why_short)
        self._how_long = explanation.how_long
        self._why_long = explanation.why_long
        self._mental_model = explanation.mental_model
        self._common_mistake = explanation.common_mistake
        self._try_this = explanation.try_this
        self._history = explanation.history
        if self._show_more.get():
            self._update_more()
        self._update_detail_window()

    def _toggle(self) -> None:
        if self._show_more.get():
            self._update_more()
            self._more_frame.pack(fill=tk.X, expand=False, pady=(4, 0))
            self._open_detail_window()
        else:
            self._more_frame.pack_forget()
            self._close_detail_window()

    def _update_more(self) -> None:
        self._fill_text(self._more_box)
        self._more_box.yview_moveto(0.0)

    def _fill_text(self, target: tk.Text) -> None:
        target.delete("1.0", tk.END)
        self._insert_section(target, "How to use", self._how_long)
        self._insert_section(target, "Why it works", self._why_long)
        if self._mental_model:
            self._insert_section(target, "Mental model", self._mental_model)
        if self._common_mistake:
            self._insert_section(target, "Common mistake", self._common_mistake)
        if self._try_this:
            self._insert_section(target, "Try this", self._try_this)
        if self._history:
            self._insert_section(target, "History", self._history)

    def _insert_section(self, target: tk.Text, title: str, body: str) -> None:
        if target.index("end-1c") != "1.0":
            target.insert(tk.END, "\n\n")
        target.insert(tk.END, f"{title}\n", "heading")
        target.insert(tk.END, body)

    def _open_detail_window(self) -> None:
        if self._detail_window is not None and self._detail_window.winfo_exists():
            self._detail_window.lift()
            self._detail_window.focus_set()
            return
        self._detail_window = tk.Toplevel(self.frame)
        self._detail_window.title("Tell me more")
        settings = load_ui_settings()
        geometry = None
        if settings.detail_geometry and self._geometry_is_reasonable(settings.detail_geometry):
            geometry = self._coerce_geometry_to_screen(settings.detail_geometry)
        if geometry:
            try:
                self._detail_window.geometry(geometry)
                self._detail_geometry = geometry
            except tk.TclError:
                geometry = None
        if geometry is None:
            self._detail_window.geometry("720x520")
        self._detail_window.minsize(420, 300)
        self._detail_window.protocol("WM_DELETE_WINDOW", self._close_detail_window)
        self._detail_window.bind("<Configure>", self._on_detail_configure)
        self._detail_window.bind("<Destroy>", self._on_detail_destroy)

        outer = ttk.Frame(self._detail_window, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)

        self._detail_box = tk.Text(outer, wrap=tk.WORD, font=("Helvetica", 10))
        detail_scroll = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=self._detail_box.yview)
        self._detail_box.configure(yscrollcommand=detail_scroll.set)
        self._configure_readonly_text(self._detail_box)
        self._detail_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._update_detail_window()

    def _close_detail_window(self) -> None:
        if self._detail_window is None:
            return
        self._persist_detail_geometry()
        window = self._detail_window
        self._detail_window = None
        self._detail_box = None
        self._more_frame.pack_forget()
        self._show_more.set(False)
        window.destroy()

    def _on_detail_configure(self, event: tk.Event) -> None:
        if self._detail_window is None or not self._detail_window.winfo_exists():
            return
        if event.widget is not self._detail_window:
            return
        self._detail_geometry = self._detail_window.geometry()

    def _on_detail_destroy(self, event: tk.Event) -> None:
        if self._detail_window is None or event.widget is not self._detail_window:
            return
        self._persist_detail_geometry()
        self._detail_window = None
        self._detail_box = None
        self._more_frame.pack_forget()
        self._show_more.set(False)

    def _persist_detail_geometry(self) -> None:
        geometry = self._detail_geometry
        if geometry is None and self._detail_window is not None and self._detail_window.winfo_exists():
            try:
                geometry = self._detail_window.geometry()
            except tk.TclError:
                geometry = None
        if geometry and self._geometry_is_reasonable(geometry):
            save_detail_geometry(geometry)

    def _geometry_is_reasonable(self, geometry: str) -> bool:
        match = re.match(r"^(\d+)x(\d+)", geometry)
        if not match:
            return False
        width = int(match.group(1))
        height = int(match.group(2))
        return width >= 200 and height >= 200

    def _coerce_geometry_to_screen(self, geometry: str) -> str | None:
        if self._detail_window is None:
            return None
        match = re.match(r"^(\d+)x(\d+)([+-]\d+)?([+-]\d+)?$", geometry)
        if not match:
            return None
        width = int(match.group(1))
        height = int(match.group(2))
        screen_w = self._detail_window.winfo_screenwidth()
        screen_h = self._detail_window.winfo_screenheight()
        max_w = max(240, screen_w - 40)
        max_h = max(240, screen_h - 80)
        width = min(width, max_w)
        height = min(height, max_h)
        if width < 200 or height < 200:
            return None
        offset_x = match.group(3)
        offset_y = match.group(4)
        if offset_x is None or offset_y is None:
            return f"{width}x{height}"
        x = int(offset_x)
        y = int(offset_y)
        x = max(0, min(x, screen_w - width))
        y = max(0, min(y, screen_h - height))
        return f"{width}x{height}+{x}+{y}"

    def _update_detail_window(self) -> None:
        if self._detail_window is None or self._detail_box is None:
            return
        self._fill_text(self._detail_box)
        self._detail_box.yview_moveto(0.0)

    def _configure_readonly_text(self, widget: tk.Text) -> None:
        widget.tag_configure("heading", font=("Helvetica", 10, "bold"))
        widget.bind("<KeyPress>", self._block_edit)
        widget.bind("<<Paste>>", self._block_event)
        widget.bind("<<Cut>>", self._block_event)
        widget.bind("<<Undo>>", self._block_event)
        widget.bind("<<Redo>>", self._block_event)
        widget.bind("<<PasteSelection>>", self._block_event)

    def _block_event(self, _event: tk.Event) -> str:
        return "break"

    def _block_edit(self, event: tk.Event) -> str | None:
        if event.keysym.startswith(("Shift", "Control", "Alt", "Meta", "Command", "Super")):
            return None
        nav_keys = {
            "Up",
            "Down",
            "Left",
            "Right",
            "Home",
            "End",
            "Prior",
            "Next",
            "KP_Up",
            "KP_Down",
            "KP_Left",
            "KP_Right",
            "KP_Home",
            "KP_End",
            "KP_Prior",
            "KP_Next",
        }
        if event.keysym in nav_keys:
            return None
        if event.state & 0x4 or event.state & 0x8 or event.state & 0x10:
            if event.keysym.lower() in {"c", "a", "insert"}:
                return None
        return "break"
