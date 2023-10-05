# Transitions


### The basics

A **transition** (below expressed in the modeling language) describes the relation between states, i.e:

    Name of start state    ->    Name of end state

e.g:

    User has finished its operations    ->    Test finished


Notice that two or more spaces are needed to separate the items from each other:

        User has finished its operations····->····Test finished
        -----------start state----------  arrow   --end state--

Many transitions can be combined (one per row) in a file in order to create a model. See example [here](../demo/actors/internet_searcher/model)

<br>

### Adding actions

A transition can also have the name of an **action** attached:

    Name of start state    name of action    ->    Name of end state
                           ----action----

e.g:

    User is not authenticated    log in    ->    User is authenticated


See [actions](actions.md) for more information.


<br>

### Adding conditions

Sometimes, you want an action to be allowed only in certain cases. You might have more than one outbound transitions from a state and you want to switch them on or off. This is why we have ***conditions**.

Example:


    Waiting for message    [No messages]           idle             ->    Waiting for message
    Waiting for message    [There are messages]    send response    ->    Response sent
                           -----conditions-----

Conditions should be put within square brackets in the model files.

See [conditions](conditions.md) for more information.
