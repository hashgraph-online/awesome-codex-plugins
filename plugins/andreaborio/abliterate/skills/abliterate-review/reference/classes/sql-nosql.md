# SQL and NoSQL injection (CWE-89, CWE-943)

## Sources
- HTTP: query string, path params, JSON/form body, headers (`X-Forwarded-*`, `Host`), cookies, multipart field names.
- Second-order: a value stored earlier (profile name, filename, tag) and later concatenated into a query by a job, report or admin screen. The source is the write, the sink is the later read.
- Identifiers that cannot be bound: `ORDER BY` column, sort direction, table/column names, `LIMIT` from `sort=`, `fields=`, `filter=` params.
- Parsed JSON that becomes an object: `req.body.password` may be `{"$ne": null}` for Mongo, not a string.
- Message queues, webhooks, imported CSV/JSON: attacker-controlled when the producer is external.

## Sinks
| Stack | Sink | Safe alternative |
| --- | --- | --- |
| node-postgres / mysql2 | `client.query(`... ${x}`)`, string concat | `query(text, [values])`; `?` / `$1` placeholders |
| Sequelize | `sequelize.query(str)` with interpolation, `Sequelize.literal(x)`, `where: sequelize.literal(...)` | `replacements`/`bind` option; `Op.*` operators with values |
| Knex | `knex.raw(`..${x}`)`, `whereRaw`, `orderByRaw` with interpolation | `raw('?? = ?', [col, val])`, `whereRaw('a = ?', [v])` |
| Prisma | `$queryRawUnsafe`, `$executeRawUnsafe`, `Prisma.raw()` with user data | tagged `` prisma.$queryRaw`... ${v}` ``, `Prisma.sql`, `Prisma.join` |
| TypeORM | `createQueryBuilder().where(`a = ${x}`)`, `manager.query(str)` | `.where('a = :a', { a })`, `find({ where })` |
| Django | `.raw(f"...")`, `.extra(where=[...], select=...)`, `RawSQL(sql, params)` with formatted sql, `cursor.execute(f"...")` | `.raw(sql, [params])`, `cursor.execute(sql, params)`, ORM filters |
| SQLAlchemy | `text(f"...")`, `execute(f"...")`, `.filter(text(user))`, `order_by(text(user))` | `text("... :p").bindparams(p=v)`, expression API, column allowlist |
| Rails ActiveRecord | `where("a = '#{x}'")`, `order(params[:s])`, `find_by_sql("..#{}")`, `pluck(params[:c])`, `update_all("...#{}")` | `where("a = ?", x)`, `where(a: x)`, `order(Arel.sql(...))` only after allowlist |
| Go database/sql | `db.Query(fmt.Sprintf(...))`, `"..."+x` | `db.QueryContext(ctx, "... $1", x)`; GORM `Where("a = ?", x)`, not `Where(fmt.Sprintf)` |
| Java / Spring | `Statement.executeQuery(str)`, `createQuery("..."+x)`, `@Query` with SpEL concat, `JdbcTemplate.query(str)` | `PreparedStatement`, named params `:p`, `setParameter` |
| PHP / Laravel | `DB::raw("..$x")`, `whereRaw("..$x")`, `DB::select("..$x")`, `orderByRaw` | `whereRaw('a = ?', [$x])`, query builder bindings |
| MongoDB | `$where` / `$function` with string JS, `find(req.body)`, `find({user: req.body.user})` with object values | `String()`/schema cast, `express-validator`/zod type check, reject keys starting with `$` |

## Guards that work / Look-alike guards
Work:
- Bound parameters for every value; the driver sends text and values separately.
- Allowlist map for identifiers: `{name:'name', date:'created_at'}[req.query.sort] ?? 'created_at'`; direction compared to `'asc'|'desc'`.
- Schema validation that forces a scalar type (zod `z.string()`, Mongoose schema with `strict` and cast, `Joi.string()`) before the query is built.
- Numeric cast that fails closed (`parseInt` + `Number.isInteger`, not just `Number(x)` written back as a string).

Look-alike:
- Blocklist regex (`/(select|union|--)/i`), `replace("'", "''")`, `addslashes`, `escape()` for a different dialect or charset.
- HTML-escaping or `encodeURIComponent` used as SQL escaping.
- Client-side validation or a UI dropdown for `sort`; the route still accepts any string.
- Validation on a sibling route; the changed route skips the middleware.
- Escaping applied to the value but the same value also reaches an unquoted position (numeric, identifier).
- ORM used elsewhere in the file; only the one `raw` call matters.
- `$where` guarded by `typeof x === 'string'` still runs attacker JS.

## Falsify before reporting
1. Is the interpolated value really attacker-controlled on a routed request, or a constant/enum/server-side id? Trace to the framework entry point.
2. Does the driver/ORM bind it? `Prisma` tagged template and `$queryRaw` bind; the same text through `$queryRawUnsafe` does not. Check the exact function name.
3. Is there an allowlist, cast or schema between source and sink on THIS path? Read the validator's definition, not its name.
4. Mongo: can the parsed body hold an object at that key? Check the body parser (`express.json`, `urlencoded({extended:true})` and `qs` produce nested objects) and any `sanitize`/cast layer.
5. Does the DB role limit impact (read-only role, row-level security)? Lowers impact, does not remove the finding.
6. Confirm: a direct call with a value containing a quote changes the generated statement (inspect logged SQL in a test DB) or alters results.

## Severity cues
- Raises: unauthenticated route; multi-statement or stacked queries supported; DB role with write or cross-tenant access; secrets or password hashes in reachable tables.
- Lowers: admin-only route; value restricted by type upstream; read-only role on non-sensitive data; identifier-only injection limited to a fixed column set.

## Regression test
- Fails before: store a record named `O'Brien` and query by that name through the real route; before the fix it errors (500) or returns wrong rows.
- Add a second case with a boolean-looking string (`x' OR '1'='1`) as the search value; assert zero extra rows and an unchanged row count in the table.
- Sort param: `sort=not_a_column` returns 400 or falls back to default; `sort=created_at` still works.
- Mongo: send `{"password": {"$ne": null}}`; assert 400/401, and a plain string password still logs in.
- Allowed case: ordinary search term, accented characters, and `%` in a LIKE term behave as before.
