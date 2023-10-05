"""Test the Finite State Machine logic"""
from app.fsm.machine import Machine, RunOptions
from app.fsm.model import Model

from app.parser import FileParser


class MockActor:
    model: Model
    name: str = "Mock Actor"


def test_instantiation():
    mock_model = Model()
    mock_actor = MockActor()
    mock_actor.model = mock_model
    machine = Machine(mock_actor)
    assert isinstance(machine, Machine)


def test_non_cyclic_model_no_actions_or_state_fn(mocker):
    # ARRANGE
    template = """
    A  ->  B
    B  ->  C
    """
    mocker.patch("os.path.exists", return_value=True)
    parser = FileParser()
    mocker.patch("pathlib.Path.read_text", return_value=template)
    mock_model = parser.parse("using/template/instead")
    run_options = RunOptions()
    run_options.max_run_time_s = 1
    mock_actor = MockActor()
    mock_actor.model = mock_model
    machine = Machine(mock_actor, **run_options.as_dict())

    # ACT
    machine.start()

    # ASSERT
    assert mock_model.initial_state.name == "A"
    assert sorted(mock_model.states) == ["A", "B", "C"]
    assert len(mock_model.states["A"].outbounds) == 1
    assert mock_model.states["A"].outbounds[0].name == "A:None:None:B"
    assert len(mock_model.states["B"].outbounds) == 1
    assert mock_model.states["B"].outbounds[0].name == "B:None:None:C"
    assert len(mock_model.states["C"].outbounds) == 0
    assert not mock_model.actions
    assert isinstance(mock_model.actions, dict)
    assert isinstance(mock_model.states, dict)
    assert isinstance(mock_model.transitions, dict)
    assert isinstance(machine, Machine)

    assert machine.current_state == mock_model.states["C"]
    assert machine.summary.actions_count == 0
    assert machine.summary.states_count == 3
    assert machine.summary.transitions_count == 2
    assert machine.summary.visited_actions == {}
