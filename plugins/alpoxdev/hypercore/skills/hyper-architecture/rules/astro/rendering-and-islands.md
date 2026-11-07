# Rendering and Islands

> Astro is static by default; make a route on demand only when it needs request data, and ship framework JavaScript only where a `client:*` directive and a reason exist.

Rules here are labelled `official` when an opened page in the dated snapshot states them, and `hypercore-default` when this package chose the default.

## 1. The rendering model

`official` — `output` accepts only `'static'` or `'server'`, and `'static'` is the default. `'server'` "does not bring any additional functionality. It only switches the default rendering behavior." (L-17, L-09)

| Setting | Meaning |
|---|---|
| `output: 'static'` (default) | Every route renders at build time unless it opts out |
| `output: 'server'` | Every route renders on demand unless it opts in |
| `export const prerender = false` | This route renders on demand, under `'static'` |
| `export const prerender = true` | This route renders at build time, under `'server'` |

Rules:

- `official` — `prerender` must be statically analyzable. A value computed at runtime is not supported.
- `official` — Any on-demand route needs an adapter. So do `server:defer` server islands and live collections.
- `official` — Static sites can opt individual routes into server rendering since 5.0 removed `output: 'hybrid'`; `'static'` absorbed that behavior (L-03).
- `hypercore-default` — Start from `'static'` and add `prerender = false` to the routes that need it. Switch the site to `'server'` only when most routes are dynamic, and say so in the change description.

## 2. Adapters

`official` — The official adapters are Node, Netlify, Vercel, and Cloudflare (L-09, L-54).

```js
import node from '@astrojs/node';

export default defineConfig({
  adapter: node({ mode: 'standalone' }),
});
```

- `official` — `@astrojs/node` takes `mode: 'standalone' | 'middleware'`, plus `staticHeaders`, `bodySizeLimit`, and `experimentalDisableStreaming`.
- `official` — HTML streams by default on on-demand routes.
- `official` — Response headers can only be modified at page level (`Astro.response.headers`, `Astro.redirect`); a child component cannot set them.
- `hypercore-default` — Detect the adapter before recommending any server feature, and name the adapter in the report. A recommendation that assumes an adapter the project does not have is wrong.

## 3. Server islands

`official` — `<Component server:defer />` splits a component into its own `/_server_islands/...` route, fetched by an injected script (L-18).

```astro
---
import Avatar from '../components/avatar.astro';
---

<Avatar server:defer>
  <p slot="fallback">Loading…</p>
</Avatar>
```

Rules:

- `official` — Props must be serializable. Functions and circular references cannot cross the boundary.
- `official` — Props travel as an encrypted query string and fall back to POST above roughly 2048 bytes, which breaks caching.
- `official` — Props are encrypted with a per-build key. Use `astro create-key` and `ASTRO_KEY` for rolling or multi-region deployments.
- `official` — `slot="fallback"` supplies the placeholder markup rendered into the static page.
- `hypercore-default` — Prefer a server island over converting a whole page to on-demand rendering when only one fragment needs cookies or personalization.

## 4. Client islands

`official` — Framework components render to static HTML by default; a `client:*` directive hydrates them (L-19, L-58).

| Directive | When the component hydrates | Use for |
|---|---|---|
| `client:load` | Immediately on page load | Interaction needed on first paint |
| `client:idle` | When the browser is idle | Secondary controls below the fold |
| `client:visible` | When the component enters the viewport | Content far down the page |
| `client:media={QUERY}` | When a media query matches | Mobile-only or desktop-only widgets |
| `client:only={FRAMEWORK}` | Client only, never server-rendered | Components that cannot render on the server |

Rules:

- `official` — Only `client:only` skips server rendering, and it requires the framework name.
- `official` — Props passed to a hydrated component have the same serializability limits as server islands; functions cannot cross.
- `official` — Only `.astro` files can mix frameworks. A React component cannot render a Svelte component.
- `hypercore-default` — Use the narrowest directive that satisfies the interaction. `client:visible` or `client:idle` for below-the-fold islands; `client:load` only when first paint needs the interaction; `client:only` only when the component genuinely cannot render on the server.
- `hypercore-default` — Every added directive needs a stated reason in the change. An island directive is a performance decision, not a default.

## 5. Framework integrations

`official` — Framework support arrives through integrations: `@astrojs/react`, `@astrojs/preact`, `@astrojs/svelte`, `@astrojs/vue`, `@astrojs/solid-js`, and `@astrojs/alpinejs` (L-19).

- `official` — Install the integration and the framework's own package; the integration does not bundle the framework runtime.
- `hypercore-default` — Prefer `.astro` components for static markup. Add a framework integration only where its component model earns the runtime.
- `hypercore-default` — When a project has several framework integrations, check whether one would do before adding another. Each adds its own hydration runtime.

## 6. Client-side scripts

`official` — An Astro `<script>` is bundled, TypeScript-compiled, deduplicated per page, given `type="module"`, and inlined when small (L-29, L-58).

| Attribute | Effect |
|---|---|
| default | Bundled, deduplicated, processed |
| `is:inline` | Left as written, not bundled |
| `define:vars` | Implies `is:inline`, so the script is not bundled and runs per instance |

Rules:

- `official` — `define:vars` implies `is:inline`; do not expect bundling or deduplication from it.
- `hypercore-default` — Prefer a bundled `<script>` over `is:inline` unless the script must run before the bundle loads or needs no processing.

## 7. What not to do

- Do not add Actions, sessions, server islands, live collections, or route caching to a project with no adapter.
- Do not switch the whole site to `output: 'server'` to make one route dynamic.
- Do not set response headers inside a child component.
- Do not pass a function, a class instance, or a circular structure to a hydrated or server island.
- Do not expect `client:*` to render the component on the server; only the absence of the directive does that.

## Checklist

- [ ] `output` and the adapter are recorded, and every touched route has an explicit `prerender` decision.
- [ ] `prerender` values are statically analyzable.
- [ ] Any on-demand route, server island, or live collection has an adapter behind it.
- [ ] Each `client:*` directive is the narrowest one that satisfies the interaction, with a stated reason.
- [ ] No non-serializable prop crosses a hydration or server-island boundary.
- [ ] Server island props stay small enough to avoid the POST fallback where caching matters.
- [ ] Response headers are set at page level.
- [ ] Framework components only mix inside `.astro` files.

## Sources

> Checked 2026-11-07. Facts come from the Astro research lane, which opened these pages on 2026-11-07; lane source ids are kept in parentheses.

| Claim | Source |
|---|---|
| `output` accepts only `'static'` and `'server'`; `'server'` only switches the default (L-17, L-09) | https://docs.astro.build/en/reference/configuration-reference/ |
| `prerender` opt-in and opt-out must be statically analyzable (L-09, L-07) | https://docs.astro.build/en/guides/on-demand-rendering/ |
| `output: 'hybrid'` removed in 5.0 and `'static'` absorbed it (L-03) | https://docs.astro.build/en/guides/upgrade-to/v5/ |
| Adapter requirement for on-demand routes, server islands, and live collections (L-09, L-18, L-10) | https://docs.astro.build/en/guides/on-demand-rendering/ |
| Official adapters and the Node adapter's options (L-09, L-54) | https://docs.astro.build/en/guides/integrations-guide/node/ |
| HTML streaming default and page-level-only response headers (L-09) | https://docs.astro.build/en/guides/on-demand-rendering/ |
| Server islands, `server:defer`, fallback slot, encrypted props, 2048-byte POST fallback (L-18) | https://docs.astro.build/en/guides/server-islands/ |
| Server island prop encryption key and `astro create-key` (L-18, L-28) | https://docs.astro.build/en/reference/cli-reference/ |
| `client:*` directives, static-by-default rendering, serializable props, `.astro`-only mixing (L-19, L-58) | https://docs.astro.build/en/reference/directives-reference/ |
| Framework integrations and their packages (L-19) | https://docs.astro.build/en/guides/framework-components/ |
| Bundled scripts, `is:inline`, `define:vars` implying inline (L-29, L-58) | https://docs.astro.build/en/guides/client-side-scripts/ |
