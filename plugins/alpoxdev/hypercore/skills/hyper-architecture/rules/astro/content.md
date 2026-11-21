# Content Layer

> Model build-time content in `src/content.config.ts` with a loader and a Zod schema, sort every query explicitly, and reserve live collections for data that must not wait for a rebuild.

Rules here are labelled `official` when an opened page in the dated snapshot states them, and `hypercore-default` when this package chose the default.

## 1. Two kinds of collections

| Kind | Config file | When it loads | Needs an adapter |
|---|---|---|---|
| Build-time collection | `src/content.config.ts` | At build time | No |
| Live collection | `src/live.config.ts` | At request time | Yes |

`official` — The Content Layer is the only content API. Legacy content collections were removed in 6.0, so `src/content/config.ts` no longer exists as a location (L-02, L-10).

## 2. Build-time collections

`official` — `src/content.config.ts` exports `collections`; each entry has a required `loader` and an optional `schema` (L-10):

```ts
import { defineCollection, reference, z } from 'astro:content';
import { glob, file } from 'astro/loaders';

const blog = defineCollection({
  loader: glob({ base: './src/content/blog', pattern: '**/*.{md,mdx}' }),
  schema: z.object({
    title: z.string(),
    publishedAt: z.coerce.date(),
    draft: z.boolean().default(false),
    author: reference('authors'),
  }),
});

const authors = defineCollection({
  loader: file('./src/content/authors.json'),
  schema: z.object({ name: z.string(), url: z.url().optional() }),
});

export const collections = { blog, authors };
```

Rules:

- `official` — `glob()` and `file()` come from `astro/loaders`. `glob()` auto-generates URL-friendly ids; `file()` needs explicit `id` keys and accepts a custom `parser()` for CSV and other formats.
- `official` — Import `z` from `astro/zod`. The `z` re-export from `astro:content` was removed in 6.0, and `astro:schema` was removed too.
- `official` — `reference('authors')` defines a relation, and validation happens when the entry is resolved through `getEntry()` or `getEntries()`.
- `official` — `deferRender: true` (7.1) defers Markdown rendering until render time, which cuts build memory.
- `official` — Zod is version 4 since Astro 6.0: `z.email()` replaces `z.string().email()`, `{ error }` replaces `{ message }`, defaults must match the output type, and `.prefault()` supplies parsed defaults (L-02).
- `hypercore-default` — Give every collection a schema. An untyped collection turns a content typo into a runtime page error instead of a build failure.

## 3. Querying

`official` — Query with `getCollection()` and `getEntry()`, and render with `render()` (L-10):

```astro
---
import { getCollection, render } from 'astro:content';

const posts = (await getCollection('blog', ({ data }) => !data.draft)).sort(
  (a, b) => b.data.publishedAt.valueOf() - a.data.publishedAt.valueOf(),
);

const { Content } = await render(posts[0]);
---
```

Rules:

- `official` — Collection order is non-deterministic. Sort explicitly whenever order is visible in the output.
- `official` — `render(entry)` returns `{ Content, headings, remarkPluginFrontmatter }`; do not reach for the entry's raw body to render it.
- `hypercore-default` — Put the filter and sort in a shared query helper when two or more routes need the same list, so the ordering rule lives in one place.

## 4. Live collections

`official` — Live collections live in a separate `src/live.config.ts`, are declared with `defineLiveCollection()`, use a custom loader implementing `loadCollection`/`loadEntry`, and are read with `getLiveCollection()`/`getLiveEntry()`. They need an adapter, and Astro ships no built-in live loaders (L-10).

Rules:

- `official` — A Zod schema is optional for a live collection but takes precedence over the loader's types when present.
- `official` — The live loader API shape (`loadCollection`/`loadEntry` return types and the error envelope) is described in prose only, not as a full signature page. Treat the exact return shape as unverified against a typed example.
- `official` — The 7.0 release notes show `Astro.cache.set(entry)` reading a loader-provided cache hint, while the caching guide documents only the explicit options object. Treat the hint form as unverified until the `astro:content` types confirm it.
- `hypercore-default` — Use a live collection only when freshness beats rebuilds. Pair it with route caching, otherwise every visitor triggers the upstream call.

## 5. TypeScript

`official` — `astro sync` generates `.astro/types.d.ts` for `astro:content`, `astro:env`, and `astro:actions`, and it runs automatically inside dev, build, and check (L-28).

- `official` — The `strict` and `strictest` tsconfig templates include what the content layer needs. The `base` template needs `strictNullChecks: true` and `allowJs: true`.
- `hypercore-default` — Do not hand-edit `.astro/types.d.ts`; a manual edit is lost on the next sync.

## 6. What not to do

- Do not create `src/content/config.ts`; the current location is `src/content.config.ts`.
- Do not read content files with `fs` inside a page when a collection would model them.
- Do not import `z` from `astro:content` or `astro:schema`.
- Do not present an unsorted `getCollection()` result as a stable order.
- Do not add a live collection to a project with no adapter.

## Checklist

- [ ] Every collection declares a `loader` and, unless it is a live collection, a `schema`.
- [ ] `z` comes from `astro/zod`, and Zod 4 syntax is used (`z.email()`, `{ error }`).
- [ ] `getCollection()` results are sorted wherever order is visible.
- [ ] `reference()` relations are resolved through `getEntry()`/`getEntries()`.
- [ ] Live collections have a custom loader, an adapter, and a caching plan.
- [ ] Unverified lane items (live loader signature, `Astro.cache.set(entry)`) are not presented as documented facts.
- [ ] `.astro/types.d.ts` was regenerated by `astro sync`, not edited by hand.

## Sources

> Checked 2026-11-07. Facts come from the Astro research lane, which opened these pages on 2026-11-07; lane source ids are kept in parentheses.

| Claim | Source |
|---|---|
| `src/content.config.ts`, required `loader`, optional Zod `schema`, `glob()`/`file()` (L-10) | https://docs.astro.build/en/guides/content-collections/ |
| `glob()` id generation, `file()` explicit ids and custom parser, `deferRender` (L-10, L-50) | https://docs.astro.build/en/guides/content-collections/ |
| `getCollection()`/`getEntry()`, non-deterministic order, `render(entry)` (L-10) | https://docs.astro.build/en/reference/modules/astro-content/ |
| `reference()` relations validated on resolution (L-10) | https://docs.astro.build/en/guides/content-collections/ |
| Live collections in `src/live.config.ts`, `defineLiveCollection()`, custom loader, adapter requirement (L-10) | https://docs.astro.build/en/guides/content-collections/ |
| Zod 4 in 6.0 with `z.email()`, `{ error }`, `.prefault()` (L-02) | https://docs.astro.build/en/guides/upgrade-to/v6/ |
| Legacy collections, `astro:schema`, and the `z` re-export removed in 6.0 (L-02) | https://docs.astro.build/en/guides/upgrade-to/v6/ |
| `astro sync` generates `.astro/types.d.ts` for content, env, and actions (L-28) | https://docs.astro.build/en/reference/cli-reference/ |
| tsconfig template requirements for the content layer (L-10) | https://docs.astro.build/en/guides/content-collections/ |
| Route caching to pair with request-time data (L-30) | https://docs.astro.build/en/guides/caching/ |
