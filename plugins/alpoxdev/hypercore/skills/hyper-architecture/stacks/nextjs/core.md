Stack guide inside `hyper-architecture` for Next.js. Read it when `rules/stack-detection.md` routes a target to Next.js; from then on this file owns that target's work.

- Scope: Use this skill when the user asks to audit, change, or extend an existing Next.js project, especially App Router work or an App Router migration that touches Server/Client boundaries, data and cache freshness, mutations, Route Handlers, Proxy, env or platform setup, or shared folder layout. It enforces current official Next.js behavior plus labelled Hypercore conventions. Do not use it for generic React architecture, Remix or TanStack Start projects, or copy-only edits that cross no architectural boundary.
- Runtime needs: Works best with repo inspection, official Next.js docs verification, and direct code edits in Next.js applications.

@architecture-rules.md
@../../rules/nextjs/routes.md
@../../rules/nextjs/project-structure.md
@../../rules/nextjs/execution-model.md
@../../rules/nextjs/data-fetching.md
@../../rules/nextjs/server-actions.md
@../../rules/nextjs/route-handlers.md
@../../rules/nextjs/services.md
@../../rules/nextjs/hooks.md
@../../rules/nextjs/db.md
@../../rules/nextjs/platform.md
@../../rules/nextjs/validation.md
@../../references/official/nextjs/current-docs-2026-11-04.md
@../../references/official/nextjs/nextjs-docs.md
@../../references/official/nextjs/drizzle-docs.md

# Next.js Architecture Enforcement

<output_language>

Default all user-facing deliverables, saved artifacts, reports, plans, generated docs, summaries, handoff notes, commit/message drafts, and validation notes to Korean, even when this canonical skill file is written in English.

Preserve source code identifiers, CLI commands, file paths, schema keys, JSON/YAML field names, API names, package names, proper nouns, and quoted source excerpts in their required or original language.

Use a different language only when the user explicitly requests it, an existing target artifact must stay in another language for consistency, or a machine-readable contract requires exact English tokens. If a localized template or reference exists (for example `*.ko.md` or `*.ko.json`), prefer it for user-facing artifacts.

</output_language>

<purpose>

- Confirm a repository is a Next.js project and identify App Router, Pages Router, or mixed mode before enforcing architecture rules.
- Enforce official Next.js behavior for file conventions, Server/Client Component boundaries, data/cache behavior (Cache Components is the recommended default since 16.4), Server Actions, Route Handlers, Proxy, and env/platform safety.
- Apply Hypercore/repo-local conventions for nested shared folders such as `src/modules/<domain>/`, `src/services/<domain>/`, `src/db/<area>/`, `src/server/<area>/`, `src/integrations/<provider>/`, and `src/config/<area>/` without presenting them as official Next.js law.
- Route Drizzle, DAL/service boundaries, and client hook orchestration to focused rule files, and keep version-sensitive official facts in `references/official/nextjs/` so the core stays lean.

</purpose>

<routing_rule>

Use this skill for architecture enforcement, implementation guidance, or review in existing Next.js projects, especially App Router work, App Router migration, Server/Client boundaries, cache/freshness, Server Actions, Route Handlers, Proxy, env/platform safety, service/DAL boundaries, client hook orchestration, Drizzle/DB placement, and nested shared-folder organization.

Do not use this skill for generic React architecture, Remix/TanStack Start projects, docs-only summaries, or copy-only edits that do not touch architectural boundaries beyond a quick safety check. In Pages Router-only projects, apply shared Next.js safety/platform checks but do not force App Router-only file conventions unless migration is requested.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Keep Next.js projects architecturally safe and aligned with official docs plus labelled Hypercore/repo-local conventions. |
| Trigger | Next.js project work involving App Router, Pages Router, Server/Client boundaries, data/cache behavior, Server Actions, Route Handlers, Proxy, platform/env, or shared folder layout. |
| Scope | Review and guide touched project architecture, topic rule files, official references, validation notes, and small reversible architecture fixes. |
| Authority | User/project instructions outrank this skill. Current official Next.js docs outrank local conventions for framework behavior. Safety policy blocks risky runtime, auth, secret, and import-boundary changes. |
| Evidence | Use local package/config/router indicators, touched source paths, topic rules/nextjs, official references, validation scripts, and project check output. |
| Tools | Use local search/read/edit/validation commands; use current official docs when API drift matters; gate destructive migrations, credentials, production side effects, and broad codemods. |
| Loop | None. This skill runs a single enforcement pass per request and re-enters only when the user asks for another pass. |
| Output | Korean architecture decision or review with rule classifications, changed files if any, validation evidence, remaining risks, and dated official-doc ambiguity notes. |
| Verification | Run `rules/nextjs/validation.md` checks relevant to touched surfaces and `bash skills/hyper-architecture/scripts/validate-architecture.sh` when this skill folder changes. |
| Stop condition | Stop after project mode is known, applicable safety gates pass, local conventions are applied or deferred, validation evidence is recorded, and unresolved API drift is dated and sourced. |

</instruction_contract>

<activation_examples>

Positive examples:

- "Audit this Next.js App Router feature for Server/Client boundaries and cache correctness."
- "Refactor this form to use Server Actions instead of an internal route handler."
- "Add a Route Handler for a webhook and verify it follows the current Next.js docs."
- "Next.js 16 cacheComponents 기준으로 data fetching 규칙을 점검해줘."
- "Next.js App Router에서 src/lib/auth/session.ts와 src/services/billing/mutations.ts처럼 nested shared folders로 정리해줘."
- "Add Drizzle schema and migrations to this Next.js app without leaking DB access into client hooks."
- "Split this Next.js form into client hooks, Server Actions, and a server-only service/DAL."

Negative examples:

- "Create a generic React architecture guide."
- "Review a Remix or TanStack Start app."
- "Write marketing copy for a Next.js landing page without touching architecture."

Boundary examples:

- "Make a tiny copy-only text change in a Next.js page." Direct editing can be enough if no architectural boundary is affected, but touched files still need a quick boundary check.
- "This repo is Pages Router only and I am not migrating to App Router." Apply shared Next.js platform, env, and server/client safety checks; relax App Router-only file conventions.

</activation_examples>

<trigger_conditions>

Router mode picks the rule set; the table in `stacks/nextjs/architecture-rules.md` § Project Modes owns the modes. No `next` dependency ends the run.

| If the task sounds like... | Default surface | Avoid by default |
|---|---|---|
| Add a form or internal UI mutation in App Router | Server Action | `route.ts` RPC |
| Add a webhook, feed, CORS endpoint, public API, XML, JSON, or stream | Route Handler | Server Action |
| Fetch initial page data for UI | Server Component | Client-first fetching |
| Add interactivity, browser APIs, or client hooks | Narrow Client Component | Root-level `'use client'` |
| Add client orchestration around a Server Action | Client hook calling the action | Hook importing DB/DAL/server-only code |
| Add domain logic, provider calls, or authorization | Server-only service/DAL layer | Route file or Client Component ownership |
| Add Drizzle schema, migrations, repositories, or DB client | `rules/nextjs/db.md` + server-only `src/db` convention | Client hooks or Route Handler request lifecycle |
| Cache repeatable data/UI in Next.js 16.4+ (recommended default) | `cacheComponents` + `partialPrefetching` + `use cache` / `cacheTag` / `cacheLife` | stale `fetch` default assumptions |
| Keep synchronous values out of the static shell | `io()` inside `<Suspense>` | `connection()` where `io()` would stay cacheable |
| Stage expensive work behind the App Shell or navigation | `prefetch()`, `navigation()`, `ensureStatic` | unprefetched blocking work |
| Refresh UI after mutation | `updateTag`, `revalidateTag`, `revalidatePath`, `refresh`, or redirect flow | undocumented freshness |
| Redirect/rewrite before render across many requests | `next.config.*` first, then Proxy if needed | Proxy as generic middleware |
| Pages Router only and no migration requested | shared Next.js checks | App Router-only file rules/nextjs |

</trigger_conditions>

<skill_architecture>

- Core (`stacks/nextjs/core.md`): trigger, contract, gate order, verification, stop condition. Rules: `stacks/nextjs/architecture-rules.md` (taxonomy and gate summary) plus the eleven topic files listed in `reference_routing`.
- References: `references/official/nextjs/current-docs-2026-11-04.md`, `nextjs-docs.md`, `drizzle-docs.md` hold dated official facts; `assets/evals/nextjs-cases.jsonl` holds trigger and behavior cases.
- The skill is self-contained and needs no other skill's path, document, or invocation.

## Available scripts

`scripts/validate-architecture.sh` validates the skill folder itself: every stack guide exists with its rule set, every local Markdown path resolves, every English file has its Korean sibling, code fences balance, guides stay within their size caps, and the eval fixtures parse. Run `bash skills/hyper-architecture/scripts/validate-architecture.sh` from the repository root (bash 3.2+, jq 1.6+); it prints a JSON summary and exits non-zero on failure.

</skill_architecture>

<loop_policy>

No optimization loop. One enforcement pass per request: gates, edits, verification. Verification runs once per request; a second pass happens only on a new request or a reported failure and re-runs only the checks tied to the touched surface. Findings come from the gate tables and project checks, not from rereading the same diff.

</loop_policy>

<language_and_translation_default>

Write findings, reviews, and change summaries in Korean. Keep identifiers, file paths, route segments, API names, and rule labels (`BLOCKED`, `WARNING`) in their source form so the report maps one-to-one onto the tables here. `stacks/nextjs/core.ko.md` mirrors this file section by section; a rule changed here is changed there in the same edit.

</language_and_translation_default>

<reference_routing>

Read `stacks/nextjs/architecture-rules.md` first, always. Then read only the files for the touched surface:

| Touched surface | File |
|---|---|
| File conventions, segment rules/nextjs, route groups, private folders, parallel/intercepted routes | `rules/nextjs/routes.md` |
| Top-level project shape, `src/`, nested `src/modules` / `src/services` / `src/db` / `src/server` / `src/integrations` / `src/config` | `rules/nextjs/project-structure.md` |
| Server/Client Components, `'use client'`, providers, serializable props, `server-only` | `rules/nextjs/execution-model.md` |
| Server-first reads, streaming, Cache Components, `use cache`, cache tags, revalidation | `rules/nextjs/data-fetching.md` |
| `use server`, forms, validation, auth, DAL delegation, freshness after mutation | `rules/nextjs/server-actions.md` |
| `route.ts`, HTTP methods, caching intent, params, CORS, webhooks | `rules/nextjs/route-handlers.md` |
| DAL/service/provider boundaries, DTOs, authorization delegation | `rules/nextjs/services.md` |
| Client hook orchestration and its boundaries | `rules/nextjs/hooks.md` |
| Drizzle schema, migrations, connection lifecycle, server-only DB placement | `rules/nextjs/db.md` |
| Env, `next.config.*`, `typedRoutes`, Proxy, route segment config, deployment settings | `rules/nextjs/platform.md` |
| Post-change checks for the touched surface | `rules/nextjs/validation.md` |
| Bundle weight, rendering and cache cost, Core Web Vitals, React Compiler, `next analyze`, `next/image` | `rules/nextjs/performance.md` |
| Lint, format, and type-check setup (oxlint, Prettier, tsconfig, package manager pinning) | `rules/setup/typescript.md` |
| Next.js behavior that may have drifted since the snapshot | `references/official/nextjs/current-docs-2026-11-04.md`, then `references/official/nextjs/nextjs-docs.md`; `references/official/nextjs/drizzle-docs.md` for Drizzle claims |

Fetch `https://r.jina.ai/https://nextjs.org/docs/...` only when the two official snapshots disagree or the page must be read as markdown.

</reference_routing>

<support_file_read_order>

1. `stacks/nextjs/architecture-rules.md` before any finding or edit.
2. The topic rule for the touched surface, in `reference_routing` order.
3. `rules/nextjs/validation.md` when the change is written and needs its checks.
4. The official snapshots — `current-docs-2026-11-04.md`, then `nextjs-docs.md`, then `drizzle-docs.md` for a Drizzle claim — only when framework behavior is version-sensitive.

</support_file_read_order>

<workflow>

| Phase | Task | Output |
|---|---|---|
| 0 | Confirm the project and router mode | Mode decision |
| 1 | Load only the rule files for the touched surface | Minimal evidence set |
| 2 | Judge the planned change against Gates 1–6 | Findings labelled BLOCKED or WARNING |
| 3 | Apply the implementation policy: auto-fix local reversible issues, refuse broad migrations | Edits or refusal with reason |
| 4 | Run the post-change checks and report evidence | Verification record |

Phase 0 uses the project-detection commands in `rules/nextjs/validation.md`; no `next` dependency ends the run.

Phase 2 — gates. Brownfield rule: do not fail untouched legacy deviations by default; safety, secret, auth, and boundary issues block immediately in touched files; bring touched files into compliance unless that requires a broad migration.

### Gate 1: Routing, File Conventions, and Project Structure

| Check | Rule |
|---|---|
| `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`, or `route.ts` placed outside valid segment structure | BLOCKED |
| `route.ts` and `page.tsx` created in the same route segment | BLOCKED |
| Route group used as if it changes the URL | BLOCKED |
| Private implementation files exposed as routable segments instead of `_folder` | BLOCKED |
| Shared `src/modules` / `src/services` / `src/db` / `src/server` / `src/integrations` / `src/config` organization forced flat or direct-leaf when nested domain/provider grouping would clarify touched code | WARNING. Prefer nested grouping |
| Repo-local folder preferences reported as official Next.js law | BLOCKED |
| Parallel/intercepted routes added without matching layout slots or hard-navigation behavior | WARNING/BLOCKED by risk |

### Gate 2: Server and Client Boundaries

| Check | Rule |
|---|---|
| Interactive component missing `'use client'` | BLOCKED |
| `'use client'` added high in the tree without need | BLOCKED |
| Client Component imports DB code, private env, `cookies()`, `headers()`, or server-only helpers | BLOCKED |
| Props crossing Server→Client are broad, secret-bearing, or non-serializable | BLOCKED |
| Provider wraps broader tree than needed | WARNING |
| Client hook imports DB, Drizzle schema, DAL, private env, `cookies()`, `headers()`, or server-only provider clients | BLOCKED |

### Gate 3: Data Fetching, Cache, and Freshness

| Check | Rule |
|---|---|
| Initial UI data fetched in a Client Component without client-only need | BLOCKED |
| Cache behavior is accidental, undocumented, or based on stale defaults | BLOCKED |
| `cacheComponents` enabled but uncached runtime data lacks `use cache`, `io()`, `loading.tsx`, or `<Suspense>` intent | BLOCKED |
| `cacheComponents` enabled without `partialPrefetching`, or `partialPrefetching` without `cacheComponents` | BLOCKED |
| `use cache` scope has no `cacheLife` and the effective lifetime cannot be stated | BLOCKED |
| `use cache` reads `cookies()` / `headers()` inside the cached scope instead of receiving serializable arguments | BLOCKED unless `use cache: private` is justified because the runtime read cannot move outward |
| `connection()` used to leave the static shell where `io()` would keep the output cacheable and prefetchable | WARNING |
| `use cache: private` nested with `use cache: remote`, or used with no runtime-read reason | BLOCKED |
| `unstable_noStore` added for new App Router work instead of `io()` or `connection()` | BLOCKED unless maintaining legacy code |
| Mutation lacks `updateTag`, `revalidateTag`, `revalidatePath`, `refresh`, redirect freshness, or documented alternative | BLOCKED |

### Gate 4: Server Actions

| Check | Rule |
|---|---|
| Internal UI mutation implemented with `route.ts` even though a Server Action fits | BLOCKED unless HTTP semantics are required |
| Action trusts `FormData`, params, headers, or search params without validation/reverification | BLOCKED |
| Action relies only on page-level auth checks | BLOCKED |
| Action returns raw DB rows or broad internal objects | BLOCKED |
| Action bypasses a needed server-only service/DAL boundary for authz, DTO shaping, or provider orchestration | WARNING/BLOCKED by risk |
| `redirect()` runs before required revalidation or tag update | BLOCKED |
| Client code assumes parallel Server Action dispatch, or uses `Promise.all` to achieve it | BLOCKED |
| Action expects `revalidateTag(tag, 'max')` to re-render the current route in its response | BLOCKED |
| `updateTag` or `refresh` called outside a Server Action | BLOCKED |

### Gate 5: Route Handlers and Proxy

| Check | Rule |
|---|---|
| Route Handler used as default internal RPC for UI-only flow | BLOCKED |
| `NextResponse.next()` used inside a Route Handler | BLOCKED |
| Route Handler caching is assumed rather than explicit where correctness matters | BLOCKED |
| `use cache` placed directly in a Route Handler body instead of a helper function | BLOCKED |
| Fresh `middleware.ts` added instead of `proxy.ts` | BLOCKED |
| Proxy added when `next.config.*`, headers, redirects, rewrites, or render-time logic is enough | BLOCKED |
| Proxy matcher is missing, too broad, or fails to exclude metadata/static surfaces where needed | BLOCKED |

### Gate 6: Platform and Environment

| Check | Rule |
|---|---|
| `.env*` files assumed to load from `src/` | BLOCKED |
| Client code reads non-`NEXT_PUBLIC_` env vars | BLOCKED |
| Runtime client env treated as build-time public env | BLOCKED |
| Removed v16 route segment config options (`dynamic`, `dynamicParams`, `revalidate`, `fetchCache`) used while `cacheComponents` is enabled | BLOCKED |
| `runtime` export added or kept, including `runtime: 'edge'` or `runtime: 'nodejs'` under `cacheComponents` | BLOCKED |
| Deployment-sensitive Server Action origin, body-size, or encryption-key changes are undocumented | WARNING/BLOCKED by risk |

Phase 3 — implementation policy. Auto-fix local, reversible issues: narrow client boundaries, move server-only code behind a DAL/helper, add `server-only`, add missing freshness, replace UI-only `route.ts` mutations with small Server Actions, tighten Proxy matcher, and clarify cache intent. Do not auto-apply broad migrations: Pages→App Router rewrites, sweeping cache model changes, mass Route Handler→Server Action conversions, or deployment-sensitive origin/encryption changes.

Phase 4 runs the post-change checks in the validation section with the commands in `rules/nextjs/validation.md`, and records the executed commands as evidence.

</workflow>

<required>

- A proven project mode before any rule is applied, and a stated reason when the mode excludes App Router rules.
- The four enforcement defaults: official docs outrank local convention; App Router rules/nextjs by default for `app/`; Server Actions for App Router UI-originated writes; every Server Action treated as a reachable POST entry point.
- Every finding tied to a gate row and labelled BLOCKED or WARNING, with repo-local conventions labelled as such.
- Post-change evidence from the checks in Phase 4 that apply to the touched surface.
- `bash skills/hyper-architecture/scripts/validate-architecture.sh` run when this skill folder itself changes.

</required>

<forbidden>

- Applying App Router file conventions to a Pages Router-only project that did not ask for migration.
- Reporting a Hypercore/repo-local folder preference as official Next.js behavior.
- Auto-applying Pages→App Router rewrites, mass mutation-style conversions, or cache-model sweeps.
- Touching credentials, production side effects, or deployment-sensitive origin/encryption settings without explicit authority.
- Silencing a gate because the same pattern exists untouched elsewhere in the repository.
- Claiming verification that was not run, or recording a gate as passed without its executed check.

</forbidden>

<validation>

- [ ] Project mode is proven and matches the edited surface.
- [ ] Every touched file was judged against Gates 1–6 and the applicable rows are recorded.
- [ ] `'use client'` boundaries are narrow, no client file reaches server-only code or private env, and cache and freshness behavior is explicit and matches the current snapshot.
- [ ] Route Handler and Proxy usage is justified, and repo-local conventions are labelled rather than presented as framework law.
- [ ] Remaining risk, deferred migrations, and dated API ambiguity are reported.
- [ ] The bundled validator passed when this skill folder changed.

Stop condition: the Next.js mode is known, all touched surfaces pass the relevant gates, verification output is fresh, and any remaining repo-local convention or risk is explicitly reported.

</validation>
