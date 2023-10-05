"""Implement logic for actions"""
from __future__ import annotations

from typing import Callable


class Action:
    def __init__(self, name: str, fn: Callable | None = None):
        self.name: str = name
        self.fn: Callable[..., None] = fn

    @property
    def fn_name(self) -> str:
        """Replace spaces with underscores and convert to lowercase"""
        return self.name.lower().replace(" ", "_")

    @property
    def is_valid(self) -> bool:
        """Return True if the action function seems executable, false otherwise."""
        return callable(self.fn)

    def __str__(self):
        """Return a pretty string representation of the Action"""
        return f"<app.fsm.action.Action object: `{self.name}` at {hex(id(self))}>"
