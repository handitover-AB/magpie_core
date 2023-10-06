<img src="../media/images/magpie.svg" width="128px" />

<br />

# Actors

An **actor** mimics a limited part of the behavior of the *application under test* related to a single user. It can be e.g. login/logout, dealing with messages, booking and canceling appointments etc.

Functionality in the application under test that involves more than one user can be tested using more than one actor running in parallel. Actors may inform other actors of what they are doing using a central event store. In order to synchronize actions between actors, it is possible to let each actor search for events and choose actions depending on published events from other actors.

### Model-based actors

Initially, this is the only actor type there is.

This actor's behavior is controlled by a [model](models.md) replicating a finite state machine, and by its configuration data.

A model-based actor is implemented as a Python module and consists of a set of files:

    model_based_actor_module_with_a_nice_name/
    ├── __init__.py
    ├── model
    ├── actions.py
    ├── states.py
    └── conditions.py

The `__init__.py` file should import the other Python files (not the `model` file):

    """__init__.py"""
    
    from . import actions, states, conditions

[Actions](model-based_actors/actions.md) are added in the `actions.py` file, [states](model-based_actors/states.md) are added in the `states.py` file and [conditions](model-based_actors/conditions.md) are added in the `conditions.py` file.