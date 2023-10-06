"""Test that colors are set correctly depending on execution results"""
from app.fsm.results import Result, VisitsAndResults
from app.fsm.model import Model, Color

# pylint: disable=protected-access


get_result_color = Model._get_result_color


def test_color_should_be_green():
    # ARRANGE
    results_pass_single1 = VisitsAndResults()
    results_pass_single1._results.append(Result.PASSED)
    results_pass_single2 = VisitsAndResults()
    results_pass_single2._results.append(Result.NOT_APPLICABLE)
    results_pass_multi1 = VisitsAndResults()
    results_pass_multi1._results.append(Result.PASSED)
    results_pass_multi1._results.append(Result.PASSED)
    results_pass_multi2 = VisitsAndResults()
    results_pass_multi2._results.append(Result.NOT_APPLICABLE)
    results_pass_multi2._results.append(Result.PASSED)

    # ACT
    color_single1 = get_result_color(results_pass_single1)
    color_single2 = get_result_color(results_pass_single2)
    color_multi1 = get_result_color(results_pass_multi1)
    color_multi2 = get_result_color(results_pass_multi2)

    # ASSERT
    assert color_single1 == Color.Green
    assert color_single2 == Color.Green
    assert color_multi1 == Color.Green
    assert color_multi2 == Color.Green


def test_color_should_be_red():
    # ARRANGE
    results_fail_single = VisitsAndResults()
    results_fail_single._results.append(Result.FAILED)
    results_fail_multi1 = VisitsAndResults()
    results_fail_multi1._results.append(Result.FAILED)
    results_fail_multi1._results.append(Result.FAILED)
    results_fail_multi2 = VisitsAndResults()
    results_fail_multi2._results.append(Result.NOT_APPLICABLE)
    results_fail_multi2._results.append(Result.FAILED)

    # ACT
    color_single = get_result_color(results_fail_single)
    color_multi1 = get_result_color(results_fail_multi1)
    color_multi2 = get_result_color(results_fail_multi2)

    # ASSERT
    assert color_single == Color.Red
    assert color_multi1 == Color.Red
    assert color_multi2 == Color.Red


def test_color_should_be_orange():
    # ARRANGE
    results_flaky1 = VisitsAndResults()
    results_flaky1._results.append(Result.PASSED)
    results_flaky1._results.append(Result.FAILED)
    results_flaky2 = VisitsAndResults()
    results_flaky2._results.append(Result.NOT_APPLICABLE)
    results_flaky2._results.append(Result.PASSED)
    results_flaky2._results.append(Result.FAILED)

    # ACT
    color_flaky1 = get_result_color(results_flaky1)
    color_flaky2 = get_result_color(results_flaky2)

    # ASSERT
    assert color_flaky1 == Color.Orange
    assert color_flaky2 == Color.Orange


def test_color_should_be_grey():
    # ARRANGE
    results = VisitsAndResults()
    # ACT
    color = get_result_color(results)

    # ASSERT
    assert color == Color.MediumDark
