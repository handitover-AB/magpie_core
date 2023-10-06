"""ToDo consumer action functions"""
from playwright.sync_api import Locator, expect

from app import Page

HOST = "localhost:8000"


########
# UTIL
#
def _complete_item(page: Page, item: str) -> None:
    """Mark provided item as completed"""
    list_items = page.locator("ul.todo-list > li > div.view")
    list_item: Locator = list_items.filter(has=page.locator("label", has_text=item))
    checkbox = list_item.locator("input.toggle")
    if not checkbox.is_checked():
        checkbox.click()
    expect(checkbox).to_be_checked()


###########
# ACTIONS
#
def open_start_page(page: Page):
    page.goto(f"http://{HOST}", wait_until="domcontentloaded")


def buy_apples(page: Page):
    page.reload()
    _complete_item(page, "Buy apples")


def get_sara(page: Page):
    page.reload()
    _complete_item(page, "Get Sara at school")


def call_workshop(page: Page):
    page.reload()
    _complete_item(page, "Call the workshop about the car")
