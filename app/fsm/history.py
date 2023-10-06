"""Implement classes that keep track of execution history"""
from __future__ import annotations

from typing import List

from app.fsm.state import State
from app.fsm.transition import Transition


##################
# HELPER CLASSES
#
class AuditTrail:
    """Save transitions in execution order"""

    def __init__(self) -> None:
        self.transitions = []

    @property
    def action_history(self) -> List[str]:
        if self.transitions:
            return [t.action.name if t.action else "" for t in self.transitions]
        return []

    @property
    def state_history(self) -> List[str]:
        if self.transitions:
            states = [self.transitions[0].start_state.name]
            states += [t.end_state.name for t in self.transitions]
            return states
        return []

    @property
    def current_state(self) -> State | None:
        if self.transitions:
            return self.transitions[-1].end_state
        return None

    @property
    def previous_state(self) -> State | None:
        if self.transitions:
            return self.transitions[-1].start_state
        return None

    def append(self, transition: Transition) -> None:
        if not isinstance(transition, Transition):
            raise ValueError(
                f"You can only append Transition objects. You passed a {type(transition)}."
            )
        self.transitions.append(transition)
