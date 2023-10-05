"""This module offers a modified expect function for use with Magpie.

The main differences are:
* Overload expect for arbirtary expressions that are
  not Playwright data types. Keep the Playwright assertions for
  Playwright data types (e.g. locators etc) and use assert_that
  assertions on other data types.
* Provide a mechanism for overriding the default assertion timeouts
"""
from __future__ import annotations

import inspect

from typing import Dict, List, Union, Optional

from assertpy import assert_that
from assertpy.assertpy import AssertionBuilder
from playwright._impl._assertions import APIResponseAssertions as APIResponseAssertionsImpl
from playwright._impl._assertions import LocatorAssertions as LocatorAssertionsImpl
from playwright._impl._assertions import PageAssertions as PageAssertionsImpl
from playwright.sync_api import Expect
from playwright.sync_api import Page
from playwright.sync_api._generated import (
    APIResponse,
    APIResponseAssertions,
    Locator,
    LocatorAssertions,
    PageAssertions,
)


from app.logger import LOGGER


# pylint: disable=protected-access

OtherTypes = Union[int, str, bool, float, Dict, List]


class ExpectMod(Expect):
    def __call__(
        self, actual: Union[Page, Locator, APIResponse, OtherTypes], message: Optional[str] = ""
    ) -> Union[PageAssertions, LocatorAssertions, APIResponseAssertions, AssertionBuilder]:
        frame = inspect.stack()[1]
        code_context = frame.code_context[0].lstrip(" ").rstrip("\n")
        file_name = "tests" + frame.filename.split("tests")[-1]
        enclosing_fn_name = inspect.currentframe().f_back.f_code.co_name
        line_no = frame.lineno
        LOGGER.info(
            "  👀  %s    [File: %s, line %s, %s()]",
            code_context,
            file_name,
            line_no,
            enclosing_fn_name,
        )

        if isinstance(actual, Page):
            return PageAssertions(
                PageAssertionsImpl(actual._impl_obj, self._timeout, message=message)
            )
        if isinstance(actual, Locator):
            return LocatorAssertions(
                LocatorAssertionsImpl(actual._impl_obj, self._timeout, message=message)
            )
        if isinstance(actual, APIResponse):
            return APIResponseAssertions(
                APIResponseAssertionsImpl(actual._impl_obj, self._timeout, message=message)
            )
        if isinstance(actual, OtherTypes):
            # Return an AssertionBuilder object with methods possible to use for assertions:
            return assert_that(actual, description=message)
        raise ValueError(f"Unsupported type: {type(actual)}")


expect = ExpectMod()
