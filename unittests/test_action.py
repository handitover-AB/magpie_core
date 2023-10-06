"""Test action logic of Finite State Machine"""
import re

from app.fsm.action import Action


def test_instantiate():
    action = Action("Dummy action")
    pattern = "<app.fsm.action.Action object: `Dummy action` at 0x[0-9a-f]+>"
    match = re.match(pattern, str(action))

    assert isinstance(action, Action)
    assert action.name == "Dummy action"
    assert action.fn is None
    assert action.fn_name == "dummy_action"
    assert match is not None


def test_action_fn():
    def dummy_fn():
        return True

    action = Action("dummy", dummy_fn)
    assert action.fn is dummy_fn
