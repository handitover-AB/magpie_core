<img src="../../media/images/magpie.svg" width="128px" />

<br />

# Conditions

Conditions are implemented in the `conditions.py` file of a model-based actor:

    model_based_actor_module/
    ├── __init__.py
    ├── model
    ├── actions.py
    ├── states.py
    └── conditions.py    <-- Here!

Condition functions should have a snake case representation of the corresponding name from the model. Condition functions should return a boolean that will determine whether the action (and its associated transition) is allowed or not. If the condition function returns True (or something truthy), the action will be allowed. If it returns False (or something falsy) the action is not allowed and the outbound transition is blocked.

In the model file:

    A state    [a condition]  the action  ->    Another state

will try to call a function called `a_condition` in the `conditions.py` file of the actor, i.e:

    """conditions.py""

    def a_condition():
        # do something here
