Stack guide inside `hyper-architecture` for Astro. Read it when `rules/stack-detection.md` routes a target to Astro; from then on this file owns that target's work.

- Scope: Use this guide when the user asks to build, audit, or restructure an Astro project, or to move an existing site onto Astro, and the work touches page routing, the rendering mode or adapter, islands and framework integrations, content collections, Actions, middleware, sessions, environment variables, route caching, testing, or build performance. It enforces current official Astro behavior (7.x, snapshot dated 2026-11-07) plus labelled Hypercore conventions. Do not use it for a Vite app that has no Astro dependency, a Next.js, TanStack Start, Expo, or Lynx app, a standalone Hono server, or a copy-only edit that crosses no architecture boundary.
- Runtime needs: Works best with repository inspection, official Astro docs verification against `references/official/astro/astro-2026-11-07.md`, and direct code edits in Astro projects.

@architecture-rules.md
@../../rules/astro/project-structure.md
@../../rules/astro/rendering-and-islands.md
@../../rules/astro/content.md
@../../rules/astro/actions-middleware-env.md
@../../rules/astro/testing.md
@../../rules/astro/performance.md
@../../references/official/astro/astro-2026-11-07.md

# Astro Architecture Enforcement

<output_language>

Default all user-facing deliverables, saved artifacts, reports, plans, generated docs, summaries, handoff notes, commit/message drafts, and validation notes to Korean, even when this canonical skill file is written in English.

Preserve source code identifiers, CLI commands, file paths, schema keys, JSON/YAML field names, API names, package names, proper nouns, and quoted source excerpts in their required or original language.

Use a different language only when the user explicitly requests it, an existing target artifact must stay in another language for consistency, or a machine-readable contract requires exact English tokens. If a localized template or reference exists (for example `*.ko.md` or `*.ko.json`), prefer it for user-facing artifacts.

</output_language>

<purpose>

- Prove the target is an Astro project and record which signal fired before applying any Astro rule.
- Establish the rendering mode (`output`) and the adapter before recommending a server feature, because Actions, sessions, server islands, live collections, and route caching all need one.
- Keep `src/pages/` routing, island hydration, content collections, server entrypoints, and the environment boundary coherent.
- Label stricter-than-official requirements as Hypercore conventions when reporting findings.
- Keep version-sensitive facts in `references/official/astro/astro-2026-11-07.md` so this core stays lean and the 300-line cap holds.

</purpose>

<routing_rule>

Use this guide for Astro implementation, review, remediation, or architecture enforcement.

Do not force it onto a Vite-only project, another app framework, a standalone Hono server, or a copy-only change that crosses no architecture boundary. An Astro project also depends on `vite` and may depend on `hono`; those are implementation details of the Astro target, not separate stacks. A Hono layer mounted through `astro/hono` adds the Hono guide only when that layer is itself touched.

This skill is self-contained. Do not block on other skills or external orchestration surfaces just to apply Astro rules.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Keep Astro projects architecturally safe and aligned with official Astro 7.x behavior plus labelled Hypercore conventions. |
| Trigger | Astro work involving pages and routes, endpoints, `output` and adapters, islands, content collections, Actions, middleware, sessions, env, caching, testing, or build performance. |
| Scope | Review and guide touched Astro source, topic rule files, the dated official snapshot, validation notes, and small reversible architecture fixes. |
| Authority | User and project instructions outrank this skill. Official Astro docs outrank Hypercore conventions for framework facts. Safety, authorization, secret, and data-boundary rules block unsafe changes. |
| Evidence | Project indicators, local manifests and config, touched paths, topic rules, the dated snapshot, and validation command output. |
| Tools | Local search, read, edit, and validation commands; gate migrations, credential access, production side effects, adapter swaps, and broad rewrites. |
| Loop | No optimization loop. After a remediation pass, allow at most two verify-repair iterations against the gates for the touched surface, and stop when the checklist passes or a blocker is reported. |
| Output | Korean architecture finding or implementation summary with rule labels, changed files, validation evidence, remaining risks, and official-versus-Hypercore distinctions. |
| Verification | Run `astro check` plus the touched surface's checks from `rules/astro/testing.md`; run `bash skills/hyper-architecture/scripts/validate-architecture.sh` when this skill folder itself changes. |
| Stop condition | Stop after the stack and rendering mode are known, applicable gates pass or are reported as blockers, and validation evidence is recorded. |

</instruction_contract>

<activation_examples>

Positive examples:

- `Audit this Astro site's routing and decide which routes should be prerendered.`
- `Move this page to on-demand rendering so it can read the session cookie.`
- `Convert this whole page to a server island instead of switching the site to output: 'server'.`
- `Astro 콘텐츠 컬렉션 스키마와 정렬을 정리해줘.`
- `Add an Astro Action for this form and validate its input.`
- `Declare these environment variables through astro:env instead of import.meta.env.`
- `Astro 빌드가 느린데 어디부터 재야 하는지 봐줘.`
- `hyper-architecture 전체 수정`

Negative examples:

- `Review my Vite + React SPA router.`
- `Set up a Next.js App Router project.`
- `Write marketing copy for a landing page built with Astro.`

Boundary examples:

- `Fix a typo in an Astro page's Korean copy.` Direct editing is enough when no architectural boundary is touched.
- `Use official Astro defaults only, not the extra Hypercore conventions.` This guide still applies, but Hypercore-only strictness relaxes to optional findings.

</activation_examples>

<trigger_conditions>

The rendering mode and adapter pick the rule set. The gate table lives in `stacks/astro/architecture-rules.md`. No `astro` dependency and no `astro.config.*` ends the run.

| If the task sounds like... | Default surface | Avoid by default |
|---|---|---|
| Add a page or a nested route | A file under `src/pages/` | A hand-written route table |
| Add a JSON, XML, feed, or webhook endpoint | A `src/pages/**/*.ts` endpoint exporting `GET`/`POST` with `satisfies APIRoute` | A page that returns a Response |
| Add a static dynamic route | `getStaticPaths()` in a prerendered route | On-demand rendering for a fixed set of paths |
| Add a route that must read cookies or headers | `export const prerender = false` on that route, with an adapter | Switching the whole site to `output: 'server'` |
| Add one personalized fragment to a static page | `<Component server:defer />` server island | Converting the whole page to on-demand rendering |
| Add an interactive widget | A framework component with the narrowest `client:*` directive | `client:load` on everything |
| Model build-time content | `src/content.config.ts` with a loader and a Zod schema | `fs` reads inside pages |
| Serve data that must not wait for a rebuild | `src/live.config.ts` plus `getLiveCollection()` and an adapter | Rebuilding the site per change |
| Handle an internal form write | An Astro Action in `src/actions/` | A hand-rolled POST page |
| Share auth, redirects, or request state | `src/middleware.ts` exporting `onRequest` and typed `locals` | Per-page duplication |
| Read configuration or secrets | `env.schema` in `astro.config.*` plus `astro:env/client` or `astro:env/server` | `import.meta.env` scattered through shared code |
| Custom worker entrypoint or mounted Hono | `src/fetch.ts` with `astro/fetch` or `astro/hono` | Authorization by `url.pathname` prefix |
| Cache a repeated on-demand response | `cache` provider plus `Astro.cache.set()` or `routeRules` | Ad-hoc in-memory maps per route |
| Build or bundle is slow | `astro build --timings`, then one measured lever | Changing several build flags at once |

</trigger_conditions>

<skill_architecture>

- Core (`stacks/astro/core.md`): trigger, contract, gate order, verification, stop condition.
- Rules: `stacks/astro/architecture-rules.md` plus the six topic files mapped in `reference_routing`.
- Reference: `references/official/astro/astro-2026-11-07.md` holds the dated package, runtime, breaking-change, and config facts.
- Assets: `assets/evals/astro-cases.jsonl` holds trigger and behavior cases.
- No bundled script beyond the folder validator: `astro check`, the touched surface's tests, and the topic checklists are the verification surface.
- The skill is self-contained; it needs no other skill's path, document, or invocation.

</skill_architecture>

<loop_policy>

- No optimization loop. One review or remediation pass per request.
- After remediation, at most two verify-repair iterations run against the gates for the touched surface. A change stays only when it is inside the touched scope and passes those gates.
- The loop ends at the first passing checklist or at a reported blocker; it never widens the touched scope to reach a green result.
- Performance work is the exception that still measures: one lever, one production build, before and after numbers, and no claim without both.

</loop_policy>

<language_and_translation_default>

Write findings, remediation summaries, and validation notes in Korean. Keep identifiers, paths, route segments, API names, and the labels `official` and `hypercore-default` in their source form so a report maps one-to-one onto the rule files. `stacks/astro/core.ko.md` mirrors this file section by section; a rule changed here is changed there in the same edit.

</language_and_translation_default>

<reference_routing>

Read `stacks/astro/architecture-rules.md` before editing. Then open the one file that owns the touched surface.

| Touched surface | File |
|---|---|
| `src/pages` routing, dynamic routes, endpoints, redirects, rewrites, error pages, folder ownership, naming | `rules/astro/project-structure.md` |
| `output`, `prerender`, adapters, streaming, server islands, `client:*` directives, framework integrations | `rules/astro/rendering-and-islands.md` |
| `src/content.config.ts`, loaders, Zod schemas, `getCollection()`, references, live collections | `rules/astro/content.md` |
| Actions, middleware and `locals`, sessions, `astro:env`, `checkOrigin`, CSP, `src/fetch.ts` authorization | `rules/astro/actions-middleware-env.md` |
| `astro check`, tsconfig, Vitest, Container API, Playwright, oxlint and Prettier for `.astro` | `rules/astro/testing.md` |
| Build time, island hydration choice, images, fonts, prefetch, view transitions, inline stylesheets, route caching | `rules/astro/performance.md` |
| Lint, format, type-check, tsconfig, package manager pinning (setup track) | `rules/setup/typescript.md` |
| Astro behavior that may have drifted since the snapshot | `references/official/astro/astro-2026-11-07.md` |

When the user asks for official defaults, start from the snapshot, treat Hypercore-only rules as optional overlays, and label which findings are which.

</reference_routing>

<support_file_read_order>

1. `stacks/astro/architecture-rules.md` for the rule taxonomy and gate summary.
2. The topic file for the touched surface, in `reference_routing` order.
3. `references/official/astro/astro-2026-11-07.md` when framework behavior or an official-defaults request is in play.
4. `rules/astro/performance.md` only for the performance track, and only after the architecture surface is settled.

</support_file_read_order>

<workflow>

| Phase | Task | Output |
|---|---|---|
| 0 | Prove the target is an Astro project, then record `output`, the adapter, and the framework integrations | Scope decision |
| 1 | Load the rule files for the touched surface | Minimal evidence set |
| 2 | Judge the planned change against the gates in `stacks/astro/architecture-rules.md` | Findings labelled BLOCKED or WARNING |
| 3 | Apply local, reversible fixes; refuse broad migrations | Edits or a refusal with reason |
| 4 | Run the touched surface's checks and record the commands | Verification record |

Phase 0 — project validation:

```bash
rg -n '"astro"' package.json
ls astro.config.mjs astro.config.ts astro.config.js astro.config.cjs 2>/dev/null
ls -d src/pages src/content.config.ts src/live.config.ts src/actions src/middleware.ts src/fetch.ts 2>/dev/null
rg -n 'adapter:|output:|@astrojs/(react|preact|svelte|vue|solid-js|alpinejs|node|vercel|cloudflare|netlify)' astro.config.* package.json
```

If no `astro` dependency and no `astro.config.*` exist, stop and route back to the normal path instead of forcing Astro rules. An `astro` dependency with no `src/pages/` is a broken project, not a different stack: report it, because without that folder the site has no routes.

Phase 2 gates, in order:

1. **Rendering and adapter** — every server feature the change needs has an adapter and an explicit `prerender` decision.
2. **Routing and structure** — routes live in `src/pages`, dynamic routes declare their mode, and endpoints are endpoints.
3. **Islands** — no framework JavaScript ships without a `client:*` directive and a reason, and no non-serializable prop crosses the boundary.
4. **Content** — collections have a loader and a schema, and query results are sorted explicitly.
5. **Server boundaries** — Actions, middleware, sessions, and env follow their ownership and authorization rules.
6. **Verification** — `astro check` passes and the touched surface's checks ran.

Phase 3 — implementation order:

1. Fix `src/pages` layout and dynamic-route mode.
2. Fix `output`, `prerender`, and adapter placement.
3. Fix island directives and prop serializability.
4. Fix content collection loaders, schemas, and sorting.
5. Fix Actions, middleware, sessions, and env declarations.
6. Run verification.

Do not auto-apply: switching `output`, adding or swapping an adapter, converting a static site to on-demand rendering, mass-migrating `import.meta.env` to `astro:env`, replacing legacy content collections, or rewriting the route tree.

</workflow>

<required>

- A proven Astro target and a named rendering mode before any rule is applied.
- An explicit answer for "does this change need an adapter?" whenever the change touches Actions, sessions, server islands, live collections, or route caching.
- The touched surface's rule file read, and official-override mode applied when requested.
- A report that labels each finding `official` or `hypercore-default`.
- Verification evidence from `astro check` and the touched surface's checks.

</required>

<forbidden>

- Forcing Astro rules on a Vite-only app or on another framework because the request sounds similar.
- Routing an Astro target to the Vite guide because `vite` appears in its manifest.
- Adding a server feature while `output` is `'static'` and no adapter is installed.
- Switching the whole site to `output: 'server'` to make one route dynamic.
- Presenting a Hypercore convention as official Astro behavior.
- Silencing a gate because untouched legacy code shows the same pattern.
- Claiming a check ran when it did not, or reporting a gate as passed without its output.

</forbidden>

<validation>

- [ ] Astro detection confirmed, with the firing signal named.
- [ ] `output`, the adapter, and the framework integrations are recorded.
- [ ] The touched surface's rule file was read, and official-override mode applied when requested.
- [ ] Every route the change touches has an explicit prerender decision, and dynamic routes match their mode.
- [ ] Islands carry a directive with a stated reason, and no non-serializable value crosses a hydration or server-island boundary.
- [ ] Actions validate input and authorize; middleware results reach pages through typed `locals`.
- [ ] Environment variables are declared in the schema and imported from `astro:env`, with no secret reachable from client context.
- [ ] `astro check` passes, and the touched surface's tests ran.
- [ ] Final findings distinguish official Astro rules from Hypercore conventions.

</validation>
