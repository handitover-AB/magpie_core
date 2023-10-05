"""Test the history module"""
import pytest

from app.fsm.history import AuditTrail
from app.fsm.action import Action
from app.fsm.state import State
from app.fsm.transition import Transition


@pytest.fixture
def audit_trail():
    trail = AuditTrail()
    start_state = State("Start")
    state_a = State("A")
    state_b = State("B")
    end_state = State("End")
    action_a_to_b = Action("a_to_b")

    for start_state, end_state, action in (
        (start_state, state_a, None),
        (state_a, state_b, action_a_to_b),
        (state_b, end_state, None),
    ):
        trail.append(Transition(start_state, end_state, action))
    return trail


def test_action_history(audit_trail: AuditTrail):
    assert audit_trail.action_history == ["", "a_to_b", ""]


def test_state_history(audit_trail: AuditTrail):
    assert audit_trail.state_history == ["Start", "A", "B", "End"]


def test_current_state(audit_trail: AuditTrail):
    assert audit_trail.current_state.name == "End"


def test_previous_state(audit_trail: AuditTrail):
    assert audit_trail.previous_state.name == "B"
