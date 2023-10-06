"""Implement logic for transitions"""
from __future__ import annotations

from enum import Enum
from typing import List, TYPE_CHECKING

from app.fsm.state import State


if TYPE_CHECKING:
    from app.fsm.action import Action
    from app.fsm.condition import Condition


class Arrow(Enum):
    HappyPath = "=>"  # pylint: disable=invalid-name
    AlternatePath = "->"  # pylint: disable=invalid-name


class Transition:  # pylint: disable=too-many-instance-attributes
    def __init__(self, start_state=None, end_state=None, action=None) -> None:
        self.start_state: State | None = start_state
        self.end_state: State | None = end_state
        self.action: Action | None = action
        self.condition: Condition | None = None
        self.probability: int = 100
        self.happy_path: bool = False
        self.source_code_file: str = ""
        self.source_code_line: int = 0
        self._errors = []

    @property
    def name(self) -> str:
        """Return an identifier string"""
        action = self.action.name if self.action else "None"
        condition = self.condition.name if self.condition else "None"
        end = self.end_state.name if self.end_state else ""
        start = self.start_state.name if self.start_state else ""
        return f"{start}:{condition}:{action}:{end}"

    @property
    def arrow(self) -> str:
        """Return a string representation of the arrow"""
        if self.happy_path:
            return Arrow.HappyPath.value
        return Arrow.AlternatePath.value

    @property
    def errors(self) -> List[str]:
        return self._errors

    def is_valid(self) -> bool:
        self._errors = []
        # DO we have a start state?
        if not isinstance(self.start_state, State):
            self._errors.append("Start state missing")
        # Do we have an end state?
        if not isinstance(self.end_state, State):
            self._errors.append("End state missing")
        # Is probability a number between 0 and 100?
        try:
            int(self.probability)
            if self.probability < 0 or self.probability > 100:
                raise TypeError()
        except (ValueError, TypeError):
            self._errors.append(
                f"Probability is {self.probability} "
                f"({self.probability.__class__.__name__}), "
                "but should be a number from 0 to 100"
            )

        # Do we have a valid action?
        # TODO

        # Do we have a valid condition?
        # TODO

        # Return True if valid, False otherwise:
        return self._errors.count() == 0

    def __str__(self):
        """Return a pretty string representation of the transition"""
        start = f'"{self.start_state.name}"'
        action = f" '{self.action.name}'" if self.action else ""
        probability = f" {self.probability}%"
        arrow = " =>" if self.happy_path else " ->"
        end = f' "{self.end_state.name}"'
        out = (
            "<app.fsm.transition.Transition object:"
            f"`{start}{action}{probability}{arrow}{end}`"
            f"at {hex(id(self))}>"
        )
        return out
