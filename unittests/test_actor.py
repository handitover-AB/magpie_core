"""Test Actor base class"""

from app.actor import Actor


def test_instantiation(mock_actor_module):
    actor = Actor(actor_module=mock_actor_module)
    assert isinstance(actor, Actor)


def test_instantiation_optional_attributes(mock_actor_module):
    actor = Actor(actor_module=mock_actor_module, name="Yo", config=0)
    assert actor.name == "Yo"
    assert actor.config == 0


def test_data_uniqueness(mock_actor_module):
    data_1 = {"apa": 1}
    data_2 = 2
    actor_1 = Actor(actor_module=mock_actor_module, config=data_1)
    actor_2 = Actor(actor_module=mock_actor_module, config=data_2)
    assert actor_1.config == data_1
    assert actor_2.config == data_2
