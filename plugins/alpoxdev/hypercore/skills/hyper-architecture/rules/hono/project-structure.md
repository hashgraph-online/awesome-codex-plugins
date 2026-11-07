# Project Structure and Ownership

> Read this rule for folder design, app composition ownership, feature growth, monorepos, or structural refactors. Official Hono facts are summarized in [`../../references/official/hono/hono-docs.md`](../../references/official/hono/hono-docs.md); the layouts below are Hypercore conventions unless marked otherwise.

## 1. Choose a profile from repository evidence

Inspect the package/runtime, source roots, entrypoints, route mounts, aliases, workspace boundaries, generated files, database and migration configuration, OpenAPI generation, tests, and current import graph. Preserve a coherent brownfield layout unless a touched boundary is unsafe or blocks the requested change.

Use the smallest profile that gives every dependency one clear owner:

| Profile | Use when | Add now |
|---|---|---|
| Compact | A small API with a few routes and little reusable domain or persistence logic | Runtime entry, `app.ts`, flat routes, only evidenced shared support |
| Product | Several domains, contributors, validators, persistence workflows, generated API docs, or typed clients | Domain route folders, service/repository boundaries, shared middleware and contract owners |
| Workspace | Multiple deployables or separately built clients consume server contracts | Product structure inside the server package plus a compiled contract package when justified |

Do not pre-create every directory. Promote a folder only when it has a distinct owner, dependency rule, or build/runtime contract. Empty layers and one-file pass-through abstractions are not scalability.

## 2. Ownership and dependency direction

```text
runtime entry -> app composition -> route module -> service/use case -> repository/client -> database/external system
```

| Concern | Default owner | Must not own |
|---|---|---|
| Runtime startup and adapter APIs | `runtime/`, `server.ts`, `worker.ts`, or configured entry | Domain routes or persistence policy |
| Root middleware, errors, not-found, version prefixes, route mounts | `app.ts` or one `routes/index.ts` mount table | Feature business logic |
| HTTP method/path, validation, auth gate, response shaping | `routes/<domain>/` | ORM queries, migrations, provider SDK details |
| Business decisions and multi-step transactions | `services/<domain>/` or feature-local `service.ts` | Hono `Context`, cookies, headers, raw request parsing |
| Queries and external SDK adaptation | `repositories/<domain>/`, `clients/<provider>/` | HTTP response shaping or route registration |
| Connection lifecycle, ORM schema, migration configuration | `database/`, configured schema/migration roots | Request routing |
| Shared API components and generated spec composition | `openapi/` and the app composition boundary | Duplicated feature operation definitions |

Dependencies point rightward/downward. Lower layers do not import Hono transport types. Feature route modules do not import another feature's route module; cross-feature workflows meet in a service/use case or a deliberately shared contract.

## 3. Compact layout

```text
src/
├── app.ts                    # runtime-neutral Hono composition and exported app type
├── server.ts                 # Node/Bun adapter; use worker.ts or index.ts when configured
├── lib/
│   └── create-app.ts         # only when shared Env/factory typing is needed
├── middleware/
│   └── request-id.ts         # only genuinely cross-cutting middleware
└── routes/
    ├── health.ts             # tiny operational endpoint
    └── users.ts              # small chained sub-app
```

A compact route may call a small pure helper directly. Add a service or repository only when business decisions, reuse, persistence, transactions, or external SDK behavior justify the boundary.

## 4. Product layout

```text
src/
├── app.ts                    # sole root composition and exported AppType surface
├── runtime/
│   ├── node.ts               # create only for supported adapters
│   └── worker.ts
├── config/
│   └── env.ts                # validated runtime configuration
├── middleware/
│   ├── auth.ts
│   └── request-id.ts
├── routes/
│   ├── index.ts              # optional sole mount table; do not duplicate app.ts ownership
│   ├── health.ts
│   └── users/
│       ├── index.ts          # chained usersApp export
│       ├── handlers.ts       # extracted with typed factory when needed
│       ├── schemas.ts        # request/response schemas
│       ├── routes.ts         # optional OpenAPI route definitions
│       ├── middleware.ts     # users-only middleware
│       └── users.test.ts
├── services/
│   └── users/
│       └── create-user.ts
├── repositories/
│   └── users/
│       └── users-repository.ts
├── clients/
│   └── mail/
│       └── mail-client.ts
├── database/
│   ├── client.ts
│   ├── schema.ts
│   └── types.ts
└── openapi/
    ├── components.ts
    └── registry.ts

drizzle/                     # generated migrations only when drizzle.config.ts points here
└── migrations/
```

The tree is illustrative; configured source, schema, and migration roots win.

## 5. Feature growth thresholds

| Pressure | Structural response |
|---|---|
| One tiny operational endpoint | Keep one route file |
| Validation or several handlers appear | Promote to `routes/<domain>/` and colocate route-only schemas/handlers |
| Business behavior is reused or independently testable | Add a feature-local or root `services/<domain>/` owner, following the existing repository pattern |
| Persistence/provider calls appear | Add a repository/client boundary; routes must not import DB tables, drivers, or provider SDKs |
| Two domains reuse a transport-agnostic contract | Promote that contract to a purpose-named shared owner; do not create a generic dumping-ground `utils/` |
| Multiple domains reuse middleware or OpenAPI components | Promote only the reused primitive to `middleware/` or `openapi/` |
| A second deployable consumes server RPC types | Consider a compiled contract package; do not deep-import server source across package boundaries |

Do not split by file count alone. A cohesive feature can remain colocated; a large file with mixed transport, business, and persistence ownership must be separated even if used once.

## 6. Composition and type surface

Official Hono guidance supports `app.route()` for larger applications and requires careful chaining for RPC inference. Keep exactly one obvious root composition path:

```ts
const routes = app
  .route('/users', usersApp)
  .route('/billing', billingApp)

export type AppType = typeof routes
export default app
```

- Put `/api` and version prefixes at the root mount or `basePath()` boundary.
- Register root middleware before affected routes and fallbacks last.
- Keep runtime startup separate from the reusable app so `app.request()` tests do not boot a server.
- Derive RPC clients, `testClient`, and generated OpenAPI from the same composed surface when the repository uses them.
- For very large RPC surfaces, prefer compiled declarations or deliberately split clients after measuring type-check/IDE pressure; never sacrifice the canonical server contract silently.

## 7. Workspace layout

```text
apps/
├── api/                     # Product profile; owns runtime and implementation
└── web/                     # consumes a stable client/contract package
packages/
└── api-contract/            # emitted types/client only when independently built and consumed
```

Keep `hono` versions compatible across producer and consumer, enable TypeScript `strict`, and use project references or emitted declarations according to the existing build system. A client package must not export database schema, secrets, runtime bindings, or server-only implementation modules.

## 8. Brownfield migration

1. Map actual entrypoints, mounts, imports, generated files, and configured roots.
2. Identify ownership violations and cycles before moving files.
3. Preserve public paths, middleware order, error behavior, `AppType`, OpenAPI output, and migration provenance.
4. Move one vertical slice at a time and update imports/configuration atomically.
5. Run focused route/request tests and type checks after each slice; keep the candidate only when behavior and guards pass.
6. Record untouched Hypercore-only drift as backlog when broad movement would exceed the request. Safety, validation, typing, persistence, and runtime-boundary violations in touched code still block.

This is a bounded migration loop: feedback is focused tests/type checks plus import-boundary inspection; the guard is unchanged public behavior and contracts; the maximum iterations equal the planned slices; discard or revert a slice that fails its guard before continuing.

## 9. Structural verification

- Confirm one runtime-neutral app and one obvious mount table.
- Confirm every route has an unambiguous owner and fallback order is preserved.
- Search routes/handlers for imports from DB clients, ORM tables, migrations, drivers, and provider SDKs.
- Search services/repositories for Hono `Context` and raw request/response dependencies.
- Check aliases, package exports, generated-file ownership, and schema/migration paths against configuration.
- Run type checking plus focused `app.request()` or `testClient()` tests for moved routes.
- When RPC/OpenAPI is present, verify the exported composed type/spec still includes representative routes and error shapes.
- Report untested runtimes, clients, migrations, or generated artifacts explicitly; do not infer success from file layout alone.

## Sources

> Checked 2026-11-04. No external source outside this package's own references informed this file; official Hono behavior is delegated to [`references/official/hono/hono-docs.md`](../../references/official/hono/hono-docs.md), verified 2026-11-04.
