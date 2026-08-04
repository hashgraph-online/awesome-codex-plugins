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

1. Install the launcher, download the repository's Compose file into reviewer's config directory,
   start the stores, and configure reviewer:

   ```bash
   uv tool install rag-reviewer
   mkdir -p ~/.config/rag-reviewer
   curl -o ~/.config/rag-reviewer/docker-compose.yml \
     https://raw.githubusercontent.com/mimfort/rag_for_git/main/docker-compose.yml
   docker compose -f ~/.config/rag-reviewer/docker-compose.yml up -d
   reviewer init
   ```

   The Compose file lives next to the env file in `$XDG_CONFIG_HOME/rag-reviewer/`
   (`~/.config/rag-reviewer/` by default), so one store stack serves every repository and the
   Compose project name stays the same no matter which repository you are standing in. Plain
   `curl -O` writes into the current directory instead; inside a clone of this repository it
   overwrites the tracked `docker-compose.yml`.

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
   must index before checking. The check currently requires `GITHUB_TOKEN`, even for a GitLab-only
   setup; validate `GITLAB_TOKEN` with a dry-run `/rag-reviewer:review-pr` against a GitLab MR until
   that limitation is removed. The status payload should show an indexed SHA and `drift == 0`.
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
   mkdir -p ~/.config/rag-reviewer
   curl -o ~/.config/rag-reviewer/docker-compose.yml \
     https://raw.githubusercontent.com/mimfort/rag_for_git/main/docker-compose.yml
   docker compose -f ~/.config/rag-reviewer/docker-compose.yml up -d
   reviewer init
   ```

2. **Choose repository and branch scope.** Set `DEFAULT_REPO` and the ordered
   `REVIEW_BRANCHES` allowlist in server env. Put repository-specific policy, ignored paths,
   context limits, and non-secret board metadata in `.review.yml`.

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
> `search_codebase` for cross-file facts and use `callers`, `related_symbols`, `definition`, or
> `implementations` only for central symbols. The base index does not see uncommitted edits, so
> read changed files from disk. If reviewer or the index is unavailable, fall back to local
> search/read tools instead of blocking.

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
  SCIP, an external type-aware code indexer, provides `CALLS` and `IMPLEMENTS`; `auto` falls back
  to tree-sitter `CALLS` when SCIP is unavailable.
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
(`--from rag-reviewer==0.4.2`, `--from git+…`); `--from PACKAGE COMMAND` is `uvx` syntax and
`uv tool install` rejects it.

Temporary/latest invocation:

```bash
uvx --from rag-reviewer@latest reviewer --help
```

`reviewer update` checks before mutating a persistent uv tool installation. Use
`reviewer install CLIENT --dry-run` to inspect integration writes.

### AI clients

Discover clients with `reviewer install --list`; install one client or every detected client:

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

After installation, start a new chat/CLI session; in an IDE, also use Reload Window.

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
- repository scope: `DEFAULT_REPO`, `REVIEW_BRANCHES`;
- board credentials: provider-specific env declared in the registry.

Credentials stay server-side. **Credentials are not returned** by board metadata or discovery
tools and must not be placed in `.review.yml`.

### Repositories and branches

`DEFAULT_REPO` identifies the fallback `owner/name`. `REVIEW_BRANCHES` is an ordered CSV allowlist;
the first entry is primary. Each branch has isolated `base:<branch>` chunks and graph nodes.

```bash
reviewer index /path/to/repo --ref main --repo owner/name
reviewer status /path/to/repo --branch main --json
reviewer search "token verification" --branch main
```

Use `reviewer migrate-branches` once when upgrading a legacy unscoped base index.

### Per-repo `.review.yml`

Per-repo policy overrides server defaults and is read from the target/base branch. Typical fields:

```yaml
paths:
  ignore:
    - generated

summary_cluster_depth: 2
summary_topk_threshold: 20

context_limits:
  search_codebase:
    floor: 4
    ceiling: 15
  graph:
    hops: 1
```

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
uncommitted worktree `.review.yml`. To copy a safe committed policy into the repo-specific home
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
```

The repo block wins; an explicit empty `task_board:` disables board work. If the block is absent,
the server may use a **non-secret deploy-wide fallback**. Calls use configured registry credentials
without returning them.

The server-side flow is **store-first**:

1. `sync_board` enumerates and normalizes tasks, then stores vectors and task-graph metadata under
   `tasks:<type>:<board>`.
2. Skills call `get_task(key, project=...)`; linked tasks/PRs/code come from task context tools.
3. Client models never enumerate the provider directly and never send credentials.

The MCP server currently exposes **38 tools**, including the native-subtask batch operation.

Legacy aliases remain **legacy metadata for older clients** for one compatibility window:
`TASK_BOARD_API_KEY → YOUGILE_API_KEY` and
`TASK_BOARD_API_BASE → YOUGILE_API_BASE`. New deployments should use registry-declared
provider credentials. See [docs/board-providers.md](docs/board-providers.md) for the current
provider matrix, target discovery, options, setup, and credential rotation.

### Observability and tuning

`reviewer serve` exposes review history and traces through the optional web extra. Summary depth,
top-k threshold, graph backend, and retrieval ceilings change cost/recall trade-offs; start with
defaults and tune only after observing real misses or excessive context.

## CLI reference

| Goal | Commands |
|---|---|
| Configure and integrate | `init`, `install`, `install-skills`, `update` |
| Validate environment | `check` |
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
- **Result:** done state plus `already_closed`/`task_link_added` reporting without duplicate links.

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
- **Reads/writes:** calls idempotent server-side `sync_board`; it reads the board and does not write
  back.
- **Result:** compact counts and per-board warnings; missing config remains board-less/fail-open.

### `summarize-subsystems` — GraphRAG subsystem summaries

- **When:** build or refresh the architectural prior used by Q&A and PR walkthroughs.
- **Invoke:** `/rag-reviewer:summarize-subsystems`.
- **Needs:** a fresh base index, code graph, reviewer MCP, and confirmation of cluster depth.
- **Reads/writes:** читает только добавленные/изменённые файлы, переиспользует сохранённые
  пофайловые fragments и атомарно пишет fragments вместе со сводкой кластера.
- **Result:** сводки и метрики `created`/`reused`/`removed`/`moved`,
  `deferred`/`raced`, `fragments_pruned` и `embedded`.

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

### `configure-review` — update `.review.yml`

- **When:** tune ignored paths, retrieval limits, summary clustering, or board metadata.
- **Invoke:** `/rag-reviewer:configure-review`.
- **Needs:** a git repository; MCP and databases are not required for baseline analysis.
- **Reads/writes:** reads tracked Python structure/history and changes approved YAML fields in either
  `home:repos/<owner>/<name>.yml` or committed `.review.yml`.
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
| PR is skipped | Its target branch is outside `REVIEW_BRANCHES`, or draft policy skips it | Inspect `prepare_review` reason and update policy only if the target is intentional |
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
- Without SCIP, tree-sitter provides a useful but name-based `CALLS` graph and no precise
  `IMPLEMENTS` coverage.
- GitHub permits inline comments only on commentable diff lines; other findings appear in summary.
- Full indexing can hit Voyage free-tier limits; updates are incremental and reuse embeddings.
- The base index is branch-scoped and blind to uncommitted working-tree changes.
- OAuth loopback flows are not supported in headless/SSH integrations; use documented PAT/API-key
  credentials.
- `reviewer check` currently validates `GITHUB_TOKEN` and the GitHub API even in a GitLab-only
  deployment; validate `GITLAB_TOKEN` with a dry-run `/rag-reviewer:review-pr` against a GitLab MR.
- Board work is optional. Missing provider configuration keeps task-aware skills board-less rather
  than blocking code retrieval.

## Development

Create an isolated environment and install development dependencies:

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

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
