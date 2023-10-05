<img src="../media/images/magpie.svg" width="128px" />

<br />

# Test Files

In order to be able to execute a test, Magpie needs instructions on what to run and how. You have to create a file containing this information; we call such files *Test Files*.

A test file should test a certain limited behavior of the application under test, typically something that would be covered by a set of correlated test cases, e.g. positive and negative tests for login/logout. Testing something else should be broken out to a file of its own.

Typlically, testing an entire application requires a lot of test files. The test files should be placed in the `tests` folder in the magpie repo root.

A test file contains at least one definition of a *Session* object. All sessions from a test file are executed in parallel by Magpie.

