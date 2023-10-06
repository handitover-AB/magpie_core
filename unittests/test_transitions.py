"""Test state logic of Finite State Machine"""
from app.fsm.transition import Transition


def test_instatiation():
    transition = Transition()

    assert isinstance(transition, Transition)
