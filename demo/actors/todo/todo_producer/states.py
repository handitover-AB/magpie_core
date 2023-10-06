"""State functions for the ToDo producer actor"""

from app import Page, expect


def at_todo_page(page: Page):
    header = page.locator("header h1")
    new_item_field = page.locator("input.new-todo")
    placeholder = page.locator("input.new-todo").get_attribute("placeholder")

    expect(page).to_have_title("Redux TodoMVC Example")

    # Check heading
    expect(header).to_have_text("todos")
    expect(header).to_be_visible()

    expect(new_item_field).to_be_visible()
    expect(new_item_field).to_be_enabled()

    # Check input field properties
    assert (
        placeholder == "What needs to be done?"
    )  # Need to overload expect with str and number support
