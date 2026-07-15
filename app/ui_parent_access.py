"""Session-scoped parent PIN gate for shell navigation."""

from __future__ import annotations

from tkinter import messagebox, simpledialog

from . import db
from .time_utils import now_iso


class ParentAccessMixin:
    def _ensure_parent_access(self) -> bool:
        if self._parent_unlocked:
            return True
        if not db.parent_pin_configured():
            if self.profile.role != "parent":
                messagebox.showerror(
                    "Parent access locked",
                    "A parent must sign in and set a parent PIN first.",
                )
                return False
            messagebox.showinfo(
                "Set parent PIN",
                "No parent PIN is set. Configure one in Parent → Profiles.",
            )
            self._parent_unlocked = True
            return True

        locked, locked_until = db.parent_pin_locked(now_iso())
        if locked:
            messagebox.showerror(
                "Parent access locked",
                f"Too many failed attempts. Try again after {locked_until}.",
            )
            return False
        pin = simpledialog.askstring(
            "Parent PIN", "Enter parent PIN:", show="*", parent=self.root
        )
        if pin is None:
            return False
        if db.verify_parent_pin(pin, now_iso()):
            self._parent_unlocked = True
            return True

        locked_until = db.record_parent_auth_failure(now_iso())
        if locked_until is None:
            messagebox.showerror("Incorrect PIN", "Parent PIN was incorrect.")
        else:
            messagebox.showerror(
                "Parent access locked",
                f"PIN failed too many times. Locked until {locked_until}.",
            )
        return False
