<img src="../../media/images/magpie.svg" width="128px" />

<br>

# Models

A *model* is first and foremost intended to represent a flow of an aspect of your application you would like to test. It makes most sense to let a model represent a limited part of the behavior of an end user of your system, like e.g. login/logout, buying a random item from your web shop, registering new user etc.

[States](states.md), [transitions](transitions.md) and [actions](actions.md) are combined in order to build a model, like in this example:


    Start             open search page   ->   At start page
    At start page     do new search      ->   At search page

    # Expand the model here, if you wish



Models are implemented in the `model` file in a model-based actor:

    model_based_actor_module/
    ├── __init__.py
    ├── model            <-- Here!
    ├── actions.py
    ├── states.py
    └── conditions.py


Look at the example [My first test](../my_first_test.md) to learn more!
