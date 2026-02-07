from __future__ import annotations

import tkinter as tk


def int_spinbox(
    parent: tk.Widget,
    variable: tk.Variable,
    from_: int,
    to: int,
    width: int = 6,
    command=None,
) -> tk.Spinbox:
    def _digits_only(value: str) -> bool:
        return value.isdigit()

    vcmd = (parent.register(_digits_only), "%P")
    box = tk.Spinbox(
        parent,
        from_=from_,
        to=to,
        textvariable=variable,
        width=width,
        validate="key",
        validatecommand=vcmd,
        command=command,
    )
    return box
