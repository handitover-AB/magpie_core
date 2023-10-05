"""Test actor logic of Finite State Machine"""
import pytest

from app.fsm.model_based_actor import ModelBasedActor


class MockStates:
    """Define a mock state object to be used in tests"""

    def end(self):  # pylint: disable=no-self-use
        return "Dummy end"

    def start(self):  # pylint: disable=no-self-use
        return "Dummy start"


# Note: mock_actor is a session-scoped fixture
# defined in conftest.py
def test_instantiation_without_states_and_actions(mock_actor_module):
    actor = ModelBasedActor(actor_module=mock_actor_module)
    assert isinstance(actor, ModelBasedActor)


def test_instantiation_with_actions(mock_actor_module):
    mock_actor_module.states = MockStates()
    actor = ModelBasedActor(actor_module=mock_actor_module)

    assert isinstance(actor, ModelBasedActor)
    assert actor.model.states["End"].fn() == "Dummy end"
    assert actor.model.states["Start"].fn() == "Dummy start"


def test_instantiation_with_states(mock_actor_module):
    mock_actor_module.states = MockStates()
    actor = ModelBasedActor(actor_module=mock_actor_module)

    assert isinstance(actor, ModelBasedActor)
    assert actor.model.states["End"].fn() == "Dummy end"
    assert actor.model.states["Start"].fn() == "Dummy start"


@pytest.mark.parametrize(
    "name, expected", (("Dummy", "dummy"), ("Dummy Name", "dummy_name"), ("", ""))
)
def test_fn_name_from_name(name, expected):
    assert ModelBasedActor._fn_name_from_name(name) == expected  # pylint: disable=protected-access


def test_data_uniqueness(mock_actor_module):
    data_1 = {"apa": 1}
    data_2 = 2
    actor_1 = ModelBasedActor(actor_module=mock_actor_module, config=data_1)
    actor_2 = ModelBasedActor(actor_module=mock_actor_module, config=data_2)
    assert actor_1.config == data_1
    assert actor_2.config == data_2
