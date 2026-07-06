# Entry-Point Detection

## What it detects

An entry point is any place where the runtime, OS, scheduler, or platform first hands control to this code — the boundary where an external trigger crosses into the program. This is a ROLE, not a framework: an HTTP/RPC handler, a CLI binary, a queue/topic worker, a scheduled job, a serverless/function handler, an app/game/UI lifecycle hook, or a program `main`. It holds for any language, stack, or domain — a web service, an ML training script, embedded firmware's reset vector, a game loop, a data-pipeline DAG, a mobile activity, or an in-house framework's registered handler. Detected for the entry-point inventory `doc` in **all modes** when ≥ 1 entry point exists (grouped by domain in large mode).

## How to find it (any codebase)

Reason from concrete evidence the repo already contains, regardless of framework:

1. **Manifest-declared executable targets** (already parsed in Step A.1): `package.json` `bin`/`main`, `pyproject` `[project.scripts]`, `Cargo` `[[bin]]`, `*.csproj` `<OutputType>Exe`, `mix` `escript`, `Package.swift` executable target. Each declared target is an entry.
2. **Orchestration declarations** that name a start command: `Dockerfile` `ENTRYPOINT`/`CMD`, `Procfile` (`web:`, `worker:`), `serverless.yml`/SAM `handler:`, k8s/Helm `command:`/`args:`. These point at the real entry file.
3. **The language's program-entry construct** in source: `main`/`func main`/`@main`/`if __name__ == "__main__"`, an exported `handler`/`fetch`/`default`, or a registered lifecycle hook.
4. **Any binding that attaches code to an external trigger** — a decorator/attribute/annotation/macro/registration call mapping a path, HTTP verb, RPC method, route, topic, or schedule to a function, even when its framework is unlisted. Follow the import that supplies the binding to confirm.
5. **Classify by BEHAVIOR, not name**: serves/accepts requests -> HTTP/RPC; reads `argv`/stdin/flags -> CLI; pulls from a queue/topic -> Worker; fires on a clock/schedule -> Cron; otherwise, a real executable target -> Other.

Guard against false positives: back every entry with a concrete artifact. Do NOT fire on the config-getter idiom `app.get('port')`, on a local helper merely named `serve`/`worker`/`consumer`/`processor` that is not actually a server or queue worker, or on a library barrel `index.*` with no declared executable target (that is a library, not an entry). Emit a signal only on positive evidence; when no candidate is unambiguous, prefer omission over a guess — never invent.

## Common signals (non-exhaustive examples)

These are non-exhaustive examples to orient pattern-matching — absence from this list is NOT absence of signal; fall back to the method above for anything not shown.

Filename patterns (any language):

| Pattern | Typical role |
|---|---|
| `main.{go,py,rs,kt,java,c,cpp}`, `Program.cs` | program entry |
| `cmd/*/main.go`, `bin/*` (executable) | CLI binary |
| `server.*`, `app.*`, `Application.{java,kt}` | HTTP / app server |
| `worker.*`, `consumer.*`, `processor.*` | background worker |
| `cli.*` | CLI entry |
| `index.{ts,js,mjs,cjs}` at package root | module/library entry (often NOT an entry point) |

Trigger-binding markers by role:

| Role | Example markers |
|---|---|
| HTTP / RPC | `app.(get\|post\|put\|delete\|patch)(`, `router.(...)`, `createServer(`, `serve(` (Bun/Deno); `@app.route`/`@router.get`, `FastAPI(`/`Flask(`, Django `urls.py` `path(`; `http.HandleFunc`, gin/chi/echo `router.GET`; actix `#[get(...)]`, axum `Router::new().route`, `#[rocket::main]`; Spring `@RestController`/`@GetMapping`, Ktor `routing {`; Rails `routes.draw`, Sinatra `get '/...'`; Next.js `app/**/route.{ts,js}` + `export function GET`, `pages/api/**`; NestJS `@Controller`/`@Get`, Fastify `fastify.get(`; ASP.NET `app.MapGet`/`[HttpGet]`; Laravel `Route::get`/`#[Route]`; Phoenix `get "/"`/`live`/`scope` in `router.ex`; Clojure Ring/Reitit `(defroutes`/`["/" ...]`; OCaml Dream `Dream.get`; gRPC service impls; GraphQL resolvers |
| CLI | TS/JS `commander`/`yargs`/`cac`/`citty`/`clipanion`; Python `click`/`typer`/`argparse` (+ `__main__`); Go `cobra`/`urfave/cli`/`kingpin`; Rust `clap`/`structopt`; Ruby `thor`/`optparse`+`ARGV` |
| Worker | TS/JS `bull`/`bullmq`/`bee-queue`/`agenda`, `kafkajs` consumer; Python `celery` `@task`/`rq`/`dramatiq`/`arq`; Go `asynq`/`machinery`, `kafka-go` `Reader`; Rust `lapin`/`rdkafka` consumer; Elixir `GenServer` in a supervision tree (`children` in `application.ex`), Oban/Broadway; data-pipeline schedulers — Airflow `DAG(`, Dagster `@job`/`@asset`, Prefect `@flow`, Kubeflow pipelines |
| Cron | `cron.schedule`, `new CronJob`, `@Scheduled`, `node-cron`, `schedule` (Python), `gocron`; files under `cron/`, `scheduled/` |
| Lifecycle / app / game | program `main`/`@main`; mobile iOS `@main App`/`@UIApplicationMain`, Android `Activity.onCreate`; Flutter `void main()` + `runApp(`; Electron/Tauri main process; game-engine hooks — Unity `Awake`/`Start`/`OnEnable`, Unreal `BeginPlay`/GameMode, Godot `_ready` |
| Embedded | reset/entry vector — cortex-m-rt `#[entry]`, ESP `app_main`, Zephyr `main`, Arduino `setup()`/`loop()` |

## Classification buckets for inventory doc

Group detected entry points by role: **HTTP** (route/RPC handlers), **CLI** (`bin/*`, `cmd/*/main.*`, framework CLIs), **Worker** (queue/topic consumers, job processors, supervised/pipeline workers), **Cron** (scheduled tasks), **Other** (program `main`; app/game/UI lifecycle hooks; embedded reset vectors; and — for IaC repos — deployable units such as a Terraform root module or Helm release). A module-root `index.*` with no declared executable target is a library, not an entry.

## One-liner per entry

Template:

```
<relative-path> — <role>. <extracted-signature-or-top-comment>.
```

Signature extraction:

- HTTP: capture the first route + method found. Example: `POST /api/oauth/callback`.
- CLI: capture the first command name. Example: `bootstrap`.
- Worker: capture the queue / topic name. Example: `queue: email-notifications`.
- Cron: capture the schedule expression. Example: `every 5 minutes`.
- Fallback: top-of-file comment, first 80 chars.

## Monorepo grouping (large mode)

Group entries by domain (see `detect-domains.md`). Example output:

```
### domain:apps-billing-api
- apps/billing-api/src/server.ts — HTTP. Exposes /invoices, /payments.
- apps/billing-api/src/worker.ts — Worker. queue: invoice-events.

### domain:apps-notifications
- apps/notifications/src/main.go — Worker. topic: user-events.
```

Each section header matches the domain's slug (per `detect-domains.md` "Domain tags").

## Output

`SKILL.md` Phase E fires the `create_document`; this catalog supplies the buckets + per-entry one-liner.

| Field | Value |
|---|---|
| `type` | `doc` |
| `directory` | `architecture` |
| `filename` | `entry-points` |
| `title` | `Entry-point inventory` |
| `status` | `accepted` |
| `tags` | `['entry-points', 'architecture']` |

Skip when no entry point is detected (a pure library / SDK) — emit a one-line note rather than an empty doc.
