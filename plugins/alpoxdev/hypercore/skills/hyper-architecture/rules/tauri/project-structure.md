# Project Structure and Ownership

> Use this rule when adopting or reviewing the renderer/Rust boundary in a Tauri v2 application. Read the dated evidence first: [Tauri v2 evidence](../../references/official/tauri/tauri-v2-2026-11-04.md) and [TanStack + Vite + React evidence](../../references/official/tauri/tanstack-vite-react-2026-11-04.md).

## Decision Summary

There is no universal React directory layout. This skill uses a **scale-triggered route/page/module structure** synthesized from Tauri's frontend/Rust split, TanStack Router's file-routing contract, React colocation guidance, and the feature-folder pattern documented by Redux. The layout is a Hypercore convention; configured framework paths and established repository conventions win.

| Concern | Default owner | Classification |
|---|---|---|
| Frontend versus native code | repository-top JavaScript project (commonly `src/`) separated from Rust/config in `src-tauri/` | Tauri official documented shape |
| URL hierarchy and route lifecycle | `src/routes/` and generated `src/routeTree.gen.ts` | TanStack Router official fact |
| Routed screen composition | `src/pages/<screen>/` once a route is no longer trivial | Hypercore convention |
| Business/domain capability | `src/modules/<domain>/` | Hypercore convention informed by feature-folder practice |
| Reusable business-agnostic UI | `src/components/` | Hypercore convention |
| Tauri renderer adapters | `src/platform/tauri/` | Hypercore convention enforcing the native boundary |
| App bootstrap and global composition | `src/main.tsx`, `src/router.tsx`, `src/app/` | Hypercore convention |
| Cross-cutting non-UI primitives | `src/shared/` with purpose-named children | Hypercore convention |

TanStack Router owns file-based routing. TanStack Query owns asynchronous cache and freshness. A `pages/`, `modules/`, or `components/` folder does not change either ownership.

## Grow by Evidence, Not by Template

Choose the smallest tier justified by current code:

| Tier | Use when | Add now |
|---|---|---|
| Compact | A few routes, each with small UI and little domain logic | Bootstrap, Router files, `routes/`, typed Tauri adapter, generated tree |
| Standard | Multiple screens or one domain has reusable UI/data/model behavior | Add `pages/`, `modules/`, `components/`, `app/`, and narrowly scoped `shared/` children as needed |
| Large | Several domains and teams, or independent application shells | Strengthen module public APIs and dependency checks; extract workspace packages only when two applications need a stable shared contract |

Do not pre-create empty tiers or every child shown below. Promote code when an observable pressure exists:

- Create a **page** when a route component becomes a screen composition, has substantial page-only UI, or needs an independently testable screen boundary.
- Create a **module** when a domain owns at least two of UI, queries, mutations, validation/model, or orchestration that evolve together.
- Create a shared **component** when two independent page/module owners need the same business-agnostic UI contract.
- Create a shared library only when it has one nameable responsibility and at least two owners.

## Compact Layout

A small application stays flat where the framework contract benefits from it:

```text
src/
├── main.tsx                 # sole React bootstrap
├── router.tsx               # one QueryClient, typed context, one router
├── routeTree.gen.ts         # generated; never hand-edit
├── routes/
│   ├── __root.tsx
│   └── index.tsx
└── platform/
    └── tauri/
        └── desktop-api.ts   # narrow typed IPC facade
```

Keeping a trivial page component in its route file is acceptable. Do not create `pages/`, `modules/`, or `components/` merely to move one file one directory deeper.

## Standard Layout

This is the recommended target once the compact layout has real ownership pressure. Omit every optional directory that has no current file.

```text
.
├── package.json
├── index.html
├── vite.config.ts
├── tsconfig.json
├── public/                              # intentionally public static inputs only
├── src/
│   ├── main.tsx                         # sole root; renders app providers
│   ├── router.tsx                       # module-owned QueryClient, context, router
│   ├── routeTree.gen.ts                 # Router plugin output; never hand-edit
│   ├── app/                             # application-wide composition only
│   │   ├── providers.tsx                # provider composition used by main.tsx
│   │   ├── app-shell.tsx                # global chrome/error boundary when needed
│   │   └── styles/                      # global styles and design tokens
│   ├── routes/                          # URL and route-lifecycle adapters
│   │   ├── __root.tsx
│   │   ├── index.tsx
│   │   ├── (workspace)/                 # URL-neutral organizational group
│   │   │   └── settings.tsx             # thin route -> SettingsPage
│   │   ├── _unlocked.tsx                # optional pathless layout
│   │   └── -route-support/               # ignored route-local helpers only
│   ├── pages/                           # routed screen composition
│   │   └── settings/
│   │       ├── settings-page.tsx
│   │       ├── settings-page.test.tsx
│   │       └── parts/                   # page-only UI, when it improves navigation
│   ├── modules/                         # cohesive business/domain capabilities
│   │   └── settings/
│   │       ├── ui/                      # module-owned reusable UI
│   │       ├── queries/                 # queryOptions factories
│   │       ├── mutations/               # mutation options and invalidation policy
│   │       ├── model/                   # schemas, domain types, pure state rules/tauri
│   │       ├── services/                # domain orchestration, only when needed
│   │       └── index.ts                 # deliberate public API
│   ├── components/                      # cross-module business-agnostic UI
│   │   └── ui/                          # Button, Dialog, Field; no domain policy
│   ├── platform/
│   │   └── tauri/                       # renderer-side typed IPC/plugin adapters
│   │       ├── desktop-api.ts
│   │       └── settings.ts
│   ├── shared/                          # cross-cutting non-UI primitives
│   │   ├── config/                      # public renderer configuration parsing
│   │   ├── hooks/                       # truly cross-domain hooks
│   │   ├── lib/                         # purpose folders such as date/ or result/
│   │   └── test/                        # shared test builders, when actually shared
│   └── assets/                          # imported renderer assets
├── src-tauri/
│   ├── Cargo.toml
│   ├── build.rs
│   ├── tauri.conf.json                  # human-owned v2 configuration
│   ├── capabilities/                    # human-owned capability manifests
│   ├── permissions/                     # app-command permissions, when used
│   ├── icons/
│   └── src/
│       ├── main.rs                      # thin desktop binary entry
│       ├── lib.rs                       # application setup and registration
│       ├── commands/                    # Tauri command transport boundary
│       ├── domain/                      # native domain types/policies, when needed
│       ├── services/                    # native use cases, when needed
│       ├── infrastructure/              # filesystem/keychain/network adapters
│       └── state/                       # managed Tauri state, when needed
├── frontend-build-output/               # generated; exact path matches frontendDist
└── src-tauri/target/                    # generated Cargo output
```

`main.tsx` is the only React bootstrap and renders the provider composition. `router.tsx` owns the exact `QueryClient`, narrow renderer dependencies, typed router context, and router consumed by those providers. The route file remains discoverable and thin; the page composes modules; modules own domain behavior; shared UI and primitives remain domain-agnostic.

## Folder Contracts

### `routes/`: URL and lifecycle, not the whole feature

Route files may own `createFileRoute`, params/search validation, `loaderDeps`, loader/beforeLoad wiring, pending/error/not-found selection, and the import of one page. They must not become the default home for domain models, broad component trees, raw Tauri calls, or shared query policy.

Use Router naming deliberately:

- `(group)/` organizes route files without changing the URL or component tree.
- `_layout.tsx` creates a pathless layout and therefore changes component nesting.
- `-name` excludes a file/folder from generation; use it only for small route-exclusive helpers.
- `route.tsx`, `index.tsx`, `$param`, and the configured tokens follow the installed Router plugin settings.

If route-local support grows beyond a few tightly coupled files, move screen composition to `pages/` or domain behavior to `modules/` rather than turning `routes/` into a second source tree.

### `pages/`: routed screen composition

A page represents one user-visible screen or a small family of closely related screens. It may compose module UI, shared components, and page-only parts. It must not own URL conventions, raw IPC, globally reusable domain behavior, or a second cache. Page-only code stays beside the page until another independent owner appears.

`pages/` does not duplicate `routes/`: the route is the URL/lifecycle adapter; the page is the rendered screen composition.

### `modules/`: cohesive domain capability

Use one stable domain or capability name such as `settings`, `documents`, or `workspace`. Do not create both top-level `features/` and `modules/`; preserve an established repository term, otherwise use `modules/` here.

A module adds only the segments it needs:

- `ui/` for module-owned reusable presentation;
- `queries/` for Query option factories and keys;
- `mutations/` for writes and precise invalidation/update policy;
- `model/` for schemas, types, and pure domain state rules;
- `services/` for multi-step orchestration that does not belong in a component;
- `index.ts` as a small public API when external owners import the module.

Do not create one module per component, route, query, or user click. Modules are cohesive change units, not taxonomy labels.

### `components/`: shared UI, with a promotion rule

Keep a component beside its page or module by default. Promote it to `components/` only when at least two independent owners use the same business-agnostic contract. `components/ui/` may contain primitives such as `Button`, `Dialog`, or `Field`; it must not import a page, module, Router route, Query key, or Tauri adapter.

Avoid a global `components/` dump containing domain-specific `SettingsForm`, `DocumentToolbar`, and unrelated one-off UI. Those remain under their owning module/page.

### `app/`, `platform/`, and `shared/`

- `app/` composes the application: providers, shell, top-level error handling, global styles. Business modules must not import from it.
- `platform/tauri/` owns command names, invocation/plugin selection, argument/result validation, and normalized renderer errors. It imports no page or module UI.
- `shared/` contains business-agnostic non-UI primitives. Prefer `shared/lib/date/` or `shared/lib/result/` over generic `utils.ts`, `helpers.ts`, or a global `types.ts`.
- `public/` and `assets/` are delivery locations, not domain owners. Never store secrets in either.

## Dependency Direction

Keep imports one-way:

```text
main/app -> routes/router -> pages -> modules -> platform/tauri
                           \          \-> components -> shared
                            \-------------------------> shared

Tauri command -> native service/use case -> domain -> infrastructure adapter
```

Practical rules:

1. Routes may import pages, module query factories needed by loaders, and typed context contracts; they do not import module internals through deep paths.
2. Pages may compose modules and shared components; one page must not import another page.
3. Modules may depend on `components/`, `platform/tauri/`, and `shared/`; sibling modules communicate through declared public APIs or a higher page/app composition, not deep imports.
4. `components/`, `platform/`, and `shared/` never import pages or modules.
5. Renderer code never imports files from `src-tauri/`. Shared TypeScript types do not bypass Rust validation or authorization.
6. Rust commands validate/map transport data and call native services; infrastructure does not depend back on commands, windows, or renderer modules.

Use path aliases only when they preserve these boundaries. An alias must not hide a forbidden upward or deep import.

## Generated, Public, and Human-Owned Files

| Path or class | Owner | Rule |
|---|---|---|
| `src/routeTree.gen.ts` or configured equivalent | `@tanstack/router-plugin/vite` | Never hand-edit; change route sources/config and regenerate |
| configured frontend output | Vite build | Fix source/config, rebuild, and align `frontendDist` with `build.outDir` |
| `src-tauri/target/` | Cargo | Never edit or review as application source |
| `src-tauri/gen/**` when created by mobile tooling | Tauri generator | Regenerate through the relevant Tauri command |
| `app > appDirectoriesOverride` in `tauri.conf.json` | Application team | Relocates `app_config_dir`, `app_data_dir`, `app_local_data_dir`, `app_cache_dir`, `app_log_dir`, and the `$APPCONFIG`-style path variables for Tauri and for plugins that use those APIs; re-check persisted data, log paths, and asset scopes when it changes |
| `src-tauri/tauri.conf.json`, capabilities, permissions, Rust source | Application team | Review and edit intentionally |
| module `index.ts` | Module owner | Export the supported surface only; do not mirror every internal file |
| lockfiles | Package manager under repository policy | Change only through a declared dependency operation |

## Brownfield Adoption

1. Inventory `vite.config.*`, route directories/tokens, generated tree path, aliases, Vite `build.outDir`, Tauri `devUrl`/`frontendDist`, package scripts, capabilities, permissions, and command registration.
2. Map current folders to responsibilities before renaming them. Do not add `pages/`, `modules/`, and `components/` simultaneously unless current files already need each boundary.
3. Pick one vocabulary. If the repository consistently uses `features/`, keep it and apply the `modules/` contract there; do not create a competing folder.
4. Move one route/page/module seam at a time, update all direct imports/tests, regenerate the route tree, and verify navigation plus affected Query/IPC behavior.
5. Move configuration last and preserve resolved output/command paths throughout the migration.
6. Stop when ownership is clear. A working small app does not need the standard tree, and a large app does not need every FSD-style layer or a workspace package by default.

Do not use a folder migration to smuggle in a Tauri v1 migration, permission expansion, dependency upgrade, workspace conversion, or release change.

## Review Gate

Reject or correct a structure when any condition holds:

1. Router-generated files are hand-edited, or route naming/group/exclusion semantics conflict with plugin configuration.
2. `routes/` contains broad feature implementation, while `pages/` duplicates URL ownership or `modules/` duplicates route files.
3. Both `features/` and `modules/` exist without an explicit, non-overlapping contract.
4. Global `components/`, `hooks/`, `types/`, `utils/`, or `services/` act as unowned dumping grounds.
5. A shared component contains domain policy, a page owns reusable domain state, or a module imports another module's internals.
6. Raw Tauri calls appear in routes/pages/components, or renderer folders import Rust implementation files.
7. Empty folders or layers were scaffolded without current owners, or a workspace/package extraction has only one consumer.
8. `frontendDist`, generated route-tree path, or human/generated ownership is ambiguous.

## Sources

> Links checked 2026-11-04.

Official constraints:

- Tauri project structure: <https://v2.tauri.app/start/project-structure/>
- Tauri application configuration: <https://v2.tauri.app/reference/config/>
- Tauri Rust commands / IPC: <https://v2.tauri.app/develop/calling-rust/>
- Tauri capabilities: <https://v2.tauri.app/security/capabilities/>
- TanStack Router file-based routing: <https://tanstack.com/router/latest/docs/framework/react/routing/file-based-routing>
- TanStack Router file naming: <https://tanstack.com/router/latest/docs/framework/react/routing/file-naming-conventions>
- TanStack Router context: <https://tanstack.com/router/latest/docs/framework/react/guide/router-context>
- TanStack Query overview: <https://tanstack.com/query/latest/docs/framework/react/overview>

Comparative organization evidence, not dependencies or framework mandates:

- React file-structure FAQ (legacy, explicitly non-prescriptive): <https://legacy.reactjs.org/docs/faq-structure.html>
- Redux feature/domain folder discussion: <https://redux.js.org/faq/code-structure/>

Hypercore layout conventions, not vendor mandates:

- `pages/`, `modules/`, `components/`, `platform/`, `shared/`, the tier table, and the promotion rules/tauri are this repository's convention; no external source
