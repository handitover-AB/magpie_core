"""Condition functions for ToDo consumer actor"""
from app import Page


def _is_on_list(page: Page, item_text: str) -> bool:
    page.reload()
    selector = "ul.todo-list > li:not(.completed) > div.view"
    list_items = page.query_selector(selector, strict=False)
    if list_items is None:
        return False
    if not isinstance(list_items, list):
        list_items = [list_items]
    for list_item in list_items:
        if list_item.query_selector("label").inner_text() == item_text:
            return True
    return False


def buy_apples_is_on_list(page: Page) -> bool:
    return _is_on_list(page, "Buy apples")


def get_sara_at_school_is_on_list(page: Page) -> bool:
    return _is_on_list(page, "Get Sara at school")


def call_workshop_is_on_list(page: Page) -> bool:
    return _is_on_list(page, "Call the workshop about the car")
