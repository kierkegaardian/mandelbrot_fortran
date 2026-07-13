from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Callable

from . import sync_service, sync_store
from .models import Profile
from .sync_config import load_sync_config
from .sync_state import load_sync_state, save_sync_enabled


FAMILY_SYNC_BETA_TITLE = "Family Sync (Beta)"
FAMILY_SYNC_PRIVACY_COPY = (
    "With sync on, MandelQuest shares family profiles, saved quiz sets and assignments, and each finished "
    "quiz's questions, answers, and results with your family's configured sync service. It does not share "
    "your parent PIN, app and offline settings, worksheets or PDFs, Summer Program and school-year plans, "
    "progress summaries, or unfinished quizzes."
)
FAMILY_SYNC_FLOW_COPY = (
    "Turn it on, start a new family or join one with a pairing code, then choose Sync now whenever you want "
    "to send and receive changes. Leaving sync off keeps MandelQuest local to this device."
)


class FamilySyncSettings:
    def __init__(self, parent: tk.Misc, profile_getter: Callable[[], Profile | None]) -> None:
        self._profile_getter = profile_getter
        self.frame = ttk.Frame(parent, padding=10)
        self.frame.pack(fill=tk.BOTH, expand=True)

        overview = ttk.LabelFrame(self.frame, text=FAMILY_SYNC_BETA_TITLE)
        overview.pack(fill=tk.X)
        self.sync_status_var = tk.StringVar(value="")
        self.sync_detail_var = tk.StringVar(value="")
        ttk.Label(overview, textvariable=self.sync_status_var, wraplength=560).pack(
            anchor=tk.W, padx=10, pady=(8, 2)
        )
        ttk.Label(
            overview,
            textvariable=self.sync_detail_var,
            wraplength=560,
            foreground="#5b6f84",
        ).pack(anchor=tk.W, padx=10, pady=(0, 6))
        self.sync_enabled_var = tk.BooleanVar(value=False)
        self.sync_enabled_btn = ttk.Checkbutton(
            overview,
            text="Enable family sync on this device (optional)",
            variable=self.sync_enabled_var,
            command=self._toggle_family_sync,
        )
        self.sync_enabled_btn.pack(anchor=tk.W, padx=10, pady=(0, 8))

        privacy = ttk.LabelFrame(self.frame, text="What sync shares")
        privacy.pack(fill=tk.X, pady=(8, 0))
        self.privacy_label = ttk.Label(privacy, text=FAMILY_SYNC_PRIVACY_COPY, wraplength=560)
        self.privacy_label.pack(anchor=tk.W, padx=10, pady=(8, 4))
        ttk.Label(privacy, text=FAMILY_SYNC_FLOW_COPY, wraplength=560, foreground="#5b6f84").pack(
            anchor=tk.W, padx=10, pady=(0, 8)
        )

        actions = ttk.LabelFrame(self.frame, text="Family link and manual sync")
        actions.pack(fill=tk.X, pady=(8, 0))
        link_actions = ttk.Frame(actions)
        link_actions.pack(anchor=tk.W, padx=10, pady=(8, 6))
        self.sync_start_btn = ttk.Button(link_actions, text="Start new family", command=self._start_family_sync)
        self.sync_start_btn.pack(side=tk.LEFT)
        self.sync_join_btn = ttk.Button(link_actions, text="Join existing family", command=self._join_family_sync)
        self.sync_join_btn.pack(side=tk.LEFT, padx=(6, 0))
        self.sync_show_code_btn = ttk.Button(
            actions,
            text="Show pairing code",
            command=self._show_pairing_code,
        )
        self.sync_show_code_btn.pack(anchor=tk.W, padx=10, pady=(0, 6))
        self.sync_now_btn = ttk.Button(actions, text="Sync now", command=self._sync_now)
        self.sync_now_btn.pack(anchor=tk.W, padx=10, pady=(0, 6))
        self.sync_last_var = tk.StringVar(value="")
        ttk.Label(actions, textvariable=self.sync_last_var, foreground="#5b6f84", wraplength=560).pack(
            anchor=tk.W, padx=10, pady=(0, 4)
        )
        self.sync_error_var = tk.StringVar(value="")
        ttk.Label(actions, textvariable=self.sync_error_var, foreground="#8a5b3c", wraplength=560).pack(
            anchor=tk.W, padx=10, pady=(0, 8)
        )
        self.refresh()

    def focus_primary_control(self) -> None:
        self.sync_enabled_btn.focus_set()

    def refresh(self) -> None:
        config = load_sync_config()
        state = load_sync_state()
        pending_count = sync_store.count_pending_changes()
        self.sync_enabled_var.set(state.sync_enabled)
        self.sync_enabled_btn.configure(
            text=(
                "Family sync is on (uncheck to turn it off)"
                if state.sync_enabled
                else "Enable family sync on this device (optional)"
            )
        )

        if not self._is_parent_profile():
            self.sync_status_var.set("Family Sync settings are available only from a parent profile.")
            self.sync_detail_var.set("Switch to a parent profile to review or change sync settings.")
            self.sync_last_var.set(_pending_copy(pending_count))
            self.sync_error_var.set("")
            self._set_action_states(can_manage=False, config_available=False, linked=False)
            return

        if config.available:
            self.sync_status_var.set(f"{config.server_label} is available for this device.")
            if state.sync_enabled:
                self.sync_detail_var.set(
                    "Family sync is on. Learning records can be shared with linked family devices "
                    "when you choose Sync now."
                )
            else:
                self.sync_detail_var.set(
                    "Family sync is optional and off. MandelQuest will keep working with data stored "
                    "only on this device."
                )
        else:
            self.sync_status_var.set("Family sync is not set up for this install.")
            if state.sync_enabled:
                self.sync_detail_var.set(
                    "Sync is still marked on, but no sync service is available. Uncheck the box to "
                    "return to local-only mode."
                )
            else:
                self.sync_detail_var.set(
                    "Local-only is active. This install has no family sync service configured, so there "
                    "is nothing to turn on."
                )

        linked = bool(state.family_id and state.pairing_token)
        if state.device_id:
            link_copy = "linked to a family" if linked else "not linked to a family"
            last_sync = state.last_sync_at or "never"
            self.sync_last_var.set(
                f"This device is {link_copy}. Last successful sync: {last_sync}. {_pending_copy(pending_count)}"
            )
        else:
            self.sync_last_var.set(f"This device has not been linked yet. {_pending_copy(pending_count)}")

        if state.last_error:
            self.sync_error_var.set(f"Last sync issue: {state.last_error}")
        elif linked and state.sync_enabled:
            self.sync_error_var.set("Family link is ready. Choose Sync now to send and receive changes.")
        elif linked:
            self.sync_error_var.set("The family link stays saved while sync is off; no changes are sent.")
        elif pending_count > 0:
            self.sync_error_var.set(
                "Local changes will stay queued until this device is linked and you choose Sync now."
            )
        else:
            self.sync_error_var.set("No local changes are waiting to sync.")

        can_toggle = config.available or state.sync_enabled
        _set_enabled(self.sync_enabled_btn, can_toggle)
        self._set_action_states(
            can_manage=config.available and state.sync_enabled,
            config_available=config.available,
            linked=linked,
        )

    def _is_parent_profile(self) -> bool:
        profile = self._profile_getter()
        return profile is not None and profile.role == "parent"

    def _require_parent_profile(self) -> bool:
        if self._is_parent_profile():
            return True
        self.sync_enabled_var.set(load_sync_state().sync_enabled)
        messagebox.showerror("Parent profile required", "Switch to a parent profile to manage Family Sync.")
        return False

    def _toggle_family_sync(self) -> None:
        if not self._require_parent_profile():
            return
        requested = self.sync_enabled_var.get()
        if requested and not load_sync_config().available:
            self.sync_enabled_var.set(False)
            messagebox.showerror(
                "Family Sync unavailable",
                "This install does not have a family sync service configured. Local-only mode will stay on.",
            )
            return
        save_sync_enabled(requested)
        self.refresh()

    def _start_family_sync(self) -> None:
        if not self._require_parent_profile():
            return
        state = load_sync_state()
        if not state.sync_enabled:
            messagebox.showinfo(FAMILY_SYNC_BETA_TITLE, "Turn on family sync on this device first.")
            return
        if state.family_id and not messagebox.askyesno(
            "Replace family link",
            "This device is already linked to a family. Start a new one anyway?",
        ):
            return
        result = sync_service.start_family_sync()
        self.refresh()
        if result.ok:
            messagebox.showinfo(FAMILY_SYNC_BETA_TITLE, result.message)
        else:
            messagebox.showerror(FAMILY_SYNC_BETA_TITLE, result.message)

    def _join_family_sync(self) -> None:
        if not self._require_parent_profile():
            return
        if not load_sync_state().sync_enabled:
            messagebox.showinfo(FAMILY_SYNC_BETA_TITLE, "Turn on family sync on this device first.")
            return
        pairing_token = simpledialog.askstring(
            "Join Family Sync (Beta)",
            "Enter the pairing code from the device that started family sync:",
            parent=self.frame,
        )
        if pairing_token is None:
            return
        result = sync_service.join_family_sync(pairing_token)
        self.refresh()
        if result.ok:
            messagebox.showinfo(FAMILY_SYNC_BETA_TITLE, result.message)
        else:
            messagebox.showerror(FAMILY_SYNC_BETA_TITLE, result.message)

    def _show_pairing_code(self) -> None:
        if not self._require_parent_profile():
            return
        state = load_sync_state()
        if not state.pairing_token:
            messagebox.showinfo(FAMILY_SYNC_BETA_TITLE, "No pairing code is stored for this device yet.")
            return
        messagebox.showinfo(FAMILY_SYNC_BETA_TITLE, f"Pairing code: {state.pairing_token}")

    def _sync_now(self) -> None:
        if not self._require_parent_profile():
            return
        result = sync_service.sync_now()
        self.refresh()
        if not result.attempted or result.ok:
            messagebox.showinfo(FAMILY_SYNC_BETA_TITLE, result.message)
        else:
            messagebox.showerror(FAMILY_SYNC_BETA_TITLE, result.message)

    def _set_action_states(self, *, can_manage: bool, config_available: bool, linked: bool) -> None:
        _set_enabled(self.sync_start_btn, can_manage)
        _set_enabled(self.sync_join_btn, can_manage)
        _set_enabled(self.sync_show_code_btn, can_manage and linked)
        _set_enabled(self.sync_now_btn, can_manage and config_available and linked)
        if not self._is_parent_profile():
            _set_enabled(self.sync_enabled_btn, False)


def _pending_copy(count: int) -> str:
    noun = "change is" if count == 1 else "changes are"
    return f"{count} local {noun} waiting to sync."


def _set_enabled(widget: ttk.Widget, enabled: bool) -> None:
    widget.state(["!disabled"] if enabled else ["disabled"])
