# Install Methods

Read this reference in `install`. It owns the method order, the per-framework recipe, the `gtag('config')` change, the Partytown caveat, and the two optional delivery paths.

> Korean version: [`install-methods.ko.md`](install-methods.ko.md)

## Contents

- Method order
- The `gtag('config')` change
- Framework recipes
- Partytown caveat
- Optional paths: tag gateway and server-side tagging

## Method order

Take the first method that fits the site, and state why the later ones were rejected.

1. **An existing GTM container.** If the page already loads `gtm.js`, keep the measurement inside that container and do not add a second tag. Google's install page says: "If you are installing a Google tag for the first time, we recommend using Google Tag Manager." Naming that tag is the end of this skill's container work: creating or editing container items is a separate change with its own approval, so this run owns the page code that feeds the container - the consent default order, one page-view source, the CSP entries, and the `dataLayer` pushes - and lists the container tag as a hand-off.
2. **The framework's official integration.** When the framework ships a supported component or module, use it instead of a hand-written snippet: `@next/third-parties/google`, `@nuxt/scripts`, Site Kit for WordPress, and the Google & YouTube channel for Shopify.
3. **The plain Google tag snippet.** Fall back to `gtag.js` when nothing above exists. Place it "immediately after the opening `<head>` HTML tag", and keep event calls below the snippet, because Google does not process data from events placed above it.

Constraints that decide the method:

- `gtag.js` "doesn't support third-party or custom tags, and can only send data to Google services." It is the right choice for a static site generator, a CMS, or a code-based setup and the wrong choice for a container that must serve several vendors.
- A container keyed to a destination-specific prefix such as `G-` "is limited to Google tags." Multi-vendor work is out of this skill's scope; say so and stop.
- The measurement ID (`G-` followed by letters and numbers) is the same value as the destination ID, and it is not the property ID.

## The `gtag('config')` change

Google's reference states it directly: "The `gtag('config')` command is deprecated. Use the Google Tag Manager UI to configure tag settings and destinations, or use `gtag('set')` for setting in-page parameters." The same page says existing snippets containing `gtag('config')` "will continue to work for backward compatibility", and the install page explains why hard-coded options are discouraged: they lock settings "into a specific point in the page or event lifecycle".

Source and date: <https://developers.google.com/tag-platform/gtagjs/reference>, read 2026-11-08.

What this means for a new install:

- Do not add new `gtag('config', 'G-...', {...})` option blocks by hand. Write the `gtag('set', ...)` calls the page needs, and list every setting that now belongs to the tag UI as a UI step with its location in the report.
- A framework wrapper may still emit `gtag('config', ...)` internally. Next.js `@next/third-parties/google` calls `gtag('config', '<gaId>' [, {'debug_mode': true}])` inside its `GoogleAnalytics` component. That emitted call is the package's contract, not a pattern to copy into application code.
- Existing `gtag('config')` snippets are not a finding. Migration is optional and is recommended only when the hand-written options are the cause of a defect.

## Framework recipes

Each recipe ends with the same two obligations: the consent default precedes every measurement command on every page, and exactly one page-view source exists.

### Next.js App Router

```tsx
// app/layout.tsx
import { GoogleAnalytics } from '@next/third-parties/google';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
      <GoogleAnalytics gaId="G-XXXXXXXXXX" />
    </html>
  );
}
```

- Events: `sendGAEvent('event', 'buttonClicked', { value: 'xyz' })`. It warns when called before the component mounts.
- With a container: `<GoogleTagManager gtmId="GTM-XXXXXXX" />` and `sendGTMEvent({ event: 'buttonClicked', value: 'xyz' })`. `gtmId` may be omitted when `gtmScriptUrl` points at a tag gateway path.
- Page views: the package relies on Analytics collecting them when the browser history state changes, so the enhanced measurement history option must be on and no manual `page_view` call may run next to it.
- Nonce: the component accepts a `nonce` prop; pass the request nonce for CSP.

### Next.js Pages Router

The same components, mounted once in `pages/_app.js`:

```jsx
import { GoogleAnalytics } from '@next/third-parties/google';

export default function App({ Component, pageProps }) {
  return (
    <>
      <Component {...pageProps} />
      <GoogleAnalytics gaId="G-XXXXXXXXXX" />
    </>
  );
}
```

### React or Vite SPA

1. Put the Google tag snippet in `index.html` immediately after the opening `<head>`.
2. Choose one page-view source. Either keep enhanced measurement's history option on and send nothing by hand, or turn both page-load and history page views off and send `page_view` yourself on each route change with `page_title` and `page_location`.
3. Never ship both. A router listener plus the history option is the double count described in the diagnosis order.
4. Reset scroll on route change so engagement time lands on the right virtual page.

### TanStack Start

No Google Analytics package exists for TanStack. Subscribe to the router and send the page view yourself:

```ts
router.subscribe('onResolved', (event) => {
  if (event.toLocation.pathname === event.fromLocation?.pathname) return;
  gtag('event', 'page_view', {
    page_title: document.title,
    page_location: window.location.href,
  });
});
```

`onResolved` is the documented hook for analytics and other imperative integrations. With this subscription in place, enhanced measurement's history option must be off.

### Nuxt

`@nuxt/scripts` ships a `googleAnalytics` registry entry:

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxt/scripts'],
  scripts: {
    registry: {
      googleAnalytics: { id: 'G-XXXXXXXXXX', trigger: 'onNuxtReady' },
    },
  },
});
```

- Use `useScriptGoogleAnalytics()` and its `proxy.gtag(...)` to send events through the module.
- The module's first-party mode bundles and proxies the script by default; confirm it is intentional before an audit calls the proxied path a defect.
- For SPA route changes, use `useScriptEventPage` and send `page_view` with `page_referrer` carried forward, with the history option off.

### Astro

Astro documents no first-party Analytics integration. Two supported shapes:

```astro
<script is:inline>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
</script>
<script is:inline async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
```

- Or render a UI-framework component in a hydrated island.
- `is:inline` keeps the script unbundled and unprocessed; a bundled script can be reordered and land before `dataLayer` exists.
- Multi-page navigation is a full page load, so the page-load page view is enough and the history option is unnecessary.

### Static HTML

Paste the snippet immediately after the opening `<head>` on every page template, keep event calls below it, and set the consent default above it. No build step is involved, so the CSP entries go into the server or CDN header configuration.

### WordPress

Use Site Kit, the official Google plugin, which connects the property and container without code edits. A theme-level snippet is a fallback for sites where the plugin cannot run, and it duplicates collection when Site Kit is also active.

### Shopify

Use the Google & YouTube sales channel, which connects the property and tracks ecommerce events without theme edits. Editing `theme.liquid` by hand is the fallback and must not run alongside the channel.

## Partytown caveat

Partytown moves third-party scripts into a web worker, and that changes what is sent:

- "the automatic Google Analytics 4 `user_engagement` event … is not sent when GA4 runs in Partytown."
- Page-exit handlers (`pagehide`, `visibilitychange`, `beforeunload`) are "not reliable" in the worker.
- `forward: ["dataLayer.push"]` is required for the main thread's `dataLayer` calls to reach the tag.

State these losses in the report instead of reporting missing engagement as a tag defect.

## Optional paths: tag gateway and server-side tagging

Both are optional. Recommend one only when the request asks for first-party script delivery or a server container; never present either as the default install.

- **Google tag gateway** serves the tag from the site's own domain through its CDN, load balancer, or web server, and sends some measurement requests through that first-party domain. The automated path configures scripts itself; the guided path "requires manual re-tagging", and every existing script source must be replaced with the new measurement path or "the browser will continue to request scripts directly from Google". If consent mode is in use, automated script setup must be off.
- **Server-side tagging** sends events to your own container instead of Google by setting the `server_container_url` config parameter. Google recommends pairing the gateway with server-side tagging for the most durable setup.
- Both change where requests go, so the collection proof must capture the request from the new path.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| GTM is Google's recommendation for a first install, and `gtag.js` can only send data to Google services | <https://developers.google.com/tag-platform/gtagjs>, <https://developers.google.com/analytics/devguides/collection/ga4/tag-options> |
| `gtag('config')` is deprecated, existing snippets keep working, and hard-coded options lock settings into a lifecycle point | <https://developers.google.com/tag-platform/gtagjs/reference>, <https://developers.google.com/tag-platform/gtagjs/install> |
| Next.js ships `GoogleAnalytics`, `GoogleTagManager`, `sendGAEvent`, and `sendGTMEvent` for the App and Pages Router | <https://nextjs.org/docs/app/guides/third-party-libraries>, <https://nextjs.org/docs/pages/guides/third-party-libraries> |
| The Next.js `GoogleAnalytics` component emits `gtag('config', ...)` | <https://github.com/vercel/next.js/blob/canary/packages/third-parties/src/google/ga.tsx> |
| TanStack Router documents `router.subscribe('onResolved', ...)` for analytics | <https://tanstack.com/router/latest/docs/framework/react/guide/router-events> |
| `@nuxt/scripts` ships a `googleAnalytics` registry entry with first-party mode | <https://scripts.nuxt.com/scripts/google-analytics> |
| Astro documents client-side scripts with `is:inline` and Partytown, and no first-party Analytics integration | <https://docs.astro.build/en/guides/client-side-scripts/>, <https://docs.astro.build/en/guides/integrations-guide/partytown/> |
| Site Kit and the Shopify Google & YouTube channel are the official no-code paths | <https://wordpress.org/plugins/google-site-kit/>, <https://help.shopify.com/en/manual/reports-and-analytics/google-analytics/google-analytics-setup> |
| Partytown drops the automatic `user_engagement` event and makes page-exit handlers unreliable | <https://partytown.qwik.dev/trade-offs/> |
| The tag gateway serves the tag from the first-party domain, and the guided path needs manual re-tagging | <https://developers.google.com/tag-platform/tag-manager/gateway>, <https://support.google.com/tagmanager/answer/16061406> |
| `server_container_url` sends events to your own server container | <https://developers.google.com/tag-platform/tag-manager/server-side/intro> |

### Evidence grade

`MEASURED` for every quoted sentence, the component props, and the endpoint behavior, from the pages above read on 2026-11-08. `LOCAL` for the method order and for the instruction to list moved settings as UI steps; those are this package's design over the deprecation note. The Vite, Astro, and static recipes are assembled from the snippet placement rule plus the single-page-view rule rather than from a framework-specific Google page.
