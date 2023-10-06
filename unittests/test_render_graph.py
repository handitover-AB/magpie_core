"""Test that the colors and styles of Graphviz renders are correct before and after execution"""
from __future__ import annotations

import copy
from string import Template as StringTemplate
from typing import Callable, Dict

import graphviz
import pytest
from app.fsm.model import Model, Color
from app.fsm.results import Result, VisitsAndResults, SessionSummary
from app.parser import FileParser


# TC 1
templates: Dict[int, str] = {
    1: """
A                   ->  B
B           act1    ->  C
C  [cond1]  act2    ->  B
C  [cond2]  reload  ->  C
C           act1    ->  D
""",
    2: """
Start                      open login page         ->   At login page without errors

At login page without errors                       ->   Enter credentials
At login page with errors                          ->   Enter credentials

Enter credentials          log in as admin         ->   At organisation settings page
Enter credentials          log in as global        ->   At calendar page for scheduling
Enter credentials          log in as globaladmin   ->   At calendar page for scheduling
Enter credentials          log in as practitioner  ->   At calendar page
Enter credentials          log in as scheduler     ->   At who to impersonate page
Enter credentials          bad credentials         ->   At login page with errors
Enter credentials          read release            ->   At release page popup
Enter credentials          login help              ->   At help page popup

At release page popup      close release page      ->   Enter credentials
At help page popup         close help page         ->   Enter credentials

At who to impersonate page   select practitioner   ->   At calendar page for scheduling

At calendar page                                            reload      ->   At calendar page
At calendar page for scheduling    [i am not a scheduler]   reload      ->   At calendar page for scheduling
At calendar page for scheduling    [i am a scheduler]       reload      ->   At who to impersonate page
At organisation settings page                               reload      ->   At organisation settings page
At who to impersonate page                                  reload      ->   At who to impersonate page
Enter credentials                                           reload      ->   Enter credentials

At calendar page                   log out         ->   At login page without errors
At calendar page for scheduling    log out         ->   At login page without errors
At organisation settings page      log out         ->   At login page without errors
At who to impersonate page         log out         ->   At login page without errors
""",
}

dots = {
    1: r"""digraph {
    label="&#10;&#10;"
    bgcolor="#E7E7E7"
    "." [label="" color="#BBBBBB" fillcolor="$fillcolor_dot" height=0.2 shape=circle style=filled width=0.2]
    A [label=A color="#BBBBBB" fillcolor="$fillcolor_a" fontcolor="#333333" fontname=Helvetica fontsize=12 shape=box style="rounded,filled" tooltip=$tooltip_a]
    B [label=B color="#BBBBBB" fillcolor="$fillcolor_b" fontcolor="#333333" fontname=Helvetica fontsize=12 shape=box style="rounded,filled" tooltip=$tooltip_b]
    C [label=C color="#BBBBBB" fillcolor="$fillcolor_c" fontcolor="$fontcolor_c" fontname=Helvetica fontsize=12 shape=box style="rounded,filled" tooltip=$tooltip_c]
    D [label=D color="#BBBBBB" fillcolor="$fillcolor_d" fontcolor="#333333" fontname=Helvetica fontsize=12 shape=box style="rounded,filled" tooltip=$tooltip_d]
    "." -> A [color="$color_dot_to_a" penwidth=$penwidth_dot_to_a style=solid]
    A -> B [color="$color_a_to_b" fontname="Times New Roman" fontsize=8 penwidth=$penwidth_a_to_b style=solid tooltip="Start state: A&#10;End state: B$visits_a_to_b"]
    B -> C [label="act1()" color="$color_b_to_c" fontname="Times New Roman" fontsize=8 penwidth=$penwidth_b_to_c style=solid tooltip="Start state: B&#10;End state: C&#10;Action: act1()$visits_b_to_c"]
    C -> B [label="act2()" color="$color_c_to_b" fontname="Times New Roman" fontsize=8 penwidth=$penwidth_c_to_b style=dashed tooltip="Start state: C&#10;End state: B&#10;Action: act2()&#10;Condition: cond1()$visits_c_to_b"]
    C -> C [label="reload()" color="$color_c_to_c" fontname="Times New Roman" fontsize=8 penwidth=$penwidth_c_to_c style=dashed tooltip="Start state: C&#10;End state: C&#10;Action: reload()&#10;Condition: cond2()$visits_c_to_c"]
    C -> D [label="act1()" color="$color_c_to_d" fontname="Times New Roman" fontsize=8 penwidth=$penwidth_c_to_d style=solid tooltip="Start state: C&#10;End state: D&#10;Action: act1()$visits_c_to_d"]
}
""",
    2: r"""digraph {
    label="&#10;&#10;"
    bgcolor="#E7E7E7"
    "." [label="" color="#BBBBBB" fillcolor="#CCCCCC" height=0.2 shape=circle style=filled width=0.2]
    "At calendar page" [label="At calendar page" color="#BBBBBB" fillcolor="#FFFFFF" fontcolor="#333333" fontname=Helvetica fontsize=12 shape=box style="rounded,filled" tooltip="At calendar page"]
    "At calendar page for scheduling" [label="At calendar page for scheduling" color="#BBBBBB" fillcolor="#FFFFFF" fontcolor="#333333" fontname=Helvetica fontsize=12 shape=box style="rounded,filled" tooltip="At calendar page for scheduling"]
    "At help page popup" [label="At help page popup" color="#BBBBBB" fillcolor="#FFFFFF" fontcolor="#333333" fontname=Helvetica fontsize=12 shape=box style="rounded,filled" tooltip="At help page popup"]
    "At login page with errors" [label="At login page with errors" color="#BBBBBB" fillcolor="#FFFFFF" fontcolor="#333333" fontname=Helvetica fontsize=12 shape=box style="rounded,filled" tooltip="At login page with errors"]
    "At login page without errors" [label="At login page without errors" color="#BBBBBB" fillcolor="#FFFFFF" fontcolor="#333333" fontname=Helvetica fontsize=12 shape=box style="rounded,filled" tooltip="At login page without errors"]
    "At organisation settings page" [label="At organisation settings page" color="#BBBBBB" fillcolor="#FFFFFF" fontcolor="#333333" fontname=Helvetica fontsize=12 shape=box style="rounded,filled" tooltip="At organisation settings page"]
    "At release page popup" [label="At release page popup" color="#BBBBBB" fillcolor="#FFFFFF" fontcolor="#333333" fontname=Helvetica fontsize=12 shape=box style="rounded,filled" tooltip="At release page popup"]
    "At who to impersonate page" [label="At who to impersonate page" color="#BBBBBB" fillcolor="#FFFFFF" fontcolor="#333333" fontname=Helvetica fontsize=12 shape=box style="rounded,filled" tooltip="At who to impersonate page"]
    "Enter credentials" [label="Enter credentials" color="#BBBBBB" fillcolor="#FFFFFF" fontcolor="#333333" fontname=Helvetica fontsize=12 shape=box style="rounded,filled" tooltip="Enter credentials"]
    Start [label=Start color="#BBBBBB" fillcolor="#FFFFFF" fontcolor="#333333" fontname=Helvetica fontsize=12 shape=box style="rounded,filled" tooltip=Start]
    "." -> Start [color="#BBBBBB" penwidth=0.75 style=solid]
    Start -> "At login page without errors" [label="open_login_page()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: Start&#10;End state: At login page without errors&#10;Action: open_login_page()"]
    "At login page without errors" -> "Enter credentials" [color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: At login page without errors&#10;End state: Enter credentials"]
    "At login page with errors" -> "Enter credentials" [color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: At login page with errors&#10;End state: Enter credentials"]
    "Enter credentials" -> "At organisation settings page" [label="log_in_as_admin()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: Enter credentials&#10;End state: At organisation settings page&#10;Action: log_in_as_admin()"]
    "Enter credentials" -> "At calendar page for scheduling" [label="log_in_as_global()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: Enter credentials&#10;End state: At calendar page for scheduling&#10;Action: log_in_as_global()"]
    "Enter credentials" -> "At calendar page for scheduling" [label="log_in_as_globaladmin()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: Enter credentials&#10;End state: At calendar page for scheduling&#10;Action: log_in_as_globaladmin()"]
    "Enter credentials" -> "At calendar page" [label="log_in_as_practitioner()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: Enter credentials&#10;End state: At calendar page&#10;Action: log_in_as_practitioner()"]
    "Enter credentials" -> "At who to impersonate page" [label="log_in_as_scheduler()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: Enter credentials&#10;End state: At who to impersonate page&#10;Action: log_in_as_scheduler()"]
    "Enter credentials" -> "At login page with errors" [label="bad_credentials()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: Enter credentials&#10;End state: At login page with errors&#10;Action: bad_credentials()"]
    "Enter credentials" -> "At release page popup" [label="read_release()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: Enter credentials&#10;End state: At release page popup&#10;Action: read_release()"]
    "Enter credentials" -> "At help page popup" [label="login_help()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: Enter credentials&#10;End state: At help page popup&#10;Action: login_help()"]
    "At release page popup" -> "Enter credentials" [label="close_release_page()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: At release page popup&#10;End state: Enter credentials&#10;Action: close_release_page()"]
    "At help page popup" -> "Enter credentials" [label="close_help_page()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: At help page popup&#10;End state: Enter credentials&#10;Action: close_help_page()"]
    "At who to impersonate page" -> "At calendar page for scheduling" [label="select_practitioner()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: At who to impersonate page&#10;End state: At calendar page for scheduling&#10;Action: select_practitioner()"]
    "At calendar page" -> "At calendar page" [label="reload()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: At calendar page&#10;End state: At calendar page&#10;Action: reload()"]
    "At calendar page for scheduling" -> "At calendar page for scheduling" [label="reload()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=dashed tooltip="Start state: At calendar page for scheduling&#10;End state: At calendar page for scheduling&#10;Action: reload()&#10;Condition: i_am_not_a_scheduler()"]
    "At calendar page for scheduling" -> "At who to impersonate page" [label="reload()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=dashed tooltip="Start state: At calendar page for scheduling&#10;End state: At who to impersonate page&#10;Action: reload()&#10;Condition: i_am_a_scheduler()"]
    "At organisation settings page" -> "At organisation settings page" [label="reload()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: At organisation settings page&#10;End state: At organisation settings page&#10;Action: reload()"]
    "At who to impersonate page" -> "At who to impersonate page" [label="reload()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: At who to impersonate page&#10;End state: At who to impersonate page&#10;Action: reload()"]
    "Enter credentials" -> "Enter credentials" [label="reload()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: Enter credentials&#10;End state: Enter credentials&#10;Action: reload()"]
    "At calendar page" -> "At login page without errors" [label="log_out()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: At calendar page&#10;End state: At login page without errors&#10;Action: log_out()"]
    "At calendar page for scheduling" -> "At login page without errors" [label="log_out()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: At calendar page for scheduling&#10;End state: At login page without errors&#10;Action: log_out()"]
    "At organisation settings page" -> "At login page without errors" [label="log_out()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: At organisation settings page&#10;End state: At login page without errors&#10;Action: log_out()"]
    "At who to impersonate page" -> "At login page without errors" [label="log_out()" color="#BBBBBB" fontname="Times New Roman" fontsize=8 penwidth=0.75 style=solid tooltip="Start state: At who to impersonate page&#10;End state: At login page without errors&#10;Action: log_out()"]
}
""",
}

dot_1_defaults = {
    "fillcolor_dot": Color.Grey,
    "fillcolor_a": Color.White,
    "fillcolor_b": Color.White,
    "fillcolor_c": Color.White,
    "fillcolor_d": Color.White,
    "fontcolor_c": Color.Dark,
    "color_dot_to_a": Color.MediumDark,
    "color_a_to_b": Color.MediumDark,
    "color_b_to_c": Color.MediumDark,
    "color_c_to_b": Color.MediumDark,
    "color_c_to_c": Color.MediumDark,
    "color_c_to_d": Color.MediumDark,
    "tooltip_a": "A",
    "tooltip_b": "B",
    "tooltip_c": "C",
    "tooltip_d": "D",
    "penwidth_dot_to_a": "0.75",
    "penwidth_a_to_b": "0.75",
    "penwidth_b_to_c": "0.75",
    "penwidth_c_to_b": "0.75",
    "penwidth_c_to_c": "0.75",
    "penwidth_c_to_d": "0.75",
    "visits_a_to_b": "",
    "visits_b_to_c": "",
    "visits_c_to_b": "",
    "visits_c_to_c": "",
    "visits_c_to_d": "",
}


# TEST CASE 2
ModelCreatorType = Callable[[str], Model]


############
# FIXTURES
#
@pytest.fixture
def model_creator(mocker) -> ModelCreatorType:
    def inner_fn(template: str) -> Model:
        mocker.patch("os.path.exists", return_value=True)
        parser = FileParser()
        mocker.patch("pathlib.Path.read_text", return_value=template)
        return parser.parse("using/template/instead")

    return inner_fn


#########
# TESTS
#
@pytest.mark.parametrize("number", [1, 2])
def test_render__to_digraph_is_digraph(model_creator: ModelCreatorType, number: int):
    digraph = model_creator(templates[number]).to_digraph()
    assert isinstance(digraph, graphviz.Digraph)


@pytest.mark.parametrize("number", [1, 2])
def test_render_session_no_execution(model_creator: ModelCreatorType, number: int):
    model = model_creator(templates[number])
    actual = model.to_dot().replace("\t", "    ").split("\n")
    expected_template = StringTemplate(dots[number])
    expected = expected_template.substitute(dot_1_defaults).split("\n")
    # ASSERT
    for actual_line, expected_line in zip(actual, expected):
        assert actual_line == expected_line


def test_render_session_partial_execution(model_creator: ModelCreatorType):
    # ARRANGE
    model = model_creator(templates[1])

    summary = SessionSummary(model)
    passed = VisitsAndResults()
    failed = VisitsAndResults()
    flaky = VisitsAndResults()
    passed.record_visit(Result.PASSED)
    failed.record_visit(Result.FAILED)
    flaky.record_visit(Result.PASSED)
    flaky.record_visit(Result.FAILED)

    # ACT - Fake execution, store results as if they came from the machine
    summary.results.states.update({"A": passed})
    summary.results.states.update({"B": flaky})
    summary.results.states.update({"C": failed})
    summary.results.actions.update({"act1": flaky})
    summary.results.actions.update({"act2": failed})
    summary.results.transitions.update({"A:None:None:B": passed})
    summary.results.transitions.update({"B:None:act1:C": flaky})
    summary.results.transitions.update({"C:cond1:act2:B": failed})

    tooltip_a = '"A&#10;&#10;PASSED&#10;Visit count: 1"'
    tooltip_b = '"B&#10;&#10;FLAKY&#10;Passed count: 1&#10;Failed count: 1"'
    tooltip_c = '"C&#10;&#10;FAILED&#10;Visit count: 1"'

    actual = model.to_dot(summary).replace("\t", "    ").split("\n")

    # ASSERT
    updated_template = copy.deepcopy(dot_1_defaults)  # Do not modify the original
    updated_template.update(
        {
            "fillcolor_a": Color.Green,
            "fillcolor_b": Color.Orange,
            "fillcolor_c": Color.Red,
            "fontcolor_c": Color.Light,
            "tooltip_a": tooltip_a,
            "tooltip_b": tooltip_b,
            "tooltip_c": tooltip_c,
            "penwidth_dot_to_a": "2",
            "penwidth_a_to_b": "2",
            "penwidth_b_to_c": "2",
            "penwidth_c_to_b": "2",
            "color_dot_to_a": Color.Green,
            "color_a_to_b": Color.Green,
            "color_b_to_c": Color.Orange,
            "color_c_to_b": Color.Red,
            "visits_a_to_b": "&#10;&#10;PASSED&#10;Visit count: 1",
            "visits_b_to_c": "&#10;&#10;FLAKY&#10;Passed count: 1&#10;Failed count: 1",
            "visits_c_to_b": "&#10;&#10;FAILED&#10;Visit count: 1",
        }
    )

    expected = StringTemplate(dots[1]).substitute(updated_template).split("\n")

    for actual_line, expected_line in zip(actual, expected):
        assert actual_line == expected_line
