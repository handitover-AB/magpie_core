"""Test session logic of Finite State Machine"""

from app.sessions import Session
from app.fsm.model_based_actor import ModelBasedActor


# Note: mock_actor is a session-scoped fixture
# defined in conftest.py
def test_instantiation_with_model_based_actor(mock_actor_module):
    actor = ModelBasedActor(actor_module=mock_actor_module)
    session = Session(name="Dummy", actor=actor)
    assert isinstance(session, Session)


def test_instantiation_with_module(mock_actor_module):
    session = Session(name="Dummy", actor_module=mock_actor_module)
    assert isinstance(session, Session)


def test_start_machine(mock_actor_module):
    session = Session(name="Dummy", actor_module=mock_actor_module)
    session.start()
    assert session.machine.current_state == session.machine.model.states.get("End")
