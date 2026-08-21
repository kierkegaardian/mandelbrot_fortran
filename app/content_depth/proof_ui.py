from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .models import ProofSpec, ProofStep
from .proof import encode_proof_answer


class ProofBuilderController:
    """Small deterministic statement/reason ordering widget."""

    def __init__(self, parent: tk.Widget, spec: ProofSpec, answer_var: tk.StringVar, on_change=None) -> None:
        self._spec = spec
        self._answer_var = answer_var
        self._steps = {step.step_id: step for step in spec.step_bank}
        self._bank_ids = [step.step_id for step in spec.step_bank]
        self._ordered_ids: list[str] = []
        self._on_change = on_change

        ttk.Label(parent, text="Build the proof. Select a statement/reason pair, add it, then order the proof.").pack(
            anchor=tk.W, pady=(0, 4)
        )
        columns = ttk.Frame(parent)
        columns.pack(fill=tk.BOTH, expand=True)
        self.bank = tk.Listbox(columns, height=8, exportselection=False)
        self.bank.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        controls = ttk.Frame(columns)
        controls.pack(side=tk.LEFT, padx=6)
        ttk.Button(controls, text="Add →", command=self._add).pack(fill=tk.X, pady=2)
        ttk.Button(controls, text="← Remove", command=self._remove).pack(fill=tk.X, pady=2)
        ttk.Button(controls, text="Move up", command=lambda: self._move(-1)).pack(fill=tk.X, pady=2)
        ttk.Button(controls, text="Move down", command=lambda: self._move(1)).pack(fill=tk.X, pady=2)
        self.ordered = tk.Listbox(columns, height=8, exportselection=False)
        self.ordered.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.bank.bind("<Return>", lambda _event: self._add())
        self.ordered.bind("<Delete>", lambda _event: self._remove())
        self.ordered.bind("<Alt-Up>", lambda _event: self._move(-1))
        self.ordered.bind("<Alt-Down>", lambda _event: self._move(1))
        self._refresh(notify=False)
        self.bank.focus_set()

    @property
    def ordered_step_ids(self) -> tuple[str, ...]:
        return tuple(self._ordered_ids)

    def restore(self, ordered_step_ids: tuple[str, ...]) -> None:
        valid = [step_id for step_id in ordered_step_ids if step_id in self._steps]
        self._ordered_ids = list(dict.fromkeys(valid))
        self._refresh()

    def _add(self) -> None:
        selection = self.bank.curselection()
        if not selection:
            return
        step_id = self._bank_ids[int(selection[0])]
        if step_id not in self._ordered_ids:
            self._ordered_ids.append(step_id)
        self._refresh()

    def _remove(self) -> None:
        selection = self.ordered.curselection()
        if not selection:
            return
        self._ordered_ids.pop(int(selection[0]))
        self._refresh()

    def _move(self, delta: int) -> None:
        selection = self.ordered.curselection()
        if not selection:
            return
        index = int(selection[0])
        target = index + delta
        if target < 0 or target >= len(self._ordered_ids):
            return
        self._ordered_ids[index], self._ordered_ids[target] = self._ordered_ids[target], self._ordered_ids[index]
        self._refresh(select_index=target)

    def _refresh(self, *, select_index: int | None = None, notify: bool = True) -> None:
        self.bank.delete(0, tk.END)
        for step_id in self._bank_ids:
            self.bank.insert(tk.END, _step_label(self._steps[step_id]))
        self.ordered.delete(0, tk.END)
        for index, step_id in enumerate(self._ordered_ids, start=1):
            self.ordered.insert(tk.END, f"{index}. {_step_label(self._steps[step_id])}")
        if select_index is not None and self._ordered_ids:
            self.ordered.selection_set(select_index)
        self._answer_var.set(encode_proof_answer(tuple(self._ordered_ids)))
        if notify and callable(self._on_change):
            self._on_change()


def _step_label(step: ProofStep) -> str:
    return f"{step.statement} — {step.reason}"
