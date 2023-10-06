<img src="../../media/images/magpie.svg" width="128px" />


<br />

# Actions

An *action* contains instructions on what you need to do in the application under test in order to trigger a *transition*
for one state to the next in your model, e.g. clicking a *Next* button in a form on a web page, click an *About*
button to display a popup, send a POST request etc.

Actions are implemented in the `actions.py` file in a model-based actor:

    model_based_actor_module/
    ├── __init__.py
    ├── model
    ├── actions.py       <-- Here!
    ├── states.py
    └── conditions.py


Action functions should have a snake case representation of the corresponding name from the model.

In the model file:

    A state    the action  ->    Another state

will on exit from the state "A state" try to call the function `the_action` in the `actions.py` file of the actor, i.e:

    """actions.py""

    def the_action():
        # do something here
