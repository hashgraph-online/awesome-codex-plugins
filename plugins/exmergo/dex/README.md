<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/preview-dark.png" />
  <img alt="Dex: let your agent build your analytics. Explore, transform, maintain." src="assets/preview-light.png" />
</picture>

> *Most deadly errors arise from obsolete assumptions.*
>
> Frank Herbert, *Children of Dune*

# Dex

**Dex lets your agent build your analytics.**

Explore your data, build models and semantic layers, and keep them in sync
as schemas change.

Works with databases, data warehouses, lakehouses, and SQL engine endpoints
through [supported connectors](#connectors).

**Built by [Exmergo](https://www.exmergo.com)**

[![PyPI](https://img.shields.io/pypi/v/exmergo-dex-core?logo=pypi&logoColor=white&color=165dfc)](https://pypi.org/project/exmergo-dex-core/)
[![License](https://img.shields.io/badge/license-Apache--2.0-165dfc)](LICENSE)
[![data-eng-bench](https://img.shields.io/badge/data--eng--bench-57%25-33cf56)](benchmarks/data-eng-bench/README.md)
[![ADE-bench](https://img.shields.io/badge/ADE--bench-80%25-33cf56)](benchmarks/ade_bench/README.md)
[![CI](https://github.com/exmergo/dex/actions/workflows/ci.yml/badge.svg)](https://github.com/exmergo/dex/actions/workflows/ci.yml)

[![Docs](https://img.shields.io/badge/docs-docs.exmergo.com%2Fdex-165dfc?logo=readthedocs&logoColor=white)](https://docs.exmergo.com/dex)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Exmergo-165dfc?logo=linkedin&logoColor=white)](https://www.linkedin.com/company/exmergo/)
[![X](https://img.shields.io/badge/Follow-%40exmergo-165dfc?logo=x&logoColor=white)](https://x.com/exmergo)
[![Star the repo!](https://img.shields.io/github/stars/exmergo/dex?style=flat&label=Star%20the%20repo!%20%E2%AD%90&labelColor=555&logo=github&logoColor=white&color=165dfc)](https://github.com/exmergo/dex)

## Install

**Any agent** (run in your terminal):

```bash
npx skills add exmergo/dex
```

**Claude Code** (run these inside Claude Code, one at a time):

```
/plugin marketplace add exmergo/exmergo-agent-plugins
```

```
/plugin install dex@exmergo
```

**Codex**:

```bash
npx skills add exmergo/dex --agent codex
```

## What you get

- **Explore** your database, data warehouse, or SQL endpoint. Find the tables that matter, understand their structure, and verify how they join. Get column profiles, personal-data flags, and an ER diagram.
- **Transform** your dbt project and semantic layer. Create models, tests, docs, and metrics as reviewable plans, then build and verify on a dev target.
- **Maintain** your models and metrics as sources change. Detect drift in schemas, volumes, grain, and metric definitions, with proposed fixes to review.

Your source data stays read-only. Builds run on a dev target, query costs are
quoted before spend, and every project change is a diff you review.
Works in Claude Code, Codex, or any agent that loads Agent Skills.

> [!IMPORTANT]
> **Dex needs [`uv`](https://docs.astral.sh/uv/) on your `PATH`.** No agent installs
> it for you. Run `brew install uv` or `pipx install uv`, or see the
> [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/)
> for other platforms. `uv` supplies Python and the engine. Use uv 0.13.4 or
> later (`uv self update`): earlier releases still trust the emSign CA roots
> withdrawn after their keys were compromised.

In Claude Code the skills appear as `/dex:explore`, `/dex:transform`, and
`/dex:maintain` and trigger on matching intent. Update later with
`/plugin marketplace update exmergo`. Codex also gets a native plugin, with no MCP
server needed. Any other agent can be pointed at [`AGENTS.md`](AGENTS.md).

Run Dex from your project directory, so it finds your `.dex/config.yml` and keeps
its cache next to your project. Dex needs an agent with a local shell, so it does
not run in claude.ai chat.

> [!TIP]
> **Skip the first-run wait.** The first command installs the engine, which takes
> tens of seconds on a cold `uv` cache. Ask your agent to warm Dex once after
> installing, or run the command below in a CI or container build step. Add
> `--connector snowflake` (or any connector) to warm one before a project exists.

```bash
uv run --no-project --script skills/<skill>/scripts/run.py --warm
```

## Why

Writing SQL is one part of analytics engineering. Your agent also needs to:

- understand the schema without starting from scratch every session,
- find the relevant tables among thousands,
- account for what a query costs,
- keep personal data out of its context,
- keep models and metric definitions coherent as their sources change.

Dex gives the agent a repeatable explore, transform, maintain loop, with
guardrails enforced in the engine.

## Try it in three commands

No existing database, no credentials, no cloud account, and no network once the
package is installed.

```bash
pip install "exmergo-dex-core[duckdb]"
dex demo
dex explore map
```

`dex demo` writes a small e-commerce DuckDB database (`dex_demo.duckdb`, 7 tables,
29,512 rows) and a `.dex/config.yml` into the current directory, so every command
after it runs with no flags. It refuses rather than overwrite anything. The data
comes from a pinned seed, so what you see is what is written here.

`explore map` maps all 7 tables, infers 5 joins, flags 6 columns as personal data,
and reports 6 data-quality findings. Every command answers with one JSON envelope.
An excerpt, for one table:

```json
{
  "identifier": "dex_demo.main.order_items",
  "row_count": 14000,
  "grain": null,
  "data_quality": [
    "order_item_id is not unique: 13000 distinct over 14000 rows (1000 rows would have to be removed for it to be unique, so it is unique for 92.9% of rows); joins on it will fan out"
  ]
}
```

### It is broken on purpose

A first run that reports a clean bill of health teaches you nothing, so the demo
ships with real defects. Dig into them:

```bash
dex explore profile order_items products
dex explore relationships --verify
dex explore query "select email from customers"
```

- **A broken grain.** A batch was loaded twice, so `order_item_id` is unique for only 92.9% of rows. Dex reports the duplicates and leaves the grain unknown rather than guessing a key.
- **A key that mixes id schemes.** `sku` is `90% numeric, 10% 32-character hexadecimal (md5-shaped)`. Cast it to a number and you silently drop 10% of products.
- **A join that looks right and is not.** `web_events.customer_id` shares a name with the CRM's key, but verification finds 100% of its values have no match.
- **A refusal.** The query firewall will not put `customers.email` into context. `select count(distinct email) from customers` runs, because a statistic is not a value.

There is also a table an interrupted load left empty, two columns whose declared
type contradicts their content, and two designed PII false positives. See the
[`dex demo` reference](https://docs.exmergo.com/dex/cli/demo).

> [!NOTE]
> DuckDB is free and local, so nothing here asks you to confirm a spend. On a
> metered connector the same commands return an estimate first and run only once
> you agree to it.

## How it works

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/how-it-works-dark.png" />
  <img width="760" height="630" alt="How it works: your coding agent runs a Dex skill, which calls the exmergo-dex-core engine; the engine queries your data (SELECT-only, cost-capped, dbt builds on dev only), writes plans as reviewable diffs to your repository, keeps its cache in .dex/, and returns one sanitized JSON envelope to the agent" src="assets/readme/how-it-works-light.png" />
</picture>

The skills connect your agent to the `exmergo-dex-core` engine, which holds the
logic and guardrails behind a [small command contract](https://docs.exmergo.com/dex/reference/command-contract).
Your dbt project and semantic-layer definitions live in your repository as
reviewable files. The `.dex/` directory holds Dex's cache and snapshots.

### Explore

Find the tables that matter, profile their columns, and verify joins before
writing SQL. Answer ad-hoc questions through a query firewall that checks for
personal data, read and query the semantic layer, and map relationships as a
Mermaid ER diagram. Exploration is read-only and needs no dbt project.
[Skill](skills/explore/SKILL.md) · [methodology](https://docs.exmergo.com/dex/concepts/methodology) · [commands](https://docs.exmergo.com/dex/cli/explore)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/explore-dark.png" />
  <img width="522" height="343" alt="Explore" src="assets/readme/explore-light.png" />
</picture>

### Transform

Build and refactor dbt models from staging to marts, with tests, docs, and declared
grain and population. Define semantic models and metrics over them, or work with a
native semantic layer without a dbt project. Review each stored plan before
applying it, then build and verify on a dev target.
[Skill](skills/transform/SKILL.md) · [what Dex writes](https://docs.exmergo.com/dex/concepts/dbt-project) · [commands](https://docs.exmergo.com/dex/cli/transform)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/transform-dark.png" />
  <img width="504" height="271" alt="Transform" src="assets/readme/transform-light.png" />
</picture>

### Maintain

Compare database schemas and profiles, the dbt project, and the semantic layer
with the last snapshot. See which models and metrics a change affects and review
the proposed edits. `maintain verify` also checks a project as it stands, with no
baseline needed.
[Skill](skills/maintain/SKILL.md) · [commands](https://docs.exmergo.com/dex/cli/maintain)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/maintain-dark.png" />
  <img width="484" height="344" alt="Maintain" src="assets/readme/maintain-light.png" />
</picture>

> [!TIP]
> **Give every agent in your repository the same procedure.**
> `dex procedure --block` prints the procedure every Dex skill follows, ready to
> paste into your `CLAUDE.md` or `AGENTS.md`, so an agent follows it even before
> it loads a skill. Dex never writes the file;
> `dex procedure --check CLAUDE.md` tells you when an upgrade has made your copy
> stale. See
> [`dex procedure`](https://docs.exmergo.com/dex/cli/procedure).

## Connectors

| Connector | Type | Self-hostable | Extra / `--connector` | Cost guardrail | Connection details |
| --- | --- | :---: | --- | --- | --- |
| <img src="https://www.exmergo.com/connectors/snowflake.png" width="20" height="20" alt=""> [**Snowflake**](https://docs.exmergo.com/dex/connectors/snowflake) | Cloud warehouse | ❌ | `snowflake` | Warehouse-seconds, with credits | `connections.toml`, `SNOWFLAKE_*` env, or a dbt profile |
| <img src="https://www.exmergo.com/connectors/bigquery.png" width="20" height="20" alt=""> [**BigQuery**](https://docs.exmergo.com/dex/connectors/bigquery) | Cloud warehouse | ❌ | `bigquery` | Bytes scanned | Application Default Credentials |
| <img src="https://www.exmergo.com/connectors/databricks.png" width="20" height="20" alt=""> [**Databricks**](https://docs.exmergo.com/dex/connectors/databricks) | Lakehouse via SQL endpoint | ❌ | `databricks` | Warehouse-seconds, with DBUs | `databricks auth login`, `DATABRICKS_*` env, or a dbt profile |
| <img src="https://www.exmergo.com/connectors/redshift.png" width="20" height="20" alt=""> [**Amazon Redshift**](https://docs.exmergo.com/dex/connectors/redshift) | Cloud warehouse, Serverless-first | ❌ | `redshift` | Compute-seconds, with RPU-hours | The AWS credential chain or `REDSHIFT_*` env |
| <img src="https://www.exmergo.com/connectors/postgresql.png" width="20" height="20" alt=""> [**Postgres**](https://docs.exmergo.com/dex/connectors/postgres) | Operational database | ✅ | `postgres` | Database-seconds | `pg_service.conf`, `DATABASE_URL`, `PG*` env, or a dbt profile<br>Also works with <img src="assets/supabase-logo.png" width="20" height="20" alt=""> [Supabase](https://supabase.com/), <img src="assets/neon-logo.png" width="20" height="20" alt=""> [Neon](https://neon.com/), and [more managed Postgres platforms](references/postgres.md#managed-postgres-platforms) |
| <img src="https://www.exmergo.com/connectors/duckdb.png" width="20" height="20" alt=""> [**DuckDB**](https://docs.exmergo.com/dex/connectors/duckdb) | Embedded analytical | ✅ | `duckdb` | Free and local | None, just a file path |
| <img src="https://www.exmergo.com/connectors/clickhouse.png" width="20" height="20" alt=""> [**ClickHouse**](https://docs.exmergo.com/dex/connectors/clickhouse) | Analytical database | ✅ | `clickhouse` | Compute-seconds on Cloud, database-seconds self-hosted | `CLICKHOUSE_URL`, `CLICKHOUSE_*` env, or a dbt profile |
| <img src="https://www.exmergo.com/connectors/trino.png" width="20" height="20" alt=""> [**Trino**](https://docs.exmergo.com/dex/connectors/trino) | Federated query engine | ✅ | `trino` | Cluster-seconds| `TRINO_URL`, `TRINO_*` env, or a dbt profile<br>Also works with: <img src="assets/mysql-logo.png" width="20" height="20" alt=""> MySQL, <img src="assets/sqlserver-logo.png" width="20" height="20" alt=""> SQL Server, <img src="assets/mongodb-logo.png" width="20" height="20" alt=""> MongoDB, and [more databases through Trino catalogs](references/trino.md#databases-through-configured-catalogs)  |

Credentials are discovered and never enter the agent's context.
Every scan is estimated, confirmed, and capped server-side, and settled spend is
recorded in a local ledger ([cost controls](https://docs.exmergo.com/dex/guardrails/cost-controls)).
Self-hosted databases bill no dollars and are still gated, because an unbounded
scan on a production Postgres primary is a real cost too.

**Coming next:** MotherDuck, Starburst Galaxy, Microsoft Fabric.

## Semantic layers

Choose the semantic layer independently of your database connector. Dex supports
dbt semantic models and native Ossie, SLayer, or Cube files. Configure the choice
in `.dex/config.yml`; Ossie, SLayer, and Cube need no dbt project.
([overview](https://docs.exmergo.com/dex/semantic-layers/overview))

| Semantic layer | Hosted | Queryable | `vendor` / `deployment` | Read through | Documentation |
| --- | :---: | :---: | --- | --- | --- |
| <img src="https://www.exmergo.com/connectors/ossie.png" width="20" height="20" alt=""> **[Apache Ossie](https://github.com/apache/ossie)** (incubating) | ❌ | ❌ | `ossie` / `local` | Native documents in the repository, no dbt or MetricFlow in the path | [Docs](https://docs.exmergo.com/dex/semantic-layers/ossie) |
| <img src="https://www.exmergo.com/connectors/dbt.png" width="20" height="20" alt=""> **[dbt](https://github.com/dbt-labs/dbt-core)** | ✅ | ✅ | `dbt` / `local` or `dbt_cloud` | MetricFlow locally, run through the Dex connector and its cost guard, or the hosted dbt Cloud Semantic Layer API | [Docs](https://docs.exmergo.com/dex/semantic-layers/overview#choosing-a-backend-ambient-like-a-connector) |
| <img src="assets/cube-logo.png" width="20" height="20" alt=""> **[Cube](https://github.com/cube-js/cube)** | ❌ | ✅ | `cube` / `local` | Plain YAML model files, read statically with no Node or Cube server; querying asks a running Cube server to render, Dex runs it under the cost guard | [Docs](https://docs.exmergo.com/dex/semantic-layers/overview#cube-models-vendor-cube) |
| <img src="assets/motley-logo.jpeg" width="20" height="20" alt=""> **[SLayer](https://github.com/MotleyAI/slayer)** (by Motley) | ❌ | ✅ | `slayer` / `local` | SLayer model files, validated by one pinned release; SLayer renders, Dex runs it under the cost guard | [Docs](https://docs.exmergo.com/dex/semantic-layers/overview#slayer-models-vendor-slayer) |

**Coming next:** hosted Cube, hosted SLayer, Snowflake Semantic Views, Looker / LookML, and Databricks Metric Views.

## See it on a real project

**[github-repo-analytics](https://github.com/exmergo/github-repo-analytics)** is a template that tracks GitHub traffic, stars, downloads and contributors for your open-source projects, free on GitHub Actions.   
Every model and metric was built and is maintained with Dex. Its [audit trail](https://github.com/exmergo/github-repo-analytics/blob/main/.dex/review/README.md) holds the raw envelopes, including the drift Dex blocked.

## Use Dex from Python

The engine is a plain Python package, `exmergo-dex-core`:

```bash
pip install exmergo-dex-core     # or: uv add exmergo-dex-core
```

Drive the same loop from Python instead of parsing CLI output:

```python
from exmergo_dex_core import DexEngine

with DexEngine(connector="duckdb", path="shop.duckdb") as eng:
    mapped = eng.map()  # a DexCache, not a JSON blob
    rows = eng.query("select status, count(*) from orders group by status")

print(mapped.relationship_count, rows.cells)
```

Every guarantee the CLI makes holds here, because it is the same code. An
unconfirmed billed call raises `ConfirmationRequiredError` carrying the estimate.
By default nothing is written to disk; `DexEngine.from_repo("path/to/repo")` opts in
to a project on disk, the way the CLI does.

For hosts embedding Dex:

- **Values-free mode** keeps every table value out of the model's view, aggregates only. ([values-free mode](https://docs.exmergo.com/dex/guardrails/values-free-mode))
- **Per-user credentials**: pass a `ConnectionSource` so each request reaches the connected system as its own principal.
- **Multi-process lifecycles**: export a plan, verify and apply it elsewhere, and get typed evidence of what a build established. ([host integration](https://docs.exmergo.com/dex/reference/host-integration))
- **Other formats and stores**: plug in a [project format](https://docs.exmergo.com/dex/reference/project-formats) or a [storage backend](https://docs.exmergo.com/dex/reference/storage-backends).

More in the [package README](packages/dex-core/README.md).

## Benchmarks

We run Dex on two public analytics-engineering benchmarks and commit every run's
raw per-task results, including the ones that flatter us least.

| Benchmark | Setup | Result | Details |
|---|---|---|---|
| **data-eng-bench** (Snowflake, 103 tasks) | Dex + Claude Sonnet 5 | **57.3%** resolved, 89.7% of assertions pass | [README](benchmarks/data-eng-bench/README.md) |
| **ADE-bench** (dbt Labs, 75 tasks) | Dex 1.17.4 + Claude Sonnet 5.5 | **80%** resolved vs 73.3% without Dex; **25% fewer failures** | [README](benchmarks/ade_bench/README.md) |

On ADE-bench, the same Claude Sonnet 5.5 model solves **60 of 75 tasks with Dex**,
compared with **55 without it**: **+6.7 percentage points**, with net gains across
six of seven projects. Both configurations make one scored attempt per task.
[Compare the runs and raw results](benchmarks/ade_bench/README.md).

We believe that benchmarks are important, but not as important as user/agent experience.  
Trust in a diff, cost surfaced before spend, and sensitive data kept out of context. We optimize for that experience
and treat these scores as guide posts. ([evaluation](https://docs.exmergo.com/dex/reference/evaluation))

## Managing the Dex lifecycle

### What Dex sends where

- **On install**, `uv` downloads the pinned engine (and a Python 3.11 to 3.14 if you have none) from PyPI or your configured index.
- **Your connected database, data warehouse, or SQL endpoint** gets SELECT-only SQL from Dex, plus the dbt builds you confirm on a dev target, with credentials from your existing credential chain.
- **dbt Cloud** is contacted only if you enable the hosted semantic layer.
- **dbt-core**, when Dex runs it, sends dbt Labs no usage statistics: Dex sets `DO_NOT_TRACK=1` for every dbt process it starts. `transform deps` downloads the packages your `packages.yml` declares.
- **Your repository** holds Dex's state in `.dex/`. dbt writes its usual `target/` and `logs/`.

> [!IMPORTANT]
> **Dex sends nothing to Exmergo.** No telemetry, analytics, license check, or
> update ping. See the [Dex privacy policy](https://www.exmergo.com/privacy/dex)
> and the [Dex terms of service](https://www.exmergo.com/terms/dex).

### What to commit in `.dex/`

Dex keeps its working state in `.dex/`. Most of it is safe to commit; the
exception is any file that can carry data values. Commit the lockfile and the
config, and keep the exploration cache out of a repo that must not publish
data values:

| File | Commit? | Can it contain data values? |
| --- | --- | --- |
| `.dex/config.yml` | Yes | No: connector targets, `pii_overrides` (column names, not values), budgets and limits. Credentials live in environment variables or dbt profiles, never in this file. |
| `.dex/snapshot.json` | Like a lockfile, where its values may be public; otherwise take a metadata-only baseline or keep it out | Yes: when snapshotted from a cache it pins the cache's datasets wholesale, including each non-PII column's capped value domain and min/max. A metadata-only baseline (no cache) carries schema and volume only. PII-flagged columns never carry value domains. |
| `.dex/cache.json` | Only if values may be public | Yes: column profiles with capped value domains (actual values with counts). Never for PII-flagged columns. |
| `.dex/plans/*.json` | Optional, as an audit trail | No data values: the proposed contents of project files. |
| `.dex/queries.jsonl` | Optional, as a ledger | SQL text, which may hold literals. |
| `.dex/drift.json` | No: regenerate with `maintain check` | Aggregates only: counts, names and schema metadata in drift findings. |

For a repo that must not publish data values, ignore the rest:

```gitignore
# Dex state that can publish data values, or is local-only output.
.dex/cache.json
.dex/dex.db
.dex/dex.db-journal
.dex/queries.jsonl
.dex/drift.json
.dex/spend.jsonl
.dex/spend.lock
.dex/cache.lock
```

`.dex/dex.db` is the SQLite backend's equivalent of `cache.json`, so it gets
the same caution. `.dex/spend.jsonl` is the billed-command ledger: byte
counts, job ids and statement hashes only, never SQL values or credentials,
but it is local spend history, so there is no reason to commit it.

### What Dex will never do

- **Write to your source data.** Dex's own SQL is SELECT-only. The only data writes are the dbt builds you confirm, on a dev target.
- **Put personal data in your agent's context.** PII is flagged by column, category, and confidence, and never surfaced. Only a human clears a flag. ([PII policy](https://docs.exmergo.com/dex/guardrails/pii-policy))
- **Spend before quoting.** A metered scan returns an estimate and runs only with your confirmation and a budget. ([cost controls](https://docs.exmergo.com/dex/guardrails/cost-controls))
- **Change your project behind your back.** Every edit is a diff, and a human edit made since planning is never overwritten. ([source of truth](https://docs.exmergo.com/dex/concepts/source-of-truth))
- **Build anywhere but dev.** Prod-looking targets are refused outright.

## Further reading

- [Documentation](https://docs.exmergo.com/dex): start here
- [CLI reference](https://docs.exmergo.com/dex/cli/overview): every command and flag
- [Command contract](https://docs.exmergo.com/dex/reference/command-contract) and [`AGENTS.md`](AGENTS.md): how any agent drives the engine
- [Cost controls](https://docs.exmergo.com/dex/guardrails/cost-controls) and [PII policy](https://docs.exmergo.com/dex/guardrails/pii-policy): the two guardrails that cut across everything
- [Configuration](https://docs.exmergo.com/dex/cli/config): read and change `.dex/config.yml` as a confirmed diff
- [Connectors](https://docs.exmergo.com/dex/connectors/duckdb): setup, cost, and read-only enforcement per connector
- [Changelog](https://docs.exmergo.com/dex/changelog)
- [`references/`](references/): the same material as Markdown, for agents and offline reading

## Dex Enterprise

Dex Enterprise runs Dex as automated workflows in your own CI. It turns tickets into
draft pull requests with `explore` and `transform`, and runs `maintain` on a schedule
to turn drift into draft pull requests for your engineers to review. No Exmergo
service sits in the request path, and everything in this repository stays
Apache-2.0. [Learn more](https://www.exmergo.com/dex/enterprise).

## Community

### Community Integrations

| Integration&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Maintainer&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | What it does | Details |
| --- | --- | --- | --- |
| <img src="assets/dagster-logo.png" width="20" height="20" alt=""> **[dagster-dex](https://github.com/catincloud-labs/dagster-dex)** | <img src="assets/catincloudlabs-logo.png" width="20" height="20" alt=""> [CatInCloud Labs](https://github.com/catincloud-labs) | Explore and maintain your Dagster assets with Dex, using the asset graph in place of a dbt project. | [Repository](https://github.com/catincloud-labs/dagster-dex) |
| <img src="assets/openlakeforge-logo.png" width="20" height="20" alt=""> **[OpenLakeForge](https://github.com/OpenLakeForge/openlakeforge)** | <img src="assets/openlakeforge-logo.png" width="20" height="20" alt=""> [OpenLakeForge](https://github.com/OpenLakeForge) | Explore an OpenLakeForge lakehouse alongside Dex through the `olf` CLI, with read-only access to Trino data, OpenMetadata domains and products, and Dagster jobs and runs. | [Skill](https://github.com/OpenLakeForge/openlakeforge/blob/main/skills/exploring-openlakeforge/SKILL.md) |

### Connect with the Community

Join the agent-native data/analytics community!

- 🌟 [Star Us on GitHub](https://github.com/exmergo/dex/)
- 👾 [Join Our Discord Community](https://www.exmergo.com/discord)
- 🔗 [Follow Us on LinkedIn](https://www.linkedin.com/company/exmergo/)
- 🐦 [Follow Us on X](https://x.com/exmergo)
- 🔨 [Follow Us on GitHub](https://github.com/exmergo/)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, linting, the pre-commit
hook, and changelog fragments. Every pull request into `main` must pass Lint and
CI, and adds a fragment under [`changelog.d/`](changelog.d/) unless no user can
see the change. Please also read the [code of conduct](CODE_OF_CONDUCT.md).

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE). The licence governs the
software. Exmergo's distribution, documentation, support, and trademarks are
covered by the [Dex terms of service](https://www.exmergo.com/terms/dex).
