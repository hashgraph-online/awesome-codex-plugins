# Web Stack Traps

Per-stack failure catalogs for TypeScript, React, accessibility, Next.js, SEO, database layers, and performance. Load the sections that match the stack in the diff.

## TypeScript Traps

Check these on every TypeScript file in the diff:

- **`any` vs `unknown`:** `any` disables type checking for everything downstream. If the type is truly unknown at the call site, use `unknown` and narrow with a type guard. Flag every `any` annotation that isn't in a third-party type shim.
- **Non-null assertions (`!`):** Each `foo!.bar` is a runtime crash waiting for the condition that makes `foo` null. Flag unless the null case is provably eliminated by a guard two lines above.
- **Missing discriminated unions:** When a function returns `{ type: 'a', ... } | { type: 'b', ... }`, the switch/if must be exhaustive. Missing `default: assertNever(x)` is a silent future bug.
- **Unsafe casts (`as Foo`):** A cast without a preceding type guard means "trust me." Flag every `as` that isn't a DOM cast (`as HTMLInputElement`) or a narrow type refinement proven by the preceding condition.
- **`Object.keys()` without `keyof typeof`:** `Object.keys(obj).forEach(k => obj[k])` fails type checking silently at runtime when keys are typed. Require `(Object.keys(obj) as Array<keyof typeof obj>)` or a typed `Object.entries()`.
- **`Promise` without `await` in an `async` function:** Returns the Promise object instead of the resolved value. Flag any `return someAsyncFn()` inside an `async` that should `return await someAsyncFn()`.

## React Traps

Check these on every React component or hook in the diff:

- **Missing `useEffect` dependency array:** `useEffect(fn)` (no array) runs on every render. `useEffect(fn, [])` runs once. `useEffect(fn, [dep])` runs when dep changes. Flag any effect where the deps array is absent or obviously incomplete (function references, object literals, values used inside the effect but not listed).
- **Stale closures:** An effect or callback captures a value at mount time and never re-captures it. Most common pattern: a `setInterval` inside `useEffect(fn, [])` that reads a stateful value. The fix is either adding the dep or using a ref.
- **Missing `key` props:** Any `.map()` returning JSX elements must have a stable, unique `key`. Using array index as key is a bug when the list can reorder or filter. Flag index-keyed lists where items have identity (id, slug, etc.).
- **Unnecessary re-renders:** Flag components that receive object or function props without `useMemo`/`useCallback` when those objects are created inline in the parent render. Flag components that could be wrapped in `React.memo` but aren't, when rendered in tight loops or high-frequency update paths.
- **Prop drilling past 2 levels:** If a prop is passed through 2+ components without being used at intermediate levels, flag as P3. The fix is context, Zustand, or component composition. Note which fits the existing pattern in this repo.
- **State mutation without setter:** `arr.push(item)` on state does not trigger a re-render. Flag any direct mutation of state variables.

## Accessibility Traps

Check these on every React component or HTML-producing file in the diff:

- **Missing alt text:** `<img>` without `alt`, or `alt=""` on non-decorative images. Empty alt skips the element for screen readers; flag when the image conveys content.
- **Interactive elements without accessible names:** `<button>`, `<a>`, `<input>` with no visible text, no `aria-label`, and no `aria-labelledby`. An icon-only button with no label is invisible to assistive tech.
- **Wrong element semantics:** `<div onClick={...}>` used as a button; `<span>` used as a link; heading levels skipped (h1 → h3) or used for visual styling instead of document hierarchy. Use the correct element or add `role=` with keyboard handlers.
- **Missing focus management:** modals, drawers, toasts, and route transitions that don't trap or restore focus. When a modal opens, focus must move inside it; when it closes, focus must return to the trigger.
- **Keyboard inaccessibility:** custom components (dropdowns, date pickers, carousels) that handle `onClick` but not `onKeyDown` (`Enter`, `Space`, arrow keys). Flag interactive elements that can't be reached or operated by keyboard alone.
- **Color contrast:** inline styles or Tailwind classes that set foreground/background color combinations. Flag likely failures: `text-gray-400` on white, `text-white` on light-colored buttons, any low-contrast pairing below ~4.5:1 for body text or ~3:1 for large text.
- **Missing form labels:** `<input>` or `<select>` without an associated `<label>` (via `htmlFor`/`id`) or `aria-label`. Placeholder text is not a label.
- **ARIA misuse:** `aria-hidden="true"` on interactive elements (traps keyboard users); `role="presentation"` on semantically meaningful elements; ARIA roles that contradict the native element's semantics.

## Next.js Traps

Check these on every Next.js file in the diff:

- **Server/client boundary:** Any file with `'use client'` cannot import server-only modules (DB clients, `fs`, `crypto`, server-side env vars). Any file without `'use client'` that uses `useState`, `useEffect`, browser globals (`window`, `document`), or event handlers is a runtime crash. Flag the mismatch, not just the symptom.
- **Missing `Suspense` boundary:** Async server components that fetch data and are rendered inside a client component tree need a `<Suspense fallback={...}>` wrapper. Missing boundaries cause the entire parent tree to suspend without a fallback.
- **Missing `error.tsx` / `loading.tsx`:** Any new route segment that fetches data or can throw should have both. Flag their absence as P2 when the route is user-facing.
- **Server-only secrets in client bundle:** `process.env.SECRET_KEY` in a `'use client'` file or in a prop passed from server to client component is exposed in the browser bundle. Only `NEXT_PUBLIC_*` vars are safe client-side. Flag any non-`NEXT_PUBLIC_` env var referenced in client code.
- **Unguarded `generateMetadata` / `getServerSideProps` fetches:** These run on every request. An uncached external fetch here is a latency and cost bomb. Flag missing `{ next: { revalidate: N } }`, a `'use cache'` directive (Next.js 16 Cache Components), or `unstable_cache` wrapping on older versions.
- **`useRouter` from `next/router` in App Router:** App Router uses `next/navigation`. Importing from `next/router` in an App Router project silently fails or returns stale data. Flag the wrong import.

## SEO Impact

Check on any file that touches routes, layouts, metadata, or public-facing content:

- **Metadata regression:** changes to `generateMetadata`, `<Head>`, `<title>`, `description`, `og:title`, `og:description`, `og:image`, `twitter:card`. Any removal or blanking of previously populated fields is a regression. Flag if `generateMetadata` now returns fewer keys than before the change.
- **Canonical drift:** `canonical` URL changed, removed, or now pointing to a different domain. Flag any change to canonical logic, canonical changes can consolidate or fragment link equity unintentionally.
- **Robots / noindex added unintentionally:** `noindex`, `nofollow`, or `X-Robots-Tag: noindex` appearing on pages that were previously indexable. Flag any new `robots` metadata that restricts crawling on a route that wasn't restricted before.
- **Sitemap impact:** new routes not added to sitemap; removed routes not pruned; `sitemap.ts` / `sitemap.xml` not updated when routes change. Flag route additions or removals without a corresponding sitemap change.
- **OG image regression:** `og:image` URLs broken, pointing to localhost, missing dimension params, or removed from previously covered pages. Flag layout-level changes that remove OG image generation entirely.
- **Structured data / JSON-LD drift:** `schema.org` markup changed, fields removed, or `@type` changed. Flag removals of `@type`, `name`, `url`, or `description` from any existing structured data block.
- **URL structure changes without redirects:** route renames, slug changes, or path restructuring without a corresponding 301. A renamed route without a redirect is a hard 404 for crawlers and any existing backlinks.
- **`llms.txt` / AI discoverability:** if the repo includes `llms.txt` or `llms-full.txt`, flag any changes that expand or restrict what AI crawlers are permitted to see.

## Database Traps (Drizzle / Prisma)

Check these on any file that touches DB queries:

- **N+1 queries:** A loop that issues a query per iteration. The fix is a single query with `WHERE id IN (...)` or a join. Flag any `.map()` or `for` loop that calls `db.query()`, `prisma.find*()`, or `db.select()` inside the body.
- **Missing index on filtered/sorted columns:** Any `WHERE`, `ORDER BY`, `GROUP BY`, or join condition on a column that isn't indexed is a full-table scan. Flag new query predicates on columns with no corresponding index in the migration/schema.
- **Multi-table writes without transactions:** Two or more `INSERT`/`UPDATE`/`DELETE` calls that must succeed or fail together. Flag any multi-table write that isn't wrapped in `db.transaction()` / `prisma.$transaction()`.
- **Missing unique constraints:** Fields that are logically unique (user email, slug, external ID) but lack a `UNIQUE` constraint are race-condition bugs at scale. Flag schema definitions where uniqueness is enforced in application code but not the DB.
- **Unbounded queries:** `db.select().from(table)` with no `LIMIT` on a user-facing route is a DoS vector and a cost spike. Flag selects with no limit when the table can grow.

## Performance Flags

- **Large dependency import:** Any new `import` of a package not already in the bundle. If the package's minzipped size is >20 KB, flag as P3 with the size estimate. Prefer tree-shaken imports (`import { X } from 'pkg'` not `import pkg from 'pkg'`).
- **Render-blocking scripts:** `<script src="...">` without `async` or `defer` in HTML head blocks page paint. Flag in any HTML template or `_document.tsx`.
- **Missing lazy loading for non-critical routes:** Any page-level component imported with a static `import` at the top of `_app.tsx` or a layout file when it could be `next/dynamic` (`ssr: false` is only allowed inside a Client Component in the App Router). Flag routes not in the critical path (settings pages, dashboards, modals).
- **Core Web Vitals regressions:** a change that adds layout shift (unsized media, late-injected banners), long main-thread tasks on interaction, or a heavier LCP element on a public route. Google's "good" thresholds are LCP at or under 2.5 s, INP at or under 200 ms, and CLS at or under 0.1 at the 75th percentile (https://web.dev/articles/vitals). Flag a likely regression on an indexed route as P2.
- **Images without `next/image`:** `<img src="...">` bypasses Next.js image optimization. Flag raw `<img>` tags in Next.js files pointing to non-SVG assets.
