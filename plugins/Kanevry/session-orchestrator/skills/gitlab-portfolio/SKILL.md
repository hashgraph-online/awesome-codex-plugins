---
name: gitlab-portfolio
description: Use when you need a single-pane cross-repo health view across all vault-registered GitLab and GitHub projects. Discovers repos from `_overview.md` frontmatter in `<vault>/01-projects/*/`, aggregates open issues, MRs, critical labels, and stale signals via parallel `glab`/`gh` calls, then writes an idempotent `_PORTFOLIO.md` dashboard. Runs automatically at session-start Phase 2 when `gitlab-portfolio.enabled=true`. Triggers: "show portfolio status", "refresh the portfolio dashboard", "which repos have critical issues", "run /portfolio". <example>Context: session-start, gitlab-portfolio.enabled=true, vault has 5 registered repos. user: "/session deep" assistant: "Portfolio: 3 critical issues across 2 repos — run /portfolio for details. Dashboard written to vault/01-projects/_PORTFOLIO.md."</example>
model: sonnet
---

# GitLab Portfolio Skill

> Aggregates cross-repo health signals from vault-registered projects into a single `_PORTFOLIO.md` dashboard — idempotent, opt-in, and `_generator`-marked.

## Soul

gitlab-portfolio gives you a single-pane view of your entire project portfolio. It iterates all vault-registered repositories, dispatches parallel CLI calls to `glab` / `gh`, and writes a structured Markdown dashboard at `<vault-dir>/01-projects/_PORTFOLIO.md`. The result is a living status snapshot — updated on demand or at session-start — that never overwrites hand-edited files.

## When to use

- You want a cross-repo issue/MR summary across many projects without opening each GitLab/GitHub UI.
- Session-start should surface a portfolio health banner (critical open issues, stale repos).
- A nightly routine should refresh the dashboard automatically via `/portfolio`.
- You need `--dry-run` preview before committing a refresh to the vault.

## When NOT to use

- Bidirectional sync (writing issues back to GitLab/GitHub) — use `gitlab-ops` for write operations.
- Single-repo deep-dives — use `/discovery` or direct `glab` commands.
- Projects not registered in the vault (`_overview.md` or `.vault.yaml`) — unregistered repos are silently skipped.
- Replacing a hand-authored `_PORTFOLIO.md` — the `_generator` guard prevents overwriting human content.

## Phase 1: Discovery

Implementation: `scripts/lib/gitlab-portfolio/aggregator.mjs` — `discoverRepos()`.

Iterates `<vault-dir>/01-projects/*/` subdirectories:

1. **Primary** — Read `_overview.md` YAML frontmatter. Look for `gitlab: <namespace/repo>` and/or `github: <owner/repo>`. Both keys may be present on a single repo.
2. **Fallback** — If `_overview.md` is absent or missing those keys, read `.vault.yaml` at the project root: `spec.links.gitlab` / `spec.links.github`.
3. **Skip** — Directories with neither source are silently skipped.

Output is an array of `RepoDescriptor` objects: `{ slug, gitlab, github }`.

## Phase 2: Aggregation

Implementation: `scripts/lib/gitlab-portfolio/aggregator.mjs` — `aggregateAll(repos, config)`.

All repos are fetched in parallel via `Promise.allSettled`. Per-repo CLI dispatch:

```bash
# GitLab
glab issue list --repo <namespace/repo> --state opened --output json
glab mr list   --repo <namespace/repo> --state opened --output json

# GitHub
gh issue list --repo <owner/repo> --state open --json number,title,labels,createdAt,updatedAt,milestone
gh pr list    --repo <owner/repo> --state open --json number,title,labels,createdAt,updatedAt
```

Per-repo summary fields derived from JSON output:

| Field | Derivation |
|---|---|
| `openIssues` / `openMRs` | array lengths |
| `critical` | issues where any label matches `critical-labels` (case-insensitive) |
| `stale` | issues where `updatedAt` older than `stale-days` days |
| `nextMilestone` | earliest non-null `milestone.title` across open issues |
| `lastActivity` | max `updatedAt` across all issues + MRs |
| `topIssues` | first 3 open issues sorted by `createdAt` ascending (oldest open first) |

On CLI failure per repo: behaviour is controlled by `mode` (see Error Handling).

## Phase 3: Output

Implementation: `scripts/lib/gitlab-portfolio/markdown-writer.mjs` — `renderDashboard(summaries, config)`.

**Output path:** `<vault-dir>/01-projects/_PORTFOLIO.md`. Frontmatter keys: `_generator: session-orchestrator-gitlab-portfolio@1`, `created` (ISO8601, set once), `updated` (ISO8601, refreshed each write), `repos` (count). Atomic write: content built in memory, committed via a single `writeFileSync`.

## Phase 4: Idempotency

`parseFrontmatter` and `emitAction` imported from `scripts/lib/vault-mirror/utils.mjs`. Rules:

1. No file → `created`.
2. File exists, `_generator` absent or differs → `skipped-handwritten` (never overwrite human content).
3. File exists, generator matches, `updated` ≤ fresh data → `updated`.
4. File exists, generator matches, `updated` > fresh data → `skipped-noop`.

Stdout action shape: `{"action":"updated","path":"01-projects/_PORTFOLIO.md","repos":16,"critical":3}`

## Config

Opt-in via the `gitlab-portfolio:` block in Session Config (`CLAUDE.md` / `AGENTS.md`):

```yaml
gitlab-portfolio:
  enabled: true
  mode: warn          # warn | strict | off
  stale-days: 30
  critical-labels: ["priority:critical", "priority:high"]
```

| Field | Default | Meaning |
|---|---|---|
| `enabled` | `false` | Master switch. |
| `mode` | `warn` | `warn` / `strict` / `off` — failure handling; `off` ≡ disabled. |
| `stale-days` | `30` | Issues older than N days are flagged stale. |
| `critical-labels` | `["priority:critical","priority:high"]` | Label substrings that classify an issue as critical (case-insensitive). |

### Security

**`--vault-dir` validation (SEC, GH #44).** The `--vault-dir` CLI argument and `vault-integration.vault-dir` Session Config value are validated against the user's home directory via `validatePathInsideProject` (`scripts/lib/path-utils.mjs`). Both phases apply:

- **Lexical:** paths containing `..` traversal that resolve outside `os.homedir()` are rejected (`exit 2`).
- **Symlink:** paths whose real-path (after symlink resolution) escapes `os.homedir()` are rejected (`exit 2`).

Configure `vault-integration.vault-dir` only with user-controlled paths under `~`. The same guard applies to the implicit Phase 2.7 portfolio snapshot at session-start. Reference: CWE-22 path traversal · `.claude/rules/security.md` SEC-014 adjacent guidance.

**Note:** `vault-dir` must be a CHILD of `~` (the home directory), not `~` itself. The guard uses strict `isPathInside` semantics, which require a proper descendant path.

## CLI

```bash
node scripts/lib/gitlab-portfolio/aggregator.mjs \
  --vault-dir ~/Projects/vault \
  [--dry-run]
```

| Flag | Required | Description |
|---|---|---|
| `--vault-dir` | yes | Absolute path to Meta-Vault root. Must exist. |
| `--dry-run` | no | Run discovery + aggregation; print diff to stdout; do not write the dashboard. |

Exit codes: `0` success · `1` bad args/config · `2` vault-dir not found or write failed · `3` repo fetch failures in `strict` mode.

## Hook

When `gitlab-portfolio.enabled: true` and `vault-integration.enabled: true`, session-start Phase 2 invokes the aggregator in parallel with ecosystem-health. The hook always runs in `warn` mode — session-start must not block on non-fatal failures. On critical issues found, a banner is emitted:

```
🔴 Portfolio: 3 critical issues across 2 repos — run /portfolio for details
```

## Output format

```markdown
---
_generator: session-orchestrator-gitlab-portfolio@1
created: 2026-05-16T08:00:00Z
updated: 2026-05-16T08:00:00Z
repos: 2
---

# Portfolio Dashboard

> Generated: 2026-05-16 08:00 UTC · 2 repos · 1 critical · 0 stale

## Summary

| Repo | Open Issues | Open MRs | Critical | Stale | Last Activity |
|---|---|---|---|---|---|
| session-orchestrator | 9 | 2 | 1 | 0 | 2026-05-16 |
| my-saas-app          | 4 | 1 | 0 | 0 | 2026-05-15 |

## session-orchestrator

**gitlab:** `kanevry/session-orchestrator` · Open: 9 issues / 2 MRs · Critical: 1 · Next milestone: v3.7

| # | Title | Labels | Updated |
|---|---|---|---|
| #41 | gitlab-portfolio skill | enhancement | 2026-05-16 |
| #42 | session-end echo-stub | bug | 2026-05-14 |
| #35 | superpowers adoption | enhancement | 2026-05-10 |

## my-saas-app

**github:** `owner/my-saas-app` · Open: 4 issues / 1 PR · Critical: 0
```

## Error handling

Behaviour is governed by `mode`. `warn`: emit warning to stderr, continue with partial data; repo rows show `(fetch failed)`. `strict`: any repo fetch failure or missing vault-dir exits 3 immediately. `off`: all errors are silently swallowed, partial data written.

`--vault-dir` not found and write errors always exit 2 regardless of `mode`. `_PORTFOLIO.md` with no `_generator` key always results in `skipped-handwritten` (all modes). No repos discovered: `warn` → exit 0 (no file written); `strict` → exit 3.

## Anti-Patterns

- **Sequential `glab` calls** — always use `Promise.allSettled`; sequential calls time out on large portfolios.
- **Writing without idempotency check** — always inspect `_generator` before overwriting.
- **Hardcoding label strings** — read `critical-labels` from config.
- **Blocking session-start on fetch failures** — hook always runs in `warn` mode.
- **Overwriting `created` on refresh** — `created` is set once; only `updated` changes.

## Critical Rules

- `_generator: session-orchestrator-gitlab-portfolio@1` MUST appear in every file written by this skill.
- Output path is always `<vault-dir>/01-projects/_PORTFOLIO.md`. No other path is valid.
- `Promise.allSettled` is mandatory — one failing repo must never abort the entire run.
- Atomic write: build full content in memory, then a single `writeFileSync`.
- Implementation files: `scripts/lib/gitlab-portfolio/aggregator.mjs` (discovery + aggregation) · `scripts/lib/gitlab-portfolio/markdown-writer.mjs` (rendering + idempotency) · shared helpers from `scripts/lib/vault-mirror/utils.mjs`.
