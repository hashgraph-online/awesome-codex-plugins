# Actions, Middleware, Sessions, and Environment

> Treat every Action as a public POST endpoint, share request state through typed `locals`, require a session driver before using sessions, and declare every environment variable in the `astro:env` schema.

Rules here are labelled `official` when an opened page in the dated snapshot states them, and `hypercore-default` when this package chose the default.

## 1. Actions

`official` — Actions live in `src/actions/index.ts`, which exports a `server` object built from `defineAction({ input, handler })` (L-11, L-12):

```ts
import { defineAction, ActionError } from 'astro:actions';
import { z } from 'astro/zod';

export const server = {
  logout: defineAction({
    handler: async (_input, context) => {
      const session = context.session;
      if (!session?.get('user')) {
        throw new ActionError({ code: 'UNAUTHORIZED', message: 'Not signed in' });
      }
      session.destroy();
      return { ok: true };
    },
  }),

  renameProject: defineAction({
    input: z.object({ id: z.string(), name: z.string().min(1).max(80) }),
    handler: async (input) => ({ ...input, updated: true }),
  }),
};
```

Rules:

- `official` — Actions require server output. With static-only output Astro throws `ActionsWithoutServerOutputError` (L-57).
- `official` — Action URLs are public at `/_actions/<name>`. The docs say "you must use the same authorization checks that you would consider for API endpoints" (L-11).
- `official` — `input` is a Zod validator, and a failure returns `BAD_REQUEST` without calling the handler.
- `official` — Without `input`, JSON requests receive `unknown` and form requests receive `FormData`. `accept: 'form'` declares a FormData action.
- `official` — Zero-JS forms work with `<form method="POST" action={actions.logout}>` on an on-demand-rendered page, and the result is read with `Astro.getActionResult()`.
- `official` — Throw `ActionError({ code: 'UNAUTHORIZED' })` for an authorization failure, and gate at the middleware level with `getActionContext(context)` when the check applies to every action.
- `hypercore-default` — Group Actions by domain in `src/actions/<domain>.ts` and re-export them from `src/actions/index.ts`. Nothing outside that `server` object is callable.
- `hypercore-default` — Validate every non-trivial input with Zod, and authorize inside the handler even when middleware also gates the route. Middleware can be bypassed by a direct `/_actions/<name>` call if it is not action-aware.

## 2. Middleware

`official` — Middleware lives in `src/middleware.ts` or `src/middleware/index.ts` and exports a named `onRequest` (L-13):

```ts
import { defineMiddleware, sequence } from 'astro:middleware';

const auth = defineMiddleware(async (context, next) => {
  const session = context.session;
  context.locals.user = session?.get('user') ?? null;
  return next();
});

const timing = defineMiddleware(async (_context, next) => {
  const start = performance.now();
  const response = await next();
  response.headers.set('x-render-ms', String(performance.now() - start));
  return response;
});

export const onRequest = sequence(auth, timing);
```

Rules:

- `official` — The export is a named `onRequest`, not a default export.
- `official` — `context.locals` is per-request and cannot be reassigned; assign its fields instead.
- `official` — Type `locals` with `declare namespace App { interface Locals { user: User | null } }` in `src/env.d.ts`.
- `official` — Compose middleware with `sequence(a, b, c)`; order is execution order.
- `hypercore-default` — Put authorization and redaction in middleware only when the rule applies to a whole route group, and still keep the check inside any Action that mutates.
- `hypercore-default` — Keep middleware free of page rendering concerns. It normalizes the request, resolves identity, and sets `locals`; pages read `locals`.

## 3. Sessions

`official` — Sessions (5.7+) are read and written through `Astro.session` or `context.session`, with `get`, `set`, `regenerate`, and `destroy` (L-14).

- `official` — A session needs a driver. The Node, Cloudflare, and Netlify adapters configure one automatically; Vercel needs explicit configuration.
- `official` — `session: false` (7.2+) removes the runtime and the adapter's default driver.
- `official` — Call `regenerate()` after a privilege change such as sign-in, and `destroy()` on sign-out.
- `hypercore-default` — Store an identifier in the session, not the whole user record; re-read the record on each request so a revocation takes effect immediately.

## 4. Environment variables

`official` — Declare variables in `env.schema` inside `astro.config.*` and import them from `astro:env/client` or `astro:env/server` (L-15, L-17):

```js
import { defineConfig, envField } from 'astro/config';

export default defineConfig({
  env: {
    schema: {
      PUBLIC_API_URL: envField.string({ context: 'client', access: 'public' }),
      API_SECRET: envField.string({ context: 'server', access: 'secret' }),
      PORT: envField.number({ context: 'server', access: 'public', default: 4321 }),
      MODE: envField.enum({
        context: 'server',
        access: 'public',
        values: ['development', 'staging', 'production'],
      }),
    },
    validateSecrets: true,
  },
});
```

Rules:

- `official` — The field helpers are `envField.string`, `number`, `boolean`, and `enum`, each taking `context: 'client' | 'server'`, `access: 'public' | 'secret'`, and optional `optional`/`default`.
- `official` — A `context: 'client'` field can never be `access: 'secret'`; the docs call that impossible by design ("no safe way to send this data to the client").
- `official` — Secrets are validated whenever anything imports `astro:env/server`, so builds may need placeholder values. `env.validateSecrets: true` validates them at dev and build start.
- `official` — `astro:env` cannot be used in `astro.config.mjs` or standalone scripts; use `process.env` there.
- `official` — `getSecret('KEY')` reads a raw value programmatically; it is adapter-provided and defaults to `process.env`.
- `official` — `import.meta.env.PUBLIC_*` still works and is client-visible, but only `PUBLIC_`-prefixed variables reach the client through that path.
- `official` — `astro:env` public client variables are compiled into the client bundle from the schema, independent of the `PUBLIC_` prefix.
- `hypercore-default` — Declare every variable in the schema and import from `astro:env`. Do not read secrets through `import.meta.env` in shared code, because that path has no validation and no context guarantee.

## 5. Security settings

`official` — `security.checkOrigin` defaults to `true` and is a CSRF guard: it checks `Sec-Fetch-Site` (falling back to `Origin`) for `POST`/`PATCH`/`DELETE`/`PUT` requests with no content type or a form-compatible one, and returns 403 for cross-origin requests (L-17).

| Setting | Default | Effect |
|---|---|---|
| `security.checkOrigin` | `true` | CSRF guard on unsafe methods |
| `security.allowedDomains` | unset | Validates `X-Forwarded-Host` against allowed patterns |
| `security.csp` | `false` | Emits a per-page CSP `<meta>` with hashes for Astro output |
| `security.actionBodySizeLimit` | 1 MB | Caps Action request bodies |
| `security.serverIslandBodySizeLimit` | 1 MB | Caps server island request bodies |

Rules:

- `official` — Keep `checkOrigin` on unless a documented reason exists.
- `official` — Set `allowedDomains` behind a proxy or CDN that rewrites `X-Forwarded-Host`. Unmatched headers are ignored and the original host is used.
- `official` — CSP emits a `<meta http-equiv="content-security-policy">` per page with hashes for Astro-emitted scripts and styles. `algorithm` accepts `'SHA-256'`, `'SHA-384'`, `'SHA-512'`, and `directives` accepts extra directives.
- `official` — CSP limits: external scripts and styles need your own hashes, `<ClientRouter />` view transitions are not supported, Shiki is not supported (use Prism), `'unsafe-inline'` suppresses hashes for that directive, and the feature does not work in dev mode — test with a build and preview.
- `official` — Only the meta-tag mechanism is documented; do not claim header-based CSP delivery from this source.
- `hypercore-default` — Do not enable `security.csp` together with `<ClientRouter />`; the combination is unsupported.

## 6. Advanced routing in `src/fetch.ts`

`official` — `src/fetch.ts` default-exports `{ async fetch(request) { ... } }` satisfying `Fetchable`, and supports `.ts`, `.js`, `.mjs`, and `.mts` (L-06, L-17, L-32).

- `official` — The default pipeline order is trailing-slash normalization, redirects, sessions, actions, user middleware, page rendering, i18n, and caching.
- `official` — `astro()` from `astro/fetch` runs the whole built-in pipeline with pre/post hooks; the individual handlers can be composed manually, and `astro/hono` exports the same names as Hono middleware.
- `official` — The incoming `url.pathname` "is not guaranteed to be the same as the route Astro matches internally", so pathname prefix checks can be bypassed.
- `official` — `notFound()` (7.4) must precede `pages()` in a custom worker entrypoint, or unmatched routes return an empty 404 with `X-Astro-Error`.
- `official` — `fetchFile: null | 'handler'` renames or disables the reserved file.
- `hypercore-default` — Never authorize in `src/fetch.ts` by matching `url.pathname` prefixes. Compose `astro/hono` handlers so route matching is authoritative.

## 7. What not to do

- Do not add an Action to a project with static-only output.
- Do not trust `FormData` or JSON input without a Zod schema.
- Do not rely on page-level auth for an Action; `/_actions/<name>` is reachable directly.
- Do not reassign `context.locals`; assign its fields.
- Do not export middleware as a default function.
- Do not read or write a session without a driver.
- Do not declare `context: 'client'` with `access: 'secret'`.
- Do not enable `security.csp` with `<ClientRouter />`.
- Do not authorize by `url.pathname` prefix in `src/fetch.ts`.

## Checklist

- [ ] Actions live in `src/actions/`, validate input with Zod, and authorize inside the handler or an action-aware middleware gate.
- [ ] Actions are only used on a project with an adapter and server output.
- [ ] Middleware exports a named `onRequest`, composes with `sequence()`, and never reassigns `locals`.
- [ ] `App.Locals` is declared in `src/env.d.ts` and matches what middleware writes.
- [ ] Sessions have a driver, and `regenerate()`/`destroy()` run on privilege changes.
- [ ] Every environment variable is declared in `env.schema` and imported from `astro:env/client` or `astro:env/server`.
- [ ] No client-context field is secret, and no secret is read through `import.meta.env`.
- [ ] `checkOrigin` is on, `allowedDomains` is set behind a proxy, and CSP is not combined with `<ClientRouter />`.
- [ ] `src/fetch.ts` authorization does not rely on pathname prefixes.

## Sources

> Checked 2026-11-07. Facts come from the Astro research lane, which opened these pages on 2026-11-07; lane source ids are kept in parentheses.

| Claim | Source |
|---|---|
| Actions in `src/actions/index.ts`, `defineAction`, `server` object (L-11, L-12) | https://docs.astro.build/en/guides/actions/ |
| Actions require server output and throw `ActionsWithoutServerOutputError` (L-57) | https://docs.astro.build/en/reference/errors/actions-without-server-output-error/ |
| Action URLs are public at `/_actions/<name>` and need API-level authorization (L-11) | https://docs.astro.build/en/guides/actions/ |
| `input` Zod validation, `BAD_REQUEST` before the handler, `accept: 'form'` (L-11, L-12) | https://docs.astro.build/en/reference/modules/astro-actions/ |
| Zero-JS forms and `Astro.getActionResult()` (L-11) | https://docs.astro.build/en/guides/actions/ |
| Named `onRequest`, `defineMiddleware()`, `sequence()`, `context.locals` typing (L-13) | https://docs.astro.build/en/guides/middleware/ |
| Session API, driver requirement, adapter defaults, `session: false` (L-14, L-17, L-50) | https://docs.astro.build/en/guides/sessions/ |
| `env.schema` field helpers, context/access pairs, the impossible client secret (L-15, L-17) | https://docs.astro.build/en/guides/environment-variables/ |
| Secret validation at import time and `env.validateSecrets` (L-15, L-17) | https://docs.astro.build/en/guides/environment-variables/ |
| `astro:env` unusable in config or standalone scripts, `getSecret()` (L-15, L-16) | https://docs.astro.build/en/reference/modules/astro-env/ |
| `import.meta.env.PUBLIC_*` and schema-driven client compilation (L-15) | https://docs.astro.build/en/guides/environment-variables/ |
| `security.checkOrigin`, `allowedDomains`, CSP mechanism and limits, body size limits (L-17, L-50) | https://docs.astro.build/en/reference/configuration-reference/ |
| `src/fetch.ts` pipeline order, `astro/fetch` and `astro/hono` composition, pathname caution (L-06, L-32, L-33) | https://docs.astro.build/en/reference/modules/astro-fetch/ |
| `notFound()` before `pages()` in a custom entrypoint (L-50) | https://docs.astro.build/en/reference/modules/astro-fetch/ |
