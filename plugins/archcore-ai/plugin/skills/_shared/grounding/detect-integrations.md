# Integration detection catalog

## What it detects

An INTEGRATION is an external, hosted, third-party service the code depends on at runtime — something operated by another vendor that the app reaches over the network or via a vendor SDK. It spans every domain: payments, cloud/storage, email/SMS, AI/LLM model hosts, queues/streaming, search, observability, analytics, auth, vector DBs, IaC providers, and the long tail beyond. Define it by the relationship (your code → someone else's running service), NOT by a fixed brand list — the vendors named below are a tiny sample of a much larger universe. It excludes anything the repo runs itself: its own app framework, local build/test tooling, and generic transports.

## How to find it (any codebase)

1. **Parse the manifest of every ecosystem present** — `package.json`, `pyproject.toml`/`requirements.txt`/`Pipfile`, `go.mod`, `Gemfile`, `Cargo.toml`, `*.csproj`, `pom.xml`/`build.gradle`, `composer.json`, etc. Read direct/top-level deps only, never transitive. Reuse the batched parse shared with `detect-stack` / `detect-data-model` / `detect-config` — do not re-read these files per detector.
2. **For each direct dependency, ask: does its name, vendor scope, or module path UNAMBIGUOUSLY denote one specific hosted third party?** Vendor namespaces (`@clerk/*`, `Azure/azure-sdk-for-go`), a `*-sdk`/`*-client` under a vendor scope, and plainly branded packages (`plaid`, `mailgun`, `pinecone-client`, `wandb`, a Terraform/Pulumi provider) qualify. Report as `<Vendor> — via <dep>` (omit the role if the use is unclear). Collapse a wildcard SDK family (`@aws-sdk/*`) to ONE line citing the most telling sub-package; dedupe to one line per service across all manifests and workspaces, citing the dep from the language with the most usage.
3. **When no manifest names the service, corroborate from secondary evidence the repo actually contains** — a `STRIPE_*`/`SENDGRID_*`-style prefixed key in `.env.example`, a named hosted service in `docker-compose`/`serverless`/IaC, or a hosted base URL in config. Cross-check the entry file's imports and what the code does at runtime to confirm the dep is live, not vestigial.
4. **Apply the conservative bar.** OMIT a generic transport (HTTP client), build tool, test runner, the app framework itself, and raw DB drivers (defer those to `detect-data-model`; record a store name only if no data-model doc will cover it, and never restate tables/columns here). Do NOT report a devDependency/type-stub-only or test-mock package as a live integration, and avoid Go module-path-suffix mis-attribution. Any target you cannot name with confidence is OMITTED.

Emit a signal only on positive evidence; when no candidate is unambiguous, prefer omission over a guess — never invent.

## Common signals (non-exhaustive examples)

These are non-exhaustive examples to orient pattern-matching — absence from this list is NOT absence of signal; fall back to the method above for anything not shown.

Matching: exact name for plain packages; **prefix** for `*` patterns (`@aws-sdk/*` = any package under `@aws-sdk/`); module-path suffix for Go (`go-redis` matches `github.com/redis/go-redis/v9`).

| Dependency (JS/TS · Python · Go · Ruby) | Service | Category |
|---|---|---|
| `stripe` · `stripe` · `stripe-go` · `stripe` | Stripe | Payments |
| `@aws-sdk/*`, `aws-sdk` · `boto3` · `aws-sdk-go-v2` · `aws-sdk-*` | AWS | Cloud & Storage |
| `@google-cloud/*` · `google-cloud-*` · `cloud.google.com/go` | GCP | Cloud & Storage |
| `@azure/*` · `azure-*` · `Azure/azure-sdk-for-go` | Azure | Cloud & Storage |
| `firebase-admin` · `firebase-admin` · — · — | Firebase | Cloud & Storage |
| `@supabase/supabase-js` · `supabase` · `supabase-go` · — | Supabase | Cloud & Storage |
| `twilio` · `twilio` · `twilio-go` · `twilio-ruby` | Twilio | Email & SMS |
| `@sendgrid/mail` · `sendgrid` · — · `sendgrid-ruby` | SendGrid | Email & SMS |
| `openai` · `openai` · — · `ruby-openai` | OpenAI | AI & LLM |
| `@anthropic-ai/sdk` · `anthropic` · `anthropic-sdk-go` · — | Anthropic | AI & LLM |
| `ioredis`, `redis` · `redis` · `go-redis` · `redis` | Redis | Data stores |
| `mongodb`, `mongoose` · `pymongo`, `motor` · `mongo-driver` · `mongo` | MongoDB | Data stores |
| `kafkajs` · `confluent-kafka`, `kafka-python` · `segmentio/kafka-go` · — | Kafka | Messaging & Queue |
| `amqplib` · `pika`, `aio-pika` · — · `bunny` | RabbitMQ | Messaging & Queue |
| `bullmq`, `bull` · `celery` · — · `sidekiq` | Job queue | Messaging & Queue |
| `@elastic/elasticsearch` · `elasticsearch` · — · — | Elasticsearch | Search |
| `algoliasearch` · `algoliasearch` · — · `algolia` | Algolia | Search |
| `@sentry/*` · `sentry-sdk` · `getsentry/sentry-go` · `sentry-ruby` | Sentry | Observability |
| `dd-trace`, `@datadog/*` · `ddtrace` · `DataDog/datadog-go` · `ddtrace` | Datadog | Observability |
| `@segment/analytics-node` · `analytics-python` · — · `analytics-ruby` | Segment | Analytics |

**Excluded — never map to a service even when present:** generic HTTP clients (`axios`, `got`, `node-fetch`, `undici`, `ky` · `requests`, `httpx`, `aiohttp` · `resty`); the app framework (`next`, `express`, `fastify`, `django`, `flask`, `gin`, `rails`); build tools (`vite`, `webpack`, `esbuild`, `rollup`, `turbo`); test runners (`jest`, `vitest`, `pytest`, `rspec`, `playwright`); raw DB drivers (`pg`, `mysql2`, `psycopg`, `asyncpg`, `jackc/pgx` — defer to `detect-data-model`). GraphQL clients (`@apollo/client`, `graphql-request`) are weak signal and usually point at the repo's OWN backend — include only when the configured endpoint is an external domain.

## Output

This catalog composes the body only. `SKILL.md` fires `create_document`.

| Field | Value |
|---|---|
| type | `doc` |
| directory | `architecture` |
| filename | `external-integrations` |
| title | `External integrations` |
| tags | `integrations`, `architecture` |
| Body cap | **≤ 15 lines** |

Body = one-liners grouped under category headings, in this order: **Payments / Cloud & Storage / Messaging & Queue / Email & SMS / AI & LLM / Search / Observability / Data stores / External APIs**. Drop any group with no detected service. One line per service:

```
## Payments
- Stripe — via `stripe`, charge and subscription billing.

## Cloud & Storage
- AWS — via `@aws-sdk/client-s3`, object storage and transactional email (SES).

## Messaging & Queue
- Kafka — via `kafkajs`, event-stream producer/consumer.

## AI & LLM
- Anthropic — via `@anthropic-ai/sdk`, model completion calls.
```

Line rules: each entry is `<Service> — via <dep>, <one-line role>`. The role names the function (payments, object storage, queue) — state the service only and omit the role when the use is ambiguous; never invent a role. The ≤ 15-line cap counts service lines only; category `##` headings do not count toward it. If detected services exceed the cap, keep the highest-signal integrations and drop the rest.

## When inconclusive / when to skip

- **No service detected from any evidence** → SKIP: create no doc, emit a one-line progress note (`no external-service SDKs detected`).
- **Only persistence drivers match** (`pg`, `psycopg`, …) → defer to `detect-data-model`; do not emit an integrations doc for drivers alone.
- **Dep matches but role is unclear** → emit the service line without a role rather than guess.
