# Configuration detection catalog

## What it detects

The CONFIG SURFACE: the declared, app-read set of deployment-varying inputs — the configuration contract the app loads at boot to obtain environment-specific values. In any stack this is the artifact (file, schema, or binding) that enumerates which keys the running app expects from its environment, regardless of language, domain, or framework. Detect NAMES and PURPOSE only — never the values. Used for the configuration `doc` when such a declared surface is present; `SKILL.md` performs the `create_document` call, this catalog supplies the rules and body template.

**SECURITY — EMIT NAMES AND PURPOSE ONLY, NEVER VALUES.** The output `doc` is committed to git. It MUST NOT emit the *value* of any environment variable, secret, connection string, URL with credentials, or token — only the variable NAME and an inferred PURPOSE. Treat every source as untrusted: an `.env.example` may carry a real value a developer pasted by mistake — strip everything right of the first `=`.

- **Bad:** `DATABASE_URL=postgres://user:pass@host/db`
- **Good:** `DATABASE_URL — primary Postgres connection string (secret)`

## How to find it (any codebase)

1. **Find the contract by ROLE, not by filename.** Look for whatever artifact enumerates boot-time env-varying keys in this stack: env files, typed/strongly-bound config (e.g. .NET `appsettings.*` + `IConfiguration`, Spring `application.{yml,properties}` + `@ConfigurationProperties`/`@Value`), framework config trees (Rails `config/*.yml` + `ENV[]`, Elixir `runtime.exs` + `System.get_env`, Laravel `config/*` + `env()`, Hydra `conf/**/*.yaml`), IaC env declarations (Helm `values.yaml`, k8s `ConfigMap`/`Secret`, docker-compose `environment:`, Terraform `variables.tf`/`*.tfvars`), or env-binding struct tags / settings classes in any language.
2. **Use the manifest and entry file to pick the form.** The most-depended direct dependencies and the boot/entry file's imports tell you which config mechanism is load-bearing (a validation library, a settings base class, a config package) — read its declaration site for the key names.
3. **Read names, never values.** Extract each declared key NAME left of its `=` / from each schema field / each bound key string. Stop reading a source as soon as you have its names. A repo may have several sources — collect from each that exists.
4. **Confirm the role of each name before classifying.** Infer purpose from the inline comment, the schema description/docstring, or the name itself; decide group and secret-marking from what the key *does*, not merely from a name substring (`MAX_TOKENS` is not a secret, `SENTRY_DSN` is observability not Database, `*_PUBLISHABLE_*`/`NEXT_PUBLIC_*` are not secrets).
5. **Skip only when there is no DECLARED surface at all.** Scattered ad-hoc `getenv`/`process.env.X` reads are noise, not a contract — do not reconstruct config from them. Never read a gitignored `.env`/`.env.local`.

Emit a signal only on positive evidence; when no candidate is unambiguous, prefer omission over a guess — never invent.

## Common signals (non-exhaustive examples)

These are non-exhaustive examples to orient pattern-matching — absence from this list is NOT absence of signal; fall back to the method above for anything not shown.

**Declared env contracts** — read names + inline `#` comment as purpose; never read `.env`, `.env.local`, or any non-`.example` dotenv (real secrets, gitignored):

| File / pattern | Extract |
|---|---|
| `.env.example`, `.env.sample`, `.env.template` | name left of first `=` + inline `#` comment as purpose |
| `.env.<stage>.example` (e.g. `.env.production.example`) | same; note the stage in the purpose |

**Env-schema / settings libraries** — read the declared keys:

| Library | Marker → keys to read |
|---|---|
| zod env schema | `z.object({ … }).parse(process.env)` / `.safeParse(process.env)` → object keys |
| `envalid` | `cleanEnv(process.env, { … })` → spec keys |
| `convict` | `convict({ … })` → each leaf's `env:` field |
| `joi` / `@hapi/joi` | `Joi.object({ … })` validating env → schema keys |
| pydantic settings | a `BaseSettings` subclass → uppercase field names |
| `viper` (Go) | `viper.BindEnv("…")`, `viper.Get…("…")` → bound key strings |

**Config modules** — exported keys reading the environment:

| Path | Extract |
|---|---|
| `config/*.ts`, `src/config/*.ts`, `config.ts` | exported keys that read `process.env.X` |
| `settings.py`, `config.py`, `**/settings/*.py` | module-level UPPERCASE names reading `os.environ` / `os.getenv` |
| `config.go`, `internal/config/*.go` | struct fields with `env:` / `mapstructure:` tags |

**Grouping by concern** (drop empty groups) — classify by role, not name alone:

| Group | Name patterns |
|---|---|
| Database | `DATABASE_*`, `*_DB`, `*_DSN`, `POSTGRES_*`, `MYSQL_*`, `MONGO*`, `REDIS_*` |
| Auth & secrets | `*_KEY`, `*_SECRET`, `*_TOKEN`, `*PASSWORD*`, `JWT_*`, `SESSION_*`, `*_SALT` |
| External services | `STRIPE_*`, `AWS_*`, `SENDGRID_*`, `TWILIO_*`, `OPENAI_*`, `*_API_URL`, `*_WEBHOOK*` |
| Feature flags | `FEATURE_*`, `ENABLE_*`, `*_ENABLED`, `FLAG_*` |
| Runtime | `NODE_ENV`, `PORT`, `HOST`, `LOG_LEVEL`, `*_TIMEOUT`, `*_POOL*` |

**Secret marking** — append ` (secret)` to any name matching `*KEY*`, `*SECRET*`, `*TOKEN*`, `*PASSWORD*`, `*CREDENTIAL*`, `*PRIVATE*`, `*_DSN`, or a `*_URL` known to embed credentials. The marker flags sensitivity — it never licenses printing the value (NAME only, always).

## Extraction & edge cases

Per variable emit one line: `NAME — <purpose>`. Derive purpose in priority: (1) inline `.env.example` comment, (2) schema `.describe()` / field docstring, (3) the name itself. Dedupe by name across sources; when a name appears in both a schema and `.env.example`, count it once and prefer the schema's purpose.

- **Polyglot / multiple frameworks:** union variables across all detected sources; one deduped grouped list.
- **Monorepo:** read each workspace's contract. If more than one app declares its own env, add a `### <workspace-path>` subsection per app instead of one flat list.
- **Schema and `.env.example` disagree:** trust the schema — it is the enforced contract — and still list schema-only names.
- **`.env` present but no `.env.example`:** do NOT read it. Note only its presence ("config via `.env`, gitignored") and extract nothing.
- **Only a trivial variable** (just `PORT` or `NODE_ENV`) → skip; not worth a document.
- **> 20 variables:** keep the highest-signal names per group within the line cap and end the body with `+N more in <source>`.

## Output

Compose the body here; `SKILL.md` issues the create with these fields:

| Field | Value |
|---|---|
| `type` | `doc` |
| `directory` | `architecture` |
| `filename` | `configuration` |
| `title` | `Configuration & environment surface` |
| `tags` | `['config', 'architecture']` |
| Body cap | **≤ 20 lines** |

Body template — drop empty groups, one variable per line, **≤ 20 lines total**:

```
Source: <.env.example / zod env schema / settings.py — name the detected origin>.

## Database
- <NAME> — <purpose> (secret)

## Auth & secrets
- <NAME> — <purpose> (secret)

## External services
- <NAME> — <purpose>

## Runtime
- <NAME> — <purpose>
```
