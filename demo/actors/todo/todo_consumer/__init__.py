"""Main module of the ToDo consumer actor"""
from app import LOGGER

from . import actions, states, conditions


def setup(_):
    LOGGER.info(
        "Hi from the consumer's setup function 👋. It doesn't "
        "do anything but add an entry in the log "
        "for demonstration purpose."
    )


def teardown(_):
    LOGGER.info(
        "Hi from the consumer's teardown function 👋. It doesn't "
        "do anything but add an entry in the log "
        "for demonstration purpose."
    )
