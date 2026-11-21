# Code Conventions

> Hono project coding rules/hono

---
## Stable Compatibility Rule

Project tooling owns formatting and import order. Hono does not require kebab-case paths, arrow functions, or one universal import grouping; those are Hypercore conventions and must be reported as such.

- Inspect the formatter, linter, TypeScript mode, module resolution, aliases, generated files, and runtime before enforcing style.
- Preserve Hono's inferred route types; do not add broad annotations solely to satisfy a style preference.
- Prefer `unknown` at untrusted boundaries and narrow through validators or explicit guards.
- Keep `import type` when required by the compiler/linter and avoid runtime imports created only for types.
- Never hand-edit generated route trees, declarations, OpenAPI artifacts, or migrations unless their owning tool and repository workflow explicitly permit it.
- A path rename is behavioral: update case-sensitive imports, exports, tests, aliases, package exports, config, and generated references atomically.

## Folder And File Naming

> camelCase and PascalCase source paths are forbidden. Keep source folders and files in kebab-case.

| Type | Rule | Example |
|------|------|---------|
| General files | kebab-case | `create-app.ts`, `request-id.ts` |
| Route folders | kebab-case | `routes/user-profile/` |
| Feature folders | kebab-case | `services/user-profile/`, `repositories/audit-log/` |
| Database folders | kebab-case | `database/`, `drizzle/migrations/` |
| Handler files | kebab-case | `handlers.ts`, `list-users.ts` |
| Schema files | kebab-case | `schemas.ts`, `user-payload.ts` |
| Middleware | kebab-case | `auth.ts`, `request-id.ts` |

Allowed exceptions:

- Tool-required root files such as `package.json`, `tsconfig.json`, `drizzle.config.ts`, lockfiles, and generated declaration files
- Provider-generated migration artifacts when the configured migration tool requires a specific name
- Framework conventions already present in the repo, only when renaming would break external contracts

In `전체 수정` mode, scan all detected Hono source folders and files, then rename kebab-case violations when every import, test path, route reference, and config reference can be updated in the same change.

---

## TypeScript Rules

| Rule | Description | Example |
|------|-------------|---------|
| Function style | const arrow function, explicit return type | `const handler = (c: Context): Response => {}` |
| No any | Use unknown or concrete types | `const payload: unknown = await c.req.json()` |
| Type imports | Separate type imports | `import type { Context } from 'hono'` |
| App generics | Type `Bindings` and `Variables` when used | `new Hono<AppEnv>()` |

---

## Import Order

```ts
import { Hono } from 'hono'
import { createFactory } from 'hono/factory'
import { zValidator } from '@hono/zod-validator'

import { createApp } from '@/lib/create-app'
import { authMiddleware } from '@/middlewares/auth'
import { createUser } from '@/services/users/create-user'

import { userSchema } from './schemas'

import type { AppEnv } from '@/lib/types'
```

---

## Comment Style

- Prefer short block comments only where a code group needs orientation
- Do not add line-by-line narration
- Keep comments durable and architecture-oriented

## Sources

> Checked 2026-11-04. No external source outside this package's own references informed this file; official Hono behavior is delegated to [`references/official/hono/hono-docs.md`](../../references/official/hono/hono-docs.md), verified 2026-11-04.
