"""Parent profile, settings, and PIN controls."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from . import db
from .time_utils import now_iso
from .ui_settings import (
    load_ui_settings,
    save_enforce_offline_mode,
    save_show_external_links,
)


class ParentProfilesMixin:
    def _build_profiles_tab(self) -> None:
        self.profile_list = tk.Listbox(self.profile_tab, height=6)
        self.profile_list.pack(fill=tk.X, padx=10, pady=6)
        ttk.Button(self.profile_tab, text="Refresh", command=self._refresh_profiles).pack(pady=(0, 8))

        form = ttk.Frame(self.profile_tab)
        form.pack(fill=tk.X, padx=10)
        ttk.Label(form, text="Name").grid(row=0, column=0, sticky=tk.W)
        self.profile_name = ttk.Entry(form)
        self.profile_name.grid(row=0, column=1, sticky=tk.EW, pady=4)

        ttk.Label(form, text="Role").grid(row=1, column=0, sticky=tk.W)
        self.profile_role = tk.StringVar(value="child")
        ttk.Radiobutton(form, text="Child", variable=self.profile_role, value="child").grid(row=1, column=1, sticky=tk.W)
        ttk.Radiobutton(form, text="Parent", variable=self.profile_role, value="parent").grid(row=2, column=1, sticky=tk.W)

        form.columnconfigure(1, weight=1)
        ttk.Button(self.profile_tab, text="Add Profile", command=self._add_profile).pack(pady=6)
        ttk.Button(self.profile_tab, text="Delete Selected", command=self._delete_profile).pack(pady=2)
        settings = load_ui_settings()
        self.show_links_var = tk.BooleanVar(value=settings.show_external_links)
        ttk.Checkbutton(
            self.profile_tab,
            text="Show external learning links (internet)",
            variable=self.show_links_var,
            command=self._toggle_external_links,
        ).pack(anchor=tk.W, padx=10, pady=(8, 4))

        self.offline_var = tk.BooleanVar(value=settings.enforce_offline_mode)
        ttk.Checkbutton(
            self.profile_tab,
            text="Enforce offline mode",
            variable=self.offline_var,
            command=self._toggle_offline_mode,
        ).pack(anchor=tk.W, padx=10, pady=(0, 8))

        pin_frame = ttk.LabelFrame(self.profile_tab, text="Parent PIN", padding=8)
        pin_frame.pack(fill=tk.X, padx=10, pady=(4, 8))
        self.parent_pin_var = tk.StringVar()
        self.parent_pin_entry = ttk.Entry(
            pin_frame, textvariable=self.parent_pin_var, show="*"
        )
        self.parent_pin_entry.pack(fill=tk.X)
        actions = ttk.Frame(pin_frame)
        actions.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(actions, text="Set PIN", command=self._set_parent_pin).pack(
            side=tk.LEFT
        )
        self.parent_pin_status = tk.StringVar(value="Parent PIN not configured")
        ttk.Label(pin_frame, textvariable=self.parent_pin_status).pack(
            anchor=tk.W, pady=(6, 0)
        )

    def _refresh_profiles(self) -> None:
        self._profiles = db.list_profiles()
        self.profile_list.delete(0, tk.END)
        for profile in self._profiles:
            self.profile_list.insert(tk.END, f"{profile.name} ({profile.role})")
        self._refresh_profiles_for_grades()
        self._refresh_profiles_for_assignments()
        if db.parent_pin_configured():
            locked, locked_until = db.parent_pin_locked(now_iso())
            if locked:
                self.parent_pin_status.set(f"Locked until {locked_until}")
            else:
                self.parent_pin_status.set("Parent PIN configured")
        else:
            self.parent_pin_status.set("Parent PIN not configured")

    def _toggle_external_links(self) -> None:
        save_show_external_links(self.show_links_var.get())

    def _toggle_offline_mode(self) -> None:
        save_enforce_offline_mode(self.offline_var.get())

    def _set_parent_pin(self) -> None:
        profile = self._profile_getter()
        if profile is None or profile.role != "parent":
            messagebox.showerror("Parent profile required", "Select a parent profile first.")
            return
        try:
            db.set_parent_pin(profile.id, self.parent_pin_var.get(), now_iso())
        except ValueError as exc:
            messagebox.showerror("Could not set PIN", str(exc))
            return
        self.parent_pin_var.set("")
        self.parent_pin_status.set("Parent PIN configured")

    def _add_profile(self) -> None:
        name = self.profile_name.get().strip()
        role = self.profile_role.get().strip()
        if not name:
            messagebox.showerror("Missing name", "Please enter a name.")
            return
        db.create_profile(name, role, now_iso())
        self.profile_name.delete(0, tk.END)
        self._refresh_profiles()
    def _delete_profile(self) -> None:
        selection = self.profile_list.curselection()
        if not selection:
            messagebox.showerror("Select a profile", "Choose a profile to delete.")
            return
        profile = self._profiles[selection[0]]
        if db.parent_pin_owner_id() == profile.id:
            messagebox.showerror(
                "PIN owner cannot be deleted",
                "Set the parent PIN from another parent profile before deleting this profile.",
            )
            return
        if not messagebox.askyesno("Confirm delete", f"Delete profile '{profile.name}' and its grades?"):
            return
        db.delete_profile(profile.id)
        self._refresh_profiles()
