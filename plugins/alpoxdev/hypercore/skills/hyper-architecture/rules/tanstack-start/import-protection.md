# Import Protection

> Enforce Start client/server import boundaries without hiding the fact that Start has defaults.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Start import protection exists and is enabled by default | Official | Verify behavior before custom config |
| The documented option table is stable enough to rely on; `mockAccess` is undocumented | Official | Cite documented options; re-check `mockAccess` per version |
| `.server.*` denied from client and `.client.*` denied from server | Official | Block leaks |
| Marker imports restrict modules to one environment | Official | Use when suffix is not enough |
| Custom deny rules/tanstack-start for `database/`, `server/`, ORM packages | Safety policy | Add/extend when project needs them |
| Never disable import protection silently | Safety policy | Block unless user explicitly requests |

## Official Defaults

TanStack Start import protection is enabled by default. Do not claim an explicit `importProtection` object is always required.

The guide no longer carries an Experimental banner. It documents the defaults table, the replace-vs-additive semantics, and the `include`, `exclude`, `ignoreImporters`, `maxTraceDepth`, and `onViolation` options. `mockAccess` is the exception: it is real in the plugin schema and absent from the guide, so it stays in the undocumented bucket.

Dev-mode violations can be false positives: build mode defers the check until after tree-shaking, so an import that disappears from the production graph may still warn in dev. Confirm a suspicious dev warning with a production build before editing the boundary.

Documented defaults (Official, the guide's option table):

| Option | Default |
|---|---|
| `enabled` | `true` |
| `behavior` | `{ dev: 'mock', build: 'error' }` |
| `log` | `'once'` |
| `include` | Start's `srcDirectory` |
| `maxTraceDepth` | `20` |

Default-denied patterns include:

- Client environment: `**/*.server.*` and Start server specifiers.
- Server environment: `**/*.client.*`.

Type-only imports and re-exports are ignored because they are erased from the runtime bundle. Mixed imports still count when they include runtime values.

## Marker Imports

```typescript
import '@tanstack/react-start/server-only'
import '@tanstack/react-start/client-only'
```

- Use one marker at most per file.
- Use markers when file names cannot clearly express the environment boundary.

## Custom Deny Rules

Add explicit `tanstackStart({ importProtection })` config when the project needs stronger rules/tanstack-start for directories or packages:

```typescript
import { tanstackStart } from '@tanstack/react-start/plugin/vite'

export default defineConfig({
  plugins: [
    tanstackStart({
      importProtection: {
        behavior: { dev: 'mock', build: 'error' },
        client: {
          files: ['**/*.server.*', '**/server/**', '**/database/**', '**/db/**'],
          specifiers: ['@prisma/client', 'bcrypt'],
        },
        server: {
          files: ['**/*.client.*', '**/client/**'],
          specifiers: ['localforage'],
        },
      },
    }),
  ],
})
```

## Replace vs Additive (Official)

The guide's option table marks each key, and this is the trap: some keys extend the built-in rules/tanstack-start and some replace them outright.

| Key | Semantics | Default it touches |
|---|---|---|
| `client.specifiers` | Additive with defaults | framework server specifiers |
| `client.files` | Replaces defaults | `['**/*.server.*']` |
| `client.excludeFiles` | Replaces defaults | `['**/node_modules/**']` |
| `server.files` | Replaces defaults | `['**/*.client.*']` |
| `server.specifiers` | Replaces defaults | `[]` — unlike `client.specifiers` it is therefore not additive in practice |
| `server.excludeFiles` | Replaces defaults | `['**/node_modules/**']` |

Setting `client.files` without re-listing `'**/*.server.*'` silently drops the default deny rule, which is why the example above repeats it. `excludeFiles` **fully replaces** `['**/node_modules/**']`; to keep skipping `node_modules` while excluding more paths, pass both patterns: `excludeFiles: ['**/node_modules/**', '**/vendor/**']`.

If `tanstackStart()` already exists, extend only the relevant nested options. Do not duplicate plugins or overwrite unrelated options.

Use `behavior: 'error'` when a project wants violations to fail even in development. Current options also include `log`, `include`, `exclude`, `ignoreImporters`, `maxTraceDepth`, and `onViolation` for scoped enforcement and diagnostics.

`client` and `server` rules/tanstack-start support `files`, `specifiers`, and `excludeFiles` (read the replace-vs-additive table above before setting any of them). The default excludes resolved files under `node_modules`; setting `excludeFiles: []` opts back into those checks for the selected environment and should be deliberate because third-party packages can produce false positives.

`mockAccess` (`'error' | 'warn' | 'off'`, default `'error'`) exists in `@tanstack/start-plugin-core@1.171.55`'s `schema.d.ts`, where it controls whether mocked imports emit a runtime console diagnostic under `behavior: 'mock'`. It is **absent from the official guide's option table** — a real schema option that the docs do not document. Cite it as undocumented and re-check it against the installed package types before relying on it; never present it as a documented option.

## Compiler Boundary Leak Rule

Server-only imports used inside a `createServerFn` handler may be removed from the client build. If the same import is referenced by code that survives client compilation, import protection should flag it.

Fix with one of:

- Split the surviving helper into `*.server.*`.
- Wrap the helper with `createServerOnlyFn`.
- Move browser-only code behind `*.client.*` or `createClientOnlyFn`.
- Put server function wrappers in `*.functions.ts` and split DB/secret/filesystem helpers to sibling `*.server.ts`.
- Do not mix safe exports with server-only exports in `src/modules/<domain>/<feature>/index.ts` or `-functions/index.ts`.

## Server Function Import Shape

Server function wrappers themselves may be statically imported from loaders/components/hooks. A wrapper still leaks if surviving client-build exports reference server-only helpers outside the handler boundary.

Recommended:

```text
src/modules/users/profile/
├── profile.functions.ts  # createServerFn exports
├── profile.server.ts     # DB/secret helper
└── profile.schemas.ts    # client-safe schema
```

Blocked or warned:

- `profile.functions.ts` references `profile.server.ts` from a helper export outside the handler.
- `index.ts` re-exports both `profile.functions.ts` and `profile.server.ts`.
- Client components import `*.server.ts`, `src/db/**`, or privileged SDKs directly.
- Server functions are dynamically imported, obscuring bundler rewrite/import-protection traces.

## Validation Checklist

- [ ] Import protection is not disabled.
- [ ] Custom deny rules/tanstack-start are present when project directories/packages require them.
- [ ] Type-only imports are not misreported as runtime boundary leaks.
- [ ] Existing `tanstackStart()` options are extended, not overwritten.
- [ ] `behavior: 'error'` vs `{ dev, build }` behavior is chosen intentionally.
- [ ] Custom `client.files` / `server.files` / `excludeFiles` lists re-state the defaults they replace.
- [ ] `excludeFiles: []` is used only when third-party resolved-file checks are intentionally required.
- [ ] `.server.*`, `.client.*`, and marker imports are used consistently.
- [ ] Server-only imports do not survive outside recognized boundaries.
- [ ] `*.functions.ts` wrappers and `*.server.ts` helpers are split.
- [ ] There are no mixed safe/server-only barrels.
- [ ] Dev warnings are confirmed with production build when tree-shaking might remove false positives.

## Sources

> Sources checked 2026-11-04: <https://tanstack.com/start/latest/docs/framework/react/guide/import-protection.md> (defaults table, replace-vs-additive semantics, documented option surface; the page carries no Experimental banner) and `@tanstack/start-plugin-core@1.171.55`'s `schema.d.ts` (`mockAccess` enum and default). They are carried in this package's own 2026-11-04 snapshot, `references/official/tanstack-start/current-docs-2026-11-04.md`; no external source is a runtime dependency. Repository-local links checked 2026-11-04.
