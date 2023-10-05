"""Implement logic for states"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List


if TYPE_CHECKING:
    from app.fsm.transition import Transition


class State:
    def __init__(self, name: str, fn: Callable | None = None) -> None:
        self.name: str = name
        self.inbounds: List[Transition] = []
        self.outbounds: List[Transition] = []
        self.fn: Callable | None = fn

    def __str__(self):
        """Return a pretty string representation of the State"""
        return f"<app.fsm.state.State object: `{self.name}` at {hex(id(self))}>"
