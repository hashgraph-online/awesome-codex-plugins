---
name: ms
description: meta_skill (ms) — the skill-search/load
---
<!-- TOC: Core Insight | Quick Start | Consume (MCP) | Write/Admin (CLI) | Footguns | Concurrency | References -->

# ms — meta_skill search/load engine

> **Core Insight:** `ms` is the skill-search engine over both corpora (agentops + jsm, ~175 skills). **Consume via MCP, write/admin via CLI.** One law: after ANY reindex/wipe, every running `ms mcp serve` MUST be killed (sessions respawn fresh). A surviving server silently reads pre-wipe data and returns `recorded:true` on writes that land in orphaned files.

## Quick Start

Find a skill (MCP-primary — BM25, currently strictly better than CLI search), then load the FULL runnable SKILL.md in one call (always `full: true` when you mean to use it):

```bash
mcp__ms__search {query: "handle a rate limit switching accounts"}
mcp__ms__load {skill: "account-rotation", full: true}
```

CLI fallback when no MCP server is attached:

```bash
ms search "switch accounts on rate limit" -O json
ms load account-rotation --full -O json | jq -r '.data.content'
```

State root: `~/Library/Application Support/ms/`.

---

## Consume — MCP-primary (`mcp__ms__*`)

Prefer the MCP tools whenever a `ms mcp serve` is attached — they are the fast, verified read path.

| Tool | Use |
|------|-----|
| `mcp__ms__search {query}` | BM25 search. **Currently strictly better than CLI search** (see Footguns — CLI hybrid is BM25-only; ms never stores doc embeddings). |
| `mcp__ms__load {skill, full: true}` | Returns the full runnable SKILL.md in ONE call, zero extraction friction. **`full: false` returns a useless metadata card — always `full: true` when you intend to use the skill.** |
| `mcp__ms__show {skill}` | Metadata card for a skill. |
| `mcp__ms__suggest {cwd}` | Suggests skills for a directory. Works — but **ignore its project-language detection** (misdetects Makefile repos as C; cosmetic only). |

**CLI fallback** (no MCP server attached):

```bash
ms search "<query>" -O json
ms load <id> --full -O json | jq -r '.data.content'   # content lives in .data.content
```

---

## Write / Admin — CLI-only (verified landing in the live DB)

The MCP feedback tool exists, but **only the CLI write path is verified to land** — trust the CLI for writes.

```bash
ms feedback add <skill> --positive --comment "..."   # feedback on a skill
ms feedback add <skill> --negative --comment "..."

ms outcome <skill> --success   # dogfood loop: record AFTER actually using a skill's guidance
ms outcome <skill> --failure

ms doctor                      # admin: health
scripts/ms-reindex.sh          # (re)index THE way: rebuild + sweep every ms mcp serve + probe (see Footguns)
ms list -O jsonl --limit 1000  # counting / enumeration
ms config                      # resolved config + skill_paths
```

---

## Footguns (all measured 2026-07-02)

| Footgun | Truth |
|---|---|
| **MCP server survives a DB wipe/reindex** | An `ms mcp serve` NEVER reopens handles — it follows renamed inodes into the backup, giving stale reads AND silent misdirected writes (`recorded:true` into orphaned files). **Reindex via `scripts/ms-reindex.sh` — THE way to reindex** (rebuilds, then TERMs every `ms mcp serve`, then probes a fresh server for orphan ids); never run bare `ms index` and leave servers up. Sessions respawn fresh. This is the one law, now mechanized (age-22g0). |
| **`ms load --pack N`** | Trap: caps at the gutted `overview` tier for ANY N (`800` == `20000`) — drops the executable steps and returns LESS than the no-flag default. Use `--full` (CLI) or `full: true` (MCP). |
| **`-O plain`** | Prints name-only on `load`; truncates list output (`[N more lines]`). The content lives in `-O json` → `.data.content`. |
| **CLI `ms search` "hybrid"** | Effectively BM25-only — ms never stores doc embeddings (`upsert_embedding` is called only from a unit test), so hybrid ≡ BM25 under ANY backend; no config/backend change fixes it (upstream gap, feature-noted; measured 2026-07-02, age-s3jf). Still loses to MCP BM25 in practice; don't prefer it. |
| **Stale `ms.lock`** | `ms doctor` prints "Lock held" for a DEAD pid yet still says all-pass. A dead-pid lock is safe to delete. |
| **Symlinks** | ms does NOT follow directory symlinks — `skill_paths` must list BOTH roots explicitly: the `~/.codex` skills dir AND the `~/dev/agentops/skills` repo dir. |
| **Binary** | Source build only (`~/dev/meta_skill`, branch `local/frontmatter-id`); the 0.1.2 release binary corrupts IDs on Anthropic-frontmatter skills. Update: `git fetch && git rebase origin/main && cargo install --path . --locked`. |

## Concurrency

Parallel CLI + MCP `load` measured clean — no lock errors. The lock hazard is the survive-a-wipe case above (kill the serve), not concurrent reads.

---

## Scenarios

```gherkin
Scenario: Load a skill's full runnable guidance
  Given an ms mcp serve is attached
  When I call mcp__ms__load {skill: "account-rotation", full: true}
  Then the full runnable SKILL.md content is returned in one call

Scenario: Reindex invalidates every running server
  Given one or more ms mcp serve processes are running
  When I run ms index (or wipe/rebuild the DB)
  Then I kill every ms mcp serve so sessions respawn against fresh data
  And a surviving server would silently read pre-wipe data and mis-land writes
```

## References

- Upstream: Jeffrey Emanuel's `meta_skill` (source at `~/dev/meta_skill`, branch `local/frontmatter-id`).
- Related consume-tool skill in this repo: [`cass`](../cass/SKILL.md) (session archaeology). The jsm `cass-memory` (cm) procedural-memory tool is the write-side complement (installed separately, not in this repo).
