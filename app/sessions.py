"""Implement logic for sessions

A session is related to an actor and can start its
execution on request. A session is executed in its
own thread and may or may not have a browser session
associated with the actor.

There is a possibility of running a setup function
before start of the actor execution. After the actor
has finished, there is a possibility of running a
teardown function.
"""
from __future__ import annotations

import os
import re
import sys
import traceback

from fnmatch import fnmatch
from pathlib import Path
from threading import Thread
from time import sleep
from typing import List, Callable, Optional, Dict, Any
from types import ModuleType

from assertpy import assert_that
from playwright.sync_api import (
    sync_playwright,
    APIResponse,
    BrowserContext,
    Response,
    Request,
    Route,
    Page as PlaywrightPage,
)

from app import LOGGER, Strategy, EVENT_STORE, OUTPUTDIR, expect
from app.actor import Actor
from app.pause_manager import pauseall
from app.fsm.model_based_actor import ModelBasedActor
from app.fsm.machine import Machine, RunOptions


def on_response(page: PlaywrightPage) -> Callable:
    """Register callback function that executes if the url matches the url_mask.

    The callback function should take two parameters (page and response) and return nothing.
    """
    callback_functions = {}

    def inner(url_mask: str, func: Callable[[PlaywrightPage, Response], None]) -> None:
        """Register callback functions on url masks"""
        callback_functions[url_mask] = func

    def handler(response: Response):
        """Handle response events and invoke callback functions"""
        for url_mask, func in callback_functions.items():
            if fnmatch(response.url, url_mask):
                func(page, response)

    # Register the container function on response events:
    page.on("response", handler)
    return inner


def mock_route(page: PlaywrightPage) -> Callable:
    """Make it possible to mock responses for HTTP requests.

    Implement a closure function for the actual mock function.
    """

    def inner(
        url_mask: str,
        *,
        status: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str | bytes] = None,
        json: Optional[Any] = None,
        path: Optional[str | Path] = None,
        content_type: Optional[str] = None,
        response: Optional[APIResponse] = None,
    ):
        def route_handler(route: Route, request: Request):
            LOGGER.info("[i] Magpie mocked http request: %s %s", request.method, request.url)
            route.fulfill(
                status=status,
                headers=headers,
                body=body,
                json=json,
                path=path,
                content_type=content_type,
                response=response,
            )

        page.context.route(url_mask, route_handler)

    return inner


class SessionConfigurationError(Exception):
    """Raise when there is a problem with the session configuraion"""


class SessionExecutionFailure(Exception):
    """Raise when a session has failures"""


class Session:  # pylint:disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        name: str,
        actor: Actor = None,
        actor_module: ModuleType = None,
        browser: str = "",
        strategy: Strategy = Strategy.SmartRandom,
        max_transitions: int = -1,
        max_run_time_s: int = -1,
        stop_on_fail: bool = False,
        tags: List[str] | None = None,
        stop_at_state: str | None = None,
        retain_trace_file: bool = False,
        device: str | None = None,
    ) -> None:
        # pragma pylint: disable=line-too-long
        """Define a session

        A session gives an actor a context in which to run.

        Args:
            name (str): The name of the session. Identifies it in logs etc.
            actor (Actor): The Python actor instance that should be used
            actor_module (ModuleType): The Python actor module that should be used (if *actor* is not specified)
            browser (str): The name of the browser to use: chrome, firefox or webkit. Empty string means no browser.
            strategy (Strategy): The strategy to use for navigation through the actor's model
            max_transitions (int): [optional] if specified, stop after this number of transitions
            max_run_time_s (int): [optional] if specified, stop after this number of seconds
            stop_on_fail (bool): [optional] if True, stop on the first error detected.
            tags (List[str]): [optional] if specified, add tags to the run data that may be used in result analysis
            stop_at_state (str): [optional] if specified, stop session at the state with this name
            retain_trace_file (bool): [optional] if True, always keep the recoded trace file (for sessions with browsers)
            device (str): [optional] name of device to emulate, see this list: https://github.com/microsoft/playwright/blob/main/packages/playwright-core/src/server/deviceDescriptorsSource.json
        """
        # Guard clauses - check data integrity
        for character in r"/\|*%?":
            if character in name:
                err_msg = f"{character} is not allowed in names. Please rename `{name}`"
                raise NameError(err_msg)
        # pragma pylint: enable=line-too-long
        self.name: str = name
        self.browser: str | None = browser
        self.tags: List[str] = tags
        self.retain_trace_file: bool = retain_trace_file
        self.device: str | None = device
        self._has_generic_failure: bool = False

        # If not supplied, assume actor is a model-based one for now (add more types later):
        self.actor: Actor = actor or ModelBasedActor(actor_module=actor_module)
        self.actor.name = name

        # Guard clause:
        if strategy == Strategy.ShortestPath and not stop_at_state:
            raise SessionConfigurationError(
                f"Session {name}: "
                "In order to be able to use the strategy ShortestPath, you must "
                "set`stop_at_state` to the name of the expected end state."
            )

        # OK, proceed:
        self.run_options = RunOptions(
            max_run_time_s, max_transitions, stop_on_fail, stop_at_state, strategy
        )
        self.machine = Machine(self.actor, **self.run_options.as_dict())

    def record_generic_failure(self):
        self._has_generic_failure = True

    def setup(self):
        """Run setup functions"""
        if hasattr(self.actor, "setup") and callable(self.actor.setup):
            LOGGER.info("Initiating setup")
            args = []
            if self.machine.has_browser:
                # TODO: support non model-based actors
                args = [self.machine.browser_page]
            self.actor.setup(*args)

    def start(self):
        self.machine.start()

    def teardown(self):
        """Run teardown functions"""
        if hasattr(self.actor, "teardown") and callable(self.actor.teardown):
            LOGGER.info("Initiating teardown")
            args = []
            if self.machine.has_browser:
                # TODO: support non model-based actors
                args = [self.machine.browser_page]
            self.actor.teardown(*args)

    @property
    def has_failures(self) -> bool:
        if self.machine:
            summary = self.machine.summary
            if summary.failed_actions or summary.flaky_actions:
                return True
            if summary.failed_states or summary.flaky_states:
                return True
            if summary.failed_transitions or summary.flaky_transitions:
                return True
        if self._has_generic_failure:
            return True
        return False

    @property
    def name_lowercase(self):
        return re.sub(r"[^a-z0-9_]", "", self.name.lower().replace(" ", "_"))


def start_session(
    session: Session, headless: bool = False
):  # pylint: disable=too-many-locals, too-many-statements
    """Runs a session. Returns False on failure, True otherwise."""
    session_data = dict()
    has_browser = session.browser

    LOGGER.info("STARTING SESSION %s", session.name)
    if session.tags:
        LOGGER.info("SESSION TAGS: %s", ", ".join(session.tags))

    # Has browser and model:
    if has_browser:
        with sync_playwright() as playwright:
            # Browser:
            browser = playwright[session.browser].launch(headless=headless)
            device_kwargs = {}
            if session.device:
                device_kwargs = playwright.devices[session.device]
            context = browser.new_context(**device_kwargs)
            page: PlaywrightPage = context.new_page()
            user_agent = page.evaluate("() => navigator.userAgent")
            LOGGER.info("Using browser: %s", user_agent)
            # Timeouts:
            default_timeout = int(os.environ.get("MAGPIE_TIMEOUT", 5000))
            context.set_default_navigation_timeout(timeout=default_timeout)
            page.set_default_navigation_timeout(timeout=default_timeout)
            context.set_default_timeout(timeout=default_timeout)
            page.set_default_timeout(timeout=default_timeout)
            expect.set_options(timeout=default_timeout)  # pylint: disable=no-member
            LOGGER.info("Using timeout value %s ms", default_timeout)
            # 🐵 MONKEY PATCHING
            #   Patch the PlaywrightPage object with the assert_that method
            #   so that the interface of the class is equal to that of the class
            #   which we defined: app.page.Page()
            page.assert_that = assert_that
            #   Patch the PlaywrightPage object with the sleep function
            page.sleep = sleep
            #   Patch the PlaywrightPage object with a data storage object:
            page.data = session_data
            page.mock_route = mock_route(page)
            page.mock_route.__doc__ = mock_route.__doc__
            page.register_on_response_callback = on_response(page)
            page.pauseall = lambda: pauseall(page)
            page.pauseall.__doc__ = pauseall.__doc__
            #   Set default timeout:
            session.machine.browser_page = page
            session_aborted = False

            context.tracing.start(screenshots=True, snapshots=True, sources=True)

            try:
                session.setup()
                session.start()
            except KeyboardInterrupt as exc:
                LOGGER.info("✋ Session aborted by user!")
                try:
                    page._loop.close()  # pylint: disable=protected-access
                except RuntimeError:
                    LOGGER.warning(
                        "Force-closed the IOLoop. Unfinished tasks were also force-quitted."
                    )
                raise KeyboardInterrupt from exc
            except Exception as exc:  # pylint: disable=broad-except
                session.record_generic_failure()
                session.machine.error_msg = f"❌ Execution failed! Error message:\n{exc}"
                LOGGER.error("❌ OOPS! %s has failed 🤔! Error message: %s", session.name, exc)
                _, _, trace = sys.exc_info()
                LOGGER.error(exc.with_traceback(trace))
                LOGGER.error(traceback.format_exc())
            finally:
                save_file: bool = False
                if session.has_failures or session.retain_trace_file:
                    save_file = True
                _stop_tracing(session, context, save_file=save_file)

            session.teardown()

            if session_aborted:
                # Force-quit the running asyncio loop:
                page._loop.close()  # pylint: disable=protected-access
            else:
                page.close()

    LOGGER.info('"%s": 🏁 Stopping session', session.machine.current_state.name)


def _stop_tracing(session: Session, context: BrowserContext, save_file: bool = False):
    if save_file:
        outputdir = Path(OUTPUTDIR)
        trace_file_path = outputdir / "trace" / f"trace_{session.name_lowercase}.zip"
        context.tracing.stop(path=trace_file_path)
        LOGGER.info("Saved trace file: %s", trace_file_path)
        LOGGER.info("View the trace file using this command:")
        LOGGER.info("  playwright show-trace %s", trace_file_path)
    else:
        context.tracing.stop()


def start_sessions(sessions: List[Session], headless: bool = False) -> None:
    """Run each session in a new thread until all threads are finished."""
    threads: List[Thread] = []

    if len(sessions) == 1:
        # Run on main thread if only one session.
        session = sessions[0]
        start_session(session, headless)

    elif len(sessions) > 1:
        # Run each session in a separate thread.
        for session in sessions:
            thread = Thread(
                target=start_session,
                args=(session, headless),
                daemon=True,
                name=session.name,
            )
            threads.append(thread)

        for thread in threads:
            thread.start()

        # Wait for execution to finish:
        try:
            for thread in threads:
                LOGGER.info("Waiting for thread `%s` to finish.", thread.name)
                thread.join()
        except KeyboardInterrupt:
            LOGGER.info("User pressed CTRL+C. Stopping all threads...")

    # Save event store:
    event_store_file = str(Path(OUTPUTDIR) / "event_store.csv")
    with open(event_store_file, "w") as log:
        log.write("Timestamp,Name,Data\n")
        for event in EVENT_STORE:
            log.write(f"{event}\n")

    LOGGER.info("Nothing to do, I think I'll stop now...")
