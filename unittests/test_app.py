"""Test Magpie run options and setup"""
import logging

from app import Strategy, LOGGER
from app.properties import running_in_docker


def test_running_in_docker_0(mocker):
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("os.path.isfile", return_value=False)
    mocker.patch("builtins.open", return_value=[])

    assert running_in_docker() is False


def test_running_in_docker_1(mocker):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.path.isfile", return_value=False)
    mocker.patch("builtins.open", return_value=[])

    assert running_in_docker() is True


def test_running_in_docker_2(mocker):
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("os.path.isfile", return_value=True)
    mocker.patch("builtins.open", return_value=["docker"])

    assert running_in_docker() is True


def test_strategy_options_exist():
    assert Strategy.HappyPath
    assert Strategy.FullCoverage
    assert Strategy.Random
    assert Strategy.PureRandom
    assert Strategy.SmartRandom


def test_logger():
    assert isinstance(LOGGER, logging.Logger)
