<img src="../media/images/magpie.svg" width="128px" />

<br />

# My first Magpie test

Let's create a simple web test that opens a ToDo application, adds an item to the list and asserts that some expected information can be found in the list.

Note for Windows users: throughout this document, Linux-style paths with forward-slash (`/`) are used. In Windows, these are back-slashes instead (`\`), so you have to use your imagination to see those instead. 

<br>

### Where to put your tests

Begin by creating a folder for your tests. Put in on the same level as the magpie_core folder.

    parent_folder_where_you_want_to_keep_magpie_core/
    ├── magpie_core    <-- All Magpie files here
    └── tests          <-- This is where your tests go

<br>

### The test file

In your `tests` folder, create a **test file**:

    tests/
    └── my_first_test.py


The test file will eventually act as an entrypoint for your test.

<br>

### Adding a session

We need to add a [Session](sessions.md) to the test file in order to run anything.

Add this to `tests/my_first_test.py`:

    """ My first test"""

    from app.sessions import Session

    my_session = Session(name="My first session")


<br>

### Trying the test file out

In order to run the test file (from the parent folder), your Python interpreter need to know where the subfolders to magpie_core are and where you put your `tests/` folder. You do that by setting the PYTHONPATH environment variable. Assuming you followed the guide above, you now have this structure:

    parent_directory/
    ├── magpie_core
    └── tests

To run the test from the parent directory, you may set the variable according to the instruction below. `.` refers to the current directory, i.e. where you put both `magpie_core` and `tests`. `magpie_core` refers to all subfolders inside it, so it will be possible to e.g. do this: `from app import Page`.

    # On Mac/Linux etc, in bash:
    export PYTHONPATH=.:magpie_core

    # On Windows, in the command prompt (cmd.exe):
    set PYTHONPATH=.:magpie_core

In some cases, you may create a `.env` file in the parent directory (i.e. `parent_directory/.env`) with this content:

    PYTHONPATH=.:magpie_core

If the latter works for you, you don't have to do the `export` or the `set` instruction above.

Now, you are ready to try it out:

    python magpie_core/main.py run tests/my_first_test.py

Oops, there is (should be) an error:
    
    File "/Users/david/opensource/magpie_core/app/fsm/model_based_actor.py", line 39, in __init__
        raise AttributeError("No actor was defined!")
    AttributeError: No actor was defined!

This is because we did not supply an [actor](actors.md) to the session. Let's create one:

<br>

### Creating an actor

OK, let's create a model-based actor. In your `tests/` folder, create a sub-folder called `actors`. In the `actor`` folder, create a sub-folder with the name of your actor module. You should now have a structure like this:

    tests/
    └── actors/
        ├── my_first_actor
        ├── __init__.py
        └── my_first_test.py

In the `__init__.py` file, add this:

    from . import my_first_actor

Save the file.

Now go ahead and create a few empty files:

    tests/
    └── actors/
        ├── my_first_actor/
        │   ├── __init__.py      <-- this one
        │   ├── model            <-- this one
        │   ├── actions.py       <-- this one
        │   ├── states.py        <-- this one
        │   └── conditions.py    <-- this one
        ├── __init__.py
        └── my_first_test.py

<br>

### Building the model

Now, it is time to start thinking about what you want your actor to do. The model is intended to replicate what you want to test, not exactly what the application under test does.

Let's examine the application. Open the **ToDo application**: https://todomvc.com/examples/react/ and play around with it for a little while.

So, let's think of a test case. What are the states of that case? Maybe these could do for now?

 * **Start**                       <-- initial state, just acts as a starting point
 * **At empty todo page**          <-- something should happen to get us here. We should do some checks!
 * **At todo page with one item**  <-- something else should happen to get us here. We should do some checks!

So, let's build a model of this test. In the `model` file, add the names of the states and the transitions that connect them:

    Start                 ->    At empty todo page
    At empty todo page    ->    At todo page with one item

It is now time to figure out **how** to move from one state to another. Let's expand the model with names of **actions** we should do. We do not yet know how to perform them, but now we just need to give them names:

    Start                 open todo page     ->    At empty todo page
    At empty todo page    add a todo item    ->    At todo page with one item

Alright! This is a good start. To be able to run this model, we need to add information to `states.py` and `actions.py`.

Let's begin with adding **state functions** to the `states.py` file. State functions should follow the [snake case name standard](https://peps.python.org/pep-0008/#function-and-variable-names):
    
    """states.py for my_first_actor"""

    def start():
        pass  # Nothing here yet
    
    def at_empty_todo_page():
        pass  # Nothing here yet
    
    def at_todo_page_with_one_item():
        pass  # Nothing here yet

Save the file. Now, let's do something similar with actions in the `actions.py` file. Actions functions should also follow the [snake case name standard](https://peps.python.org/pep-0008/#function-and-variable-names).

This time, we'll make it a bit more advanced. Let's add instructions that match the intent of each action. Check out how to work with Playwright for Python in oder to understand the instructions below:

    """actions.py for my_first_actor"""

    from magpie_core.app import Page

    def open_todo_page(page: Page):
        page.goto("https://todomvc.com/examples/react/#/")

    def add_a_todo_item(page: Page):
        todo_field = page.get_by_placeholder("What needs to be done?")
        todo_field.fill("Buy milk")
        todo_field.press("Enter")

Save the changes.

<br>

### Adding the actor to the test file

Let's get rid of the run-time error we received above by adding the actor to the Session object in the test file. We need to instatiate a ModelBasedActor object and assign it to the Session object along with some useful settings:

    """My first test"""

    from app.sessions import Session
    from app.fsm.model_based_actor import ModelBasedActor

    from tests.actors import my_first_actor

    my_actor = ModelBasedActor(actor_module=my_first_actor)

    my_session = Session(
        name="My first session",
        actor=my_actor,
        browser="chromium"
    )

<br>

### Do a test run

From the **parent directory**, you should now be able to run the test file:

    python magpie_core/main.py run tests/my_first_test.py

Let's hope everything works for you, otherwise ensure that you followed all steps above.
Result information will be printed to the console. A folder called `output` will be created
in the parent directory. In this folder, there will be a number of files created:

    output/
    ├── My_first_session.dot.svg    <-- A rendered model file (for humans)
    ├── My_first_session.log.csv    <-- Results for states, actions and transitions (for machines)
    └── event_store.csv             <-- Event store changes (for machines)


The rendered model file will be colorized by execution result status: Pass = green, Fail = red, Flaky = orange, Not run = grey

Note: The event store is not dealt with in this example, so you may just ignore that file for now.

<br>

### Making the test pass or fail - adding oracles

Finally, it is time to add some checks in order to create a proper test. Checks should be added to **states**. Let's see how it should be done.

So, let's think about what checks we could do. Maybe we could begin by checking that there are no items in the todo-list when we enter the state **At empty todo page**? We can do that by counting the number of `div.view` items in the DOM. 

In order to add a check, we will use a function called `expect()`.

Change the contents of the `states.py` file to this:

    """states.py for my_first_actor"""

    from app import Page

    def start():
        pass  # Nothing here yet
    
    def at_empty_todo_page(page: Page):
        num_todo_items = page.locator("div.view").count()
        expect(num_todo_items).is_equal_to(0)
    
    def at_todo_page_with_one_item():
        pass  # Nothing here yet


Try it out by running the same commad as before:

    python magpie_core/main.py run tests/my_first_test.py

If it worked, you should see a new line in the console log:

    👀  expect(page.locator("div.view").count()).is_equal_to(1)    [File: tests/actors/my_first_actor/states.py, line 9, at_empty_todo_page()]


<br>

### Expanding the test

Now, let's check that the "Buy milk" item appears and that there is not more than one item in the list. Change the contents of the `states.py` file to this:

    """states.py for my_first_actor"""

    from app import Page

    def start():
        pass  # Nothing here yet
    
    def at_empty_todo_page(page: Page):
        num_todo_items = page.locator("div.view").count()
        expect(num_todo_items).is_equal_to(0)

    def at_todo_page_with_one_item(page: Page):
            num_todo_items = page.locator("div.view").count()
            expect(num_todo_items).is_equal_to(1)
            item_text = page.locator("div.view").text_content()
            expect(item_text).is_equal_to("Buy milk")


Save the file and re-run the test to see your new checks in action. Look for the "👀  expect[...]" apperances in the console log.

<br>

### Testing repeatability

It is pretty simple to turn the test into a cyclic one, trying the same things over and over until the assigned time is out. The added value comes from the fact that you will know more about the repeatability of a function under test, whether it behaves correctly every time it is tried, not just once.

So, begin with expanding the model a bit:

    Start                        open todo page     ->    At empty todo page
    At empty todo page           add a todo item    ->    At todo page with one item
    At todo page with one item   reset page         ->    At empty todo page

If you look closely, you will see that the last transition ends in a state that is the start state of another transition. You have now created a cyclic model. In order to stop the execution, you have to add another argument to the Session object in your test file. Change your file to this:

    """My first test"""

    from app.sessions import Session
    from app.fsm.model_based_actor import ModelBasedActor

    from tests.actors import my_first_actor

    my_actor = ModelBasedActor(actor_module=my_first_actor)

    my_session = Session(
        name="My first session",
        actor=my_actor,
        browser="chromium",
        max_run_time_s=10
    )

Save the file. You now have to add the new action function `reset_page`. Open your `actions.py` file and edit the contents to this:

    """actions.py for my_first_actor"""

    from app import Page

    def open_todo_page(page: Page):
        page.goto("https://todomvc.com/examples/react/#/")

    def add_a_todo_item(page: Page):
        todo_field = page.get_by_placeholder("What needs to be done?")
        todo_field.fill("Buy milk")
        todo_field.press("Enter")

    def reset_page(page: Page):
        select_all_locator = page.locator("section.main > label").first
        select_all_locator.click()
        page.get_by_role("button", name="Clear completed").click()

Save the file and re-run the test. Now, marvel at the repeated execution of the same states and actions, checking the outcome every time the state functions and action functions are called.

This concludes your first experiment with Magpie. Hope you learned something, have fun in the future 🙂
