<img src="../media/images/magpie.svg" width="128px" />

<br />

# Sessions

A **session** is where you put context around an actor. You define which actor the session is going to use, in which browser and which strategy you want the model exploration to have etc.

A test file may contain more than one session. All sessions in a test file will be executed in parallel by Magpie. This means that we can test concurrency effects by having multiple sessions running in the same test.

In the session setup you can specify a device, which should map to one of the [**playwright devices**](https://github.com/microsoft/playwright/blob/main/packages/playwright-core/src/server/deviceDescriptorsSource.json). This will entail a matching set of properties such as scale factor, resolution, if it is a mobile device, has touch etc.
