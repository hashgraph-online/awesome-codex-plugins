# Databuddy DevTools

Use this file when a user wants to debug Databuddy locally, inspect events/identity/queues/flags, override flags, or manage flags from the browser overlay.

## Install

```bash
bun add -d @databuddy/devtools
```

Keep DevTools development-only or preview-only. Do not hard-code admin API keys in source.

## React

```tsx
import { DatabuddyDevtools } from "@databuddy/devtools/react";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <DatabuddyDevtools enabled={process.env.NODE_ENV !== "production"} />
    </>
  );
}
```

Manual mount:

```ts
import { mountDevtools } from "@databuddy/devtools/react";

const unmount = mountDevtools();
```

## Vue

```vue
<script setup>
import { DatabuddyDevtools } from "@databuddy/devtools/vue";
</script>

<template>
  <RouterView />
  <DatabuddyDevtools :enabled="import.meta.env.DEV" />
</template>
```

Manual mount:

```ts
import { mountDevtools } from "@databuddy/devtools/vue";

const unmount = mountDevtools();
```

## What DevTools Reads

The overlay observes existing SDK globals. It does not replace the Databuddy SDK.

| Global | Purpose |
| --- | --- |
| `window.databuddy` | primary browser tracker |
| `window.db` | tracker alias |
| `window.databuddyConfig` | rendered tracker options |
| `window.__tracker` | internal queues, global properties, session metadata |
| `window.__databuddyFlags` | browser flag manager created by React/Vue flags SDK |

Shortcut: `Cmd/Ctrl + Shift + D` toggles the overlay. `Escape` closes it.

## Capabilities

- Runtime status and diagnostics.
- Client, anonymous, and session IDs.
- URL attribution params and storage keys.
- Global properties.
- Queue lengths and flush state for track, batch, vitals, and errors.
- Observed calls to `track`, `screenView`, `flush`, and `clear`.
- Manual test event, custom event, screen view, flush, clear, and session reset actions.
- Feature flag readiness, config, evaluated values, variants, reasons, and sources.
- Local feature flag overrides.
- Flag catalog fetch and flag create/update/delete when an API key with `manage:flags` is provided.

## Feature Flag Debugging

DevTools shows flags only when the browser app has a flag manager. React `DatabuddyProvider` creates it when a component first reads a flag (`useFlag`, `useFlagDetails` or `useFlagsStatus`); Vue `createFlagsPlugin` mounts it with the plugin. Until then, the flag panel should say flags are unavailable.

Flag sources:

| Source | Meaning |
| --- | --- |
| `server` | result came from the flags API |
| `cache` | cached result |
| `default` | local default or fallback |
| `error` | evaluation failed |
| `override` | local DevTools override |

Overrides are stored locally and do not change server definitions. Clear overrides before validating production behavior.

## Flag Management

DevTools can manage flag definitions from the overlay:

- requires an API key with `manage:flags`
- uses `x-api-key`
- reads definitions from `GET /public/v1/flags/definitions`
- creates with `POST /public/v1/flags`
- updates with `PATCH /public/v1/flags/{id}`
- deletes with `DELETE /public/v1/flags/{id}`
- uses the current flag `clientId` from SDK config or tracker config
- respects the configured flag `environment` when fetching definitions

The default admin API host is `https://api.databuddy.cc`; local or preview environments can override the admin API URL in the overlay.

## Debugging Flow

1. Confirm the tracker script is injected and has `data-client-id`.
2. Confirm `anonymousId` and `sessionId` exist.
3. Send a test event and confirm it appears in the event log.
4. Flush queues before navigation-heavy repros.
5. For flags, confirm `__databuddyFlags` exists, `clientId`, API host, and environment are correct, and `isReady` is true.
6. Confirm targeting context includes the IDs the rollout needs: `userId`, `organizationId`, or `teamId`.
7. Inspect the flag source, reason, value, and variant.
8. Use an override to test UI branches, then clear it.
9. Trigger the intended outcome event and verify it includes `flag_key`, `variant`, and status when relevant.
10. If managing definitions, paste a scoped API key at runtime; do not commit it.

## Common Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Overlay opens but tracker missing | `DatabuddyProvider` (or the Vue `<Databuddy />` component) never mounted or `clientId` unresolved | mount the SDK near the app root and verify env |
| Script present but no client id | wrapper dropped `clientId` prop | check component props and rendered script attributes |
| Flags panel unavailable | no browser flag manager | wrap the app in `DatabuddyProvider` and render a component that reads a flag, or install Vue `createFlagsPlugin` |
| Flag override stuck | local override still set | clear override in DevTools |
| Cannot fetch catalog | missing admin key or wrong API URL | paste `manage:flags` key and verify API host |
| 403 while managing flags | key lacks access to this client | use a key scoped to the website or with broader flag access |
