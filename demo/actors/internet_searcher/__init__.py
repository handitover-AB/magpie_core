"""Main module of the Maggie actor"""
from app import LOGGER

from . import actions, states


def setup(_):
    LOGGER.info(
        "Hi from Maggie's setup function 👋. It doesn't "
        "do anything but add an entry in the log "
        "for demonstration purpose."
    )


def teardown(_):
    LOGGER.info(
        "Hi from Maggie's teardown function 👋. It doesn't "
        "do anything but add an entry in the log "
        "for demonstration purpose."
    )
