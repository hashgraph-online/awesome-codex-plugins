# SDK Capabilities

Use this reference when you need a concise explanation of the app-side Sealos SDK surface.

## Runtime model

A Sealos app is typically a web app loaded inside Sealos Desktop through an iframe. The app SDK communicates with Desktop through `postMessage`.

## Install

Install the official package before using the SDK in starter code:

```bash
pnpm add @labring/sealos-desktop-sdk
```

Implications:

1. The SDK must be initialized in the browser.
2. Session-dependent calls usually succeed only when the page is opened by Sealos Desktop.
3. Repeated initialization can create noisy listeners or stale instances.

## Common imports

Use the official package name in examples:

```ts
import { EVENT_NAME } from '@labring/sealos-desktop-sdk';
import { createSealosApp, sealosApp } from '@labring/sealos-desktop-sdk/app';
```

If a specific repository already exposes the SDK through a local workspace alias, preserve that only when the repository clearly depends on it.

## Core app-side APIs

### `createSealosApp()`

Initialize the SDK in a client-only context.

Typical behavior:

1. Register the `message` listener.
2. Create the request-response bridge to Desktop.
3. Return a cleanup function when supported by the implementation.

Use it once near the app root.

### `sealosApp.getSession()`

Fetch the current Sealos session.

Typical useful fields:

```ts
type SessionUser = {
  id: string;
  name: string;
  avatar: string;
  k8sUsername: string;
  nsid: string;
};
```

Use `session.user.id` as the stable business key unless the repository uses a stronger existing convention.

### `sealosApp.getLanguage()`

Fetch the current Desktop language.

Typical response:

```ts
{ lng: 'en' }
```

### `sealosApp.addAppEventListen(EVENT_NAME.CHANGE_I18N, handler)`

Listen for language changes emitted by Desktop.

Use this only when runtime language changes matter. Many simple apps can read language once and stop there.

### `sealosApp.getWorkspaceQuota()`

Fetch workspace quota information. Use this when the app creates or provisions resources that should respect workspace limits.

### `sealosApp.getHostConfig()`

Fetch host configuration and feature flags, such as subscription availability or cloud-domain details.

### `sealosApp.runEvents(name, data)`

Send an event to Desktop.

Important limitation:

This is only useful when Desktop actually implements the named event. Treat event names such as `openDesktopApp` as platform conventions, not universally guaranteed APIs.

## Practical rules

1. Never call the SDK from the server.
2. Expect failure when the app is opened directly in a browser tab.
3. Keep one root integration layer.
4. Prefer a user-facing fallback message instead of silent failure.
