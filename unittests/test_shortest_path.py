"""Test shortest path algorithm"""
import pytest

from app.parser import FileParser
from app.fsm.model import Model, NavigationStrategy, PathError


@pytest.fixture
def model(mocker) -> Model:
    """Return a predefined model

    Use the FileParser class but mock the file handling and insert
    a multi-line string instead, pretending to be the file contents.
    """
    # Init
    mocker.patch("os.path.exists", return_value=True)
    # ARRANGE
    parser = FileParser()
    template = """
    A    ->   B
    A    ->   C

    B   [cond1]    aa    ->   B
    B   [cond2]    bb    ->   G
    
    C   [cond3]    cc    ->   C
    C   [cond4]    dd    ->   D
    C              ee    ->   E
 
    D    ->   C

    E    ->   D
    E    ->   F

    F    ->   D
    """
    mocker.patch("pathlib.Path.read_text", return_value=template)
    return parser.parse("using/template/instead")


def test_multiline_model_positive_tests(model: Model):
    # ACT
    path_a_to_a = model.shortest_path("A", "A")
    path_a_to_c = model.shortest_path("A", "C")
    path_a_to_f = model.shortest_path("A", "F")
    path_a_to_g = model.shortest_path("A", "G")

    # A to A should yield an empty path:
    with pytest.raises(StopIteration):
        next(path_a_to_a)

    assert path_a_to_c.strategy == NavigationStrategy.PESSIMISTIC
    assert next(path_a_to_c) == "C"
    with pytest.raises(StopIteration):
        next(path_a_to_c)
    assert path_a_to_c.strategy == NavigationStrategy.PESSIMISTIC

    assert list(path_a_to_f) == ["C", "E", "F"]
    assert path_a_to_f.strategy == NavigationStrategy.PESSIMISTIC

    assert list(path_a_to_g) == ["B", "G"]
    assert path_a_to_g.strategy == NavigationStrategy.OPTIMISTIC


def test_multiline_model_negative_tests(model: Model):
    """All combinations here should raise a PathError"""
    test_args = [("D", "A"), ("C", "B"), ("DUMMY1", "B"), ("B", "DUMMY2"), ("", "")]
    for from_node, to_node in test_args:
        with pytest.raises(PathError):
            model.shortest_path(from_node, to_node)
