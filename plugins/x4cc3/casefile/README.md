# Casefile — Offensive Security Case Tracker

Track durable security cases during bug bounties, CTFs, and security audits. Each case is a structured record that persists across sessions.

Casefile now has two surfaces backed by the same ledger:

- **pi extension** — registers pi tools, `/casefile`, and prompt context injection.
- **Codex plugin** — bundles a Casefile skill and MCP server for Codex tool access.

## Install for pi

From npmjs:

```bash
pi install npm:pi-casefile
```

From GitHub Packages:

```bash
pi install npm:@x4cc3/pi-casefile
```

For GitHub Packages, configure npm access first:

```ini
@x4cc3:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=YOUR_GITHUB_TOKEN
```

Or from source:

```bash
pi install git:github.com/x4cc3/casefile
```

For local development, symlink or copy into `~/.pi/agent/extensions/casefile/`.

## Use with Codex

This repo is also a Codex plugin root. The plugin files are:

- `.codex-plugin/plugin.json` — Codex plugin manifest
- `.agents/plugins/marketplace.json` — Codex marketplace entry for CLI installs
- `.mcp.json` — bundled MCP server config
- `skills/casefile/SKILL.md` — Codex workflow instructions
- `mcp/server.ts` — MCP stdio server backed by `ledger.ts`

Install from this GitHub repo with the Codex CLI:

```bash
codex plugin marketplace add x4cc3/casefile --ref master
codex plugin add casefile@casefile
```

Then start a new Codex thread and ask Codex to use Casefile. If you already added
the marketplace and want the newest version, run:

```bash
codex plugin marketplace upgrade casefile
codex plugin remove casefile
codex plugin add casefile@casefile
```

The MCP server starts over stdio and waits for MCP client input:

```bash
bun run mcp
```

For local Codex plugin testing, point a Codex marketplace entry at this plugin root or copy the repo into a local plugin directory and install it from that marketplace.

## pi Tools

| Tool | Description |
|------|-------------|
| **CaseAdd** | Open a new hypothesis or investigation case |
| **CaseUpdate** | Update status, evidence, confidence, severity, next steps |
| **CaseGet** | Full details of a single case by ID |
| **CaseList** | Browse cases with status/severity/priority/tag filters + pagination |
| **CaseSearch** | Full-text search across cases, optionally field-scoped |
| **CaseLink** | Bidirectionally link two cases (exploit chains) |
| **CaseUnlink** | Remove a link between two cases |
| **CaseReport** | Generate a markdown report from a case |

## Codex MCP Tools

| Tool | Description |
|------|-------------|
| `casefile_add` | Open a new hypothesis or investigation case |
| `casefile_update` | Update status, evidence, confidence, severity, next steps |
| `casefile_get` | Full details of a single case by ID |
| `casefile_list` | Browse cases with status/severity/priority/tag filters + pagination |
| `casefile_search` | Full-text search across cases, optionally field-scoped |
| `casefile_link` | Bidirectionally link two cases |
| `casefile_unlink` | Remove a bidirectional case link |
| `casefile_report` | Generate a markdown report from a case |
| `casefile_count` | Count cases by status and severity |

## Case Fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Short case title (required) |
| `status` | enum | `hypothesis` → `investigating` → `confirmed` → `blocked`/`killed`/`reported` |
| `confidence` | enum | `low`, `medium`, `high` |
| `severity` | enum | `info`, `low`, `medium`, `high`, `critical` |
| `priority` | enum | `P0`–`P4` triage rating |
| `target` | string | Target asset, host, repo, or scope |
| `endpoint` | string | Route, file, or object path |
| `bug_class` | string | Bug class (SSRF, IDOR, XSS, etc.) |
| `summary` | string | Short report summary |
| `evidence` | string | Observed evidence or reproduction steps |
| `impact` | string | Security impact or chain value |
| `next_step` | string | Next validation or exploit step |
| `poc` | string | Proof of concept steps |
| `remediation` | string | How to fix it |
| `references` | string[] | External URLs, CVEs |
| `blockers` | string[] | Current blockers |
| `tags` | string[] | Tags for filtering |
| `assumptions` | string[] | Explicit assumptions, unknowns, or uncertainty notes |
| `linked_case_ids` | string[] | Related case IDs managed by `CaseLink`/`CaseUnlink` |

## Commands

- `/casefile` — Interactive dashboard showing all cases with status summary

## Context Injection

On each turn, the extension injects a `<casefile_context>` block into the system prompt showing active cases (excluding killed/reported). Case titles and next steps are sanitized and truncated before injection, and the prompt marks them as untrusted data.

## Storage

By default, pi cases are stored per project at `.pi/casefile.jsonl` under the detected workspace root. The Codex plugin opts into neutral project storage at `.casefile/casefile.jsonl`. This prevents old bounty cases from leaking into unrelated directories.

Environment overrides:

- `CASEFILE_PATH=/absolute/or/relative/file.jsonl` — force an exact ledger path for any surface
- `CASEFILE_SCOPE=project` — use project-local neutral storage at `.casefile/casefile.jsonl`
- `CASEFILE_SCOPE=global` — use the shared global ledger at `~/.casefile/casefile.jsonl`
- `CODEX_CASEFILE_PATH` / `CODEX_CASEFILE_SCOPE` — Codex-specific aliases
- `PI_CASEFILE_PATH=/absolute/or/relative/file.jsonl` — force an exact ledger path
- `PI_CASEFILE_SCOPE=project` — use legacy project-local pi storage at `.pi/casefile.jsonl`
- `PI_CASEFILE_SCOPE=global` — use the legacy shared global pi ledger at `~/.pi/casefile/casefile.jsonl`

Each line is a complete JSON record. Features:

- **Project-scoped storage by default** — separate ledgers across workspaces
- **Append-based adds/updates** — preserves history, deduped on read (last write wins)
- **Duplicate add guard** — repeated `CaseAdd` calls for the same active title/scope return the existing case instead of appending a duplicate
- **Mutation locking** — serializes writes and reduces concurrent update loss
- **Atomic rewrite** — link/unlink/delete rewrite through temp file + rename
- **Dead-end memory** — use `CaseUpdate` with `status: killed` for duplicates, disproven leads, or cases that should not be pursued again
- **Evidence guardrails** — confirmed cases require both observed evidence and a PoC/repro note; blocked, killed, and reported cases require supporting fields
- **Promotion guard** — new cases must start as hypothesis or investigating; use `CaseUpdate` for blocked, killed, confirmed, or reported states
- **Redundant update guard** — repeated `CaseUpdate` calls that only restate an unchanged status (including already-confirmed cases) are no-ops
- **Link/report guardrails** — repeated link/unlink calls are no-ops, and reports require confirmed or reported cases
- **Report export** — report tools write markdown under `report/` next to the active ledger

## Offensive Security Workflow

1. **Hypothesize** — `CaseAdd` with `status: hypothesis`
2. **Investigate** — `CaseUpdate` to `status: investigating`, add `evidence`
3. **Confirm** — `CaseUpdate` to `status: confirmed`, set `severity`, write `poc`
4. **Chain** — `CaseLink` to connect primitives to escalations
5. **Report** — `CaseReport` to draft markdown, then `CaseUpdate` to `status: reported`, add `remediation` and `references`
6. **Kill** — `CaseUpdate` to `status: killed` for dead ends, duplicates, or disproven leads; include `evidence`, `blockers`, or `assumptions` explaining why
