"""Allow all actor threads to be paused and resumed from any actor."""
from threading import Event

from app import LOGGER
from app.page import Page


_PAUSEALL = Event()


def pauseall(page: Page = None):
    """Pause script execution for all actors.

    Resume execution by calling page.resumeall()
    """
    LOGGER.info("pauseall() requested")
    _PAUSEALL.set()
    if page:
        page.pause()
        resumeall()


def resumeall():
    """Resume script execution for all actors."""
    LOGGER.info("resumeall() requested")
    _PAUSEALL.clear()


def is_paused() -> bool:
    """Return True if pause is set, False otherwise."""
    return _PAUSEALL.is_set()
