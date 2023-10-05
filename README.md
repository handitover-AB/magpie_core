<img src="media/images/magpie.svg" width="128px" />

<br />

# Magpie

Magpies are good at finding bugs. Legend has it that Magpies predict fortune, good or bad. Fortune telling would be a fantastic property of a test tool, wouldn't it? Naming the tool Magpie should help us find inspiration to deliver on that promise!

Magpie was initially created as an internal tool for writing and executing automated end-to-end tests at [Visiba Care](https://www.visibacare.com). Magpie allows creation and execution of end-to-end tests that are maintainable and will provide value for your organization over a long time. Now, Visiba Care releases the code to the public domain for everyone to enjoy, use, and contribute to.

Using Magpie, it is possible to do functional testing using one or more model-based actors running in parallel, mimicing the behavior of your end users.

Magpie is implemented in [Python](https://www.python.org), Magpie uses well-known libraries for interactions with applications under test. For web testing, [Playwright-Python](https://playwright.dev/python/docs/intro) (a free third-party library from from Microsoft) is used for interaction with web applications.

Test steps are written in Python. Models are described in a proprietary, simple, natural language.


### Why Magpie?

**Separation of concerns**

Using model-based testing, *what* to test is separated from *how* it is done. This enables different people to work with each if desired, greatly improving test design quality and maintenance. You may focus on what you want to test before you figure out how to implement the instructions for each step.


**Coverage and repeatability**

Using multi-actor tests with cyclical models (they don't have to be cyclical), you have a chance of finding more bugs in any given amount of time, compared with traditional scripted testing. Why? Increased coverage. The actors use the system like your end-users do, covering more combinations of sub-system states along the way. Some states may be visited more than once and order of execution can be more random than with traditional scripts.


### Getting started

Have a look at the example [My first Magpie test](doc/my_first_test.md) to learn more about how Magpie works and how you can use it to build tests.


### Licensing

This project is licensed under the terms of the [MIT/X Consortium License](LICENSE.md).
