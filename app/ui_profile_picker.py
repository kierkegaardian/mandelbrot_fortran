from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from . import db
from .models import Profile
from .time_utils import now_iso


class ProfilePicker:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.selected: Profile | None = None
        self.win = tk.Toplevel(root)
        self.win.title("Choose Profile")
        self.win.geometry("420x420")
        self.win.grab_set()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        self.win.bind("<Escape>", lambda _event: self._on_close())
        self.win.bind("<Alt-c>", lambda _event: self._create())

        self._profiles: list[Profile] = []
        self._build()
        self.refresh_profiles()

    def _build(self) -> None:
        ttk.Label(
            self.win,
            text="Who is using the app?",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(16, 8))
        self.profiles_container = tk.Frame(
            self.win, bg="#f3f4f6", bd=1, relief=tk.RIDGE
        )
        self.profiles_container.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)

        ttk.Separator(self.win).pack(fill=tk.X, padx=24, pady=(12, 12))
        ttk.Label(
            self.win,
            text="Add a new profile",
            font=("Segoe UI", 12, "bold"),
        ).pack(pady=(0, 8))

        form = ttk.Frame(self.win)
        form.pack(fill=tk.X, padx=24, pady=(0, 16))
        ttk.Label(form, text="Name").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.name_entry = ttk.Entry(form, font=("Segoe UI", 11))
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, pady=4, padx=(8, 0))
        self.name_entry.bind("<Return>", lambda _event: self._create())

        ttk.Label(form, text="Role").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.role_var = tk.StringVar(value="child")
        role_frame = ttk.Frame(form)
        role_frame.grid(row=1, column=1, sticky=tk.W, padx=(8, 0))
        ttk.Radiobutton(
            role_frame,
            text="Learner",
            variable=self.role_var,
            value="child",
        ).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Radiobutton(
            role_frame,
            text="Parent",
            variable=self.role_var,
            value="parent",
        ).pack(side=tk.LEFT)
        form.columnconfigure(1, weight=1)

        ttk.Button(
            self.win, text="Create Profile", command=self._create
        ).pack(pady=(0, 16))

    def refresh_profiles(self) -> None:
        self._profiles = db.list_profiles()
        for child in self.profiles_container.winfo_children():
            child.destroy()
        if not self._profiles:
            ttk.Label(
                self.profiles_container,
                text="No profiles yet. Create one below!",
                font=("Segoe UI", 11, "italic"),
                background="#f3f4f6",
            ).pack(pady=20)
            self.name_entry.focus_set()
            return
        for index, profile in enumerate(self._profiles):
            icon = "🧑‍🎓" if profile.role == "child" else "🧑‍🏫"
            button = ttk.Button(
                self.profiles_container,
                text=f"{icon}  {profile.name}",
                style="Accent.TButton" if profile.role == "child" else "TButton",
                command=lambda selected=index: self._select_idx(selected),
            )
            button.pack(fill=tk.X, padx=12, pady=6)
            if index == 0:
                button.focus_set()

    def _create(self) -> None:
        name = self.name_entry.get().strip()
        role = self.role_var.get().strip()
        if not name:
            messagebox.showerror("Missing name", "Please enter a name.")
            return
        try:
            db.create_profile(name, role, now_iso())
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Could not create profile", str(exc))
            return
        self.name_entry.delete(0, tk.END)
        self.refresh_profiles()

    def _select_idx(self, index: int) -> None:
        self.selected = self._profiles[index]
        self.win.destroy()

    def _on_close(self) -> None:
        self.selected = None
        self.win.destroy()


def pick_profile(root: tk.Tk) -> Profile | None:
    picker = ProfilePicker(root)
    root.wait_window(picker.win)
    return picker.selected
