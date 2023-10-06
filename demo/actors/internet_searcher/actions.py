"""Implement actions for internet search test"""
from app import Page


def do_new_search(page: Page):
    input_field = page.locator('input[name="q"]')
    input_field.click()
    input_field.fill("Magpie")
    with page.expect_navigation():
        input_field.press("Enter")


def do_nothing(page: Page):
    page.sleep(1)


def open_search_page(page: Page):
    page.goto("https://start.duckduckgo.com")
    page.wait_for_load_state()


def reload_page(page: Page):
    page.reload()
