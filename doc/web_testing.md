<img src="../media/images/magpie.svg" width="128px" />

<br />


# Web testing - good practices

Web testing is an art in itself. Below are a few tips for how to do some common operations. Read more [here](https://playwright.dev/python/docs/api/class-locator)

<br>

### Waiting for an element

Use `page.wait_for_selector(LOCATOR)` where LOCATOR is a string constant containing a reference to the DOM object you want to check. For more information on locators, look [here](https://playwright.dev/python/docs/locators).

<table><tr><td style="padding: 1em;">
⚠️ <i>IMPORTANT: Locators should be robust! Base your locators on properties that won't be affected if other parts of the page changes.<br>
Some tips can be found on <a href="https://www.checklyhq.com/learn/headless/basics-selectors/">this page</a></i>
</td></tr></table>

Furthermore, it is good practice to assign locator strings to constants with good names for increased reusability within/between your scripts.


Example:

    StartPage__OK_BUTTON = "submit[text='Send']"
    [...]
    page.locator(StartPage__OK_BUTTON).click()

<br>

### Checking properties of an element

First, wait for the element, see previous section.

If the element exists, it will be returned from the `wait_for_selector()` function. In order to check properties of the element, assign a variable to the result of the waiting operation and use that for further processing:

    ok_button_text = page.wait_for_selector(StartPage__OK_BUTTON).text_content()
    page.expect(ok_button_text).is_equal_to("OK")

There is a good guide on what is possible to do with a DOM element, once you have looked it up using a locator. See [this page](https://playwright.dev/python/docs/api/class-locator) for more information.