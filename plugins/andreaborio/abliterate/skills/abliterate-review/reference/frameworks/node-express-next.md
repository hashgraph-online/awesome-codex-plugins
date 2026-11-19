# Node: Express, Fastify, Next.js

## Entry points
- Express: `app.get/post/put/patch/delete/all(path, ...handlers)`, `router.use('/x', router)`, `app.use(path, mw)`. Routers are mounted elsewhere: find the mount prefix.
- Fastify: `fastify.route({...})`, `fastify.get(...)`, plugins registered with `register(plugin, {prefix})`; hooks `onRequest`/`preHandler` apply per encapsulation scope.
- Next.js App Router: `app/**/route.ts` exporting `GET/POST/PUT/PATCH/DELETE`; `app/**/page.tsx` server components; Server Actions = functions with `'use server'` (each is a public POST endpoint, even when only imported by one form); `pages/api/**` in the Pages Router.
- Jobs/webhooks: queue consumers (`bull`, `bullmq`, SQS handlers), `cron` files, webhook routes that verify signatures (check raw body is used).
- Enumerate:
  - `grep -rnE "\.(get|post|put|patch|delete|all|use)\(" --include=*.{js,ts}`
  - `find app -name 'route.*'`, `grep -rln "'use server'"`, `find pages/api`
  - `grep -rnE "router\.|Router\(\)"` to resolve mounts

## Where auth and authorization live
- Express: middleware order is execution order. A route declared BEFORE `app.use(auth)` is unprotected; `router.use(auth)` guards only that router. `app.use('/api', auth)` covers only that prefix (not `/api2` or a second mount); check the exact prefix and that every router is mounted under it. A `next(err)` or missing `return` after `res.status(401).send()` continues to the handler.
- Auth middleware that only authenticates (`passport.authenticate`, `req.user` set) does not authorize; look for ownership/role checks in the handler or service.
- Fastify: `preHandler: [fastify.authenticate]` on the route or an `addHook` in the right plugin scope; hooks do not apply to sibling scopes.
- Next.js `middleware.ts` (`proxy.ts` from Next 16): guarded paths come from `config.matcher`. Gaps: matcher that omits `/api`, `_next/data` routes, route groups, or trailing/locale variants; matching on `pathname.startsWith`. Middleware is a coarse filter: Server Actions, route handlers and server components must re-check the session themselves. Do not rely on middleware alone for authorization.
- NextAuth/Auth.js: `getServerSession(authOptions)` / `auth()` inside the handler; a `session` callback that adds `role` is only trustworthy if derived server-side from the DB or verified token. Client `useSession` checks are UI only. Check `authorized`/`callbacks.jwt` that copy user-supplied fields.
- Server Actions: arguments are attacker-controlled; check session, ownership and input validation in the action body.
- Next.js matcher that excludes anything ending in an extension (`.*\\.[a-zA-Z0-9]+$`) also excludes dynamic pages such as `/orders/x.png`. A Server Action can be invoked on any page URL, so the action runs with no middleware. This is a request to a running system: do not send it yourself; record it as `needs-evidence` with the decisive check for the user to run on their own deployment: `POST` that path with header `Next-Action:` set to a non-existent id and no cookie; `Server action not found` instead of the login redirect means the dispatcher is reachable past the middleware.

## Data access
| Safe | Unsafe |
| --- | --- |
| `pg` `query(text, values)`, Prisma `findMany({where})`, tagged `$queryRaw`, Sequelize `replacements`, Knex `?`/`??` bindings | template strings in `query`, `$queryRawUnsafe`, `sequelize.literal`, `knex.raw` with interpolation |
| Mongoose with schema cast; `String(req.body.x)` | `Model.find(req.body)`, `$where`, object-valued fields from `urlencoded({extended:true})` or `express.json` |
| Scoped queries `where: {id, orgId: session.orgId}` | `findUnique({where:{id}})` then ownership check missing |
See `classes/sql-nosql.md`, `classes/access-control.md`.

## Rendering and output
- React/JSX escapes by default; hatches: `dangerouslySetInnerHTML`, `href`/`src` with user URL, `innerHTML` via refs. Server-rendered templates (EJS `<%-`, Pug `!=`, Handlebars `{{{ }}}`) are raw.
- `res.send(string)` with interpolated HTML is unescaped; `res.json` of ORM objects leaks all columns (`select` fields, DTO mapping).
- Next.js: props passed from a server component to a client component are serialized into the page; secrets and extra fields leak there. `NEXT_PUBLIC_*` is shipped to the browser.
- `res.redirect(userInput)`, `NextResponse.redirect(new URL(userInput, req.url))` (still external if absolute).

## Framework-specific pitfalls
- `app.use(cors())` or `cors({origin: true, credentials: true})` reflects any origin.
- `express.static` over a directory that contains uploads or dotfiles; `dotfiles` option default ignores them, check overrides.
- `trust proxy` unset/wrong makes `req.ip`/protocol-based checks and rate limits wrong behind a proxy; set too permissively, `X-Forwarded-For` is spoofable.
- `bodyParser` raw vs json: webhook signature must verify the raw body.
- Global error handler returning `err.stack`; async handler errors in Express 4 are not caught (unhandled rejection or hanging requests) unless wrapped.
- Prototype pollution via `_.merge`/deep-merge of `req.body`.
- Next.js route handlers cache `GET` responses depending on config; per-user data in a cached `GET` leaks across users (see `classes/state-race.md`).
- `fetch` of user URLs in server code: SSRF (see `classes/ssrf.md`); `next/image` `remotePatterns` too broad.
