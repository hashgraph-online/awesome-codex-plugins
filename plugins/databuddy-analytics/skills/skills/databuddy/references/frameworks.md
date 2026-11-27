# Databuddy Framework Setup

Use this file for browser analytics setup in React, Next.js, Vue, Nuxt, vanilla HTML, CMSs, and tag managers.

## React / Next.js

`DatabuddyProvider` is a client component, so it can render directly from a Next.js App Router layout. Without children it only loads tracking:

```tsx
import { DatabuddyProvider } from "@databuddy/sdk/react";

<DatabuddyProvider
  clientId={process.env.NEXT_PUBLIC_DATABUDDY_CLIENT_ID!}
  autocapture={{ webVitals: true, errors: true }}
/>
```

Wrap the app instead when you have signed-in users or flags. Pass the user, or `null` when signed out, and the provider calls `identify()` and `reset()` for you:

```tsx
<DatabuddyProvider
  clientId={process.env.NEXT_PUBLIC_DATABUDDY_CLIENT_ID!}
  user={user ? { id: user.id, traits: { email: user.email, plan: user.plan } } : null}
  userPending={isPending}
>
  {children}
</DatabuddyProvider>
```

Options: `autocapture` (`true`, `false`, or `{ interactions, attributes, outgoingLinks, errors, webVitals, hashChanges }`; only `interactions` is on by default), `batching`, `retries`, `sampleRate`, `skipPaths`, `maskPaths`, `filter` (pageviews and page exits), `beforeSend` (every event, with `event.type` naming its shape; not session replays), `consent` (a live `() => boolean` read before every send and retry; never stored; flags are evaluated anonymously while it returns `false`), `linkDomains` (other domains you own; links and forms there carry the visitor's IDs), `cleanUrl` (`false`, or a function calling the router's replace, when a router such as Next.js's App Router owns the URL), `replay`, `disabled`, and `debug`. CDN script tags take `data-consent-cookie="name=value"` and `data-strip-params='["gclid"]'` for the same needs without JavaScript. The same options work with `init()` from `@databuddy/sdk` outside React. The older flat names (`trackWebVitals`, `batchSize`, `samplingRate`, ...) still work but are deprecated; map them with `https://www.databuddy.cc/docs/sdk/upgrade`.

Custom event:

```tsx
import { track } from "@databuddy/sdk";

track("signup_completed", { method: "google", source: "homepage" });
```

## Vue

Use the Vue component in `App.vue` near `RouterView` so it mounts once for the app.

```vue
<script setup>
import { Databuddy } from "@databuddy/sdk/vue";
const clientId = import.meta.env.VITE_DATABUDDY_CLIENT_ID;
</script>

<template>
  <Databuddy
    :client-id="clientId"
    :autocapture="{ webVitals: true, errors: true }"
  />
  <RouterView />
</template>
```

Vue templates use kebab-case props with the same options as React: `client-id`, `:autocapture`, `:batching`, `:sample-rate`, `:skip-paths`, and `:mask-paths`.

Custom event:

```vue
<script setup>
import { track } from "@databuddy/sdk";

function handleSignup() {
  track("signup_clicked", { source: "header" });
}
</script>

<template>
  <button @click="handleSignup">Sign up</button>
</template>
```

## Nuxt 3

Register the Vue component in a client-only plugin, then use runtime config in `app.vue`.

```ts
// plugins/databuddy.client.ts
import { Databuddy } from "@databuddy/sdk/vue";

export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.component("Databuddy", Databuddy);
});
```

```vue
<!-- app.vue -->
<script setup>
const runtimeConfig = useRuntimeConfig();
</script>

<template>
  <Databuddy
    :client-id="runtimeConfig.public.databuddyClientId"
    :autocapture="{ webVitals: true }"
  />
  <NuxtPage />
</template>
```

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      databuddyClientId: process.env.NUXT_PUBLIC_DATABUDDY_CLIENT_ID,
    },
  },
});
```

## Vanilla / CMS / GTM

```html
<script
  src="https://cdn.databuddy.cc/databuddy.js"
  data-client-id="your-client-id"
  data-track-web-vitals
  async
></script>
```

Use the CDN path for plain HTML, CMS templates, and tag managers. For strict CSP, see [troubleshooting.md](./troubleshooting.md).
