# Data Flow From Entry Points

> Trace one entry — CLI command, HTTP route, queue message, scheduled tick — through every handler and dependency until it hits a sink. Linear paths, not speculative breadth.

## When to use

- "What happens when <event> arrives?"
- About to modify a handler and need its blast radius.
- Architecture docs disagree with code; need ground-truth path.

## The four entry surfaces

| Surface | Where to look | Signals |
|---------|---------------|---------|
| CLI | `cmd/`, `bin/`, `src/main.*` | clap, cobra, click, typer, commander, yargs |
| HTTP | `routes/`, `api/`, `handlers/` | axum, actix, fastapi, express, gin, flask |
| Queue / event | `consumers/`, `workers/`, `events/` | bull, sidekiq, celery, kafka, rabbitmq |
| Scheduler | `jobs/`, `cron/`, `schedules/` | cron strings, `@scheduled`, systemd timers |

Find all surfaces present before tracing. Trace one of each that the work touches.

## Trace procedure

### 1. Locate the dispatcher

Find the registration call (`router.add(...)`, `app.command(...)`, `consumer.subscribe(...)`). Record `file:line` and the handler symbol.

### 2. Read the handler

Note in order:
- Inputs and validation.
- Direct dependencies (DI params, module-level singletons).
- External calls made directly inside the handler.
- Errors caught vs. propagated.

### 3. Walk one level deep

For each direct dependency:
- Self-describing name → note purpose, do not open.
- Ambiguous name → open just long enough for one-line description.
- Touches a sink → always open; sinks are part of the trace.

Stop at level 2 unless level 3 is obviously where the work happens.

### 4. Find the sink

| Sink | Grep signals |
|------|--------------|
| DB | `query`, `execute`, `INSERT`, `UPDATE`, ORM session calls |
| HTTP egress | `fetch`, `reqwest`, `requests.`, `http.Client`, SDK ctors |
| Filesystem | `open`, `File::`, `fs.`, `pathlib`, write/read fns |
| Queue publish | `publish`, `produce`, `enqueue`, `send_message` |
| Stdout / logs | `print`, `println`, structured loggers when output is the product |

### 5. Note error and retry behavior

Where caught? Where propagated? Retries or circuit breakers visible? Surprise behavior lives here.

## Output shape

One trace, one page, linear:

```markdown
## Trace: POST /api/jobs

Entry: `src/api/jobs.rs:42` → `create_job` handler

create_job (src/api/jobs.rs:42)
  ↓ validates JobRequest (src/api/jobs.rs:55)
  ↓ JobService::submit (src/services/job.rs:18)
       ↓ JobRepository::insert (src/storage/jobs.rs:30) — sink: SQLite
       ↓ Queue::publish (src/queue/mod.rs:22) — sink: Redis stream
  ↓ returns 202 with job id

Errors:
- Validation failure → 400 at handler boundary
- Storage failure → bubbles, logged in middleware (src/middleware/log.rs:12), 500
- Queue failure → swallowed at JobService::submit:24 — KNOWN GAP
```

## Scoped searches

Always pass a directory; never grep the whole repo unscoped.

```bash
# Entry-point registration
rg -n "Router::|router\.|@app\.|app\.(get|post)|Cmd\(\"|@click\.command|cobra\.Command" src/

# Handler signatures
rg -n "fn (handle|create|update|get|list|delete)_" src/api/ src/handlers/

# DB sinks
rg -n "query!?\(|execute!?\(|\.query\(|\.exec\(|SELECT |INSERT |UPDATE " src/

# HTTP egress
rg -n "reqwest::|requests\.|fetch\(|http\.Client" src/

# Queue publish
rg -n "publish\(|produce\(|enqueue\(|send_message" src/
```

Pair with `references/iterative-retrieval.md` when first scoped search misses.

## Anti-patterns

| Avoid | Do instead |
|-------|------------|
| Five shallow traces | One end-to-end trace first |
| Reading every imported file | Names usually suffice; open ambiguous or sink-touching only |
| Ignoring error paths | Note catches vs. propagation |
| Stopping at the service layer | Walk to the sink |
| Whole-repo grep | Always scope to a directory |
| Branching trace into a tree | Pick one path; record alternates as siblings |

## See also

- Onboarding context: `references/onboarding-methodology.md`
- Prior-work search: `references/iterative-retrieval.md`

---

> Pattern adopted from `codebase-archaeology` (ACFS skill corpus). Methodology only — no verbatim text.
