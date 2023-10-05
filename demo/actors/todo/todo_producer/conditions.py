"""Condition finctions for ToDo consumer actor"""

from app import Page


def _is_not_on_list(page: Page, item: str) -> bool:
    there_are_items = page.query_selector("ul.todo-list li", strict=False)
    if there_are_items:
        items = page.query_selector_all("ul.todo-list li label")
        return item not in [i.inner_text() for i in items]
    return True


def buy_apples_is_not_on_list(page: Page) -> bool:
    return _is_not_on_list(page, "Buy apples")


def get_sara_at_school_is_not_on_list(page: Page) -> bool:
    return _is_not_on_list(page, "Get Sara at school")


def call_workshop_is_not_on_list(page: Page) -> bool:
    return _is_not_on_list(page, "Call the workshop about the car")
