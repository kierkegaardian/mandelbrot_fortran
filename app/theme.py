from __future__ import annotations

import tkinter as tk
from tkinter import ttk

COLORS: dict[str, str] = {
    "app_bg": "#f2f5f9",
    "panel_bg": "#ffffff",
    "panel_alt_bg": "#f8fbfd",
    "canvas_bg": "#f4f7fb",
    "fractal_bg": "#10141b",
    "accent": "#3f78a6",
    "accent_strong": "#23527a",
    "text_primary": "#243341",
    "text_secondary": "#4f6b7a",
    "text_muted": "#6b7d88",
    "success": "#2f6f3e",
    "warning": "#8d6720",
    "danger": "#a13b3b",
    "assignment": "#7a4f2e",
    "border_soft": "#d3dbe2",
    "tab_bg": "#e8eef5",
    "tab_selected": "#ffffff",
    "hud_fg": "#c8d8e8",
    "hud_bg": "#10141b",
    "loading_dot": "#5b8def",
}

MASTERY_COLORS: dict[str, str] = {
    "Not started": "#dfe3e8",
    "Needs work": "#f3d4d4",
    "Developing": "#f2e3b6",
    "Proficient": "#c7e3f2",
    "Mastered": "#cbe8d1",
}

SKILL_ACCENTS: dict[str, str] = {
    "counting": "#5b8def",
    "add_subtract": "#67b26f",
    "multiply": "#4b89da",
    "divide": "#63ad77",
    "ratios": "#f2b05e",
    "fractions": "#5b8def",
    "integers": "#5f84c2",
    "order_of_operations": "#4f6b7a",
    "geometry_shapes": "#7b8f3f",
    "data_displays": "#6d7fc0",
    "algebra_linear": "#3f78a6",
    "geometry_area": "#6a8aa8",
    "trig_right_triangle": "#5f7ea5",
    "stats_percent": "#4f7b9d",
    "stats_mean": "#4f7b9d",
    "stats_probability": "#4f7b9d",
}

FONTS: dict[str, tuple[str, int] | tuple[str, int, str]] = {
    "heading": ("Segoe UI", 14, "bold"),
    "subheading": ("Segoe UI", 12, "bold"),
    "body": ("Segoe UI", 11),
    "body_bold": ("Segoe UI", 11, "bold"),
    "small": ("Segoe UI", 10),
    "mono": ("Consolas", 11),
}


def apply_theme(root: tk.Tk) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        # Keep default theme if clam is unavailable.
        pass

    root.configure(bg=COLORS["app_bg"])

    style.configure("TFrame", background=COLORS["app_bg"])
    style.configure("Card.TFrame", background=COLORS["panel_bg"])
    style.configure(
        "TLabel",
        background=COLORS["app_bg"],
        foreground=COLORS["text_primary"],
        font=FONTS["body"],
    )
    style.configure(
        "Heading.TLabel",
        background=COLORS["app_bg"],
        foreground=COLORS["text_primary"],
        font=FONTS["heading"],
    )
    style.configure(
        "Subtle.TLabel",
        background=COLORS["app_bg"],
        foreground=COLORS["text_secondary"],
        font=FONTS["small"],
    )
    style.configure(
        "TButton",
        padding=(12, 8),
        background=COLORS["tab_bg"],
        foreground=COLORS["text_primary"],
    )
    style.map(
        "TButton",
        background=[("active", COLORS["panel_alt_bg"])],
    )
    style.configure(
        "Accent.TButton",
        background=COLORS["accent"],
        foreground="#ffffff",
    )
    style.map(
        "Accent.TButton",
        background=[("active", COLORS["accent_strong"])],
        foreground=[("active", "#ffffff")],
    )
    style.configure("TNotebook", background=COLORS["app_bg"], borderwidth=0)
    style.configure("TNotebook.Tab", padding=(14, 8), font=FONTS["body"])
    style.map(
        "TNotebook.Tab",
        background=[("selected", COLORS["tab_selected"]), ("!selected", COLORS["tab_bg"])],
        foreground=[("selected", COLORS["accent_strong"]), ("!selected", COLORS["text_primary"])],
    )
    style.configure(
        "TCombobox",
        fieldbackground=COLORS["panel_bg"],
        background=COLORS["panel_bg"],
    )
    style.configure("TEntry", fieldbackground=COLORS["panel_bg"], background=COLORS["panel_bg"])
    style.configure("TProgressbar", troughcolor="#e7edf4", bordercolor="#e7edf4", lightcolor="#5b8def", darkcolor="#5b8def")
    style.configure(
        "Accent.Horizontal.TProgressbar",
        troughcolor="#e7edf4",
        background=COLORS["accent"],
        lightcolor=COLORS["accent"],
        darkcolor=COLORS["accent"],
    )

    style.configure(
        "NotStarted.Horizontal.TProgressbar",
        troughcolor="#e7edf4",
        background=MASTERY_COLORS["Not started"],
        lightcolor=MASTERY_COLORS["Not started"],
        darkcolor=MASTERY_COLORS["Not started"],
    )
    style.configure(
        "NeedsWork.Horizontal.TProgressbar",
        troughcolor="#f7eaea",
        background=MASTERY_COLORS["Needs work"],
        lightcolor=MASTERY_COLORS["Needs work"],
        darkcolor=MASTERY_COLORS["Needs work"],
    )
    style.configure(
        "Developing.Horizontal.TProgressbar",
        troughcolor="#f7f0df",
        background=MASTERY_COLORS["Developing"],
        lightcolor=MASTERY_COLORS["Developing"],
        darkcolor=MASTERY_COLORS["Developing"],
    )
    style.configure(
        "Proficient.Horizontal.TProgressbar",
        troughcolor="#e6f0f7",
        background=MASTERY_COLORS["Proficient"],
        lightcolor=MASTERY_COLORS["Proficient"],
        darkcolor=MASTERY_COLORS["Proficient"],
    )
    style.configure(
        "Mastered.Horizontal.TProgressbar",
        troughcolor="#e5f1e8",
        background=MASTERY_COLORS["Mastered"],
        lightcolor=MASTERY_COLORS["Mastered"],
        darkcolor=MASTERY_COLORS["Mastered"],
    )


def progress_style_for_mastery(mastery: str) -> str:
    mapping = {
        "Not started": "NotStarted.Horizontal.TProgressbar",
        "Needs work": "NeedsWork.Horizontal.TProgressbar",
        "Developing": "Developing.Horizontal.TProgressbar",
        "Proficient": "Proficient.Horizontal.TProgressbar",
        "Mastered": "Mastered.Horizontal.TProgressbar",
    }
    return mapping.get(mastery, "TProgressbar")
