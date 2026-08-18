# rag-reviewer

[Русский](README.ru.md)

AI-assisted pull-request reviews grounded in whole-repository context: hybrid search, a code
graph, and inline comments anchored to changed lines.

> Requires Python 3.11–3.13 and external Voyage, PostgreSQL/ParadeDB, and Neo4j services.
> Publishing reviews also requires credentials for the selected version-control provider.

[![PyPI](https://img.shields.io/pypi/v/rag-reviewer?color=2563eb&label=PyPI)](https://pypi.org/project/rag-reviewer/)
[![Python 3.11–3.13](https://img.shields.io/badge/python-3.11%E2%80%933.13-2563eb)](https://pypi.org/project/rag-reviewer/)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e)](LICENSE)

## Start here

Choose the shortest route for what you need now. Both routes lead to the same workflows and
reference sections later in this document.

| If you want to… | Follow |
|---|---|
| Try reviewer and get a first result | [Try reviewer](#try-reviewer) |
| Use reviewer with a team on one shared host | [Deploy for a team](#deploy-for-a-team) |

## Try reviewer

You need Python 3.11–3.13, [uv](https://docs.astral.sh/uv/), Docker, a Voyage API key, and a
version-control system (VCS) token if reviewer should read or publish pull-request reviews. The
stores run locally; embedding and reranking requests go to Voyage.

1. Install the launcher, synchronize reviewer's managed artifacts, start the stores, and configure
   reviewer:

   ```bash
   uv tool install rag-reviewer
   reviewer update
   docker compose -f ~/.config/rag-reviewer/docker-compose.yml up -d
   reviewer init
   ```

   `reviewer update` creates the managed Compose file next to the env file in
   `$XDG_CONFIG_HOME/rag-reviewer/` (`~/.config/rag-reviewer/` by default). One store stack therefore
   serves every repository, and the Compose project name stays independent of the current working
   directory. The command also refreshes detected AI-client integrations and skills.

2. See the supported AI clients and connect one:

   ```bash
   reviewer install --list
   reviewer install codex
   ```

3. Build the branch-scoped searchable snapshot called the base index, then check the environment
   and inspect index freshness:

   ```bash
   reviewer index /path/to/repo --ref main
   reviewer check
   reviewer status /path/to/repo --branch main --json
   ```

   Indexing initializes the `chunks` schema that `reviewer check` queries, so a fresh installation
   must index before checking. The check validates every configured VCS provider; its successful
   identity check does not prove repository-specific permissions. The status payload should show an
   indexed SHA and `drift == 0`.
   Full indexing sends code chunks to Voyage and can be slow on its free tier. Without a base
   index, PR review has only the diff and its temporary changed-file index (overlay), and therefore
   thinner repository context.

4. Open a new client session and run the first review:

   ```text
   # Claude Code
   /rag-reviewer:review-pr owner/repo#123 --dry-run

   # Codex
   $rag-reviewer:review-pr owner/repo#123
   ```

   Invocation syntax differs by client. A dry run returns grounded findings without publishing;
   a normal run publishes through `publish_review` and therefore requires VCS write credentials.

For a temporary launcher without a persistent tool installation:

```bash
uvx --from rag-reviewer@latest reviewer
```

## Deploy for a team

This route assumes that team members open their AI-client sessions on one shared host under one
service account. Each client launches its own `reviewer-mcp` stdio process; those processes share
PostgreSQL/ParadeDB and Neo4j through the Compose services bound to `127.0.0.1`, plus the service
account's reviewer env. It is not one central MCP daemon. MCP requests carry repository, branch,
project, and `provider_options`, and tool results return selected code context to the AI client.
For separate workstations, use secured network-accessible stores and configure their DSNs and
reviewer env on every workstation instead of using the loopback Compose defaults.

1. **On the shared host, start the stores and configure secrets for the service account.**

   ```bash
   reviewer update
   docker compose -f ~/.config/rag-reviewer/docker-compose.yml up -d
   reviewer init
   ```

2. **Choose repository and branch scope.** Set `DEFAULT_REPO` as the fallback repo, and either
   the ordered `REVIEW_BRANCHES` CSV allowlist in server env or (preferred) a per-repo home
   layer — see [Repositories and branches](#repositories-and-branches). Put repository-specific
   policy, ignored paths, context limits, and non-secret board metadata in `.review.yml`.

3. **Build and verify every tracked branch.**

   ```bash
   reviewer index /srv/rag_for_git --ref main --repo mimfort/rag_for_git
   reviewer check
   reviewer status /srv/rag_for_git --branch main --json
   ```

4. **Connect team clients.**

   ```bash
   reviewer install --all
   reviewer install codex --dry-run
   ```

   Run installation on the shared host as the same service account. `--all` configures the
   supported clients for that account; `--dry-run` reports planned config writes. Open a new chat
   or CLI session afterwards; IDE integrations may also require Reload Window.

5. **Add optional board context.** Select a registered provider in `.review.yml`, keep its
   credentials in the reviewer env, and validate the exact project:

   ```bash
   reviewer check --board-project TYPE=PROJECT
   ```

   Repeat `--board-project` for additional providers. See [Task boards](#task-boards) and the
   [provider reference](docs/board-providers.md).

## Core workflows

Reviewer workflows are delivered as namespaced skills. Each skill defines its own read/write
boundaries and confirmation gates; the MCP server performs storage, graph, VCS, and board work.

### Review a pull request

Use `review-pr` for bug finding. It prepares a PR session, retrieves code and graph
context, analyzes changed files, verifies candidate findings, and publishes only grounded results.
Use `--dry-run` first when validating a deployment. Inline comments can target only commentable
diff lines; off-diff findings go to the summary.

### Solve a task

Use `solve-task` to turn a board task or free-text request into a persisted brief before
development. It checks index freshness, warms task context, gathers related work and code, then
hands the brief to brainstorming. It does not implement the task by itself.

### Ask a grounded codebase question

Use `ask` for onboarding and codebase Q&A. Answers cite real `path:line` locations from
the base index and code graph. It reads and explains; it neither reviews a PR nor modifies code.

### Walk a human reviewer through a PR

Use `pr-walkthrough` for a reading guide: where to start, what each file changes, and
which callers are affected. It is intentionally separate from bug review.

### Run a focused review

Use `performance-review` for repeated I/O, N+1 work, poor asymptotics, batching, caching,
and memory risks. Use `maintainability-review` for complexity, duplication, readability,
separation of concerns, and repository conventions. Both stay within the requested dimension.

### Create, decompose, and finish board tasks

`create-task` drafts a canonical task body and writes only after confirmation.
`decompose-task` turns one stored parent into a fully previewed native-child batch, asks for one
confirmation, preserves the previewed idempotency key on retries, then re-syncs and verifies every
relationship and child read.
`finish-task` links the PR, moves the task to a discovered done target, adds a task link
to the PR body, and re-syncs the task corpus—also only after confirmation.

### Reviewer grounding in plan/review phases (optional)

[Reviewer grounding in plan/review phases](#reviewer-grounding-in-planreview-phases-optional)
lets planning and review phases reuse session-less reviewer tools when the base index is current.

> **Reviewer grounding (plan/review, optional, fail-open).** Run
> `reviewer status /path/to/repo --branch main --json` first. When `drift == 0`, prefer
> `search_codebase` for cross-file facts and use `callers`, `related_symbols`, `definition`,
> `implementations`, or `family` only for central symbols. The base index does not see
> uncommitted edits, so read changed files from disk. If reviewer or the index is unavailable,
> fall back to local search/read tools instead of blocking.

- `family(repo, node_id, branch)` — the family of look-alike symbols ("who else is
  like this"): inheritance plus structural contract match. For roll-out tasks
  ("add a field to every provider"), where one file found is a representative of a
  family of N.

## How it works

RAG means retrieval-augmented generation: the model receives code selected by hybrid semantic and
lexical search instead of only the PR diff. The graph adds structural relationships.

```text
PR → prepare_review → base + overlay retrieval → skill analysis
   → verify → policy gate → grounding → dedup → inline comments + summary → cleanup
```

- **Base index.** Persistent chunks live under `base:<branch>`. PostgreSQL/ParadeDB combines
  pgvector approximate nearest-neighbor (ANN) search with BM25 lexical ranking; Voyage produces
  embeddings and reranks candidates.
- **Overlay.** Changed PR files use an ephemeral `pr:N` ref. Retrieval takes unchanged files from
  base and changed files from overlay.
- **Code graph.** Neo4j nodes use `node_id = path#fqn`, where `fqn` is the fully qualified name.
  SCIP, an external type-aware code indexer, provides `CALLS` and method-level `IMPLEMENTS`; `auto`
  falls back to tree-sitter `CALLS` plus class-level `IMPLEMENTS` (from syntax) when SCIP is
  unavailable.
- **Grounded publishing.** Findings must quote real changed code. GitHub suggestions are emitted
  only when the replacement is safely applyable on the RIGHT side of the diff.
- **Idempotency.** Hidden fingerprints prevent reposting the same finding. Overlay/session cleanup
  runs after publication and fail-soft on errors.

For the module-level map and invariants, see [CLAUDE.md](CLAUDE.md).

## Installation and configuration

### Requirements

- Python `>=3.11,<3.14`;
- Docker for the default PostgreSQL/ParadeDB and Neo4j stack;
- Voyage API credentials for embeddings and reranking;
- VCS credentials for PR reads and publication;
- a supported AI client with the reviewer MCP integration.

### Installation and updates

Persistent CLI:

```bash
uv tool install rag-reviewer
reviewer update
```

`uv tool install` takes the package name and installs both of its commands, `reviewer` and
`reviewer-mcp`. Its `--from` option only pins a different source for the same package
(`--from rag-reviewer==0.4.3`, `--from git+…`); `--from PACKAGE COMMAND` is `uvx` syntax and
`uv tool install` rejects it.

For the one-time transition from 0.4.3, start the new lifecycle through latest uvx and explicitly
allow it to upgrade the existing persistent tool:

```bash
uvx --refresh --from rag-reviewer@latest reviewer update --upgrade-tool
```

Every later update is the short command `reviewer update`. It performs one lifecycle:

- checks PyPI and upgrades the persistent `uv tool` package when a newer version exists;
- refreshes every detected AI-client MCP integration, native plugin, and file-based skill set;
- synchronizes `$XDG_CONFIG_HOME/rag-reviewer/docker-compose.yml` from the canonical repository;
- records the managed Compose content hash in `.reviewer-update.json`.

If the Compose file differs from its recorded hash, reviewer treats it as user-modified, leaves it
unchanged, and prints a warning. Update does not run `docker compose pull`, restart services, remove
containers, or delete volumes, so existing databases, indexes, tasks, and subsystem summaries stay
intact. Apply a new Compose definition when convenient with the documented `docker compose ... up
-d` command.

Temporary/latest invocation:

```bash
uvx --from rag-reviewer@latest reviewer --help
```

An ordinary uvx invocation never mutates a separate persistent tool; only the explicit
`--upgrade-tool` bootstrap does. Use `reviewer install CLIENT --dry-run` to inspect a named
integration write.

### AI clients

`reviewer update` refreshes all detected clients automatically. Use `reviewer install --list` and a
named install when connecting a client for the first time, before it can be detected:

```bash
reviewer install codex
reviewer install --all
reviewer install-skills codex
```

Codex-specific lifecycle:

```bash
uvx --from rag-reviewer@latest reviewer install codex
uvx --from rag-reviewer@latest reviewer install codex --dry-run
codex plugin list --json
codex mcp list
```

Claude Code global plugin lifecycle:

```bash
uvx --from rag-reviewer@latest reviewer install claude-code
claude plugin list --json
claude plugin marketplace list --json
```

After installation or update, start a New Chat/new CLI session; in an IDE, also use Reload Window.

### Breaking skill-name migration

This release removes the redundant `reviewer_` segment from every skill name. Legacy skill
invocations are unsupported: update the plugin/cache, use the short names listed below, then open
a New Chat or new CLI session. In an IDE, also use Reload Window.

### Required services and credentials

Run `reviewer init` to write the selected env file and `reviewer check` to validate it. Resolution
order is `REVIEWER_ENV_FILE` → `$XDG_CONFIG_HOME/rag-reviewer/.env` → `./.env`.

Important groups:

- Voyage: `VOYAGE_API_KEY`;
- stores: `PG_DSN`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`;
- VCS: provider token plus optional API base;
- repository scope: `DEFAULT_REPO`, `REVIEW_BRANCHES` (branch allowlist fallback; a per-repo home
  layer takes precedence — see [Repositories and branches](#repositories-and-branches));
- board credentials: provider-specific env declared in the registry.

Published host ports of the Compose storage services are variables, not literals:
`PARADEDB_PUBLISH_PORT` (default `5433`), `NEO4J_BOLT_PUBLISH_PORT` (default `7687`) and
`NEO4J_HTTP_PUBLISH_PORT` (default `7474`). Container ports stay fixed. `reviewer init` asks for
them in the storage group and derives the first two from `PG_DSN` and `NEO4J_URI`, so the client
string and the published port cannot drift apart silently; a mismatch on a local host prints a
warning without blocking.

```bash
PARADEDB_PUBLISH_PORT=6543 NEO4J_BOLT_PUBLISH_PORT=7999 \
  docker compose -f ~/.config/rag-reviewer/docker-compose.yml up -d
```

`reviewer start` and `reviewer stop` manage that Compose file for you:

```bash
reviewer start   # up -d --wait, waits for the ParadeDB and Neo4j healthchecks
reviewer stop    # stops the containers; named volumes and the built index survive
```

`reviewer stop` also stops the web admin when it was started with `--profile web`: without an
explicit profile selection docker compose does not see it. It leaves the test services
(`--profile test`) alone — those belong to the repository clone's own Compose project. Both
storages declare `stop_grace_period: 60s`: the default 10s are not enough for the Neo4j JVM to
shut down cleanly, which left the store to be recovered on the next start.

Both run under the explicit Compose project `rag-reviewer`. A clone of this repository runs its
own stack under the project name `rag_for_git` — the two publish the same host ports and keep
separate volumes, so do not run them at the same time. Contributors working inside the clone
should keep using `docker compose up -d` there.

`reviewer stop` never removes volumes: it runs `docker compose stop`, which has no `-v` flag at
all.

On Docker Engine older than 25.0, the `start_interval` healthcheck key is ignored, so the first
Neo4j probe only happens after the plain `interval` (300s) — exactly the `--wait` timeout used by
`reviewer start`. On such engines `reviewer start` can report a timeout failure even though the
stack came up fine; upgrading Docker Engine removes the issue.

Prefer variables over editing the Compose file: a hand-edited
`~/.config/rag-reviewer/docker-compose.yml` no longer matches its recorded hash, so `reviewer
update` treats it as user-modified (status `preserved`) and stops delivering new Compose
definitions to it. A `preserved` Compose file also stops receiving new healthcheck definitions, so
`reviewer start` falls back to waiting for the `running` state instead of real readiness.

Credentials stay server-side. **Credentials are not returned** by board metadata or discovery
tools and must not be placed in `.review.yml`.

### Configuration ownership

| Location | Owner | Stores | Must not store |
|---|---|---|---|
| global `.env` | deployment/operator | secrets, credentials, DSNs, runtime infrastructure and compatibility fallbacks | repository policy |
| home global YAML | OS account running reviewer | shared non-secret defaults | credentials |
| home per-repo YAML | OS account running reviewer | `repository.primary_branch`, `repository.index_branches`, operator-owned repo policy | credentials |
| committed `.review.yml` | repository team | team-visible review policy and non-secret task-board metadata | credentials or `repository` |
| git remote / CLI | repository/operator | canonical `owner/name` identity and explicit command overrides | persisted secrets |
| Postgres / Neo4j | reviewer runtime | derived indexes, task/review state and code graph | source-of-truth configuration |

#### Single repository

Run `reviewer init` from the clone, inspect the global `.env` and home per-repo previews, then run
`reviewer check` and `reviewer config show --repo owner/name`.

#### Second repository

Run `reviewer init --scope repo` from the second clone. It creates or previews only that repository's
home per-repo YAML and does not rewrite global `.env` or the first repository's config.

#### CI / server

Inject secrets into global `.env` or the process from a secret manager. Use noninteractive init only
for deterministic preview/write, mount home YAML for the service account, and keep team-owned policy
in committed `.review.yml`. Pass `--repo owner/name` when no usable git remote is present.

### VCS credentials

| Provider | Environment | Minimum access | Reviewer reads | Reviewer writes | `reviewer check` |
|---|---|---|---|---|---|
| GitHub | `GITHUB_TOKEN` | fine-grained PAT: Pull requests: Read and write; Contents: Read | PR metadata, files, comments, contents, compare | review comments/summary and PR body backlink | authenticates `/user` identity |
| GitLab | `GITLAB_URL`, `GITLAB_TOKEN` | PAT/project token with `api` scope | MR metadata, changes, notes, repository files, compare | discussions/notes and MR description backlink | authenticates `/api/v4/user` identity |

The health check proves URL/token authentication, not every granular repository permission. The
selected repository permissions are exercised by an actual review. `reviewer init` shows the same
contract before prompting only for the selected provider's credentials.

### Repositories and branches

`DEFAULT_REPO` identifies the fallback `owner/name`. The repo tag is resolved as `--repo` →
`git remote origin` → `DEFAULT_REPO`, and the resolution reports its own origin: `cli`,
`git:origin`, or `env:DEFAULT_REPO`. Because an index written under the wrong tag surfaces only
as odd search results, `reviewer index` **refuses** to write when the name was substituted from
`DEFAULT_REPO` rather than derived from the clone — pass `--repo owner/name` or fix the origin
URL. `reviewer status` stays fail-open and instead exposes the origin: a warning line in the text
output and a `repo_source` key in `--json`.

Tracked branches for a repository are
resolved in layered order — the first source that defines them wins entirely (no per-branch
merge): a per-repo home file `$XDG_CONFIG_HOME/rag-reviewer/repos/<owner>/<name>.yml` →
the home-global `review.yml` → the env `REVIEW_BRANCHES` CSV allowlist → `["main"]`. In every
source the first entry is primary unless `primary_branch` is set explicitly. Each branch has
isolated `base:<branch>` chunks and graph nodes. Run `reviewer config show --repo owner/name`
to see the effective branches and which layer produced them.

```bash
reviewer index /path/to/repo --ref main --repo owner/name
reviewer status /path/to/repo --branch main --json
reviewer search "token verification" --branch main
```

Use `reviewer config migrate --repo owner/name` to copy the env `REVIEW_BRANCHES` allowlist into
the per-repo home layer (no-op if a home layer already sets branches), or `reviewer migrate-branches`
once when upgrading a legacy unscoped base index.

### Per-repo `.review.yml`

Per-repo policy overrides server defaults and is read from the target/base branch. Typical fields:

```yaml
paths:
  ignore:
    - generated

summary_cluster_depth: 2
summary_topk_threshold: 20

summary_paths:
  ignore:
    - tests
    - test

context_limits:
  search_codebase:
    floor: 4
    ceiling: 15
  graph:
    hops: 1
```

`summary_paths.ignore` only filters which files feed subsystem-summary clustering — unlike
`paths.ignore`, it does not affect indexing or PR review. Default is `["tests", "test"]`; there
is no env layer (like `context_limits`), and an explicit empty list disables the filter.

### Layered repository policy

Policy is resolved in this exact order; each later source wins for the same top-level key:

```text
ENV
  < $XDG_CONFIG_HOME/rag-reviewer/review.yml
  < committed .review.yml at the selected target ref
  < $XDG_CONFIG_HOME/rag-reviewer/repos/<owner>/<name>.yml
```

When `XDG_CONFIG_HOME` is unset, the home root is `~/.config/rag-reviewer`. Merging is only at the
top level: a later mapping, list, or `null` replaces the complete earlier value; nested mappings
are not deep-merged. That replacement is **shadowing**. Inspect the effective policy, source for
each key, and shadowed sources with:

```bash
reviewer config show --repo group/service --branch main --json
```

The committed layer is fetched at the selected ref, so review/config resolution never reads an
uncommitted worktree `.review.yml`.

It is read **from a local clone whenever one is usable**, and only otherwise through the hosting
API. `config show` uses `--path <clone>` if given and the current directory otherwise; the MCP
server uses the clone path recorded by `reviewer index` (which already runs from a clone). A
candidate is accepted only if it is a git repository whose remote matches the target repo — a clone
with **no** recognizable remote is accepted too, which is exactly the case where the committed layer
was previously unreachable. If the ref does not resolve in the clone (branch not fetched), the read
falls back to the API rather than silently reporting an empty layer. The report states which path
was taken:

```bash
reviewer config show --repo group/service --branch main --path /srv/clones/service
# committed: local        ← resolved without a single network call
```

In JSON the same value is the `committed_source` key (`local` / `vcs`); the clone path itself is
never printed.

To copy a safe committed policy into the repo-specific home
layer without modifying the committed file, run:

```bash
reviewer config migrate --repo group/service --branch main
```

Migration is non-destructive: an equivalent destination is a no-op, while a differing destination
is reported as a conflict and left unchanged. Home files with credential-like keys are rejected as
policy layers and their values are never displayed; keep credentials in server environment instead.
Home configuration belongs to the OS account running reviewer. On a shared service account it can
silently affect that account's workloads, so use committed `.review.yml` for team-visible policy and
restrict the service account's home configuration permissions.

Use `configure-review` to update context fields without clobbering unrelated keys. It
recommends the per-repo home target first, or can explicitly update the committed `.review.yml` for
team-visible policy.

### Task boards

Board selection is generic and registry-driven. Credentials come from server env; `.review.yml`
contains only non-secret metadata:

```yaml
task_board:
  type: <registered-provider>
  project: PRI
  key_pattern: "[A-Z]+-\\d+"
  url_template: "https://tasks.example/{code}"
  create_target: Backlog
  done_target: Done
  options:
    <provider-option>: <discovered-value>
  sync_filter:
    max_age_days: 180
    include_archived: false
```

The repo block wins; an explicit empty `task_board:` disables board work. If the block is absent,
the server may use a **non-secret deploy-wide fallback**. Calls use configured registry credentials
without returning them.

`sync_filter` is a generic sibling of provider `options`. By default `max_age_days` is absent (no
age limit) and `include_archived: true`. Age uses task last-modified time with an inclusive cutoff,
so a task exactly at the boundary remains eligible. An unknown age is not filtered by age. Only
while `include_archived: false`, unknown archive does not itself exclude the row and an archive
warning is emitted only then. Age filtering runs first and may still exclude the row; in that case
archive uncertainty is not counted or warned. Archive is separate from terminal/done state.
Repositories with the same `task_board.project` share one task corpus. Retention never deletes
implicitly: purge is explicit. A filter change backfills newly eligible tasks on the next successful
full sync.

The server-side flow is **store-first**:

1. `sync_board` enumerates and normalizes tasks, then stores vectors and task-graph metadata under
   `tasks:<type>:<board>`.
2. Skills call `get_task(key, project=...)`; linked tasks/PRs/code come from task context tools.
3. Client models never enumerate the provider directly and never send credentials.

The MCP server currently exposes **42 tools**, including the native-subtask batch operation.

Legacy aliases remain **legacy metadata for older clients** for one compatibility window:
`TASK_BOARD_API_KEY → YOUGILE_API_KEY` and
`TASK_BOARD_API_BASE → YOUGILE_API_BASE`. New deployments should use registry-declared
provider credentials. See [docs/board-providers.md](docs/board-providers.md) for the current
provider matrix, target discovery, options, setup, and credential rotation.

### Observability and tuning

`reviewer serve` exposes review history and traces through the optional web extra. Summary depth,
top-k threshold, graph backend, and retrieval ceilings change cost/recall trade-offs; start with
defaults and tune only after observing real misses or excessive context.

Review cost accounting uses two independent channels. The plugin's `PreToolUse` hook
(`plugin/hooks/review_cost.py`) reads the Claude Code session transcript client-side and writes a
per-stage token usage sidecar that `publish_review` reads server-side, weighting token buckets
(fresh input, output, cache write, cache read) rather than summing raw token counts. The step-by-step
tool-call trace (`review_steps`, shown on the run's trace page) is recorded entirely server-side and
independently of the hook. `total_cost` and the per-stage breakdown are weighted, unitless scores —
not dollar amounts.

## CLI reference

| Goal | Commands |
|---|---|
| Configure and integrate | `init`, `install`, `install-skills`, `update` |
| Validate environment | `check` |
| Manage local infrastructure | `start`, `stop` |
| Manage indexes | `index`, `status`, `search`, `migrate-branches`, `gc` |
| Run observability UI | `serve` |
| Start MCP directly | `reviewer-mcp` |

Use `reviewer COMMAND --help` for the current option set. `status` does not spend Voyage tokens;
`search` and indexing do.

## Skills reference

The examples below use Claude-style `/rag-reviewer:...` invocation. Codex exposes the same
namespaced skills with `$rag-reviewer:...`.

### `review-pr` — full PR review

- **When:** find correctness, security, performance, and maintainability issues in a PR.
- **Invoke:** `/rag-reviewer:review-pr owner/repo#123 --dry-run`.
- **Needs:** reviewer MCP, VCS access, stores, and preferably a fresh base index/graph.
- **Reads/writes:** reads PR/code/task context; publishes through `publish_review` unless dry-run.
- **Result:** grounded inline comments plus a summary; deterministic publish handles dedup.

### `solve-task` — task to development brief

- **When:** start implementation from a key such as `PRI-220` or a free-text request.
- **Invoke:** `/rag-reviewer:solve-task PRI-220`.
- **Needs:** reviewer MCP; board context is optional and the pipeline continues board-less.
- **Reads/writes:** reads task/code context and writes one brief under `docs/superpowers/briefs/`.
- **Result:** a compact brief handed to brainstorming; implementation happens in later skills.
- **Context gathering:** one server-side call, `prepare_task_context`, replaces the former
  `reviewer status` → `sync_board` → `get_task` → `search_*` chain — preflight, board warm-up, the
  task itself, linked/similar tasks, relevant subsystems, and code all come back in a single
  payload. Fail-open semantics are preserved: anything unavailable (stale index, missing board,
  empty search) is reported per-section in `gaps` instead of aborting the skill. Graph expansions
  (`get_related_symbols`, `callers`, `implementations`, `family`, …) and `get_pr_diff` stay
  separate calls made at the LLM's discretion, since they depend on what the brief turns up.
- **Startup survey:** one `AskUserQuestion` panel asks three things before anything else — the
  brief model tier (`cheap`/`mid`/`premium`), the interaction mode, and the execution strategy.
  No answer, or a headless run, applies the defaults `mid` / `normal` / `subagent` without
  blocking.
- **Interaction modes:** `normal` — brainstorming questions plus spec and plan approvals;
  `auto` — questions asked, approvals dropped; `full-auto` — no questions, the recommended option
  taken at every fork, approvals dropped. In every mode the spec and the plan are still written,
  self-reviewed and committed. `full-auto` still asks before `git push`, opening a PR, or writing
  to the board.
- **Execution strategies:** `inline` (executing-plans), `subagent` (subagent-driven-development),
  `lite` (`plugin/skills/_profiles/execution-lite.md` — one reviewer per group of up to 3 tasks
  sharing files, a 3-round fix cap, a mandatory final whole-branch review), and `auto` (resolved
  after the plan by an ordered rubric: risk signals or >8 tasks or >10 files → `subagent`;
  ≤3 tasks and ≤3 files → `inline`; otherwise `lite`).
- **Run state:** the chosen mode and strategy are written to `.superpowers/solve-task/<KEY>.md`,
  which is git-ignored — never to the brief, the spec, or the plan.

### `ask` — grounded codebase Q&A

- **When:** ask where code lives or how a subsystem works.
- **Invoke:** `/rag-reviewer:ask how does index freshness work?`.
- **Needs:** a built base index and graph.
- **Reads/writes:** reads repository context and local files; does not modify or review code.
- **Result:** a Russian explanation with real `path:line` citations.

### `pr-walkthrough` — human reading guide

- **When:** orient a human reviewer without running a bug review.
- **Invoke:** `/rag-reviewer:pr-walkthrough owner/repo#123`.
- **Needs:** reviewer MCP, PR access, base index, and graph.
- **Reads/writes:** reads impact/diffs/callers; posts only on explicit request.
- **Result:** centrality-first reading order, per-file summary, and grounded impact notes.

### `performance-review` — performance-only review

- **When:** inspect a diff for repeated work, N+1 I/O, asymptotics, batching, caching, or memory.
- **Invoke:** `/rag-reviewer:performance-review`.
- **Needs:** a diff/PR or explicit change scope; reviewer context is fail-open.
- **Reads/writes:** reads the selected changes and nearby context; does not publish by itself.
- **Result:** only concrete performance findings, with assumptions stated.

### `maintainability-review` — maintainability-only review

- **When:** inspect complexity, readability, duplication, boundaries, and repository conventions.
- **Invoke:** `/rag-reviewer:maintainability-review`.
- **Needs:** a diff/PR or explicit change scope plus repository guidance.
- **Reads/writes:** reads changes and nearby patterns; does not change behavior.
- **Result:** focused simplification findings, excluding unrelated correctness/performance advice.

### `create-task` — create a canonical board task

- **When:** file a grounded task on the configured board.
- **Invoke:** `/rag-reviewer:create-task describe the requested change`.
- **Needs:** registered board config, discovered create target/options, and project credentials.
- **Reads/writes:** reads code for evidence; calls `create_task` only after explicit confirmation.
- **Result:** canonical body, task key/URL, and a refreshed task corpus.

### `decompose-task` — create native child tasks from one parent

- **When:** split an existing board task into grounded, independently actionable native children.
- **Invoke:** `/rag-reviewer:decompose-task PRI-224`.
- **Needs:** a stored parent, configured board, authoritative `native_subtasks` capability, task
  context, similar tasks, and relevant code from `search_codebase`.
- **Board config:** inspect the repository `task_board` key once. A present null/empty/disabled
  explicitly disables board work and never calls deploy-wide `get_board_config`. Only an absent
  repository key may call `get_board_config` once; a mapping freezes generic `type`, `project`, and
  `options` for the entire flow.
- **Preview/confirmation:** shows the provider, parent, idempotency key, and complete canonical body
  of every child, then asks for one explicit confirmation of the whole preview; no earlier write.
- **Write/verification:** sends exactly one confirmed initial batch. Every actually attempted batch
  write is verified regardless of status (`ok`, `partial`, `error`, or timeout) before declaring
  its outcome or offering recovery.
- **Verification:** performs exactly one project-scoped sync, re-reads the parent with `get_task`
  and graph/context with `get_task_context` even when no child keys were returned, and point-reads
  every returned child key with `get_task`.
- **Recovery:** partial, timeout, or error recovery is never automatic. The skill preserves and
  reports `status`, `category`, and `retryable`. After verification, only transport timeout or
  unknown outcome or `retryable=true` reaches a new explicit user choice between exact retry or
  stop; `retryable=false`, and `unsupported`, `conflict`, and `parent_not_found` stop without retry.
  Exact retry replays the same full payload, order, and idempotency key; it never mints a new key,
  never edits wording, and never sends only the remainder.
- **Result:** created/attached/unattached/pending children and warnings, reported without guessing.

### `finish-task` — close a task after its PR

- **When:** a PR exists and the board task should be linked and completed.
- **Invoke:** `/rag-reviewer:finish-task PRI-220 https://github.com/owner/repo/pull/123`.
- **Needs:** task key, PR URL, registered board config, and discovered done target/options.
- **Reads/writes:** after explicit confirmation, appends the PR idempotently, updates the task,
  prepends a task backlink to the PR body, and re-syncs.
- **Result:** done state plus `already_closed`/`task_link_status` (`added` | `already_present` |
  `failed`) reporting without duplicate links; `task_link_added` keeps its old meaning
  ("written just now").

### `report-bug` — report a defect of reviewer itself

- **When:** a reviewer MCP tool broke its own documented contract, a skill step was impossible with
  the available tools, a stated invariant failed, or a reviewer frame appeared in a traceback.
  Problems of the user's project (environment, external services, permissions, their own code) are
  deliberately out of scope: the channel is only worth having while it stays silent on them.
- **Invoke:** `/rag-reviewer:report-bug`.
- **Needs:** nothing beyond the MCP server; a GitHub token only for the publishing path.
- **Reads/writes:** the server triages the symptom class, anonymizes every text field
  deterministically in Python (source fragments, absolute paths, repo/branch/file names, task keys
  and board URLs, self-hosted hosts, e-mails, tokens) and assembles the issue for
  `mimfort/rag_for_git`. **What leaves your machine** is the anonymized narrative plus an
  Environment block of *shape only*: orchestrator and subagent models, mode, CLI and OS, reviewer /
  plugin / Python versions and install mode, registered board type, VCS type and whether it is
  self-hosted (never the host), graph backend, index presence and drift as a number, and integer
  counts of clusters/files/findings/tasks. The exact final text is shown before anything is sent,
  and the Environment block can be trimmed line by line or dropped entirely without blocking the
  report.
- **Approval:** publication happens **only** after an explicit human yes, and never in headless,
  cron or background runs — this is enforced server-side, not by the prompt. The issue is created
  from the user's GitHub account, so their username becomes visible in a public repository; the
  skill says so before asking. A matching open issue gets a comment instead of a duplicate.
- **Result:** `published` / `commented` with URLs, or `fallback` with ready-made markdown and a
  prefilled issue link for manual posting — a failure to report never breaks the session.
- **Automatic trigger:** a `PostToolUse` hook watches reviewer tool results and recognizes two
  shapes deterministically — a traceback with `reviewer/*` frames, and a `status` value outside a
  tool's documented set — so noticing a defect is not left to the model's attention. Routine
  failures are checked **first** and always win: unavailable stores, missing keys or tokens, board
  rate limits, 401/403/404, network timeouts, a missing or stale index, and an untracked branch
  never produce a nudge. Invariant violations (idempotency, dedup, counters) stay model-noticed:
  they are invisible in a single response, and guessing from one call is how a hook turns into
  noise. The nudge carries only the shape of the failure, fires at most once per symptom per
  session, and costs nothing when nothing is wrong.
- **Switch:** `bug_reports: false` in a repository's `.review.yml` disables the channel and the
  hook for that repository, `REVIEW_BUG_REPORTS=false` for the whole deploy.

### `sync-codebase` — build or update the base index

- **When:** initialize an index, refresh stale code, or rebuild the graph.
- **Invoke:** `/rag-reviewer:sync-codebase --path /srv/repo --ref main`.
- **Needs:** git clone, `uvx`, reviewer services, Voyage, and optional SCIP.
- **Reads/writes:** reads the selected git ref and writes branch-scoped vectors/graph nodes.
- **Result:** incremental index report; failures name the missing prerequisite.

### `sync-tasks` — warm task vectors and graph

- **When:** synchronize a configured board before task search or solve-task.
- **Invoke:** `/rag-reviewer:sync-tasks`.
- **Needs:** use `reviewer init`, configure the selected provider as documented in
  `docs/board-providers.md`, then validate it with `reviewer check`.
- **Reads/writes:** calls idempotent server-side `sync_board` in repo mode with canonical repo and
  tracked branch. The server resolves effective policy; the client does not reconstruct it. It reads
  the board and does not write back. Policy errors never retry as an unfiltered explicit call.
- **Result:** `eligible`, `filtered_by_age`, `filtered_archived`, `age_unknown`, `archive_unknown`,
  `filter_applied`, `filter_fingerprint`, `filter_source`, `by_board`, `purge`, and `warnings`;
  missing config remains board-less/fail-open.

### `summarize-subsystems` — GraphRAG subsystem summaries

- **When:** build or refresh the architectural prior used by Q&A and PR walkthroughs.
- **Invoke:** `/rag-reviewer:summarize-subsystems`.
- **Needs:** a fresh base index, code graph, reviewer MCP, and confirmation of cluster depth.
- **Reads/writes:** reads skeletons of only added/changed files via `get_file_skeletons` (job's
  input is a skeleton, not the source), batched up to 15 paths per job, reuses stored per-file
  fragments, and atomically writes fragments together with the cluster summary.
- **Result:** сводки и метрики `created`/`reused`/`removed`/`moved`,
  `deferred`/`raced`, `fragments_pruned` и `embedded`.
- **Payload:** the cluster listing runs in compact, paginated mode
  (`compact=True`, `offset`/`limit`): metadata plus `added`/`changed`/`removed`/`moved` counters,
  no paths and no fingerprints, so its size grows with the number of clusters rather than files
  (10 922 B compact vs 97 530 B full on this repository; the full format itself was 106 878 B
  before PRI-229). Per-cluster file detail comes from `get_subsystem_summary_work`. In full
  format `files` lists only unchanged files — the delta lists are not repeated there.

Первый полный прогон после обновления создаёт fragments для всех текущих файлов, но не удаляет
старые сводки: каждый кластер заменяется только после успешной атомарной записи нового bundle.
При настроенном cap bootstrap может занять несколько проходов. Freshness считается по
skeleton-коду, поэтому правка только тела функции намеренно остаётся невидимой, пока не изменится
skeleton. Layout identity — canonical token от default `summary_cluster_depth` и
нормализованных `summary_cluster_depth_overrides`: смена любого из них принудительно пересобирает
все fragments, даже если default depth прежний. Частичный или ограниченный cap-ом прогон не
запускает prune; optimistic race (`stored=false`) тоже считается отложенным, не успехом, и
запрещает prune в этом проходе. Полный проход передаёт в prune token и точную карту
`cluster_key → source_hash`; сервер повторно выводит layout и под advisory lock проверяет каждую
summary и same-generation fragment coverage до удаления сирот и финализации state. Embedding
backfill пишет вектор только по exact CAS `source_hash + title + summary`, поэтому конкурентная
перезапись текста не получает устаревший вектор и не увеличивает `embedded`.

### `configure-review` — update layered policy and branches

- **When:** tune tracked branches, ignored paths, retrieval limits, summary clustering, or board
  metadata.
- **Invoke:** `/rag-reviewer:configure-review`.
- **Needs:** a git repository; MCP and databases are not required for baseline analysis.
- **Reads/writes:** reads tracked Python structure/history and changes approved YAML fields in either
  `home:repos/<owner>/<name>.yml` or committed `.review.yml`; branch values always go to the home
  per-repo YAML.
- **Result:** preserved foreign keys/comments plus exact rebuild guidance.

## Operations, troubleshooting, and limitations

### Health checks

Use these before investigating application behavior:

```bash
reviewer check
reviewer status /path/to/repo --json
docker compose ps
```

`reviewer check` validates configured credentials and service connectivity without spending
Voyage quota. `status` compares the indexed SHA with the selected local ref and reports chunks,
graph nodes, subsystem summaries, and commit drift for each tracked branch.

### Index freshness and recovery

- `drift == 0`: the base index matches the selected ref.
- `drift > 0`: run `reviewer index /path/to/repo --ref BRANCH` after considering Voyage cost.
- `drift == null` or zero chunks: the branch has no usable base record; build it explicitly.
- Missing `IMPLEMENTS` edges: ensure SCIP is installed and rebuild with the SCIP backend.
- Orphaned `pr:N` overlays or expired persisted sessions: run `reviewer gc`.

Base indexes track committed refs, not working-tree edits. During planning or review, read
uncommitted files directly from disk.

### Common failures

| Symptom | Likely cause | Next action |
|---|---|---|
| `reviewer check` reports Postgres/Neo4j unavailable | Default stores are not running or DSNs differ | Run `docker compose -f ~/.config/rag-reviewer/docker-compose.yml up -d`, then repeat `reviewer check` |
| Voyage returns 429 | Free-tier RPM/TPM quota is exhausted | Wait for the quota window; rerun incremental indexing rather than deleting the index |
| PR is skipped | Its target branch is not tracked for this repository (see `reviewer config show`), or draft policy skips it | Inspect `prepare_review` reason; if the target is intentional, add the branch via the per-repo home layer (or `REVIEW_BRANCHES` fallback), not just policy |
| `config show` reports a `skipped` `.review.yml` layer and exits non-zero | The committed policy layer could not be fetched (no network/token, 404) or could not be parsed | Home layers are still applied — check the reported `category`/`http_status`; fix the remote or the committed YAML. Review, indexing, and migration stay loud and fail instead. A home layer with a forbidden credential key is also reported as `skipped` and exits `1`, even though the layer is simply excluded from resolution |
| Task lookup is empty | Board is disabled/unconfigured or the corpus is cold | Validate [board setup](docs/board-providers.md), then run `/rag-reviewer:sync-tasks` |
| Q&A misses new local code | Base index contains only a committed ref | Read the local file or commit/index the intended branch |
| AI client cannot see new skills | Client session predates installation | Start a New Chat/new CLI session; use Reload Window in an IDE |

Secondary context is deliberately fail-open: an unavailable graph, board, subsystem prior, or
historical PR diff should reduce context and produce a warning, not invent data.

### Web admin

The optional web UI shows review runs, findings, traces, and aggregate statistics:

```bash
pip install -e ".[web]"
cd web/frontend && npm install && npm run build && cd ../..
reviewer serve
```

The **Quality** page shows the trend of the solve-task brief quality metric across tasks: median
core-recall (precision is plotted per task on the trend chart; it has no median of its own), a bulk
subsample (tasks with `expected_core >= 10`, the `BULK_CORE_THRESHOLD`) with a horizontal line for
the offline baseline for before/after comparison, and a breakdown of misses by taxonomy.
The data source is the `brief_quality` table, populated on every real `publish_review` call
(written by `MCPReviewService`, not a separate process). If a task's brief is missing, or has no
`## Relevant code` section at all, the measurement is skipped — no point shows up on the chart
instead of a zero or an error. A section that exists but is empty is not a skip: it is a valid
measurement with `predicted = 0`.

The container keeps its internal listen port separate from the published loopback port. Build it
once and choose both at runtime (replace `database` with a Postgres host reachable from the
container):

```bash
docker build -f web/Dockerfile -t rag-reviewer-web .
docker run --rm \
  --env PG_DSN=postgresql://reviewer:reviewer@database:5432/reviewer \
  --env REVIEWER_WEB_PORT=8080 \
  --publish 127.0.0.1:18000:8080 \
  rag-reviewer-web
```

The Compose service is opt-in, so ordinary `docker compose up` still starts infrastructure only:

```bash
docker compose --profile web up -d web
REVIEWER_WEB_PORT=8080 REVIEWER_WEB_PUBLISH_PORT=18000 \
  docker compose --profile web up -d web
```

Without overrides, both the internal and published ports default to `8000`.

Set `WEB_ADMIN_USER` and `WEB_ADMIN_PASSWORD` before exposing it beyond localhost. Store and API
errors are reported without preventing the process from starting where fail-soft behavior is safe.

### Security

- Keep Voyage, VCS, board, database, and web-admin credentials in server env, never `.review.yml`.
- Use least-privilege VCS tokens; publishing and `finish-task` perform external writes.
- Review every confirmation gate before comments, board tasks, status transitions, or PR-body
  changes.
- Stored copies stay in the configured databases, but code chunks and search text are sent to
  Voyage; PR diffs and retrieved context are also sent by the AI client to its AI model provider.
- External provider calls require network access; ordinary unit tests do not.

### Known limitations

- Python is the supported analysis language; SCIP gives the most accurate graph.
- Without SCIP, tree-sitter provides a useful but name-based `CALLS` graph plus class-level
  `IMPLEMENTS` from syntax; method-level override `IMPLEMENTS` coverage stays SCIP-only.
- GitHub permits inline comments only on commentable diff lines; other findings appear in summary.
- Full indexing can hit Voyage free-tier limits; updates are incremental and reuse embeddings.
- The base index is branch-scoped and blind to uncommitted working-tree changes.
- OAuth loopback flows are not supported in headless/SSH integrations; use documented PAT/API-key
  credentials.
- Board work is optional. Missing provider configuration keeps task-aware skills board-less rather
  than blocking code retrieval.

## Development

Create an isolated environment and install development dependencies:

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
git config core.hooksPath .githooks
```

The last command enables the tracked `pre-commit` hook: it runs `ruff check` on staged `.py`
files and blocks the commit when they are not clean. Git cannot enable hooks automatically, so
every clone opts in once. Bypass a single commit with `git commit --no-verify`.

Unit tests prohibit external and localhost sockets and exclude integration tests by default:

```bash
.venv/bin/pytest -q
.venv/bin/ruff check .
```

Run integration services in the isolated test profile:

```bash
docker compose --profile test up -d --wait paradedb-test neo4j-test
.venv/bin/pytest -q -m integration
docker compose --profile test rm -sfv paradedb-test neo4j-test
```

Never use `docker compose --profile test down -v`: the test and development services share a
Compose project, so that command can remove development volumes.

### solve-task metrics (offline)

An offline harness measures the cost of the solve-task stage and retrieval
quality over the accumulated brief corpus (`docs/superpowers/briefs/`), stores a
history of snapshots and compares runs. No Postgres, Neo4j or network needed —
local git only.

```bash
python -m eval.solve_task_metrics snapshot            # recompute metrics, store a snapshot, refresh the report
python -m eval.solve_task_metrics stats --last 10     # trend of the latest snapshots as a table, no recompute
python -m eval.solve_task_metrics compare --back 1    # deltas of the latest snapshot against N steps back
python -m eval.solve_task_metrics forecast            # core-recall forecast with a spread
```

Cost is measured in weighted input-equivalents (`output ×5`, `cache-write ×1.25`,
`cache-read ×0.1`); the raw token sum is shown for reference only — it is not
proportional to cost. Quality is core-recall over a narrowed denominator; tasks
whose diff contains no core files count as "no measurement point", not as zero
recall. Snapshots live in `eval/solve_task_metrics_history.jsonl`, the report in
`eval/solve_task_metrics_report.md`.

| Area | Responsibility |
|---|---|
| `reviewer/index/`, `reviewer/retrieval/` | chunking, vectors/BM25, freshness, reranking |
| `reviewer/graph/` | tree-sitter/SCIP graph construction and Neo4j access |
| `reviewer/mcp/`, `reviewer/services/` | PR sessions, tools, prepare/publish orchestration |
| `reviewer/tasks/` | task storage, graph, sync, and registered board providers |
| `plugin/skills/` | user-facing agent workflows |
| `tests/` | offline unit and isolated integration contracts |

Read [CLAUDE.md](CLAUDE.md) before changing architecture or invariants. Keep Russian comments,
docstrings, and CLI messages; use Conventional Commits without self-attribution.

## License

[MIT](LICENSE) © rag_for_git contributors.
