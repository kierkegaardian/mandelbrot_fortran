from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
import sys

from . import db


def _on_close(root, app) -> None:
    if hasattr(app, "shutdown"):
        app.shutdown()
    root.destroy()


def _run_smoke_test() -> None:
    if not os.environ.get("MANDELQUEST_DATA_DIR", "").strip():
        raise RuntimeError("--smoke-test requires an explicit MANDELQUEST_DATA_DIR")
    db.init_db()
    created_at = datetime.now(timezone.utc).isoformat()
    profile = db.create_profile("Smoke Test", "child", created_at)
    if not any(candidate.id == profile.id for candidate in db.list_profiles()):
        raise RuntimeError("profile write/read smoke failed")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="initialize an isolated database, verify a write/read roundtrip, and exit",
    )
    args, _unknown = parser.parse_known_args(argv)
    return args


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.smoke_test:
        _run_smoke_test()
        print("[smoke-test] OK")
        return

    import tkinter as tk
    from tkinter import messagebox

    from .ui_profile_picker import pick_profile
    from .ui_root import AppShell

    db.init_db()
    root = tk.Tk()
    profile = pick_profile(root)
    if profile is None:
        messagebox.showinfo("Goodbye", "No profile selected. Closing the app.")
        root.destroy()
        sys.exit(0)

    app = AppShell(root, profile)
    root.protocol("WM_DELETE_WINDOW", lambda: _on_close(root, app))
    root.after(200, app.fractal.render)
    root.mainloop()


if __name__ == "__main__":
    main()
