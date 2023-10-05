"""Common state functions"""
from app import Page


def at_todo_page(page: Page):
    page.wait_for_url("/todo")
