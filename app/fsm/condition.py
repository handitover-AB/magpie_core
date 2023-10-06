"""Implement logic for condition expressionss"""
from __future__ import annotations

from typing import Callable


class Condition:
    def __init__(self, name: str, fn: Callable | None = None):
        self.name: str = name
        self.fn: Callable[..., bool] = fn

    @property
    def fn_name(self) -> str:
        """Replace spaces with underscores and convert to lowercase"""
        return self.name.lower().replace(" ", "_")

    @property
    def is_valid(self) -> bool:
        """Return True if the condition function seems executable, false otherwise."""
        return callable(self.fn)

    def __str__(self):
        """Return a pretty string representation of the Condition"""
        return f"<app.fsm.condition.Condition object: `{self.name}` at {hex(id(self))}>"
