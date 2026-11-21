# Project Structure and Routing

> Only `src/pages/` is framework law in Astro; every other folder is a labelled team convention, and every route must declare whether it renders at build time or on demand.

Rules here are labelled `official` when an opened page in the dated snapshot states them, and `hypercore-default` when this package chose the default.

## 1. Folder ownership

Astro reserves `src/pages/` and treats the rest of `src/` as yours. The docs call `src/components`, `src/layouts`, and `src/styles` "a common convention ... but it is not required" (L-05).

| Path | Ownership | Label |
|---|---|---|
| `src/pages/` | Routes and endpoints only | `official` |
| `src/layouts/` | Page shells, `<html>` wrappers, shared `<head>` | `hypercore-default` |
| `src/components/` | Reusable UI, islands, `.astro` partials | `hypercore-default` |
| `src/styles/` | Global CSS and tokens imported by layouts | `hypercore-default` |
| `src/lib/` | Framework-neutral helpers | `hypercore-default` |
| `src/lib/server/` | Server-only modules that must never reach a `client:*` island | `hypercore-default` |
| `src/actions/` | Action definitions, re-exported from `src/actions/index.ts` | `official` (path), `hypercore-default` (domain split) |
| `src/content.config.ts` | Content collection definitions | `official` |
| `src/live.config.ts` | Live collection definitions | `official` |
| `src/middleware.ts` or `src/middleware/index.ts` | Request middleware | `official` |
| `src/fetch.ts` | Custom worker entrypoint for advanced routing | `official` |
| `src/env.d.ts` | `App.Locals` and `ImportMeta` augmentation | `official` |
| `public/` | Files copied untouched to the output root | `official` |

Rules:

- `official` — Keep `src/pages/` for routes only. A helper, type, or fixture placed there becomes a routable URL or a build error.
- `official` — Files in `public/` are copied as-is and are never optimized; source CSS and JS belong in `src/`.
- `hypercore-default` — Put server-only code under `src/lib/server/` and add no client import path to it, so an island cannot pull a secret into the browser bundle.
- `hypercore-default` — Split `src/actions/` by domain (`src/actions/billing.ts`) and re-export from `src/actions/index.ts`; only what the `server` object exposes is callable.
- `hypercore-default` — Do not create `src/content/config.ts`. Legacy collections were removed in 6.0 and the current file is `src/content.config.ts`.
- `hypercore-default` — Never hand-write into `dist/` or `.astro/`; `astro sync` owns `.astro/types.d.ts`.

## 2. File-based routing

`official` — `.astro` pages and `.js`/`.ts` endpoints under `src/pages` become routes; `.md` and `.mdx` pages also render as routes (L-06, L-05).

| File | URL |
|---|---|
| `src/pages/index.astro` | `/` |
| `src/pages/about.astro` | `/about` |
| `src/pages/blog/index.astro` | `/blog` |
| `src/pages/blog/[slug].astro` | `/blog/:slug` |
| `src/pages/docs/[...path].astro` | `/docs/*` (rest param) |
| `src/pages/rss.xml.ts` | `/rss.xml` (endpoint) |
| `src/pages/404.astro` | `404.html` at build time |

Rules:

- `official` — `[param]` matches one segment and `[...rest]` matches the rest of the path. They are not interchangeable.
- `official` — Route priority resolves in this order: reserved routes, more segments, static over dynamic, named params over rest params, prerendered dynamic over on-demand dynamic, endpoints over pages, file routes over redirects (L-06). Do not rely on it silently; when two routes could match, rename one.
- `official` — Reserved prefixes are `_astro/`, `_server_islands/`, and `_actions/`. Do not create a page that collides with them.
- `official` — `src/pages/404.astro` builds `404.html`. `src/pages/500.astro` works only with on-demand rendering and receives an `error` prop (L-37).

## 3. Dynamic routes and `getStaticPaths()`

`official` — A prerendered dynamic route exports `getStaticPaths()` returning `{ params, props? }` (L-06, L-07):

```astro
---
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  const posts = await getCollection('blog');
  return posts.map((post) => ({
    params: { slug: post.id },
    props: { post },
  }));
}

const { post } = Astro.props;
---
```

Rules:

- `official` — Params are not decoded. Call `decodeURI()` when a segment can contain encoded characters.
- `official` — `paginate()` provides the `page` prop for paginated collections.
- `official` — `routePattern` (5.14+) exposes the file's pattern inside `getStaticPaths`.
- `official` — An on-demand route must not export `getStaticPaths()` and therefore cannot receive its `props`.
- `official` — `Astro` is deprecated inside `getStaticPaths()`; use `import.meta.env.SITE` instead of `Astro.site`.
- `hypercore-default` — Keep `getStaticPaths()` free of network calls at request time; it runs at build time only, and a slow call there slows every build.

## 4. Endpoints

`official` — An endpoint is a `.js` or `.ts` file under `src/pages` that exports a method function or `ALL`, typed with `satisfies APIRoute` (L-08):

```ts
import type { APIRoute } from 'astro';

export const GET: APIRoute = ({ params, request }) => {
  return new Response(JSON.stringify({ slug: params.slug }), {
    headers: { 'Content-Type': 'application/json' },
  });
};
```

Rules:

- `official` — Prefer an endpoint over a page when the response is not HTML. A page that returns a `Response` is a route the router cannot reason about.
- `official` — A URL with a file extension (`sitemap.xml.ts`) only matches without a trailing slash.
- `hypercore-default` — Authorize inside the endpoint, exactly as an Action would. Endpoints are public URLs.

## 5. Redirects, rewrites, and error pages

- `official` — Configure redirects in `astro.config.*`: `redirects: { '/old': '/new' }`, or the object form for a custom `status`. External absolute URLs are allowed. Static builds emit a `<meta http-equiv="refresh">` (L-06, L-17).
- `official` — File routes beat redirects. If a page exists at the old path, the redirect never runs.
- `official` — `Astro.rewrite('/path')` and `context.rewrite()` keep the browser URL and re-run the full render phase, including middleware. A missing target returns 404.
- `official` — A redirect that only exists to move traffic belongs in config, not in a page that calls `Astro.redirect()` on every request.

## 6. Naming

`hypercore-default` — Use kebab-case for folders and files (`src/components/blog-card.astro`, `src/lib/server/session.ts`). Framework-required names (`src/content.config.ts`, `src/middleware.ts`, `src/env.d.ts`, `src/fetch.ts`) keep their exact spelling.

`hypercore-default` — Component files export one component and are named after it in PascalCase inside the file, while the file itself stays kebab-case.

## 7. Migration rules

- Preserve public URLs when moving files. A route rename is a breaking change unless a redirect ships in the same change.
- Preserve `prerender` values. A file move that silently drops `export const prerender = false` turns a dynamic page into a build-time page.
- Preserve middleware order when splitting `src/middleware.ts` into `src/middleware/index.ts`.
- Do not rename reserved files to match a local convention; the framework will stop finding them.

## Checklist

- [ ] `src/pages/` contains routes and endpoints only.
- [ ] Every folder outside `src/pages/` is reported as a team convention, not framework law.
- [ ] Dynamic routes use the right param form, and on-demand routes carry no `getStaticPaths()`.
- [ ] Endpoints export a method and are typed with `satisfies APIRoute`.
- [ ] `404.astro` exists where a custom not-found page is wanted, and `500.astro` only on an on-demand site.
- [ ] No file collides with `_astro/`, `_server_islands/`, or `_actions/`.
- [ ] `dist/` and `.astro/` were not edited by hand.
- [ ] Route moves kept their public URL or shipped a redirect.

## Sources

> Checked 2026-11-07. Facts come from the Astro research lane, which opened these pages on 2026-11-07; lane source ids are kept in parentheses.

| Claim | Source |
|---|---|
| Only `src/pages/` is reserved and other folders are convention (L-05) | https://docs.astro.build/en/basics/project-structure/ |
| `public/` files are copied untouched and never optimized (L-05, L-20) | https://docs.astro.build/en/basics/project-structure/ |
| File-based routing for `.astro`, `.md`, `.mdx` pages and `.js`/`.ts` endpoints (L-06, L-05) | https://docs.astro.build/en/guides/routing/ |
| `[param]`, `[...rest]`, route priority order, reserved routes (L-06) | https://docs.astro.build/en/guides/routing/ |
| `getStaticPaths()`, undecoded params, `paginate()`, `routePattern` (L-06, L-07) | https://docs.astro.build/en/reference/routing-reference/ |
| On-demand routes cannot use `getStaticPaths()` or receive its props (L-06) | https://docs.astro.build/en/guides/routing/ |
| `Astro` deprecated inside `getStaticPaths()` (L-02) | https://docs.astro.build/en/guides/upgrade-to/v6/ |
| Endpoint method exports, `satisfies APIRoute`, extension URL matching (L-08) | https://docs.astro.build/en/guides/endpoints/ |
| `404.astro` builds `404.html`; `500.astro` is on-demand only (L-37) | https://docs.astro.build/en/basics/astro-pages/ |
| Redirect config, external URLs, `<meta http-equiv="refresh">` fallback, file routes beating redirects (L-06, L-17) | https://docs.astro.build/en/guides/routing/ |
| `Astro.rewrite()` keeps the URL and re-runs middleware (L-06) | https://docs.astro.build/en/guides/routing/ |
| `astro sync` generates `.astro/types.d.ts` (L-28) | https://docs.astro.build/en/reference/cli-reference/ |
| Legacy content collections removed in 6.0, current file is `src/content.config.ts` (L-02, L-10) | https://docs.astro.build/en/guides/upgrade-to/v6/ |
