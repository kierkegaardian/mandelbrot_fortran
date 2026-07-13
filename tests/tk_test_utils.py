from __future__ import annotations

import os
import tempfile
import tkinter as tk
from tkinter import messagebox, simpledialog
import traceback
import unittest


def tk_available() -> bool:
    try:
        root = tk.Tk()
        root.withdraw()
        root.update_idletasks()
        root.destroy()
    except tk.TclError:
        return False
    return True


class TkAppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._roots: list[tk.Tk] = []
        self._tk_errors: list[str] = []
        self._messagebox_errors: list[str] = []
        self._askyesno_answers: list[bool] = []
        self._askstring_answers: list[str | None] = []

        self._old_data_dir = os.environ.get("MANDELQUEST_DATA_DIR")
        os.environ["MANDELQUEST_DATA_DIR"] = self._tmp.name

        self._orig_showinfo = messagebox.showinfo
        self._orig_showerror = messagebox.showerror
        self._orig_askyesno = messagebox.askyesno
        self._orig_askstring = simpledialog.askstring

        messagebox.showinfo = self._fake_showinfo
        messagebox.showerror = self._fake_showerror
        messagebox.askyesno = self._fake_askyesno
        simpledialog.askstring = self._fake_askstring

    def tearDown(self) -> None:
        for root in reversed(self._roots):
            try:
                root.destroy()
            except tk.TclError:
                pass

        messagebox.showinfo = self._orig_showinfo
        messagebox.showerror = self._orig_showerror
        messagebox.askyesno = self._orig_askyesno
        simpledialog.askstring = self._orig_askstring

        if self._old_data_dir is None:
            os.environ.pop("MANDELQUEST_DATA_DIR", None)
        else:
            os.environ["MANDELQUEST_DATA_DIR"] = self._old_data_dir

        self._tmp.cleanup()

    def _fake_showinfo(self, _title, _message, **_kwargs):
        return "ok"

    def _fake_showerror(self, title, message, **_kwargs):
        self._messagebox_errors.append(f"{title}: {message}")
        return "ok"

    def _fake_askyesno(self, _title, _message, **_kwargs):
        if self._askyesno_answers:
            return self._askyesno_answers.pop(0)
        return True

    def _fake_askstring(self, _title, _prompt, **_kwargs):
        if self._askstring_answers:
            return self._askstring_answers.pop(0)
        return "1234"

    def _report_tk_error(self, exc, value, tb) -> None:
        self._tk_errors.append("".join(traceback.format_exception(exc, value, tb)))

    def _new_root(self, *, withdraw: bool = False) -> tk.Tk:
        root = tk.Tk()
        root.report_callback_exception = self._report_tk_error
        if withdraw:
            root.withdraw()
        self._roots.append(root)
        return root

    def _pump(self, root: tk.Tk) -> None:
        root.update_idletasks()
        root.update()
        self.assertEqual([], self._messagebox_errors, "\n".join(self._messagebox_errors))
        self.assertEqual([], self._tk_errors, "\n\n".join(self._tk_errors))

    def _close_shell(self, root: tk.Tk, shell) -> None:
        shell.shutdown()
        self._pump(root)
        root.destroy()

    def _set_answer(self, panel, question, answer: str) -> None:
        if question.choices:
            panel.choice_var.set(answer)
        else:
            panel.answer_var.set(answer)

    def _wrong_answer(self, question) -> str:
        if question.choices:
            for choice in question.choices:
                if choice != question.correct_answer:
                    return choice
            return question.choices[0]
        return "__wrong__" if question.correct_answer != "__wrong__" else "__different__"

    def _texts_under(self, widget) -> list[str]:
        values: list[str] = []
        try:
            text = str(widget.cget("text"))
        except Exception:
            text = ""
        if text:
            values.append(text)
        for child in widget.winfo_children():
            values.extend(self._texts_under(child))
        return values
