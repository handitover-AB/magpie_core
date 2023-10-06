"""Main module for the Magpie application"""
import os
import sys
import threading

from functools import wraps
from pathlib import Path
from typing import Callable
from playwright.sync_api import Response as HttpResponse

from app.expect_mod import expect as expect_mod
from app.eventstore import TSEventStore
from app.fsm.execution_options import Strategy
from app.page import Page
from app import custom_errors
from app.logger import LOGGER  # Expose global logger


###################
# EXECUTION PATHS
#
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)


###########
# GLOBALS
#

# Create global thread-safe event store:
EVENT_STORE = TSEventStore()

# Set output directory:
default_output_path = Path(".") / "output"
OUTPUTDIR_PATH = Path(os.environ.get("OUTPUTDIR", default_output_path))
if not OUTPUTDIR_PATH.exists():
    OUTPUTDIR_PATH.mkdir()
OUTPUTDIR = str(OUTPUTDIR_PATH)


########################
# MODIFY EXPECT OBJECT
#
expect = expect_mod


########################
# PARALLELLISM CONTROL
#
# Create a global lock object, for thread synchronization:
THREAD_LOCK: threading.Lock = threading.Lock()


##############
# DECORATORS
#
def retry_with_reload(times: int):
    """To be used on functions allowed to fail a number of times before failing the test

    With this decorator the page is reloaded if a check fails.
    """

    def decorator(fn: Callable[[Page], None]):
        @wraps(fn)
        def wrapper(page: Page):
            for _ in range(times):
                try:
                    fn(page)
                    break
                except AssertionError as exc:
                    LOGGER.warning("RETRYING: Reloading page. Check(s) failed: %s", str(exc))
                    page.reload()
                    page.wait_for_load_state("networkidle")

        return wrapper

    return decorator
