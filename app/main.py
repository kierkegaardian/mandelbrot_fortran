from __future__ import annotations

import sys
import tkinter as tk
from tkinter import messagebox

from . import db
from .ui_profile_picker import pick_profile
from .ui_root import AppShell


def main() -> None:
    db.init_db()
    root = tk.Tk()
    profile = pick_profile(root)
    if profile is None:
        messagebox.showinfo("Goodbye", "No profile selected. Closing the app.")
        root.destroy()
        sys.exit(0)

    app = AppShell(root, profile)
    root.after(200, app.fractal.render)
    root.mainloop()


if __name__ == "__main__":
    main()
