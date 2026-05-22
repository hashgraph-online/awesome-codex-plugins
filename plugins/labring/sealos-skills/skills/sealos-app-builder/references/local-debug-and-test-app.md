# Local Debug and Test App

Use this reference when SDK calls work inconsistently during development.

## Why direct browser access is misleading

A Sealos app can render normally in a browser tab and still fail to integrate with Desktop.

That usually happens because:

1. the app is not inside the Sealos Desktop iframe
2. Desktop is not present to answer SDK requests
3. calls such as `getSession()` or `getLanguage()` time out or reject

## Local debugging checklist

1. Start the app locally.
2. Confirm the root Sealos provider initializes only in the browser.
3. Open the app through a Sealos Desktop test app, not only through the raw URL.
4. Verify `getSession()` succeeds inside Desktop.
5. Verify the standalone fallback is readable outside Desktop.

## Test app guidance

For end-to-end Sealos debugging, create a test app in Sealos Desktop that points to the local or preview URL of your app.

Use it to verify:

1. session retrieval
2. language retrieval
3. runtime language change handling
4. business API writes tied to the Sealos user
5. cross-app event behavior, if any

## Failure patterns

### `getSession()` fails outside Desktop

This is expected. Show a user-facing fallback instead of treating it as a mysterious bug.

### Session works only after reload

Check whether the SDK is being initialized more than once or from multiple entry points.

### Event listeners behave strangely

Look for duplicate `createSealosApp()` calls or repeated event subscriptions without cleanup.
