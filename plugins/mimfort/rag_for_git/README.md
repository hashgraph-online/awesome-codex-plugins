# rag_for_git

> **An AI pull-request reviewer that reads your whole repository — hybrid RAG + a code graph + Claude Code.**
> Plain linters check a diff in isolation; this agent gives the model the same context a human
> reviewer has — semantic + lexical retrieval over the entire repo and a structural code graph —
> then posts the result back to GitHub as **inline comments on the exact diff lines, with applyable fixes**.

[![PyPI](https://img.shields.io/pypi/v/rag-reviewer?color=2563eb&label=PyPI)](https://pypi.org/project/rag-reviewer/)
[![Python 3.11–3.13](https://img.shields.io/badge/python-3.11%E2%80%933.13-2563eb)](https://pypi.org/project/rag-reviewer/)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e)](LICENSE)
[![MCP server](https://img.shields.io/badge/MCP-server-8b5cf6)](#mcp-tools-reference)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-d97757)](#claude-code-plugin-marketplace)

> 🇷🇺 Русская версия — глубокий, сверенный с кодом разбор: [README.ru.md](README.ru.md)

---

## Table of contents

- [Why it exists](#why-it-exists)
- [What a review looks like](#what-a-review-looks-like)
- [Highlights](#highlights)
- [How a review runs](#how-a-review-runs)
- [How it works / Architecture](#how-it-works--architecture)
- [One-click install prompt](#one-click-install-prompt)
- [Installation](#installation)
- [Configuration reference](#configuration-reference)
- [CLI reference](#cli-reference)
- [Reviewer grounding in plan/review phases](#reviewer-grounding-in-planreview-phases-optional)
- [Skills reference](#skills-reference)
- [MCP tools reference](#mcp-tools-reference)
- [Plugin usage](#plugin-usage)
- [Per-repo policy & task board](#per-repo-policy--task-board)
- [Observability web admin](#observability-web-admin)
- [Known limitations & caveats](#known-limitations--caveats)
- [Tests](#tests)
- [Project layout](#project-layout)
- [Contributing](#contributing)
- [License](#license)

---

## Why it exists

Plain linters catch syntax and style but miss **meaning and relationships** — the things a human
reviewer actually looks for:

- a changed function contract that silently breaks its callers,
- a guard clause removed three files away from where it mattered,
- a change that contradicts an existing test,
- an edge case that only shows up once you read the helper it calls.

Catching those needs **context beyond the diff**: who calls this, what it implements, which tests
pin its behaviour. `rag_for_git` gives the model that context — semantic + lexical retrieval over
the **whole repository** and a structural **code graph** — then runs an agentic tool loop per
changed file and posts the result back to GitHub as **inline comments on the exact diff lines,
plus a summary and applyable fixes**.

It is not a wrapper around "send the diff to an LLM." It is a retrieval + code-graph pipeline with
a deterministic, anti-hallucination publishing tail.

## What a review looks like

An *illustrative* inline comment the agent posts on a changed line — it found the bug by following
the call graph from the edited function to its callers and a contract test:

> **🟠 correctness — an expired token is no longer rejected**
>
> `verify_token` used to raise on an expired signature; the new guard only checks `payload is
> None`, so `_decode()` returning a payload with a past `exp` now passes as valid. Two call sites
> depend on that raise — `require_auth` (`auth/deps.py:48`) and the contract test
> `test_expired_rejected` (`tests/test_auth.py:71`), which this change would break.
>
> ```suggestion
>     if payload is None or payload.get("exp", 0) < now:
>         raise InvalidToken("expired or malformed token")
> ```
> <!-- ai-review:9f3c2a -->

Every finding is grounded on an **exact quote** from the diff, carries a category / severity /
confidence, and — when it's safe — ships as a one-click GitHub `suggestion`. A hidden fingerprint
(`<!-- ai-review:… -->`) makes re-runs **idempotent**: the same issue is never posted twice.

## Highlights

- **Whole-repo context, not just the diff.** Hybrid retrieval (pgvector ANN + BM25, fused with RRF,
  reranked by Voyage) over the entire indexed codebase — for changed files the agent sees the new
  version, for everything else a stable base index.
- **It sees impact.** A Neo4j code graph (`CALLS` / `IMPLEMENTS`) expands each changed symbol 1–2
  hops to surface callers, callees, implementations, and the tests that pin them.
- **Anti-hallucination by construction.** A finding must quote real code to be placed on a line; a
  dedicated **verify** pass drops invented findings; line grounding is exact-match.
- **Real GitHub output.** Inline comments on diff lines, applyable `suggestion` blocks under safe
  invariants, a summary for everything off-diff — idempotent across re-runs.
- **Lives in your editor, not a CI black box.** Ships as a **Claude Code plugin** and as an **MCP
  server** usable from 12+ AI clients (Cursor, VS Code, Gemini CLI, Codex, Windsurf, Claude
  Desktop, …). One `uvx` command; published on [PyPI](https://pypi.org/project/rag-reviewer/).
- **Local-first.** Your code stays on your machine — only embedding/query text goes to Voyage; the
  stores (Postgres/ParadeDB + Neo4j) run in local Docker.
- **More than review.** The same RAG + graph powers grounded codebase **Q&A** (`ask`), PR
  **walkthroughs**, and per-subsystem summaries.
- **From task to implementation — the killer feature.** `solve-task` reads a task from your board,
  pulls related tasks/prs/code via the RAG + graph, distills a structured brief, and hands off to the
  **full superpowers cycle**: brainstorming → writing-plans → subagent-driven-development →
  executing-plans → finishing. The only end-to-end pipeline that truly connects your task tracker
  to implementation.

## How a review runs

A single PR review is three stages:

**`prepare_review` (MCP)** → **analyze (Claude subagents)** → **`publish_review` (MCP)**

1. **prepare** — `GitHubProvider` pulls the PR (base/head SHA) and changed files; changed `.py`
   files are chunked (tree-sitter) and embedded (Voyage) into an ephemeral overlay `ref="pr:N"`;
   policy and per-file review units are assembled.
2. **analyze** — the Claude Code skill fans out one subagent per file. Each reasons over the diff
   in a tool loop, pulling in whatever code it needs: `search_code`, `get_related_symbols`,
   `read_file`, `get_definition`, `find_callers`, `get_changed_file_diff`. In parallel,
   dimension subagents run a **performance** and **maintainability** pass, plus a **requirements**
   pass when a task board is wired up, and a final **verify** pass strips hallucinations.
3. **publish** — a deterministic tail: policy gate (category/severity/confidence/paths) → line
   grounding by exact code quote (anti-hallucination) → dedup → assemble (inline vs summary,
   suggestion invariants, fingerprint idempotency, comment cap) → post to GitHub → history record
   → overlay/session cleanup.

If a review is abandoned between `prepare_review` and `publish_review` (user cancelled, orchestrating
LLM session died), publish never runs — such an overlay is collected by GC: opportunistically on the
next `prepare_review`, and via the `reviewer gc` command.

> Status: working v1. Target analysis language is **Python**; VCS is **GitHub** (behind a
> `VCSProvider` interface). Proven live: it catches real bugs and sees the impact on calling code
> and existing tests.

## How it works / Architecture

The core is the `reviewer/` library, assembled in `reviewer/app.py::build_components(settings)`
from `Settings` (pydantic-settings, `.env`). Entry points are `reviewer/entrypoints/cli.py` (Click)
and `reviewer/entrypoints/mcp_server.py` (FastMCP). Three pieces work together:

- **RAG (hybrid retrieval).** Postgres/ParadeDB stores code chunks with `pgvector` (HNSW ANN) and
  `pg_search` (BM25). A query embeds with Voyage, runs both ANN and BM25 search, and the result
  lists are merged with **Reciprocal Rank Fusion (RRF)**, then reranked with Voyage `rerank-2.5`.
- **Code graph (SCIP or tree-sitter, Neo4j).** Symbols and their relationships live in Neo4j.
  The graph orchestrator (`graph/backend.py`) picks a backend via `GRAPH_BACKEND`
  (`auto|scip|treesitter`): **SCIP** (`@sourcegraph/scip-python`) gives a precise, type-aware graph
  with `CALLS` + `IMPLEMENTS` edges; **tree-sitter** is a fast fallback with `CALLS`-by-name only.
  Retrieval expands the changed symbols 1–2 hops to surface callers/callees/implementations/tests.
- **Claude Code plugin via MCP.** The `reviewer-mcp` server exposes `prepare_review`,
  `publish_review`, and the agent tools. The Claude Code plugin (`plugin/`) drives the review: it
  calls `prepare_review`, runs analysis subagents against those MCP tools, then calls
  `publish_review`.

**The single key linking RAG and the graph is `node_id = "path#fqn"`** (e.g.
`rag/embedder.py#VoyageEmbedder.embed_query`). Both the chunk in Postgres and the node in Neo4j use
it, so graph expansion and chunk retrieval are stitched together without any mapping table.

**Index freshness: a stable base + a PR overlay.** A full reindex of a large repo is expensive, so
the index keeps a persistent base and layers PR changes on top:

- **`ref="base:<branch>"`** — the persistent index of a tracked branch (e.g. `"base:main"`,
  `"base:master"`). Each tracked branch in `REVIEW_BRANCHES` has its own isolated index. Updated
  incrementally by `reviewer index --ref <branch>` (only changed files are chunked; only chunks
  with a new `content_hash` are re-embedded — embeddings are reused across branches by hash,
  saving Voyage quota).
- **`ref="pr:N"`** — an ephemeral overlay of just the PR's changed files at its HEAD.
- **On a query**: `retrieval = (base:<branch> where path ∉ changed) ∪ overlay`. For changed files
  the agent sees the **new** version; for everything else, the stable base.
- **Multi-branch.** A PR is reviewed against the index of its target branch (`base_ref` from the
  PR). A PR targeting an untracked branch is skipped (`prepare_review` returns
  `{"status":"skipped",...}`). The code graph (Neo4j `:Symbol`) is also branch-scoped via a
  `branch` property, with unique constraint `(repo, branch, id)`.

```
                ┌─────────────────────────── reviewer (core library) ───────────────────────────┐
                │                                                                                 │
  GitHub PR ───▶│  VCSProvider (github.py)  ──diff/files/patches──▶  MCPReviewService             │
  (owner/repo#N)│        ▲  publish inline + summary                       │ prepare_review        │
                │        │                                                 ▼                       │
                │        │                          ┌──────────── retrieval/Retriever ──────────┐ │
                │        │                          │  hybrid search        graph expansion      │ │
                │        │                          │  ┌──────────────┐   ┌───────────────────┐  │ │
                │        │                          │  │ Postgres      │   │ Neo4j             │  │ │
                │        │                          │  │ (ParadeDB)    │   │ Symbol(path#fqn)  │  │ │
                │        │                          │  │ pgvector(HNSW)│   │ -[:CALLS]->        │  │ │
                │        │                          │  │ + pg_search   │   │ (IMPLEMENTS: SCIP) │  │ │
                │        │                          │  │   (BM25, RRF) │   │ expand 1–2 hops    │  │ │
                │        │                          │  └──────┬───────┘   └─────────┬─────────┘  │ │
                │        │                          │   Voyage embed/rerank   tree-sitter graph  │ │
                │        │                          └─────────────────┬─────────────────────────┘ │
                │        │                                            ▼ ContextPack                │
                │        │                       Claude Code subagents (skill /rag-reviewer:reviewer_review-pr)
                │        │                         tools: search_code, get_related_symbols,        │
                │        │                         read_file, get_definition, find_callers, …      │
                │        └─────────────────── publish_review (gate/grounding/dedup/assemble) ◀─────┘
                └─────────────────────────────────────────────────────────────────────────────────┘

  Stores (Docker):  Postgres/ParadeDB (:5433)  ·  Neo4j (:7687)
  External API:     Voyage (embeddings voyage-code-3 + reranker rerank-2.5)
```

For a deeper, code-verified walkthrough of every module and the data flow, see
[README.ru.md](README.ru.md) (Russian).

## One-click install prompt

Copy and paste into any AI coding assistant:

```
uvx --from rag-reviewer reviewer install --all
```

This auto-detects installed AI clients and wires the MCP server. For manual setup see [Manual setup](#manual-setup-alternative) below.

---

## Installation

The MCP server is published on PyPI as [`rag-reviewer`](https://pypi.org/project/rag-reviewer/)
and runs via `uvx` — **no clone of this repo required**.

Requirements: Docker, [`uv`](https://docs.astral.sh/uv/getting-started/installation/) (includes `uvx`),
a Voyage API key, a GitHub token. Python 3.11–3.13 (only needed for a `pip`/editable install; `uvx`
manages its own).

### Quick setup (recommended, all platforms)

```bash
# 0) Install the reviewer CLI — once, globally
uv tool install rag-reviewer
# uv and uvx are the same binary; installing uv gives you both.
# The MCP server launched by your editor uses uvx @latest and self-updates automatically.

# 1) Infrastructure
curl -O https://raw.githubusercontent.com/mimfort/rag_for_git/main/docker-compose.yml
docker compose up -d          # Postgres/ParadeDB (:5433) + Neo4j (:7687)

# 2) Configure keys and settings interactively
reviewer init
#    Interactive wizard: fills VOYAGE_API_KEY, GITHUB_TOKEN, and optional groups
#    (stores, multi-repo, task board). Re-run any time to update settings.
#    CI / non-interactive: reviewer init --yes  (accepts all defaults silently)

# 3) Register the MCP server (and skills) in your editor/CLI
reviewer install --all        # auto-detect installed clients + install skills
#    or a specific one: reviewer install cursor|vscode|claude-code|claude-desktop|windsurf|gemini|antigravity|mimo|opencode|kimi|trae|codex
#    file-based skills go to Gemini/Mimo/OpenCode/Kimi; --no-skills skips skills

# 4) Verify
reviewer check

# Update CLI later:
uv tool upgrade rag-reviewer
```

> **`reviewer install` is cross-platform** (Windows / macOS / Linux). It injects the
> absolute path to `uvx` automatically — no `bash -lc` wrapper needed. The manual
> JSON configs below use `bash -lc` for macOS/Linux only; on Windows use
> `reviewer install` or set `"command": "uvx"` with `"args": ["--from",
> "rag-reviewer@latest", "reviewer-mcp"]` directly.

> **Claude Code is global by default.** `reviewer install claude-code` manages the
> user-scope `rag-reviewer` plugin from the canonical HTTPS marketplace source, so it
> works from any current directory and in every project. It also writes the global
> `mcp__reviewer__*` allowlist rule in `~/.claude/settings.json` (`permissions.allow`).
> Use `reviewer install claude-code --no-skills` when you need only a global MCP server
> and no plugin skills.

> **Where keys are read from.** The reviewer resolves its `.env` from a fixed
> location, **not** the current working directory — MCP clients launch the server
> with an arbitrary CWD, so a project-local `.env` is unreliable. Lookup order:
> `$REVIEWER_ENV_FILE` → `$XDG_CONFIG_HOME/rag-reviewer/.env` (default
> `~/.config/rag-reviewer/.env`) → `./.env` (handy when running from a repo clone).
> Real environment variables always win over the file, so you can instead pass keys
> via an `"env": { "VOYAGE_API_KEY": "…", "GITHUB_TOKEN": "…" }` block in your MCP
> client config — works in every client.

- **Voyage** (`VOYAGE_API_KEY`): https://dashboard.voyageai.com/ — free token pool; attach a card
  to lift the 3 RPM / 10K TPM limit (charged only beyond the free pool).
- **GitHub** (`GITHUB_TOKEN`): a PAT with *Pull requests: Read and write* + *Contents: Read*
  (fine-grained) or the `repo` scope (classic). Quick option: `gh auth token`.

All other settings have defaults (documented in `.env.example` and in
[Configuration reference](#configuration-reference) below).

### Manual setup (alternative)

If you prefer to configure your client config by hand rather than using `reviewer install`:

Each AI coding tool has its own config file. Pick yours:

| Tool | Global config file | Project config | Install guide |
|---|---|---|---|
| **Claude Code** | user-scope plugin marketplace (`reviewer install claude-code`) | `.claude-plugin/` ✓ | — |
| **Cursor** | `~/.cursor/mcp.json` | `.cursor/mcp.json` ✓ | — |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` | — | — |
| **Claude Desktop** | macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`; Windows: `%APPDATA%\Claude\claude_desktop_config.json` | — | — |
| **Antigravity** | `~/.gemini/antigravity/mcp_config.json` | — | — |
| **Mimo Code** | `~/.config/mimocode/mimocode.json` | `.mimocode/mimocode.json` ✓ | [INSTALL.md](.mimocode/INSTALL.md) |
| **OpenCode** | `~/.config/opencode/opencode.json` | `.opencode/opencode.json` ✓ | [INSTALL.md](.opencode/INSTALL.md) |
| **Kimi Code** | `~/.kimi-code/mcp.json` | `.kimi-code/mcp.json` ✓ | [INSTALL.md](.kimi-code/INSTALL.md) |
| **Gemini CLI** | `~/.gemini/settings.json` | `.gemini/settings.json` ✓ | [GEMINI.md](GEMINI.md) |
| **Codex CLI** | `~/.codex/config.toml` | `.codex-plugin/plugin.json` ✓ | [AGENTS.md](AGENTS.md) |
| **Trae IDE** | `~/Library/Application Support/Trae/User/mcp.json` | — | — |
| **VS Code** | `~/Library/Application Support/Code/User/mcp.json` (key: `servers`, not `mcpServers`) | — | — |

Files marked ✓ are already present in this repo — if you open rag_for_git as a project in
that tool, the MCP server auto-connects. For a **global install** (works from any project),
add the entry to the corresponding global config file. For Claude Code, use the user-scope
plugin command below instead of a project-local MCP file.

The MCP entry format by tool (macOS/Linux — use `reviewer install` on Windows):

**Mimo Code** (`mimocode.json`):
```json
{
  "$schema": "https://mimo.xiaomi.com//config.json",
  "mcp": {
    "reviewer": {
      "type": "local",
      "command": ["/bin/bash", "-lc", "uvx --from rag-reviewer@latest reviewer-mcp"],
      "enabled": true
    }
  }
}
```

**OpenCode** (`opencode.json`):
```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "reviewer": {
      "type": "local",
      "command": ["/bin/bash", "-lc", "uvx --from rag-reviewer@latest reviewer-mcp"]
    }
  }
}
```

**Kimi Code / Cursor / Gemini CLI / Trae / Claude Desktop / Windsurf / Antigravity** (standard `mcpServers` JSON):
```json
{
  "mcpServers": {
    "reviewer": {
      "command": "/bin/bash",
      "args": ["-lc", "uvx --from rag-reviewer@latest reviewer-mcp"]
    }
  }
}
```

**VS Code** (`mcp.json` — note: key is `servers`, not `mcpServers`):
```json
{
  "servers": {
    "reviewer": {
      "command": "/bin/bash",
      "args": ["-lc", "uvx --from rag-reviewer@latest reviewer-mcp"]
    }
  }
}
```

**Codex CLI**: install with the canonical commands in [AGENTS.md](AGENTS.md), then verify:
```bash
codex plugin list --json
codex mcp list
```

Success means `rag-reviewer` is installed and enabled and `codex mcp list` contains exactly one
`reviewer`. Identified legacy skills are moved to
`$CODEX_HOME/reviewer-legacy-backups/<timestamp>`; modified or ambiguous copies stay untouched.
Failures print the config backup path. Open a New Chat/new CLI session after installation; in an
IDE, also use Reload Window.

### Claude Code (global plugin marketplace)

Install or update it from any directory:

```bash
uvx --from rag-reviewer@latest reviewer install claude-code
```

The command manages the user-scope `rag-reviewer` plugin through the canonical HTTPS
source `https://github.com/mimfort/rag_for_git.git`; it does not depend on the current
project. Verify the installed plugin with the public CLI:

```bash
claude plugin list --json
# optional: confirm the canonical marketplace source too
claude plugin marketplace list --json
```

`plugin list` should contain an enabled `rag-reviewer@rag-reviewer-marketplace` entry with
`"scope": "user"`. The optional marketplace listing should report `"source": "git"` and
the exact HTTPS URL above. Open a New Chat/new CLI session afterwards; in an IDE, use Reload
Window as well.

To register only the global MCP server and intentionally skip plugin skills, run:

```bash
uvx --from rag-reviewer@latest reviewer install claude-code --no-skills
```

**Manual fallback** (only if the installer cannot be used):

```bash
claude plugin marketplace add https://github.com/mimfort/rag_for_git.git \
  --scope user --sparse .claude-plugin plugin
claude plugin install rag-reviewer@rag-reviewer-marketplace --scope user
```

You get:

- **Skills:** `/rag-reviewer:reviewer_review-pr`, `/rag-reviewer:reviewer_solve-task`,
  `/rag-reviewer:reviewer_sync-codebase`, `/rag-reviewer:reviewer_sync-tasks`,
  `/rag-reviewer:reviewer_performance-review`, `/rag-reviewer:reviewer_maintainability-review`,
  `/rag-reviewer:reviewer_ask`, `/rag-reviewer:reviewer_pr-walkthrough`,
  `/rag-reviewer:reviewer_configure-review`, `/rag-reviewer:reviewer_summarize-subsystems`,
  `/rag-reviewer:reviewer_finish-task`
  (see [Skills reference](#skills-reference)).
- **MCP server** `reviewer` exposing the 31 tools in [MCP tools reference](#mcp-tools-reference).

> Run `/plugin` to confirm `rag-reviewer` is installed and enabled.

### Install skills globally (optional)

Every directory under `plugin/skills/` that contains `SKILL.md` is registered under the
`rag-reviewer` namespace. `_common` and nested references are delivered as supporting files but are
not registered as skills. These skills wrap the MCP tools into guided flows. Without them you can still call MCP tools
directly, but the skills are the intended entry point.

**`reviewer install` already installs them** for clients that support file-based skills (Gemini,
Mimo, Kimi, OpenCode). To (re)install just the skills — or pick a specific client — use:

```bash
uvx --from rag-reviewer reviewer install-skills --all     # all detected skills-capable clients
uvx --from rag-reviewer reviewer install-skills gemini    # a specific one
uvx --from rag-reviewer reviewer install-skills --list    # show targets + directories
```

It downloads the skills from GitHub (no repo clone) and unpacks them into each client's global
skills directory, with a path-traversal guard. Manual fallback (equivalent):

```bash
curl -sL https://github.com/mimfort/rag_for_git/archive/refs/heads/main.tar.gz -o /tmp/rag-reviewer.tgz
mkdir -p ~/.gemini/skills
tar xz -C ~/.gemini/skills --strip-components=3 -f /tmp/rag-reviewer.tgz 'rag_for_git-main/plugin/skills'
rm /tmp/rag-reviewer.tgz
```

| Tool | Global skills directory |
|---|---|
| Gemini CLI | `~/.gemini/skills/` |
| Mimo Code | `~/.config/mimocode/skills/` |
| Kimi Code | `~/.kimi-code/skills/` + `extra_skill_dirs` in `~/.kimi-code/config.toml` |
| OpenCode | `~/.config/opencode/skills/` |
| Claude Code | bundled in the plugin (step above) |
| Cursor | project-level via `.cursor-plugin/plugin.json` |

That's it. Build the base index (recommended — see [CLI reference](#cli-reference)) and review a PR
(see [Plugin usage](#plugin-usage)).

---

## Configuration reference

Everything is configured through environment variables (`.env`, see `.env.example` with comments).
The **only required external key is `VOYAGE_API_KEY`**; `GITHUB_TOKEN` is required for PR review.
All other settings have working defaults that match the bundled `docker-compose.yml`. The `.env`
is resolved from `$REVIEWER_ENV_FILE` → `~/.config/rag-reviewer/.env` → `./.env` (real env vars
always win).

### Voyage — embeddings + reranker (required)

| Variable | Default | Purpose |
|---|---|---|
| `VOYAGE_API_KEY` | `""` | **Required.** Voyage key for embeddings + reranking. |
| `EMBEDDING_MODEL` | `voyage-code-3` | Embedding model. |
| `EMBEDDING_DIM` | `1024` | Embedding dimension; **must match** the `vector(N)` column in Postgres — changing it requires a reindex. |
| `EMBEDDING_BATCH_SIZE` | `256` | Texts per embedding request (≤1000 and ≤120K tokens). |
| `RERANK_MODEL` | `rerank-2.5` | Voyage reranker model. |

### GitHub (required for PR review)

| Variable | Default | Purpose |
|---|---|---|
| `GITHUB_TOKEN` | `""` | PAT — *Pull requests: Read and write* + *Contents: Read*. |
| `GITHUB_RETRY_ATTEMPTS` | `3` | Retries on GitHub API network errors. |
| `GITHUB_RETRY_BACKOFF_BASE` | `1.0` | Exponential backoff base (seconds). |

### Stores (Postgres/ParadeDB + Neo4j)

| Variable | Default | Purpose |
|---|---|---|
| `PG_DSN` | `postgresql://reviewer:reviewer@localhost:5433/reviewer` | ParadeDB (pgvector + pg_search) on host port **5433**. |
| `PG_POOL_MIN_SIZE` | `1` | Min Postgres pool connections. |
| `PG_POOL_MAX_SIZE` | `4` | Max Postgres pool connections. |
| `NEO4J_URI` | `neo4j://localhost:7687` | Neo4j bolt URI. |
| `NEO4J_USER` | `neo4j` | Neo4j user. |
| `NEO4J_PASSWORD` | `reviewerpass` | Neo4j password (one-off dev default). |
| `GRAPH_BACKEND` | `auto` | Code-graph engine: `auto` (SCIP if `scip-python` in PATH, else tree-sitter), `scip`, `treesitter`. |

### Multi-platform VCS (optional)

| Variable | Default | Purpose |
|---|---|---|
| `VCS_PROVIDER` | `github` | VCS provider: `github` or `gitlab`. |
| `GITLAB_TOKEN` | `""` | GitLab PAT for PR review. |
| `GITLAB_URL` | `""` | GitLab instance URL; empty → `https://gitlab.com`. |

### Multi-repo / multi-branch (optional)

| Variable | Default | Purpose |
|---|---|---|
| `DEFAULT_REPO` | `""` | Default `owner/name` for session-less tools and `reviewer index` without `--repo`; empty = multi-repo (repo must be passed explicitly). |
| `REVIEW_BRANCHES` | `main` | CSV of tracked branches; the first is **primary** (default for `reviewer index --ref` and CLI search). PRs targeting a branch outside the list are skipped. |

### Review policy (env defaults; per-repo `.review.yml` overrides)

| Variable | Default | Purpose |
|---|---|---|
| `REVIEW_SEVERITY_THRESHOLD` | `medium` | Minimum severity to keep: `low`/`medium`/`high`/`critical`. |
| `REVIEW_MIN_CONFIDENCE` | `0.5` | Drop findings with confidence below this (0..1). |
| `REVIEW_MAX_COMMENTS` | `25` | Cap on inline comments per review. |
| `REVIEW_MAX_FILES` | `50` | Cap on `.py` files reviewed; the rest go to the summary as skipped. |
| `REVIEW_CATEGORIES` | `""` | CSV whitelist of categories (`correctness`, `security`, `performance`, `style`, `requirements`); empty = all. |
| `REVIEW_SUGGESTIONS` | `apply` | `apply` = applyable GitHub `suggestion` blocks; `text` = text-only advice. |
| `REVIEW_OUTPUT_LANGUAGE` | `ru` | Language of the published findings' text. |
| `REVIEW_SKIP_DRAFTS` | `true` | Don't review draft PRs. |
| `MAX_TOOL_RESULT_CHARS` | `8000` | Max length of a tool result fed into the prompt. |

### Observability & sessions (optional)

| Variable | Default | Purpose |
|---|---|---|
| `REVIEW_HISTORY` | `true` | Record run history in Postgres (`review_runs`/`review_findings`), fail-soft. |
| `REVIEW_SESSION_PERSIST` | `true` | Persist the PR session in Postgres for crash recovery. |
| `REVIEW_SESSION_TTL_HOURS` | `24` | TTL (hours) of a persisted session. |
| `WEB_ADMIN_USER` | `""` | Basic-auth user for `reviewer serve`; empty = no auth. |
| `WEB_ADMIN_PASSWORD` | `""` | Basic-auth password; empty = no auth. |

### Summary & graph tuning (optional)

| Variable | Default | Purpose |
|---|---|---|
| `SUMMARY_CLUSTER_DEPTH` | `2` | Max path-segment depth for subsystem cluster keys (`DEFAULT_REPO`-only; per-repo override in `.review.yml`). |
| `SUMMARY_TOPK_THRESHOLD` | `20` | If summary count exceeds this, use ANN top-k by query proximity. |
| `SUMMARY_REBUILD_CAP` | `None` | Cap on stale clusters rebuilt per pass (None/0 = unlimited). |
| `REVIEW_GROUNDING_MAX_DISTANCE` | `5` | Max line distance for snapping a reported line to the nearest commentable diff line during grounding. |

### Task board (optional) — deploy-wide default

A board connection is the same for every repo of one team, so it is configured **once** in the
reviewer-mcp env rather than duplicated in each repo's `.review.yml`. See
[Per-repo policy & task board](#per-repo-policy--task-board).

| Variable | Default | Purpose |
|---|---|---|
| `YOUGILE_API_KEY` | `""` | **REST API key** for YouGile server-side bulk sync. |
| `YOUGILE_API_BASE` | `""` | YouGile REST API base URL; empty → `https://yougile.com/api-v2`. |
| `YOUTRACK_TOKEN` | `""` | **REST API token** for YouTrack server-side bulk sync. |
| `YOUTRACK_BASE_URL` | `""` | YouTrack REST API base URL. |
| `TASK_BOARD_MCP` | `""` | Name of the connected board MCP server (LLM-side tools `mcp__<mcp>__*`). |
| `TASK_BOARD_KEY_PATTERN` | `""` | Task-key regex, e.g. `[A-Z]+-\d+`. |
| `TASK_BOARD_URL_TEMPLATE` | `""` | Task-link template, e.g. `https://ru.yougile.com/team/<id>/#{code}`. |
| `TASK_BOARD_TYPE` | `""` | **Deprecated** — type is now auto-derived from which credentials are set (`YOUGILE_API_KEY` / `YOUTRACK_TOKEN`). |
| `TASK_BOARD_API_KEY` | `""` | **Legacy** — prefer `YOUGILE_API_KEY`. Still works as fallback. |
| `TASK_BOARD_API_BASE` | `""` | **Legacy** — prefer `YOUGILE_API_BASE`. Still works as fallback. |

> **Getting `YOUGILE_API_KEY` (Yougile).** UI: press `Ctrl + ~` (or ⚙ next to the company name →
> "Настроить") → **API** → create/copy the key. REST: get `companyId` (`Ctrl + Alt + Q`, or
> `POST /api-v2/auth/companies {login,password}`), then `POST /api-v2/auth/keys {login,password,companyId}`.
> The key belongs **only** in the reviewer-mcp env (`~/.config/rag-reviewer/.env`), not in a chat or a client config.

---

## Reviewer grounding in plan/review phases (optional)

The reviewer MCP tools are available in every phase, not only inside a PR review. If you
run a plan/review workflow (e.g. Superpowers' writing-plans, or any code-review step), you
can have the agent ground its work in the RAG + code graph instead of raw grep. This is
opt-in: paste the block below into your agent context file (CLAUDE.md / AGENTS.md /
GEMINI.md / .cursorrules — whichever your client uses).

> **Reviewer grounding (plan/review, optional, fail-open).** When the reviewer MCP is
> connected and its base index is fresh (`reviewer status --json` -> `drift == 0`), prefer the
> session-less reviewer tools over grep to ground cross-file facts during planning and review:
> `search_codebase` (relevant code), `callers` (blast-radius of a signature you are about to
> change), `related_symbols`, `definition`. Be targeted — skip small/familiar edits and files
> already in context (Voyage is rate-limited). The base index tracks the target branch, not
> your working tree: grounding is reliable for existing code but blind to symbols you just
> edited locally — verify those with Read. If reviewer is absent or the index is stale, fall
> back to grep/Read.

---

## CLI reference

All commands run via `uvx --from rag-reviewer <command>`, or after `uv tool install rag-reviewer` /
`pip install -e ".[dev]"` simply as `reviewer`. Two entry points are installed:
`reviewer` (the CLI below) and `reviewer-mcp` (the MCP server, started by your editor/plugin).

| Command | Arguments | Options | What it does |
|---|---|---|---|
| `check` | — | — | Verify environment readiness (keys, Postgres, Neo4j, GitHub). Prints ✓/✗ per item; exits 1 on any problem. Spends no Voyage quota. |
| `init` | — | `--path FILE` (default `~/.config/rag-reviewer/.env`), `--yes` (accept defaults, CI mode) | Interactive wizard that writes the `.env` (Voyage/GitHub + optional groups). |
| `install` | `[client]` | `--all`, `--list`, `--path FILE`, `--pin VERSION`, `--no-latest`, `--no-skills`, `--dry-run` | Register the MCP server (and skills) in AI clients (cross-platform). |
| `install-skills` | `[client]` | `--all`, `--list`, `--path FILE` | Install only the skills into a client's global skills directory. |
| `update` | — | — | Check PyPI for a newer `rag-reviewer` and report how to upgrade. |
| `index` | `<repo>` (path to local clone) | `--ref BRANCH` (git ref to read; default = primary branch), `--branch NAME` (storage key; default = `--ref`), `--repo OWNER/NAME` (default from git `origin`) | Build/update the base index of a branch (vectors + graph). Done once, then incremental. |
| `search` | `<query>` | `--repo OWNER/NAME` (default `DEFAULT_REPO`), `--branch NAME` (default primary) | Diagnostic hybrid search over a branch's base index. |
| `status` | `[path]` (default `.`) | `--repo OWNER/NAME` (default from git `origin`), `--branch NAME` (default: all `REVIEW_BRANCHES`), `--json` (machine-readable output) | Index health / freshness vs the clone's HEAD. Spends no Voyage quota. |
| `gc` | — | — | Purge orphaned overlays (abandoned reviews) and expired sessions. |
| `migrate-branches` | — | — | One-time: rename legacy `ref="base"` → `base:<primary>` after upgrading to multi-branch. |
| `serve` | — | `--host HOST` (default `127.0.0.1`), `--port PORT` (default `8000`) | Run the observability web admin on the host. |
| `reviewer-mcp` | — | — | MCP server (stdio transport). Started automatically by the plugin / editor. |

Examples:

```bash
# First-time setup
uvx --from rag-reviewer reviewer init
uvx --from rag-reviewer reviewer install --all
uvx --from rag-reviewer reviewer check

# Build the base index (whole-repo context for RAG + graph)
uvx --from rag-reviewer reviewer index /path/to/repo --ref main --repo owner/name
uvx --from rag-reviewer reviewer index /path/to/repo --ref master --repo owner/name   # second tracked branch

# Diagnostics (no Voyage spend except `search`)
uvx --from rag-reviewer reviewer search "token verification" --branch master
uvx --from rag-reviewer reviewer status /path/to/repo --branch dev

# Web admin
uvx --from rag-reviewer reviewer serve --host 127.0.0.1 --port 8000
```

Reviewing works even without a prior `index` — context is then limited to the diff and the overlay
(RAG/graph are "thin"). For full whole-repo impact analysis, run `index` against the target branch.

---

## Skills reference

Skills are the guided entry points for the workflow. With the plugin installed they are invoked as
`/rag-reviewer:<name>` in Claude Code (the leading `/rag-reviewer:` is the plugin namespace; on
other clients the skill name is the same). Arguments are passed as free text after the skill name
(`$ARGUMENTS`).

### `reviewer_review-pr` — full PR review

Orchestrates the three-stage pipeline (`prepare_review` → subagents → `publish_review`).

- **Arguments:** the PR as `owner/repo#N`, `owner/repo N`, or a GitHub PR URL. Add `--dry-run` to
  assemble and return the full report **without** posting to GitHub.
- **MCP tools used:** `prepare_review`, `search_code`, `get_related_symbols`, `read_file`,
  `get_definition`, `find_callers`, `get_changed_file_diff`, `get_impact`, `submit_findings`,
  `get_candidate_findings`, `submit_verdicts`, `publish_review`; plus
  `index_task` / `get_task_context` / `search_tasks` when a task board is wired up.
  Task reads are scoped via `project=<task_board.project>` passed to `get_task`/`get_task_context`/`search_tasks` (PRI-170).
- **Flow:** prepare (PR + policy + units + board config) → fan out one analysis subagent per file →
  parallel **performance** / **maintainability** dimensions (+ **requirements** if a `TaskBrief`
  exists) + **blast-radius** (impact analysis via `get_impact`, plus shared-interface conformance: a changed `Protocol`/ABC → enumerate implementations and confirm all are updated) → **verify** pass (drops `is_real=false` findings) → publish (gate/grounding/dedup/assemble).
  If `prepare_review` returns `status:"skipped"` (target branch not tracked) it stops; draft PRs are
  skipped unless `REVIEW_SKIP_DRAFTS=false`.

### `reviewer_solve-task` — from task to implementation (killer feature)

This is the plugin's standout capability: it reads a task from your board, pulls everything the
implementer needs via the RAG + code graph, and hands off to the **full superpowers development
cycle** — not just a single step.

Reads a task (if a key + board), pulls related/similar tasks and relevant code, distills a brief,
and enters brainstorming. It disciplines context-gathering — it does **not** write the code.

- **Arguments:** a task key (e.g. `PRI-4`, must match `key_pattern`) **or** a free-text description
  (e.g. "add a logout endpoint"). Board-less mode falls back to description + code search.
- **MCP tools used:** `get_board_config`, `get_subsystem_summaries`, `get_task`, `index_task`, `get_task_context`, `search_tasks`,
  `search_codebase`, `related_symbols`, `callers`, `definition`, `get_pr_diff`; plus the connected
  board MCP (`mcp__<board>__*`) to read the task. All task tools are scoped via `project=<task_board.project>`.
- **Flow:** preflight (index freshness check → task corpus warmup via `sync_board`) → subsystem prior via `get_subsystem_summaries` → resolve board config → identify task (key vs free text) → store-first task read via `get_task(key, project=...)` (hit = use directly; miss = board MCP fallback) → best-effort, fail-open context
  gathering (task graph, similar tasks, relevant code, lazy PR diffs of similar tasks) → distill a
  structured brief (Task / Related work / Relevant code / Constraints) → persist it to
  `docs/superpowers/briefs/` (`ГГГГ-ММ-ДД-<KEY>-<slug>.md`, survives context compaction) → hand off to
  `superpowers:brainstorming` with the brief file path as seed → **full superpowers cycle**: brainstorming →
  writing-plans → subagent-driven-development → executing-plans → finishing-a-development-branch.
- **Cheaper model for the brief (cross-CLI).** Before building the brief, `solve-task` asks which
  model tier to run it on (by tier — cheap / mid / premium — not by model name, so it works across
  CLIs) and recommends a mid (Sonnet-class) default: gathering and distilling the brief is light
  reasoning, so a top-tier model is overkill. Where the harness supports per-subagent model override
  it dispatches the brief-building on the chosen model; otherwise it builds inline.

### `reviewer_sync-codebase` — build/update the base index

Thin wrapper over `reviewer index` (vector store + code graph) from a local clone.

- **Arguments (all optional):** `--path <path>` (default: CWD), `--ref <branch>` (default: `main`),
  `--repo <owner/name>` (default: derived from `git remote get-url origin`),
  `--backend <auto|scip|treesitter>` (default: `auto`, sets `GRAPH_BACKEND`).
- **MCP tools used:** none directly — it shells out to `uvx --from rag-reviewer reviewer index`.
- **Flow:** resolve inputs → check prerequisites (`uvx`, git repo, `reviewer check`, Docker up) →
  run indexing → optional `reviewer search` to verify → report chunks/nodes/edges and which graph
  backend was used.

### `reviewer_sync-tasks` — warm the task graph & vector store

A thin trigger over the server-side ETL tool `sync_board` — the reviewer enumerates the board over
REST itself, so the LLM passes no task text (O(1) tokens regardless of board size).

- **Arguments (all optional):** `--board <name>` (limit to one board/project), `--board-type <yougile|youtrack>` (limit the sync to one board type), `--limit <N>` (smoke
  run; **disables purge and watermark advance**), `--purge-orphaned` (remove tasks no longer on the
  board; off by default), `--no-keep-with-prs` (with purge, also remove tasks that have PR history —
  protected by default).
- **MCP tools used:** `sync_board` (single call).
- **Flow:** map args → one `sync_board(...)` call → print a counts summary (enumerated/changed/
  embedded/unchanged/failed, purge, warnings). On `{"status":"error",...}` the board is not
  configured server-side — set `TASK_BOARD_*` in `~/.config/rag-reviewer/.env` and reconnect.

### `reviewer_performance-review` — performance-only review

Reviews a diff only for performance/efficiency risks (N+1 queries, repeated work, bad asymptotics,
missing batching/caching, blocking I/O, memory growth).

- **Arguments (standalone):** scope — `staged`, `unstaged`, uncommitted, branch-vs-base, a commit,
  a branch comparison, a file list, or a PR-like scope. If unclear, it asks. Inside
  `reviewer_review-pr` it runs as a dimension over the provided unit diffs.
- **MCP tools used (when run in the PR pipeline):** `search_code`, `read_file`, `find_callers`,
  `get_related_symbols`, `get_definition`, `get_changed_file_diff`.
- **Output:** JSON `{"findings":[{category:"performance", severity, file, line, side, code_quote,
  message, suggestion, fix, confidence}]}`.

### `reviewer_maintainability-review` — maintainability-only review

Reviews a diff only for maintainability risks (unnecessary complexity, poor readability,
duplication, weak separation of concerns, convention drift).

- **Arguments (standalone):** same scope options as the performance review. Inside
  `reviewer_review-pr` it runs as a dimension over the provided unit diffs.
- **MCP tools used (when run in the PR pipeline):** `search_code`, `get_related_symbols`,
  `read_file`, `get_definition`, `find_callers`, `get_changed_file_diff`.
- **Output:** JSON `{"findings":[{category:"maintainability", severity, file, line, side, code_quote,
  message, suggestion, fix, confidence}]}`.

### `reviewer_ask` — grounded codebase Q&A

Answers a free-text question about the codebase with citations (`path:line`), using RAG + the code
graph. For onboarding / explaining a subsystem — **not** for reviewing PRs. Requires a built base
index.

- **Arguments:** a free-text question (e.g. "where is authentication", "how does index freshness
  work", "explain the retrieval pipeline", "как устроено…").
- **MCP tools used:** `search_codebase`, `related_symbols`, `callers`, `definition`; plus harness
  `Read`/`Grep`/`Glob`.
- **Flow:** on first use per session — `reviewer status` freshness check with drift warning → resolve repo/branch → optional: `get_subsystem_summaries` for architectural prior → `search_codebase` → optionally expand via the graph → answer with
  an Evidence list of `path:line` citations.

### `reviewer_pr-walkthrough` — PR walkthrough for human reviewers

Build a human-facing reading guide for a GitHub PR (where to start, what each file changes, what it impacts).

- **Arguments:** `owner/repo#N`, `owner/repo N`, or a GitHub PR URL.
- **MCP tools used:** `prepare_review`, `get_impact`, `get_subsystem_summaries`, `post_pr_walkthrough`.
- **Flow:** prepare PR session → compute blast-radius via `get_impact` → pull subsystem summaries → assemble a structured reading guide (overview → per-file narrative → impact map) → optionally post via `post_pr_walkthrough` (carries a `<!-- ai-walkthrough -->` marker, separate from bug findings).

### `reviewer_configure-review` — configure per-repo review policy

Configure or update a repo's `.review.yml` (subsystem cluster depth, per-prefix overrides, summary thresholds, ignore patterns) and task board selection.

- **Arguments:** none — interactive flow; edits `.review.yml` in the current repo.
- **MCP tools used:** none — standalone (needs only git).
- **Flow:** analyze repo structure → propose `.review.yml` draft with context-layer settings → user reviews and edits → writes to `.review.yml` in the target branch.

### `reviewer_summarize-subsystems` — build subsystem summaries (GraphRAG)

Precompute concise per-subsystem summaries over the base code index for cheap high-level priors in ask/PR-walkthrough.

- **Arguments (all optional):** `--depth <N>` (cluster depth, default from env), `--cap <N>` (limit stale cluster rebuilds).
- **MCP tools used:** `list_subsystem_clusters`, `index_subsystem_summary`, `prune_subsystem_summaries`, `backfill_summary_embeddings`.
- **Flow:** list clusters → for each stale cluster, generate title+summary → index → after a full pass, prune orphaned summaries → embed any summaries with NULL embeddings.

---

## MCP tools reference

The `reviewer-mcp` server exposes 31 tools. PR-session tools require an active `prepare_review` for
that `(repo, pr)` in the same running server; the rest are session-less.

### Review lifecycle

| Tool | Signature | Returns / does |
|---|---|---|
| `prepare_review` | `(repo: str, pr: int)` | Open a PR session: sync base index, build the PR overlay, load policy, assemble per-file units. Returns PR meta + policy + units (or `{"status":"skipped"}` for an untracked target branch). |
| `publish_review` | `(repo, pr, summary, dry_run=False, task_key=None)` | Deterministic tail: gate → grounding → dedup → inline/summary split → post to GitHub → history → overlay cleanup. `dry_run=true` returns the report without posting; `task_key` links the PR to a task on real publish. Findings are accumulated in-session via `submit_findings`/`submit_verdicts` (PRI-156). |

Each finding: `{category, severity(low|medium|high|critical), file, line, side(RIGHT|LEFT),
code_quote, message, suggestion, fix:{start_line,end_line,replacement}|null, confidence:0..1}`.

### PR-session analysis tools (require `prepare_review`)

| Tool | Signature | Returns / does |
|---|---|---|
| `search_code` | `(repo, pr, query: str)` | Hybrid semantic+lexical search over `base ∪ overlay`. |
| `get_related_symbols` | `(repo, pr, node_id: str)` | Graph neighbors (calls/implementations) of `node_id` = `path#fqn`. |
| `read_file` | `(repo, pr, path, start=1, end=400, skeleton=False)` | Source of a file at the PR HEAD (1-based, inclusive). `skeleton=True` returns AST skeleton (def/class signatures) instead of bodies. |
| `get_definition` | `(repo, pr, symbol: str)` | Definition of a symbol (graph → index → semantic fallback). |
| `find_callers` | `(repo, pr, node_id: str)` | Direct callers of `node_id` `path#fqn` (impact analysis). |
| `get_changed_file_diff` | `(repo, pr, path: str)` | Unified diff of another changed file in the same PR. |
| `get_impact` | `(repo, pr)` | Blast-radius: symbols with signature changes → their callers outside the PR diff. |
| `submit_findings` | `(repo, pr, findings: list[dict])` | Submit analysis findings into the session (schema-enforced, PRI-156). |
| `get_candidate_findings` | `(repo, pr)` | Read accumulated findings with server-assigned IDs for verification. |
| `submit_verdicts` | `(repo, pr, verdicts: list[dict])` | Submit verify verdicts (`{id, is_real}`) into the session. |
| `post_pr_walkthrough` | `(repo, pr, markdown: str)` | Post a human-facing PR reading guide as a review comment (separate from bug findings). |

### Session-less tools (Q&A, `solve-task`)

| Tool | Signature | Returns / does |
|---|---|---|
| `search_codebase` | `(repo, query, top_k=10, branch=None, include_tests=False)` | Hybrid search over a repo's base index; line-numbered, deduped, tests excluded by default. |
| `related_symbols` | `(repo, node_id, branch=None)` | Graph neighbors (calls/implements/tests) of a symbol. |
| `callers` | `(repo, node_id, branch=None)` | Incoming `CALLS` of `node_id` `path#fqn`. |
| `definition` | `(repo, symbol, branch=None)` | Symbol definition (graph → index → semantic fallback). |
| `get_pr_diff` | `(repo, number: int)` | Unified diff of any (historical) PR; capped, fail-soft. |
| `get_task` | `(key: str, project: str \| None = None)` | Read one task's normalized `TaskBrief` from the store (`{key, aliases, title, description, status, url, criteria}`). Returns `null` if not found. |
| `list_subsystem_clusters` | `(repo, branch=None, depth=None, min_size=None, cap=None)` | Cluster the base code graph by module paths for `/reviewer_summarize-subsystems`. |
| `index_subsystem_summary` | `(repo, branch, cluster_key, title, summary, source_hash)` | Persist one subsystem summary (idempotent upsert). |
| `get_subsystem_summaries` | `(repo, branch=None, cluster_key=None, query=None, top_k=None)` | Retrieve precomputed subsystem summaries. |
| `prune_subsystem_summaries` | `(repo, branch=None)` | Remove subsystem summaries orphaned by depth changes or removed modules. |
| `backfill_summary_embeddings` | `(repo, branch=None)` | Self-heal: embed any subsystem summaries with NULL embeddings. |

### Tasks / boards

| Tool | Signature | Returns / does |
|---|---|---|
| `sync_board` | `(board=None, limit=None, purge_orphaned=False, keep_with_prs=True, board_type=None)` | Server-side ETL: enumerate the board over REST, normalize to `TaskBrief`, index. Incremental via a per-board watermark; O(1) tokens. |
| `index_task` | `(task: dict)` | Index one normalized `TaskBrief` into the task graph + vector store (idempotent). |
| `index_tasks_batch` | `(tasks: list[dict])` | Same for a list, in one Voyage call. |
| `search_tasks` | `(query, top_k=5, project=None)` | Semantically similar tasks from the indexed corpus. |
| `get_task_context` | `(key: str, project=None)` | Graph context: the task, its PRs, linked tasks and their PRs, and the touched code. |
| `purge_orphaned_tasks` | `(active_keys: list[str], keep_with_prs=True)` | Remove tasks no longer on the board (PR-linked tasks protected by default). |
| `get_board_config` | `()` | Deploy-wide board config (`TASK_BOARD_*`); fallback for `sync-tasks`/`solve-task`. Credentials are **not** returned. |

---

## Plugin usage

With the plugin installed and Claude Code open at the repo root, call a skill:

```text
/rag-reviewer:reviewer_review-pr owner/repo#42        # review a PR (prepare → subagents → publish)
/rag-reviewer:reviewer_review-pr owner/repo#42 --dry-run   # assemble the report without posting
/rag-reviewer:reviewer_sync-codebase --ref main      # build/update vector store + code graph
/rag-reviewer:reviewer_sync-tasks                    # warm the task graph (server-side ETL)
/rag-reviewer:reviewer_solve-task PRI-4              # gather task context, then hand off to dev
/rag-reviewer:reviewer_ask how does index freshness work   # grounded codebase Q&A
```

A typical end-to-end run:

```bash
git clone https://github.com/ORG/REPO /tmp/REPO
reviewer index /tmp/REPO --ref main       # build base index + graph for main
reviewer index /tmp/REPO --ref master     # optionally index a second branch (REVIEW_BRANCHES=main,master)
# in Claude Code (from the repo root):  /rag-reviewer:reviewer_review-pr ORG/REPO#42
```

---

## Per-repo policy & task board

A `.review.yml` file in the **target (base) branch** overrides the env defaults (a PR cannot weaken
its own review — see *Caveats*):

```yaml
categories: { correctness: true, security: true, performance: true, style: false, requirements: true }
severity_threshold: medium
min_confidence: 0.5
paths: { ignore: ["**/migrations/**", "vendor/**"] }
max_comments: 25

# Optional task context: read the task from a board and check requirement compliance.
# The board (MCP) is connected by the user on the Claude Code side; the plugin does not bundle it.
task_board:
  type: yougile          # yougile | youtrack — selects the skill playbook
  mcp: yougile           # name of the connected board MCP server (tools are mcp__<mcp>__*)
  key_pattern: "[A-Z]+-\\d+"   # optional; matches Yougile PRI-34/ID-34 and YouTrack PROJ-123
  project: PRI          # optional; scopes task sync/queries to this project (code prefix; empty = all)
  url_template: 'https://ru.yougile.com/team/<teamId>/#{code}'  # optional; clickable task links

summary_cluster_depth: 2           # optional; default from env SUMMARY_CLUSTER_DEPTH
summary_cluster_depth_overrides:   # optional; per-prefix depth overrides
  reviewer/retrieval: 3
  reviewer/graph: 1
summary_topk_threshold: 20         # optional; default from env SUMMARY_TOPK_THRESHOLD

output_language: ru               # optional; overrides REVIEW_OUTPUT_LANGUAGE
grounding_max_distance: 5          # optional; overrides REVIEW_GROUNDING_MAX_DISTANCE
```

**The `task_board` block is a deploy-wide default, not a per-repo requirement.** A board connection
is the same for every repo of one team, so configure it **once** in the reviewer `.env`
(`YOUGILE_API_KEY` / `YOUTRACK_TOKEN` / `TASK_BOARD_MCP` / `TASK_BOARD_KEY_PATTERN` / `TASK_BOARD_URL_TEMPLATE`) and
every repo inherits it — no `.review.yml` needed just for the board. A `task_board` block in a repo's
`.review.yml` **overrides** that default for that repo; an explicit empty `task_board:` **disables**
the board for it. `review-pr` reads this through the policy; `solve-task` reads it via the
`get_board_config` MCP tool (and the board-MCP, LLM-side) as a fallback when the local `.review.yml`
has no block.

**Bulk task sync is server-side, not LLM (`sync_board`).** The `sync-tasks` skill is a thin trigger:
it calls one MCP tool, `sync_board(board, limit, purge_orphaned, keep_with_prs)`, and the reviewer
server enumerates the board over **REST** itself (`reviewer/tasks/boards/`, behind a
`TaskBoardProvider` interface — Yougile is the reference), normalizes each task into a `TaskBrief`
in Python, and indexes it via the existing batch indexer. The LLM passes no task text, so a sync
costs O(1) tokens regardless of board size. It is incremental via a per-board timestamp watermark in
`index_meta` (`ref="tasks:<board>"`): a repeat sync touches ~0 tasks; `--limit` disables purge and
the watermark advance. The board REST credentials live only in the reviewer-mcp environment
(now `YOUGILE_API_KEY` / `YOUTRACK_TOKEN`; legacy `TASK_BOARD_API_KEY` / `TASK_BOARD_API_BASE` still work as fallback). This inverts the "reviewer Python never touches the
board" rule **for bulk sync only** — single-task reads in `solve-task` / `review-pr` still go through
the board-MCP on the LLM side. The task graph (`:Task`) is global, so one task can span PRs across
several microservice repos.

### Context layer (PRI-161)

- `paths.ignore` — a list of fnmatch patterns; listed paths are **not indexed** (vectors and graph) and not commented on. A bare folder name (e.g. `eval`) catches the entire subtree; `eval/*` is the explicit form; globs like `*.gen.py` are supported. Saves Voyage quota and cuts noise.
- `summary_cluster_depth_overrides` — a map of `prefix → depth` for per-directory cluster-depth overrides (longest-prefix-match by path segments); supplements the global `summary_cluster_depth`. Changing depth rebuilds affected summaries.
- `summary_topk_threshold` — scale threshold for the subsystem-summary prior. When the number of summaries for a repo/branch **exceeds** this threshold, queries use ANN top-k by proximity; otherwise all summaries are returned (back-compat for small repos). Default from env (`SUMMARY_TOPK_THRESHOLD`, 20).

All keys are read from the target branch's `.review.yml`. Example — in the root `.review.yml`.

---

## Observability web admin

Every `publish_review` records the run in Postgres (`review_runs` / `review_findings`): repo/PR,
model, timings, status, findings with verdicts and whether they were posted. The write is
**fail-soft** (a logging failure never breaks the review) and gated by `REVIEW_HISTORY` (default
`true`). The web admin (FastAPI + React/Vite SPA) shows run history, aggregates (gate filter rate,
trends over time, findings by category/severity) and per-run details with finding drill-down.

`review_findings` persists **every candidate** (not just published ones) with an `outcome` column —
the terminal funnel state (`published_inline` / `published_summary` / `verify_rejected` /
`gate_dropped` / `deduped` / `already_posted`) — and `reject_reason` (verifier text for
`verify_rejected`, the fired policy rule for `gate_dropped`, else `NULL`). This makes generation
precision measurable and separates "verify killed a hallucination" from "verify killed a real bug".
The columns are additive and idempotent (`ADD COLUMN IF NOT EXISTS` + best-effort backfill of
historical published rows); the legacy `is_real`/`published`/`inline` columns are still populated.

```bash
# On the host — build the frontend, then serve the SPA + FastAPI:
pip install -e ".[web]"
(cd web/frontend && npm install && npm run build)
reviewer serve                 # http://127.0.0.1:8000 (options: --host / --port)
```

API: `GET /api/runs` (filterable list), `GET /api/runs/{id}` (run + findings),
`GET /api/runs/{id}/trace` (step trace, forward-only — empty for pre-feature runs),
`GET /api/stats?days=N` (aggregates).

---

## Known limitations & caveats

A factual list of what this does and does not do today.

- **No automatic trigger.** A review is not started on PR open/update. It is a manual skill
  invocation inside Claude Code — there is no GitHub App / webhook / CI integration out of the box.
- **Graph auto-reindex is incremental, not full-precision.** On `prepare_review`, when the base
  branch SHA drifts, the code graph is patched for the changed files (tree-sitter, repo-scoped) in
  the same step that self-heals vector chunks — incoming `CALLS` edges from unchanged callers are
  preserved. Not refreshed until the next manual `reviewer index`: `IMPLEMENTS` edges, outgoing
  `CALLS` into unchanged files, and new incoming `CALLS` from unchanged callers. Full SCIP precision
  is restored by `reviewer index`.
- **Multi-repo via a `repo` discriminator.** One deployment hosts N repositories isolated by a
  `repo` (`owner/name`) column/property across Postgres and Neo4j; each review is scoped to its PR's
  repo (no cross-repo retrieval). Index a repo with `reviewer index <path> --repo owner/name` (or let
  it derive `owner/name` from the git `origin` remote, or set `DEFAULT_REPO`). The task graph
  (`:Task`) is intentionally global, so one task can span PRs across several microservice repos.
  Within a repo, each tracked branch has its own isolated index (`ref="base:<branch>"` in Postgres;
  `branch` property on Neo4j `:Symbol` nodes, unique constraint `(repo, branch, id)`).
- **Language scope: Python only.** The chunker (tree-sitter) and the SCIP backend (`scip-python`)
  are Python-specific. Other languages would go behind the same chunker/`GraphIndexer` interfaces.
- **VCS scope: GitHub only.** Only GitHub implements `VCSProvider`; GitLab/Bitbucket are not
  implemented (the abstraction exists, the providers do not).
- **Graph backend trade-off.** A precise, type-aware graph (`CALLS` + `IMPLEMENTS` edges) requires
  `scip-python` in `PATH`. Without it, the tree-sitter fallback gives `CALLS`-by-name only (no
  `IMPLEMENTS`). Mode is chosen via `GRAPH_BACKEND=auto|scip|treesitter`; in `auto`, a SCIP failure
  silently falls back to tree-sitter with a warning, while `scip` propagates the error.
- **Review surface.** Inline comments are only possible on diff lines (the changed/context lines of a
  hunk); everything else goes into the summary. An applyable `suggestion` block is emitted only under
  safe invariants (`apply` mode, an exact replacement, the whole range inside the RIGHT side of the
  diff, no overlap with other fixes); otherwise the advice is plain text.
- **MCP session is in-process.** State between `prepare_review` and `publish_review` lives in the
  running `reviewer-mcp` process (`_Session` in `MCPReviewService`). Both calls for one PR must hit
  the **same** running server — a restart in between loses the session (mitigated by
  `REVIEW_SESSION_PERSIST`).
- **Voyage free tier** = 3 RPM / 10K TPM; TPM is the main blocker — a full `reviewer index` of a
  large repo throttles (there is retry/backoff with jitter). A single PR review (overlay + query
  embeddings) fits within the limit.
- **LLM cost.** A review fans out Claude subagents per file plus dimension passes — that is real
  token cost, not free.
- **Observability web admin auth is optional.** Basic auth is enabled only if `WEB_ADMIN_USER` /
  `WEB_ADMIN_PASSWORD` are set; by default it is not hardened for public exposure (`reviewer serve`
  binds to loopback by default).
- **GitHub API caps.** The PR file list is paginated by 100; the compare API used to re-sync the base
  index returns at most 300 files — very large diffs are truncated.
- **`.review.yml` comes from the base branch** (by design — a PR cannot weaken its own review), not
  from the PR head.

## Tests

```bash
# unit: no Postgres, Neo4j, localhost service, or external network
.venv/bin/pytest -q
# isolated integration infra
docker compose --profile test up -d --wait paradedb-test neo4j-test
# integration; pipeline also needs VOYAGE_API_KEY
.venv/bin/pytest -q -m integration
# safe teardown only
docker compose --profile test rm -sfv paradedb-test neo4j-test
```

Default `pytest` starts no infrastructure and excludes integration tests
(`addopts = -m 'not integration'`). Unit tests cannot use external or localhost sockets. Any test
that uses the real network must carry `@pytest.mark.integration`.

Database integration tests use `TEST_PG_DSN`, `TEST_NEO4J_URI`, `TEST_NEO4J_USER`, and
`TEST_NEO4J_PASSWORD`. These `TEST_*` values must never equal development or production endpoints.
The development and test Compose services differ in ports, credentials, and storage. Test data uses
`tmpfs`, and the test service images are pinned by digest.

Never use `docker compose --profile test down -v`: the test and development services share a
Compose project, so that command would remove development containers and named volumes. Only the
targeted `docker compose --profile test rm -sfv paradedb-test neo4j-test` command is safe.

```bash
.venv/bin/ruff check .              # lint (line-length 100, target py311)
```

## Project layout

```
reviewer/
  config/      Settings (pydantic-settings): env → review thresholds, stores, branches, board
  vcs/         VCSProvider + github.py (httpx) · diff.py (lines available for inline)
  index/       chunker(tree-sitter) · embeddings(Voyage) · reranker · store(pgvector+pg_search/RRF) · freshness
  graph/       builder(tree-sitter call-graph) · scip(SCIP parser) · backend(backend orchestrator) · store(Neo4j)
  retrieval/   Retriever: hybrid + graph expansion + rerank → ContextPack
  llm/         _retry.py (retry/backoff for Voyage)
  tools/       agent tools (search_code, get_related_symbols, read_file, get_definition, …)
  tasks/       TaskBrief normalization · boards/ (TaskBoardProvider REST: yougile) · TaskService.index_batch
  agent/       state (ReviewUnit) · assemble · dedup
  mcp/         MCPReviewService: prepare / tool calls / publish; session management
  services/    ReviewService.prepare: ingest PR, overlay, units
  policy/      ReviewPolicy: env defaults + .review.yml + gating
  entrypoints/ cli.py (Click) · mcp_server.py (FastMCP, 31 tools)
  install.py   reviewer init / install / install-skills (cross-platform client wiring)
  web/         FastAPI + React/Vite SPA — observability web admin
  app.py       dependency assembly from Settings
plugin/        Claude Code plugin (10 skills /rag-reviewer:reviewer_*)
docker-compose.yml   ParadeDB (pgvector+pg_search) + Neo4j
```

---

## Contributing

Issues and PRs are welcome. To work on the project locally:

```bash
git clone https://github.com/mimfort/rag_for_git
cd rag_for_git
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
```

Run the canonical workflow and follow its safety rules in [Tests](#tests). Commit messages follow
Conventional Commits. The architecture is documented in depth in [README.ru.md](README.ru.md)
(Russian) and `CLAUDE.md`.

## License

[MIT](LICENSE) © rag_for_git contributors.
