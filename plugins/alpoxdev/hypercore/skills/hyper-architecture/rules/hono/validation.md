# Validation

> Request validation rules/hono for Hono

---
## Stable Package Baseline

As verified on 2026-11-04: `@hono/zod-validator` 0.9.1 supports Hono `>=4.11.2` and Zod `^3.25.0 || ^4.0.0`; `@hono/standard-validator` 0.4.1 supports Hono `>=4.11.2` and Standard Schema `^1.0.0`. The Hono floor for this file is `4.13.16`, because earlier releases skip `validator('form')` validation for `multipart/form-data` requests that carry an extra parameter such as `charset`. Inspect the installed lockfile before using APIs or syntax.

- Validate every externally controlled `param`, `query`, `header`, `cookie`, `json`, or `form` value that influences behavior.
- Consume validator output only through `c.req.valid(target)`; do not parse the same body again.
- Header schema keys must be lowercase.
- JSON validation requires an appropriate `Content-Type`; test missing/wrong content types and malformed bodies.
- Form and multipart validation must be run against a real `multipart/form-data` request that includes a `charset` or boundary parameter. On Hono below 4.13.16 the validator sees an empty object while the handler still reads every field, so a normal test passes while validation is bypassed.
- Define hook/error behavior once per API surface so validation errors share a stable, non-sensitive envelope.
- Keep coercion and defaults intentional. Query/path inputs start as strings and must not acquire surprising domain semantics.
- Do not add or swap validation libraries merely to match this skill.

## Core Rule

Validate request data before service logic consumes it.

## Approved options

- `validator()` for narrow built-in checks
- `@hono/zod-validator` when the repo uses Zod
- `@hono/standard-validator` when the repo already standardizes on Standard Schema libraries

`@hono/standard-validator` 0.4.0 adds `flattenErrors`, which sorts form-level and field-level errors by path. 0.4.1 stops echoing the `cookie` header in the default 400 body of `header` validation, so do not re-add raw request headers to a custom error payload.

## Example

```ts
import { z } from 'zod'
import { zValidator } from '@hono/zod-validator'

const createUserSchema = z.object({
  email: z.email(),
  name: z.string().min(1),
})

const app = new Hono().post(
  '/',
  zValidator('json', createUserSchema),
  async (c) => {
    const payload = c.req.valid('json')
    return c.json({ payload }, 201)
  }
)
```

## Review Checklist

- Params/query/json/form use validator middleware when non-trivial
- Form and multipart routes have a regression test with an extra content-type parameter
- Validation happens before domain logic
- One feature does not mix unrelated validation styles without reason
- No new dependency is added without need
- Hono is at least 4.13.16 wherever `validator('form')` is used


## Sources

> Checked 2026-11-04.

| Claim | Source |
|---|---|
| Validator package versions and peer ranges | [npm registry: `@hono/zod-validator`](https://registry.npmjs.org/@hono/zod-validator), [npm registry: `@hono/standard-validator`](https://registry.npmjs.org/@hono/standard-validator) |
| `validator('form')` multipart bypass and its 4.13.16 fix | [`hono` v4.13.16 release](https://github.com/honojs/hono/releases/tag/v4.13.16) |
| `flattenErrors` and the `cookie` header removal from the 400 body | [`@hono/standard-validator` releases](https://github.com/honojs/middleware/releases) |
| Middleware-based validation and the third-party validator recommendation | [Validation Guide](https://hono.dev/docs/guides/validation) |
