"""Unit test fixtures"""
import pytest


@pytest.fixture(scope="module")
def mock_actor_module(module_mocker):
    class MockModelBasedActor:
        __name__ = "dummy"
        __file__ = "dummy.py"

    model = "Start  ->  End"
    _actor = MockModelBasedActor()
    # Fake that the model file exists and that the model
    # file contains the contents of the model variable:
    module_mocker.patch("os.path.exists", return_value=True)
    module_mocker.patch("pathlib.Path.read_text", return_value=model)
    return _actor
