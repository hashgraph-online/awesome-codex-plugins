# Install Recipes

Read this file in `install`, and in `audit` or `diagnose` when a finding is about the snippet, the framework, SPA page views, CSP, or loading cost. Facts are dated; recheck the volatile ones (marked `volatile`) before relying on them.

## Contents

- 1. GTM or a direct Google tag
- 2. Snippet forms
- 3. Framework recipes
- 4. SPA page views
- 5. Content Security Policy
- 6. First-party serving and performance
- Sources

## 1. GTM or a Direct Google Tag

| Situation | Choose |
|---|---|
| Several Google or third-party products, frequent tag changes, non-developers editing tags | GTM (`GTM-` container) |
| One Google product (for example only GA4 or only Ads) with few changes | A direct Google tag (`gtag/js?id=G-...`) may be simpler |
| The site already loads one of them | Keep it; do not add the other for the same ID |

- Google: "If your site platform or Content Management System permits it, Google Tag Manager should be your first choice", but a Google tag "may be the fastest and easiest method" for one product with few changes.
- "You should avoid installing redundant tags or tag management systems." One container per page; "the best practice is to set up one container per web domain."
- The container ID prefix decides what the container may run (`volatile`, since 2026-07-09): a `GTM-` container allows all tag types; a container loaded with a `G-` or `AW-` ID "is limited to Google tags".
- Loading a `G-`, `AW-`, or `DC-` ID through the `gtm.js` path "is an unsupported implementation". Use `gtm.js` with a `GTM-` ID and no `gtag('config')`, or `gtag/js?id=<ID>` with `gtag('config', '<ID>')`.
- `gtag('config')` is deprecated: "Use the Google Tag Manager UI to configure tag settings and destinations, or use `gtag('set')` for setting in-page parameters." Existing setups keep working. Since 2026-10-08 `gtm.js` "will initialize on container load, regardless of any gtag('config') commands", and config commands surface in the dataLayer as `gtag.config` events, which wildcard Custom Event triggers match (`volatile`).

## 2. Snippet Forms

Copy the snippet from the container's Install dialog (Admin > Install Google Tag Manager) or the Tag Manager API `snippet` method. Google lists three live forms; an agent that writes one from memory usually produces the previous form.

### Current form (Install dialog, one block, `volatile`)

```html
<!-- Google Tag Manager -->
<script async src="https://www.googletagmanager.com/gtm.js?id=GTM-XXXXXXX"></script>
<script>
window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());
</script>
<!-- End Google Tag Manager -->
```

- "Copy the first block of code and paste it as high in the `<head>` tag as possible." This form has no `<noscript>` part.
- The loader is `async`, so the inline line normally runs before `gtm.js` executes. When the site must guarantee order (consent defaults, page-level pushes), put those scripts above this block.

### Previous form (two parts, still supported)

```html
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
<!-- End Google Tag Manager -->
```

```html
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXXX"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
```

- "If you already have your website tagged with the previous version of the snippet, you do not need to retag your website." The noscript part goes "as high in the `<body>` tag as possible".
- The fourth IIFE argument renames the dataLayer; the loader then adds `&l=<name>`. Use a custom name only when another script already owns `dataLayer`.
- The CSP nonce form (§5) is built on this form.

### Environment form

An environment snippet (Admin > Environments > Get Snippet) adds `&gtm_auth=<token>&gtm_preview=env-<n>&gtm_cookies_win=x` to the loader and the noscript URL. "Reset Link" invalidates installed snippets. Google: environments are "designed for use with non-production environments"; production gets the standard snippet. Treat `gtm_auth` as a secret (`rules/safety-gates.md` §3).

### Placement rules

- Order inside `<head>`: consent default (`references/consent.md` §2) -> page-level `dataLayer.push` values needed at container load -> the container snippet -> everything else.
- One loader per container per page. Never add the snippet in a layout and again in a page, a CMS plugin, or a tag inside another container.

## 3. Framework Recipes

| Framework | Where | How | Notes |
|---|---|---|---|
| Next.js App Router | `app/layout.tsx` | `import { GoogleTagManager, sendGTMEvent } from '@next/third-parties/google'`; `<html><GoogleTagManager gtmId="GTM-XXXXXXX" /><body>...</body></html>` | Props: `gtmId` or `gtmScriptUrl`, `dataLayer`, `dataLayerName`, `auth`, `preview`, `nonce`. It "fetches the original inline script after hydration" (`afterInteractive`), renders no noscript, and the ID is absent from server HTML, so audits need a rendered check. Push events with `sendGTMEvent({ event: '...', ... })`. |
| Next.js Pages Router | `pages/_app.tsx` | Same component inside the app root | Same caveats |
| Next.js with consent defaults | `app/layout.tsx` | `<Script id="consent-default" strategy="beforeInteractive">` with the `gtag('consent','default',...)` call, placed before `GoogleTagManager` | `beforeInteractive` scripts go into the initial HTML |
| Nuxt | `nuxt.config.ts` | `@nuxt/scripts`: `scripts.registry.googleTagManager: { id: 'GTM-XXXXXXX' }` or `useScriptGoogleTagManager({ id })` | Options include `l`, `auth`, `preview`, `defaultConsent` (queued before `gtm.js`), `trigger` (default `onNuxtReady`); push through `proxy.dataLayer.push(...)` |
| Astro | `src/layouts/*.astro` `<head>` | Paste the snippet with `is:inline`; with `@astrojs/partytown` use `type="text/partytown"` and `partytown({ config: { forward: ['dataLayer.push'] } })` | Without `forward`, main-thread pushes never reach the worker |
| SvelteKit | `src/app.html` `<head>` | Paste the snippet above `%sveltekit.head%` | Push from components with `window.dataLayer.push` |
| Vite or React SPA | `index.html` `<head>` | Paste the snippet | Add the SPA rule (§4) |
| TanStack Start, Remix, React Router | The root route's document `<head>` | Render the snippet as `<script>` elements in the root document (`dangerouslySetInnerHTML` for the inline part) | Server-rendered, so the served-HTML check works |
| WordPress | Theme `header.php` after `wp_head()` start, or one plugin | Use one method only: a plugin (for example Site Kit by Google) or the theme, never both | Check `gtm-detect.sh` and the served page for a second loader from another plugin |
| Static HTML | Every page's `<head>` | Paste the snippet in a shared include | |

- Verify every framework install on the served page (`scripts/gtm-site-check.sh`) and, for client-injected loaders (Next.js component, Nuxt Scripts), in a rendered browser.
- Shopify checkout and other sandboxed pixel runtimes run custom pixels in a restricted worker; GTM there is not a page-level install. Treat it as out of the standard recipe and say so. [INFERENCE from the platform's sandbox description]

## 4. SPA Page Views

- GA4 enhanced measurement sends `page_view` "each time the page loads or the browser history state is changed by the active site", listening for `pushState`, `popState`, and `replaceState`. The browser-history part is an advanced setting of the Page views option.
- Choose exactly one source of route-change `page_view`:
  - Enhanced measurement history events on, and no GTM page_view tag on History Change or a custom route event. (Simplest.)
  - Enhanced measurement history events off, and one GA4 event tag `page_view` on a History Change trigger or a custom `virtual_page_view` dataLayer event pushed by the router.
- Prove it: one `/g/collect` request with `en=page_view` per route change in a rendered browser.

## 5. Content Security Policy

- Nonce-aware container code (previous form with nonce propagation):

```html
<script nonce='{SERVER-GENERATED-NONCE}'>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;var n=d.querySelector('[nonce]');
n&&j.setAttribute('nonce',n.nonce||n.getAttribute('nonce'));f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
```

- GTM "will then propagate the nonce to any scripts that it adds to the page". `'unsafe-inline'` is the discouraged fallback. The current one-block form has two scripts; both need the nonce.
- Minimum for GTM: `script-src-elem https://www.googletagmanager.com`; `img-src https://www.googletagmanager.com`; `connect-src https://www.googletagmanager.com https://www.google.com`. For GA4 add `img-src https://*.google-analytics.com` and `connect-src https://*.google-analytics.com`. Each Google top-level domain is listed separately; CSP has no wildcard on the right side of a host.
- Preview mode adds `https://tagmanager.google.com` to `script-src-elem` and `style-src`, `https://fonts.googleapis.com` to `style-src`, `https://ssl.gstatic.com https://www.gstatic.com` to `img-src`, and `https://fonts.gstatic.com data:` to `font-src`. Debug sessions also use `tagassistant.google.com`; allow it on the environment where Preview runs.
- GTM may register a service worker; Google's CSP table needs `frame-src https://www.googletagmanager.com` for it (`volatile`).
- Custom JavaScript variables "evaluate to `undefined` in the presence of a CSP unless the `'unsafe-eval'` directive is given". Prefer custom templates over adding `'unsafe-eval'`.
- Every third-party tag in the container needs its own hosts; read them from the CSP violation reports of a rendered Preview session.

## 6. First-Party Serving and Performance

- Google tag gateway for advertisers serves GTM from a path on the site's own domain (for example `/metrics/`) through a CDN or the origin (`volatile`; Cloudflare, Akamai, Fastly, CloudFront, GCP). The path is not `/`, at most 100 characters. It does not support the noscript snippet. In Next.js use `gtmScriptUrl="/metrics/?id=GTM-XXXXXXX"`. Setting it up changes CDN or DNS configuration: approval tier in `rules/safety-gates.md`.
- Server-side tagging is a separate tagging server; see `references/container-design.md` §8.
- Cost: "Google Tag Manager limits container size to 300 KB and warns about container size after it's reached 70% of the size limit"; the median container is about 50 KB and the library about 33 KB compressed. `gtm.js` is served with `cache-control: private, max-age=900` (observed 2026-11-08).
- web.dev: "Use only one container per page"; fire non-essential tags after `Window Loaded`; image pixels are cheapest, then custom templates, then Custom HTML. Preview mode is slower, so do not compare Web Vitals from Preview with production.
- Do not load UX features through GTM: "some users block tag managers. Using a tag manager to implement UX features may result in a broken website for some of your users."

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Current and previous snippet forms, placement, no retagging | <https://support.google.com/tagmanager/answer/14847097> |
| One container per domain | <https://support.google.com/tagmanager/answer/6103576> |
| GTM versus Google tag, avoid redundant tag systems, container ID prefix | <https://developers.google.com/tag-platform/devguides/prerequisites>, <https://support.google.com/tagmanager/answer/17070049> |
| Non-GTM IDs on `gtm.js` unsupported; `gtag('config')` deprecated; 2026-10-08 change | <https://support.google.com/tagmanager/answer/17231523>, <https://developers.google.com/tag-platform/gtagjs/reference>, <https://support.google.com/tagmanager/answer/4620708> |
| Environments and their snippet | <https://support.google.com/tagmanager/answer/6311518> |
| Next.js component props and behavior | <https://nextjs.org/docs/app/guides/third-party-libraries>, <https://github.com/vercel/next.js/blob/canary/packages/third-parties/src/google/gtm.tsx> |
| Nuxt Scripts GTM options | <https://scripts.nuxt.com/scripts/tracking/google-tag-manager> |
| Partytown forward config | <https://docs.astro.build/en/guides/integrations-guide/partytown/>, <https://partytown.qwik.dev/google-tag-manager/> |
| Enhanced measurement history page views | <https://support.google.com/analytics/answer/9216061> |
| CSP nonce snippet, hosts, Custom JavaScript variables | <https://developers.google.com/tag-platform/security/guides/csp> |
| Google tag gateway | <https://developers.google.com/tag-platform/tag-manager/gateway/setup-guide?setup=manual> |
| Container size, one container per page, tag-type cost, UX through tag managers | <https://web.dev/articles/tag-best-practices> |

### Evidence grade

Official Google, Vercel, Nuxt, and Astro documentation read 2026-11-08, plus one observed response header. SvelteKit, TanStack Start, Remix, WordPress, and Shopify rows follow each framework's document-head convention and were not re-read in this run.
