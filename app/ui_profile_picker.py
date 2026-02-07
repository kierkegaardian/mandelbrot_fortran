from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from . import db
from .models import Profile
from .time_utils import now_iso


class ProfilePicker:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.selected: Optional[Profile] = None
        self.win = tk.Toplevel(root)
        self.win.title("Choose Profile")
        self.win.geometry("420x420")
        self.win.grab_set()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        self._profiles: list[Profile] = []
        self._build()
        self.refresh_profiles()

    def _build(self) -> None:
        ttk.Label(self.win, text="Who is using the app?", font=("Helvetica", 14, "bold")).pack(pady=(12, 6))

        self.listbox = tk.Listbox(self.win, height=8)
        self.listbox.pack(fill=tk.X, padx=16)

        ttk.Button(self.win, text="Select Profile", command=self._select).pack(pady=(8, 12))

        ttk.Separator(self.win).pack(fill=tk.X, padx=16, pady=8)
        ttk.Label(self.win, text="Add a new profile", font=("Helvetica", 12, "bold")).pack(pady=(8, 4))

        form = ttk.Frame(self.win)
        form.pack(fill=tk.X, padx=16)

        ttk.Label(form, text="Name").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.name_entry = ttk.Entry(form)
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, pady=4)

        ttk.Label(form, text="Role").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.role_var = tk.StringVar(value="child")
        ttk.Radiobutton(form, text="Child", variable=self.role_var, value="child").grid(row=1, column=1, sticky=tk.W)
        ttk.Radiobutton(form, text="Parent", variable=self.role_var, value="parent").grid(row=2, column=1, sticky=tk.W)

        form.columnconfigure(1, weight=1)

        ttk.Button(self.win, text="Create Profile", command=self._create).pack(pady=8)

    def refresh_profiles(self) -> None:
        self._profiles = db.list_profiles()
        self.listbox.delete(0, tk.END)
        for profile in self._profiles:
            label = f"{profile.name} ({profile.role})"
            self.listbox.insert(tk.END, label)

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

    def _select(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showerror("Pick a profile", "Please choose a profile from the list.")
            return
        idx = selection[0]
        self.selected = self._profiles[idx]
        self.win.destroy()

    def _on_close(self) -> None:
        self.selected = None
        self.win.destroy()


def pick_profile(root: tk.Tk) -> Optional[Profile]:
    picker = ProfilePicker(root)
    root.wait_window(picker.win)
    return picker.selected
