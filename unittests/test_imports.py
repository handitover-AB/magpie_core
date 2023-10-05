"""Test that imports do not raise any exceptions for Finite State Machine"""


def test_import_files():
    import app.fsm  # pylint: disable=import-outside-toplevel

    assert app.fsm is not None
