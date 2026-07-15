"""Global keyboard navigation shared by the application shell."""

from __future__ import annotations

from typing import Any


class ShellShortcutsMixin:
    def _bind_global_shortcuts(self) -> None:
        for index in range(6):
            self.root.bind_all(
                f"<Control-Key-{index + 1}>",
                lambda _event, selected=index: self._select_tab(selected),
            )
        self.root.bind_all("<Control-Tab>", self._next_tab)
        self.root.bind_all("<Control-ISO_Left_Tab>", self._prev_tab)
        self.root.bind_all("<Control-Shift-Tab>", self._prev_tab)
        self.root.bind_all("<Control-r>", lambda _event: self._refresh_active_module())
        self.root.bind_all("<F5>", lambda _event: self._refresh_active_module())
        self.root.bind_all("<Control-l>", lambda _event: self._focus_active_controls())
        self.root.bind_all("<Control-n>", self._shortcut_parent_create)
        self.root.bind_all("<Control-Return>", self._shortcut_quiz_submit)
        self.root.bind_all("<Alt-s>", self._shortcut_quiz_start)
        self.root.bind_all("<Alt-n>", self._shortcut_quiz_submit)
        self.root.bind_all("<Alt-i>", self._shortcut_quiz_intuition)
        self.root.bind_all("<Alt-d>", self._shortcut_dashboard_daily)
        self.root.bind_all("<Alt-a>", self._shortcut_dashboard_assignment)
        for index in range(6):
            self.root.bind_all(
                f"<Alt-Key-{index + 1}>",
                lambda _event, selected=index: self._shortcut_parent_tab(selected),
            )

    def _select_tab(self, index: int) -> None:
        if 0 <= index < len(self._modules):
            self.notebook.select(index)

    def _next_tab(self, _event: object = None) -> str:
        index = self.notebook.index(self.notebook.select())
        self._select_tab((index + 1) % len(self._modules))
        return "break"

    def _prev_tab(self, _event: object = None) -> str:
        index = self.notebook.index(self.notebook.select())
        self._select_tab((index - 1) % len(self._modules))
        return "break"

    def _active_module(self) -> Any:
        index = self.notebook.index(self.notebook.select())
        return self._modules[index][1]

    def _call_active(self, expected: Any, method_name: str) -> str:
        module = self._active_module()
        method = getattr(module, method_name, None)
        if module is expected and callable(method):
            method()
            return "break"
        return ""

    def _refresh_active_module(self) -> None:
        index = self.notebook.index(self.notebook.select())
        module = self._modules[index][1]
        refresh = getattr(module, "_refresh_active_tab_shortcut", None)
        if callable(refresh):
            refresh()
            return
        self._show_module(index)

    def _focus_active_controls(self) -> None:
        focus = getattr(self._active_module(), "focus_primary_control", None)
        if callable(focus):
            focus()

    def _shortcut_parent_create(self, _event: object = None) -> str:
        return self._call_active(self.parent, "_create_active_item_shortcut")

    def _shortcut_quiz_start(self, _event: object = None) -> str:
        return self._call_active(self.quiz, "_start_quiz_shortcut")

    def _shortcut_quiz_submit(self, _event: object = None) -> str:
        return self._call_active(self.quiz, "_submit_or_next_shortcut")

    def _shortcut_quiz_intuition(self, _event: object = None) -> str:
        return self._call_active(self.quiz, "_show_intuition_shortcut")

    def _shortcut_dashboard_daily(self, _event: object = None) -> str:
        return self._call_active(self.dashboard, "_daily_shortcut")

    def _shortcut_dashboard_assignment(self, _event: object = None) -> str:
        return self._call_active(self.dashboard, "_assignment_shortcut")

    def _shortcut_parent_tab(self, index: int) -> str:
        module = self._active_module()
        select_tab = getattr(module, "_select_parent_tab", None)
        if module is self.parent and callable(select_tab):
            select_tab(index)
            return "break"
        return ""
