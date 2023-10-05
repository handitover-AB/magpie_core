"""Main module of the ToDo producer actor"""
from app import LOGGER

from . import actions, states, conditions


def setup(_):
    LOGGER.info(
        "Hi from the producer's setup function 👋. It doesn't "
        "do anything but add an entry in the log "
        "for demonstration purpose."
    )


def teardown(_):
    LOGGER.info(
        "Hi from the producer's teardown function 👋. It doesn't "
        "do anything but add an entry in the log "
        "for demonstration purpose."
    )
