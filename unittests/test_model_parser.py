"""Unit tests for model parsing"""
import pytest

from app.parser import FileParser

from app.fsm.model import ModelRowParts, ModelError


##################
#  UTIL FUNCTION
#
def get_parser_for_template(template, mocker) -> FileParser:
    mocker.patch("os.path.exists", return_value=True)
    parser = FileParser()
    mocker.patch("pathlib.Path.read_text", return_value=template)
    return parser


###################
#  POSITIVE TESTS
#
def test_instatiate_parser():
    """Simple smoke test - can we instantiate the parser?"""
    parser = FileParser()
    assert isinstance(parser, FileParser)


@pytest.mark.parametrize(
    "template, expected_parts",
    [
        ["A  =>  B", ("A", "", "", "=>", "B")],
        ["ÅÄÖ  =>  ÖÄÅ", ("ÅÄÖ", "", "", "=>", "ÖÄÅ")],
        ["🙂  =>  🙃", ("🙂", "", "", "=>", "🙃")],
        ['"A: X"  \'a\'  ->  "B: Y"', ("A: X", "", "a", "->", "B: Y")],
        ['"A: X"  [c d]  \'a\'  ->  "B: Y"', ("A: X", "c d", "a", "->", "B: Y")],
    ],
)
def test_row_parser_positive_tests(template: str, expected_parts: ModelRowParts):
    """Test the row parser"""
    # ARRANGE
    parser = FileParser()
    # ACT
    parts, _ = parser.parts_from_row(template)
    # ASSERT
    assert list(parts) == list(expected_parts)


def test_multiline_model_positive_test(mocker):
    # Init
    mocker.patch("os.path.exists", return_value=True)
    # ARRANGE
    parser = FileParser()
    template = """
    Start                                         =>  First state
    First state                  'first action'   ->  Second state
    Second state  [condition 1]  'first action'   =>  First state
    Second state  [condition 2]  'do nothing'     ->  Second state
    """
    mocker.patch("pathlib.Path.read_text", return_value=template)

    # ACT
    model = parser.parse("using/template/instead")

    # ASSERT
    # Assert transitions:
    assert len(model.transitions) == 4

    transition = model.transitions["Start:None:None:First state"]
    assert transition.action is None

    transition = model.transitions["First state:None:first action:Second state"]
    assert transition.happy_path is False
    assert transition.action.name == "first action"
    assert transition.action.fn_name == "first_action"

    transition = model.transitions["Second state:condition 1:first action:First state"]
    assert transition.happy_path is True
    assert transition.condition.name == "condition 1"
    assert transition.condition.fn_name == "condition_1"
    assert transition.action.name == "first action"
    assert transition.action.fn_name == "first_action"

    transition = model.transitions["Second state:condition 2:do nothing:Second state"]
    assert transition.happy_path is False
    assert transition.condition.name == "condition 2"
    assert transition.condition.fn_name == "condition_2"
    assert transition.action.name == "do nothing"
    assert transition.action.fn_name == "do_nothing"

    # Assert states:
    assert len(model.states) == 3
    assert model.initial_state == model.states["Start"]

    state = model.states["Start"]
    assert state.name == "Start"
    assert state.inbounds == []
    assert state.outbounds == [model.transitions["Start:None:None:First state"]]

    state = model.states["First state"]
    assert state.name == "First state"
    assert state.inbounds == [
        model.transitions["Start:None:None:First state"],
        model.transitions["Second state:condition 1:first action:First state"],
    ]
    assert state.outbounds == [model.transitions["First state:None:first action:Second state"]]

    state = model.states["Second state"]
    assert state.name == "Second state"
    assert state.inbounds == [
        model.transitions["First state:None:first action:Second state"],
        model.transitions["Second state:condition 2:do nothing:Second state"],
    ]
    assert state.outbounds == [
        model.transitions["Second state:condition 1:first action:First state"],
        model.transitions["Second state:condition 2:do nothing:Second state"],
    ]


###################
#  NEGATIVE TESTS
#
def test_do_not_allow_same_rows_twice_1(mocker):
    # ARRANGE
    template = """
    Start                          =>  First state
    Start                          =>  First state
    """
    parser = get_parser_for_template(template, mocker)

    # ACT:
    with pytest.raises(ModelError) as err:
        parser.parse("using/template/instead")
    err_msg = str(err.value) if err else ""

    # ASSERT:
    assert err_msg == (
        '"using/template/instead", line 2: Duplicate transition,'
        " only one transition between `Start` and `First state` is allowed."
        " Remove the superfluous one(s).\n"
    )


def test_do_not_allow_same_rows_twice_2(mocker):
    # ARRANGE
    template = """
    Start                          =>  First state
    First state   'first action'   ->  Second state
    Start                          =>  First state
    """
    parser = get_parser_for_template(template, mocker)

    # ACT:
    with pytest.raises(ModelError) as err:
        parser.parse("using/template/instead")
    err_msg = str(err.value)

    # ASSERT:
    assert err_msg == (
        '"using/template/instead", line 3: Duplicate transition,'
        " only one transition between `Start` and `First state` is allowed."
        " Remove the superfluous one(s).\n"
    )


def test_do_not_allow_unreachable_states(mocker):
    # ARRANGE
    template = """
    Start                          =>  First state
    Second state                   ->  First state
    """
    parser = get_parser_for_template(template, mocker)

    # ACT:
    with pytest.raises(ModelError) as err:
        parser.parse("using/template/instead")
    err_msg = str(err.value) if err else ""

    # ASSERT:
    assert err_msg == (
        '"using/template/instead", line 2: Unreachable state: `Second state`!'
        " Please check your spelling. If correct,"
        " you need to add a transition pointing to this state.\n"
    )


@pytest.mark.parametrize("template", ["Start  =>", "=>  End", "=>", "A", "[C]"])
def test_not_enough_parts_should_fail(template, mocker):
    # ARRANGE
    parser = get_parser_for_template(template, mocker)

    # ACT:
    with pytest.raises(ModelError) as err:
        parser.parse("using/template/instead")
    err_msg = str(err.value) if err else ""

    # ASSERT:
    assert err_msg == (
        '"using/template/instead", line 1: Too few items,'
        " review your syntax and add the missing parts.\n"
    )
