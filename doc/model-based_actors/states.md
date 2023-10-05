<img src="../../media/images/magpie.svg" width="128px" />

<br />

# States

Each state of a model represents a unique condition in the *application under test*. A state can be associated with a function containing a set of assertions that should be run whenever the application under test enters it.

States are implemented in the `states.py` file in a model-based actor:

    model_based_actor_module/
    ├── __init__.py
    ├── model
    ├── actions.py
    ├── states.py        <-- Here!
    └── conditions.py

State functions should have a snake case representation of the corresponding name from the model.

In the model file:

    A state    ->    Another state

will on entering each state try to call the functions `a_state` and `another_state`, respectively, in the `states.py` file of the actor, i.e:

    """states.py""

    def a_state():
        # do something here

    def another_state():
        # do something here


<br>

### Naming

Each state has to have a good, descriptive name. The name should reflect some property of the anticipated state the application under test will be in, so that it can be idetified easier in logs and test results.

<br>

### State Design

This is where you should put your [test oracles](https://en.wikipedia.org/wiki/Test_oracle), i.e. the principle you use to determine whether your application behaves correctly or not.

Some examples of instructions to put in a *state function* if you are testing web applications:

* assert that the **url/title is correct** (if applicable)
* assert that relevant **database state/contents** is correct
* assert **visibility and state of all elements** you expect to exist (texts, buttons, checkboxes, ...)
* ...and more, keep your imagination going 🙂

<br>


### Make the test fail if something does not behave as expected


Use the `expect()` method and its descendants to create a check that fails on certain conditions.
The check should be written so that it is True when everything is OK, in the form `page.expect(<some_value>).<some_expected_condition>`

Example (web):

    from app import Page, expect

    def a_state_with_a_descriptive_name(page: Page):
        login_text = page.locator("#login_button").text_content()
        expect(login_text).contains("Log in")
        expect(app_page.url).contains("/articles")


<br>

## More on web testing

Read more [here](../web_testing.md) on how to do good web testing