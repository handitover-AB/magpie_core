"""Implement a shadow of the PlaywrightPage class, for VSCode Intellisense"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Callable

from assertpy.assertpy import AssertionBuilder
from playwright.sync_api import APIResponse, Response
from playwright.sync_api import Page as PlaywrightPage

# Expose `expect` in the page namespace:
from playwright.sync_api import expect  # pylint: disable=unused-import


class Page(PlaywrightPage):
    """Add the assert_that method to the Page class

    N.B: This code is used to get the appropriate intellisense
    functionality to work in the VSCode editor.

    These are *not* the methods that are called in run time!

    The assert_that method has to be monkey-patched onto the
    page object used in run time; see the start_session() method
    in the sessions module.

    See the magpie_core/app/sessions.py file.
    """

    @staticmethod
    def assert_that(*args, **kwargs) -> AssertionBuilder:
        """Add assert_that library"""

    @staticmethod
    def sleep(time_s: float) -> None:
        """Sleeps for time_s seconds"""

    @staticmethod
    def pauseall() -> None:
        """Pauses script execution for all actors.

        For sessions without browsers, you will have to call the resumeall() function
        to resume execution.

        For sessions with browsers, Playwright will stop executing the script and wait
        for the user to either press 'Resume' button in the page overlay or to call
        `playwright.resume()` in the DevTools console.

        User can inspect selectors or perform manual steps while paused. Resume will continue
        running the original script from the place it was paused.

        **NOTE** This method requires Playwright to be started in a headed mode, with a
        falsy `headless` value in the `browser_type.launch()`.
        """

    @staticmethod
    def resumeall() -> None:
        """Resume script execution for all actors."""

    @staticmethod
    def mock_route(
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
        """Make it possible to mock responses for HTTP requests."""

    @staticmethod
    def register_on_response_callback(url_mask: str, callback_fn: Callable[[Page, Response], None]):
        """Register callback function that executes if the url matches the url_mask.

        The callback function should take two parameters (page and response) and return nothing.

        Example:
            def exciting_data_handler(page: Page, response: Response):
                page.data["EXCITING_DATA"] = response.json()

            page.on_response("**/api/ExcitingDataApi",exciting_data_handler)
        """
