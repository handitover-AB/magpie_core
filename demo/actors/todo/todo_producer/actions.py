"""ToDo producer action functions"""
from app import Page

HOST = "localhost:8000"


########
# UTIL
#
def _add_item(page: Page, item: str):
    input_field = page.wait_for_selector("input.new-todo")
    input_field.type(item)
    input_field.press("Enter")


###########
# ACTIONS
#
def open_start_page(page: Page):
    page.goto(f"http://{HOST}", wait_until="domcontentloaded")


def add_apples(page: Page):
    page.reload()
    _add_item(page, "Buy apples")


def add_get_sara(page: Page):
    page.reload()
    _add_item(page, "Get Sara at school")


def add_call_workshop(page: Page):
    page.reload()
    _add_item(page, "Call the workshop about the car")
