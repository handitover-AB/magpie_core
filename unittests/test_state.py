"""Test state logic of Finite State Machine"""
import re

from app.fsm.state import State


def test_instatiation():
    state = State("Dummy state")
    pattern = "<app.fsm.state.State object: `Dummy state` at 0x[0-9a-f]+>"
    match = re.match(pattern, str(state))

    assert isinstance(state, State)
    assert state.name == "Dummy state"
    assert match is not None
