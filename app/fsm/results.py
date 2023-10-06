"""Implement logic for results management"""
from __future__ import annotations

from enum import Enum, auto
from typing import List, Dict, Tuple, TYPE_CHECKING

from app.fsm.action import Action
from app.fsm.state import State
from app.fsm.transition import Transition

if TYPE_CHECKING:
    from app.fsm.model import Model


VisitsType = Dict[str, List[str]]


######################
#  UTILITY FUNCTIONS
#
def _percentage_with_check(numerator: Dict, denominator: Dict) -> int | None:
    """Calculate percentage from number of items in numerator and denominator"""
    try:
        percentage = round(100 * len(numerator) / len(denominator))
    except (TypeError, ZeroDivisionError):
        return None
    return percentage


###################
#  PUBLIC CLASSES
#
class Result(Enum):
    """Define possible outcomes"""

    PASSED = auto()
    FAILED = auto()
    NOT_APPLICABLE = auto()

    def __str__(self):
        return self.name


class VisitsAndResults:
    def __init__(self) -> None:
        self._visits_count: int = 0
        self._results: List[Result] = []

    @property
    def visits_count(self) -> int:
        return self._visits_count

    @property
    def is_visited(self) -> bool:
        return self._visits_count > 0

    @property
    def is_failed(self) -> bool:
        """Has only failed results"""
        return self._result_count(Result.PASSED) == 0 and self._result_count(Result.FAILED) > 0

    @property
    def is_flaky(self) -> bool:
        """Has failed and passed results"""
        return self._result_count(Result.PASSED) > 0 and self._result_count(Result.FAILED) > 0

    @property
    def short_summary(self) -> str:
        """Return a short human-friendly result summary string"""
        out = []
        if self.has_result(Result.PASSED):
            out.append(f"✅: {self._result_count(Result.PASSED)}")
        if self.has_result(Result.FAILED):
            out.append(f"❌: {self._result_count(Result.FAILED)}")
        if self.has_result(Result.NOT_APPLICABLE):
            out.append(f"--: {self._result_count(Result.NOT_APPLICABLE)}")
        return " ".join(out)

    @property
    def fail_count(self) -> int:
        return self._result_count(Result.FAILED)

    @property
    def pass_count(self) -> int:
        return self._result_count(Result.PASSED)

    def record_visit(self, result: Result | None = None) -> None:
        """Count the visit and record a result, if provided"""
        self._visits_count += 1
        if result:
            self._results.append(result)

    def has_result(self, result_type: Result) -> bool:
        """Return True if there is at least one result of the provided type, False otherwise"""
        filtered = [result for result in self._results if result == result_type]
        return len(filtered) > 0

    def _result_count(self, result_type: Result) -> int:
        return len([res for res in self._results if res == result_type])


class Results:
    """Keep result collections"""

    def __init__(self) -> None:
        self.actions: Dict[str, VisitsAndResults] = dict()
        self.states: Dict[str, VisitsAndResults] = dict()
        self.transitions: Dict[str, VisitsAndResults] = dict()


class SessionSummary:
    """Provide multiple visualization options for result summaries."""

    def __init__(self, model: Model) -> None:
        self.model = model
        self.results = Results()
        self.duration: float = 0

    @property
    def total_transitions_visits_count(self) -> int:
        return sum([trns.visits_count for trns in self.results.transitions.values()])

    @property
    def actions_count(self) -> int:
        return len(self.model.actions)

    @property
    def states_count(self) -> int:
        return len(self.model.states)

    @property
    def transitions_count(self) -> int:
        return len(self.model.transitions)

    @property
    def actions_coverage(self) -> float:
        """Return the percentage of covered actions"""
        return _percentage_with_check(self.visited_actions, self.model.actions)

    @property
    def states_coverage(self) -> float:
        """Return the percentage of covered states"""
        return _percentage_with_check(self.visited_states, self.model.states)

    @property
    def transitions_coverage(self) -> float:
        """Return the percentage of covered transitions"""
        return _percentage_with_check(self.visited_transitions, self.model.transitions)

    @property
    def visited_actions(self) -> Dict[str, Action]:
        items = self.model.actions.items()
        action_names = self.results.actions.keys()
        return {name: action for name, action in items if name in action_names}

    @property
    def unvisited_actions(self) -> Dict[str, Action]:
        items = self.model.actions.items()
        action_names = self.results.actions.keys()
        return {name: action for name, action in items if name not in action_names}

    @property
    def failed_actions(self) -> Dict[str, Action]:
        visited_actions = self.results.actions.items()
        return {name: action for name, action in visited_actions if action.is_failed}

    @property
    def flaky_actions(self) -> Dict[str, Action]:
        visited_actions = self.results.actions.items()
        return {name: action for name, action in visited_actions if action.is_flaky}

    @property
    def failed_states(self) -> Dict[str, State]:
        visited_states = self.results.states.items()
        return {name: state for name, state in visited_states if state.is_failed}

    @property
    def flaky_states(self) -> Dict[str, State]:
        visited_states = self.results.states.items()
        return {name: state for name, state in visited_states if state.is_flaky}

    @property
    def visited_states(self) -> Dict[str, State]:
        items = self.model.states.items()
        visited_states = self.results.states.keys()
        return {name: state for name, state in items if name in visited_states}

    @property
    def unvisited_states(self) -> Dict[str, State]:
        items = self.model.states.items()
        visited_states = self.results.states.keys()
        return {name: state for name, state in items if name not in visited_states}

    @property
    def failed_transitions(self) -> Dict[str, Transition]:
        visited = self.results.transitions.items()
        return {name: item for name, item in visited if item.is_failed}

    @property
    def flaky_transitions(self) -> Dict[str, Transition]:
        visited = self.results.transitions.items()
        return {name: item for name, item in visited if item.is_flaky}

    @property
    def visited_transitions(self) -> Dict[str, Transition]:
        items = self.model.transitions.items()
        visited_transitions = self.results.transitions.keys()
        return {name: trns for name, trns in items if name in visited_transitions}

    @property
    def unvisited_transitions(self) -> Tuple[Transition]:
        items = self.model.transitions.items()
        visited_transitions = self.results.transitions.keys()
        return (trns for name, trns in items if name not in visited_transitions)

    def record_visit(self, obj: Action | State | Transition, result: Result) -> None:
        """Store visits and results for actions, states and transitions"""
        object_collection: Dict[str, VisitsAndResults] = None
        # Pick the right collection to work with:
        if isinstance(obj, Action):
            object_collection = self.results.actions
        elif isinstance(obj, State):
            object_collection = self.results.states
        elif isinstance(obj, Transition):
            object_collection = self.results.transitions
        else:
            return

        # Create a result keeping object if it does not exist:
        if obj.name not in object_collection:
            object_collection[obj.name] = VisitsAndResults()

        # Record result:
        object_collection[obj.name].record_visit(result)
