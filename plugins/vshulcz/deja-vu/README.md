<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/vshulcz/deja-vu/main/assets/logo-dark.svg">
    <img src="https://raw.githubusercontent.com/vshulcz/deja-vu/main/assets/logo.svg" width="240" alt="deja-vu">
  </picture>
</p>

<p align="center"><b>Instant local memory for 52 coding agents — reads the session logs already on your disk.</b><br>
Survives /compact, hands off across agents, and recovers overwritten code. One Go binary, zero LLM calls, no API key, 0.7–0.8 ms lookups.</p>

<p align="center">English | <a href="docs/readme/README.zh.md">简体中文</a> | <a href="docs/readme/README.zh-TW.md">繁體中文</a> | <a href="docs/readme/README.ja.md">日本語</a> | <a href="docs/readme/README.ko.md">한국어</a> | <a href="docs/readme/README.es.md">Español</a> | <a href="docs/readme/README.pt.md">Português</a> | <a href="docs/readme/README.fr.md">Français</a> | <a href="docs/readme/README.de.md">Deutsch</a> | <a href="docs/readme/README.ru.md">Русский</a> | <a href="docs/readme/README.tr.md">Türkçe</a> | <a href="docs/readme/README.hi.md">हिन्दी</a></p>

<p align="center">
  <a href="https://trendshift.io/repositories/83640" target="_blank"><img src="https://trendshift.io/api/badge/trendshift/repositories/83640/daily?language=Go" alt="vshulcz/deja-vu — #1 Go Repository Of The Day on Trendshift" width="250" height="55"></a>
</p>

<p align="center">
  <a href="https://github.com/vshulcz/deja-vu/actions/workflows/ci.yml"><img src="https://github.com/vshulcz/deja-vu/actions/workflows/ci.yml/badge.svg?branch=main&event=push" alt="CI"></a>
  <a href="https://github.com/vshulcz/deja-vu/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/coverage-88%25-brightgreen" alt="Coverage"></a>
  <a href="https://github.com/vshulcz/deja-vu/releases"><img src="https://img.shields.io/github/v/release/vshulcz/deja-vu" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  &middot;
  <a href="https://vshulcz.github.io/deja-vu/">Website</a> &middot; <a href="https://vshulcz.github.io/deja-vu/view/">Live demo</a> &middot; <a href="https://vshulcz.github.io/deja-vu/guide/getting-started.html">Docs</a> &middot; <a href="https://vshulcz.github.io/deja-vu/guide/benchmarks.html">Benchmarks</a> &middot; <a href="docs/ARCHITECTURE.md">Architecture</a>
</p>

<p align="center"><img src="https://raw.githubusercontent.com/vshulcz/deja-vu/main/assets/demo.gif" width="720" alt="deja-vu answering a question from prior session history"></p>

```sh
npx @vshulcz/deja-vu audit --secrets               # scan local logs for expiry & leaked keys, no install
npx @vshulcz/deja-vu install --auto                # install and wire detected agents
curl -fsSL https://raw.githubusercontent.com/vshulcz/deja-vu/main/install.sh | sh && deja install --auto
claude plugin marketplace add vshulcz/deja-vu && claude plugin install deja-vu@deja-vu
codex plugin marketplace add https://github.com/vshulcz/deja-vu && codex plugin add deja-vu@deja-vu
gemini extensions install https://github.com/vshulcz/deja-vu
opencode plugin add opencode-deja
```

```sh
$ deja "jwt refresh token"             # lexical + structural search across 52 coding agents
$ deja handoff --to codex              # transfer goal, decisions & open work across agents
$ deja restore internal/auth/jwt.go    # recover an edit span replaced before git commit
$ deja blame internal/auth/jwt.go:42   # trace which agent session wrote or replaced a line
$ deja audit --secrets                 # inspect store paths, cleanup risk & leaked keys
```

## Overview

Coding agents already persist transcripts to local JSONL and SQLite stores (`~/.claude`, `~/.codex`, Cursor `state.vscdb`, OpenCode, Gemini CLI, Hermes, and the remaining supported harnesses). `deja` indexes those transcripts in place into an append-only inverted index under `~/.cache/deja` and exposes history through a terminal TUI, CLI, MCP server, and lifecycle hooks.

- **Works retroactively from day one.** Existing transcripts across all [fifty-two agents](#supported-harnesses) are searchable immediately without capture daemons or API keys.
- **Survives `/compact` and context resets.** Captures pre-compaction tasks, settled decisions, files, and verification commands and injects a bounded recovery packet on the next turn ([details](docs/compaction.md)).
- **Cross-agent handoff (`deja handoff`).** Transfers goal, standing constraints, touched files, passed checks, and open work between harnesses.
- **Code recovery and attribution (`deja restore`, `deja blame`, `deja origin`).** Indexes recorded edit spans, opened files, and exit-coded shell commands to recover clobbered uncommitted changes and map commits/lines back to agent sessions.
- **Decision lifecycle and staleness tracking.** `deja promote <id> --state rejected` flags reverted approaches on later hits (`--state accepted` takes the mark back); search warns when referenced workspace files changed after the session.
- **Team repository memory.** `deja repo add` exports redacted curated notes into `.deja/memory.jsonl` with `merge=union` git merge semantics ([details](#memory-in-the-repository)).
- **Incremental indexing & redaction.** Append-only `records.bin`, token bucket overlays, and watermarked `manifest.gob` keep repeat freshness checks to ~50 ms and index footprint at ~4% on multi-GB stores; credentials are stripped at index time ([architecture](docs/ARCHITECTURE.md), [privacy](#privacy)).

## Interactive search

Running `deja` without arguments opens a terminal search over uncommitted-change sessions and project history (`deja brief` prints a plain-text summary; `deja view` generates a standalone local HTML explorer — [live demo](https://vshulcz.github.io/deja-vu/view/)).

<p align="center"><img src="https://raw.githubusercontent.com/vshulcz/deja-vu/main/assets/tui.gif" width="720" alt="Interactive terminal search and cross-agent handoff"></p>

- **Navigate:** `↑↓` selects a session, `↵` opens at the match, `/` searches within a transcript, `]` / `[` step turns, `^s` toggles relevance/date sort (`deja search --sort date`).
- **Filter:** prefix by agent (`codex:`), time (`today`, `yesterday`, `week`, `month`), or project (`in:<project>`).
- **Act:** `r` resumes in the native harness; `o` hands off to another agent; `tab` switches between current project, all projects, and **Deleted** transcripts retained in the index (`R` restores, `D` deletes, `?` shows bindings).

## Install

`install.sh` installs the binary to `~/.local/bin`; `deja install --auto` wires MCP recall and hooks into detected agents and builds the initial index (~10 s).

<p align="center"><img src="https://raw.githubusercontent.com/vshulcz/deja-vu/main/assets/banner.png" width="700" alt="First-run index summary and sample query"></p>

<details>
<summary><b>Package managers, Windows (Scoop / winget), native plugin bundles, and binary-only setup</b></summary>

Alternative installers: `brew install deja-vu`, `mise use -g aqua:vshulcz/deja-vu`, `nix run github:numtide/llm-agents.nix#deja-vu`, `go install github.com/vshulcz/deja-vu/cmd/deja@latest`, or `npx @vshulcz/deja-vu "query"` to run without installing. Desktop MCP clients can open the signed `.mcpb` bundle from the [latest release](https://github.com/vshulcz/deja-vu/releases/latest).

Codex CLI, opencode, Claude Code, Qwen, and OpenClaw also accept native marketplace/registry installs (alongside [`cursor-plugin/`](cursor-plugin/) for Cursor and [`antigravity-plugin/`](antigravity-plugin/) for Antigravity; Copilot CLI installs only the skill from the bundle — run `deja install copilot-auto` for hooks and MCP):

```sh
codex plugin marketplace add https://github.com/vshulcz/deja-vu && codex plugin add deja-vu@deja-vu
opencode plugin add opencode-deja
claude plugin marketplace add vshulcz/deja-vu && claude plugin install deja-vu@deja-vu
```

`install.sh` targets macOS and Linux and exits with `unsupported OS` on Windows. On Windows, install via Scoop or winget, or extract `deja-vu_<version>_windows_amd64.zip` from the [latest release](https://github.com/vshulcz/deja-vu/releases/latest) onto `PATH`:

```powershell
scoop install deja-vu
winget install vshulcz.deja-vu
```

Using the binary alone for indexing, search, `show`, `ctx`, and `blame` works with no harness wiring; running `deja install` to wire MCP and hooks is optional. Without wiring, `deja doctor` reports detected MCP targets as `config missing` or `not-wired`. `deja warmup` also installs `~/.agents/skills/deja-search/SKILL.md` ([`skills/deja-search/SKILL.md`](skills/deja-search/SKILL.md)) for harnesses that rely on CLI skills instead of MCP. `deja install --all` configures MCP without session-start hooks; see the [agent setup guide](https://vshulcz.github.io/deja-vu/guide/agents.html).

</details>

<details>
<summary>User-level guidance targets</summary>

Install also writes user-level guidance for the harnesses it detects: Claude Code, Codex, opencode, Gemini CLI, Antigravity, Qwen, Kimi Code, pi, Senpi, Copilot, VS Code Copilot Chat, Goose, OpenClaw, Hermes, Roo Code, omp, Amp, prime-agent, DeepSeek Harness, Continue, Crush, CodeBuddy Code, WorkBuddy, Zed, TRAE CLI, TRAE IDE, Muse Code, CodeWhale, ZCode and Junie each get it in their own guidance file (or under the configured `XDG_CONFIG_HOME`). Re-run rewrites deja's skill or marked block without changing surrounding user content. Use `deja install --all --no-guidance` to opt out; Grok Build, Devin CLI and Ante get the shared skill in `~/.agents/skills`, which is what they read; the `~/.grok/GROK.md` written beside it is for the unrelated community CLI that shares that directory. Cursor has no user-level instructions file, so it gets the shared skill in `~/.agents/skills` — one of the four places Cursor reads skills from — read only when something looks relevant rather than every session. Kilo Code, gajae-code, Kimchi, Command Code, Cherry Studio and Reasonix get the skill, MiniMax Code gets it inside the plugin package, and Kiro the skill and a steering file, from their own install target.

</details>

## Memory in the repository

To share vetted project decisions and dead ends through git, promote candidates from any local agent history into `.deja/memory.jsonl`:

```text
$ deja repo candidates
4cd7e7bb9c rejected Reverted the retry with jitter: it broke idempotency because the sender re-signs each attempt with a new delivery id.  (session s1, claude 2026-08-03)
$ deja repo add 4cd7e7bb9c
added 1 entry to .deja/memory.jsonl
nothing is committed: review with `git diff .deja/` and commit it like code
```

Entries are redacted on write (secret matches are rejected), stored as sorted content-hashed JSON lines, and paired with `merge=union` in `.deja/.gitattributes` so parallel branch additions merge cleanly. Cloned repositories load these entries under untrusted framing (`{"activations":{"auto":{"repo":false}}}` in `policy.json` disables hook injection). See the [repo memory guide](https://vshulcz.github.io/deja-vu/guide/repo-memory.html).

In GitHub Actions, run `deja` directly in CI without a separate install step:

```yaml
- uses: vshulcz/deja-vu@main
  with:
    args: audit --fail-on-secrets
```

## Privacy

Indexing and search run locally with no remote inference. Network requests occur only for explicit `deja update` / `deja sync ssh`, `deja doctor` version checks, configured `deja embed` endpoints, and a daily release version check (`DEJA_OFFLINE=1` or `DEJA_NO_UPDATE_NOTICE=1` disables it).

Known credential shapes (cloud/provider keys, bearer tokens, JWTs, PEM/PGP blocks, credential URLs, CLI password flags, high-entropy assignments) are replaced at index time with `[redacted:<kind>]` while leaving surrounding text searchable. `deja secrets [--scrub]` scans and optionally rewrites credentials inside source transcripts (backing up originals). `deja forget` permanently excludes sessions across rebuilds, and `~/.config/deja/exclude` filters projects or whole harnesses (`harness:opencode`). See [`docs/SECURITY-MODEL.md`](docs/SECURITY-MODEL.md).

## CLI & MCP

```text
$ deja "jwt refresh token"
[claude] api        · Jul 8 · 8f31c0a9 — 2 matches
  login started failing after refresh token rotation; jwt kid mismatch in tests
  fixed by reloading jwks cache after rotateKey and adding a clock-skew test
[codex]  web        · Jul 1 · b77d91e2 — 1 match
  refresh token cookie needed SameSite=Lax in local callback flow
```

| Command | Purpose |
| --- | --- |
| `deja <query>` | Multi-word AND + quoted-phrase search across all stores; falls back to word forms/close spellings when exact matches miss (`code` finds `opencode`). Supports `--sort date`, `--harness`, `--project`, `--since`, `--role`. |
| `deja` / `deja brief` | Launch interactive TUI search, or print a concise non-interactive summary. |
| `deja wip` | Reconstruct active task, settled points, edited files, and last command from the latest session here. |
| `deja blame <path>[:line]` | List sessions that discussed or modified a file, or attribute a line via git commit + recorded edit spans (`--attribution`, `--json`, `--git-note`). |
| `deja origin [rev\|range]` | Map commits or ranges to originating agent sessions and user turns (`attributed`, `uncertain`, `unknown`). |
| `deja review [rev\|range]` | Surface prior sessions and curated notes for files touched in a working tree diff or commit range. |
| `deja files <topic>` | Reverse lookup: files modified in sessions matching a topic. |
| `deja how <tool>` | Observed command invocations and flags run previously in this environment. |
| `deja fix <error>` | Recorded remediation commands that succeeded after the same failure output (never destructive actions). |
| `deja friction` | Errors recurring across 3+ sessions by harness. |

<details>
<summary>Session inspection, curation, sync, and diagnostics</summary>

| Command | Purpose |
| --- | --- |
| `deja ctx <query>` | Markdown digest with changed code spans, formatted for prompt injection. |
| `deja recall <words>` | Same ~4 KB scoped snippet page returned by the MCP `recall` mode (`DEJA_RECALL_GLOBAL=1` removes project bias). |
| `deja resume <id>` | Reopen a session in its native agent (`--app` opens Codex desktop). |
| `deja restore <path>` | Recover an uncommitted `old_string` edit span replaced by an agent without overwriting automatically. |
| `deja promote <id>` | Promote a transcript conclusion to a curated note (`--state accepted\|rejected\|superseded`, `--repo` for `.deja/notes.jsonl`). |
| `deja share <id>` | Export a redacted session digest for sharing. |
| `deja sync export\|import\|ssh` | Watermarked, idempotent append-only history sync between machines. |
| `deja repo candidates\|add` | Curate sanitized repository notes into `.deja/memory.jsonl`. |
| `deja view` / `deja stats` | Generate a local standalone HTML explorer (`deja view`), audit history telemetry, or export profile heatmaps (`deja stats --card`, [PNG converter](https://vshulcz.github.io/deja-vu/card/)). |
| `deja secrets [--scrub]` | Report or scrub secret matches in source transcripts. |
| `deja rules [sync\|candidates]` | Sync standing rules from `~/.config/deja/rules.md` or inspect correction turns. |
| `deja audit [--json]` | Inspect retention settings, purged sessions, recoverable spans, and hook/MCP wiring. |
| `deja doctor [--deep]` / `deja mcp` | Verify store parity and run the stdio (`--http` for Streamable HTTP) MCP server. |

</details>

Reference: [CLI commands](https://vshulcz.github.io/deja-vu/guide/commands.html) · [JSON schema](docs/json-output.md).

### MCP tools

`deja mcp` exposes **one tool**, `deja`, multiplexed on `mode` (477 schema tokens/turn; legacy six-tool names remain accepted on `tools/call` for older configs). `deja mcp --context-search` serves a single `context_search` tool for Qwen Code's External Context MCP Profile v1 ([details](docs/registry/qwen.md)).

<details>
<summary>Tool schema and modes</summary>

| Tool | Arguments | Returns |
| --- | --- | --- |
| `deja` | `mode`, `q`, `harness?`, `project?`, `limit?` | Mode-specific bounded payload below. |

| Mode | `q` | Optional args | Returns |
| --- | --- | --- | --- |
| `recall` | 1–3 exact terms (path, error, flag, symbol) | `harness?`, `limit?`, `offset?` | Compact snippets capped at 4 KB. |
| `context` | 1–3 exact terms | `harness?` | Markdown session digest with modified code spans. |
| `blame` | File path (optional `:line`) | `harness?`, `project?`, `since?`, `limit?`, `all?` | Sessions and decisions tied to the file. |
| `fix` | Verbatim failing output | `limit?` | Prior successful commands after the same error. |
| `how` | Command or tool name (e.g. `go test`) | `project?`, `limit?` | Observed invocations and flags here. |
| `orient` | Empty or project topic | `project?`, `limit?` | Frequent project commands and active files. |
| `remember` | Fact or decision | `project?`, `tags?` | Persists note locally, or into `.deja/memory.jsonl` with `repo:` / `repo:rejected` / `repo:gotcha`. |
| `handoff` | Session id or harness name | `harness?` | Structured task packet to resume in another agent. |

</details>

## Supported harnesses

All fifty-two supported coding agents share one index, CLI, and MCP server (`DEJA_*_ROOT` and upstream relocation env vars are honored; [session format registry](https://vshulcz.github.io/deja-vu/registry/README.html)). TRAE IDE transcripts live in an encrypted database, so `deja install trae-ide` wires MCP and skills (plus hooks under `trae-ide-auto` once enabled in IDE settings) without transcript ingestion.

<!-- matrix:start -->
aider &middot; Amp &middot; Ante &middot; Antigravity &middot; Cherry Studio &middot; Claude Code &middot; Claw Code &middot; Cline &middot; CodeArts Desktop &middot; CodeBuddy Code &middot; CodeWhale &middot; Codex CLI &middot; Command Code &middot; Continue &middot; Copilot CLI &middot; VS Code Copilot Chat &middot; Crush &middot; Cursor &middot; DeepSeek Harness &middot; Devin CLI &middot; Doubao &middot; Gemini CLI &middot; gajae-code &middot; Goose &middot; Grok Build &middot; Hermes &middot; JetBrains AI Assistant &middot; Junie &middot; Kilo Code &middot; Kimchi Coding &middot; Kimi Code &middot; Kiro &middot; MiniMax Code &middot; MiMo-Code &middot; Muse Code &middot; TeleAgent &middot; Omnigent &middot; omp (Oh My Pi) &middot; OpenClaw &middot; opencode &middot; Orca &middot; pi &middot; prime-agent (PrimeIntellect) &middot; Qoder &middot; Qwen Code &middot; Reasonix &middot; Roo Code &middot; Senpi &middot; TRAE CLI &middot; Windsurf / Devin Desktop &middot; ZCode &middot; Zed.

<details>
<summary>What each one supports</summary>

| Harness | MCP recall | Auto-recall | Skill | Command | Resume | Handoff | Needs |
| --- | :-: | :-: | :-: | :-: | :-: | :-: | --- |
| aider | ⚠ | ✅ | ✕ | ⚠ | ✕ | ✅ | deja aider |
| Amp | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | threads from 0.0.1774963753 on live on ampcode.com; deja reads those its plugin has written out, and older local ones |
| Ante | ✅ | ✕ | ✅ | ✅ | ✅ | ✅ | — |
| Antigravity | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Cherry Studio | ✅ | ✅ | ✅ | ✕ | ✕ | paste | import the server once in Settings -> MCP; enable the skill for the agent |
| Claude Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Claw Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| Cline | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| CodeArts Desktop | ⚠ | ⚠ | ⚠ | ⚠ | ✕ | paste | — |
| CodeBuddy Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| CodeWhale | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| Codex CLI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Command Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| Continue | ✅ | ⚠ | ✅ | ✅ | ✅ | ✅ | — |
| Copilot CLI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| VS Code Copilot Chat | ✅ | ✅ | ✅ | ✅ | ✕ | ✅ | — |
| Crush | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 |
| Cursor | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 (IDE chats, CLI tool output) |
| DeepSeek Harness | ✅ | ✅ | ✅ | ✅ | ✕ | ✅ | zstd |
| Devin CLI | ✅ | ✅ | ✅ | ✕ | ✅ | ✅ | sqlite3 |
| Doubao | ⚠ | ⚠ | ⚠ | ⚠ | ✕ | paste | — |
| Gemini CLI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| gajae-code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| Goose | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | deja goose |
| Grok Build | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 (grok-dev store) |
| Hermes | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 |
| JetBrains AI Assistant | ✅ | ⚠ | ⚠ | ⚠ | ✕ | paste | none |
| Junie | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| Kilo Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 for the CLI store |
| Kimchi Coding | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| Kimi Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Kiro | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 for the CLI database |
| MiniMax Code | ✅ | ✅ | ✅ | ✕ | ✅ | ✅ | the MiniMax Code CLI (`mcode`) for `deja resume` and `deja handoff --to mcode --exec`; `sqlite3` for the session's workspace |
| MiMo-Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 |
| Muse Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| TeleAgent | ⚠ | ⚠ | ⚠ | ⚠ | ✕ | paste | sqlite3 |
| Omnigent | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 |
| omp (Oh My Pi) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| OpenClaw | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 (2026.8+ store); zstd for .zst archives and compressed events (2026.9.9+) |
| opencode | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 |
| Orca | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 |
| pi | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| prime-agent (PrimeIntellect) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Qoder | ? | ? | ? | ? | ? | paste | none |
| Qwen Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Reasonix | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | zstd for 1.x sessions |
| Roo Code | ✅ | ✕ | ✅ | ✅ | ✅ | paste | roo CLI (editor tasks reopen in the editor) |
| Senpi | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| TRAE CLI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| Windsurf / Devin Desktop | ✅ | ⚠ | ✅ | ✅ | ✕ | paste | none |
| ZCode | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 for the CLI database |
| Zed | ✅ | ✕ | ✅ | ✅ | ✕ | paste | sqlite3 + zstd |

✅ works &middot; — possible, not built yet &middot; ✕ the harness has no such mechanism &middot; ⚠ waiting on the harness itself &middot; ? not investigated

</details>
<!-- matrix:end -->

<details>
<summary><h3>Harnesses with a package of their own</h3></summary>

`deja install --auto` wires all integrations directly. Ecosystem-native packages are also published and interoperate without duplicate registration:

| Harness | Package | Install |
| --- | --- | --- |
| opencode | npm `opencode-deja` | `opencode plugin add opencode-deja` |
| DeepSeek Harness | npm `dsh-deja` | `dsh plugin --profile web add dsh-deja` |
| Zed | `deja-context-server` | Zed → Extensions → deja |
| Kimi Code | plugin `deja` | `/plugins install https://github.com/vshulcz/deja-vu` |
| Gemini CLI | extension `@vshulcz/deja` | `gemini extensions install https://github.com/vshulcz/deja-vu` |
| Antigravity | plugin `deja-vu` ([`antigravity-plugin/`](antigravity-plugin/)) | `agy plugin install deja-vu` |
| Codex CLI | plugin `deja-vu` | `codex plugin marketplace add https://github.com/vshulcz/deja-vu` then `codex plugin add deja-vu@deja-vu` |
| Grok Build | plugin `deja` | `grok plugin marketplace add vshulcz/deja-vu` then `grok plugin install deja` |
| OpenClaw | ClawHub &amp; npm `@vshulcz/openclaw-deja` | `openclaw plugins install clawhub:@vshulcz/openclaw-deja` |
| pi (and omp) | npm `@vshulcz/pi-deja` | `pi install npm:@vshulcz/pi-deja` |
| Hermes | memory provider `deja-memory` | `hermes plugins install vshulcz/deja-vu/extensions/hermes` |
| Magpie | npm `@vshulcz/magpie-deja` | `magpie plugin add @vshulcz/magpie-deja` |
| Orca | v2 `trusted-worker` plugin `deja` | `Orca → Plugins → extensions/orca` |
| CodeWhale | bundle `deja-vu` | `/plugin install extensions/codewhale` |
| VS Code / Cursor / Windsurf | status extension `vshulcz.deja-status` | `code --install-extension vshulcz.deja-status` |
| JetBrains IDEs | [JetBrains Marketplace](https://plugins.jetbrains.com/plugin/35998-deja-vu-cross-agent-ai-session-memory) | `idea installPlugins com.github.vshulcz.deja-vu` |
| Neovim | `lazy.nvim` &amp; CodeCompanion ([`extensions/nvim/`](extensions/nvim/)) | `{ "vshulcz/deja-vu", opts = {} }` |
| tmux | TPM popup &amp; status (`deja.tmux`) | `set -g @plugin 'vshulcz/deja-vu'` |
| Raycast | [Raycast Store](https://www.raycast.com/vshulcz/deja-vu) | `open raycast://extensions/vshulcz/deja-vu` |
| Spec Kit | Spec Kit extension | `specify extension add deja-vu --from https://github.com/vshulcz/deja-vu/releases/latest/download/deja-spec-kit.zip` |
| CC Switch | 1-click import (`ccswitch://`) | [Add MCP to CC Switch](ccswitch://v1/import?resource=mcp&apps=claude,codex,gemini,opencode&config=eyJtY3BTZXJ2ZXJzIjp7ImRlamEiOnsiY29tbWFuZCI6Im5weCIsImFyZ3MiOlsiLXkiLCJAdnNodWxjei9kZWphLXZ1Iiwic2VydmUiXX19fQ==) |

Standalone agent skills (`npx skills add https://github.com/vshulcz/deja-vu --skill deja-search`, `openclaw skills install @vshulcz/deja-search`, `hermes skills install vshulcz/deja-vu/skills/deja-search`) drive the installed `deja` binary.

</details>

## Semantic recall (optional)

Point `deja embed` at a local Ollama, LM Studio, or OpenAI-compatible embeddings endpoint with `DEJA_EMBED_URL` to enable hybrid vector reranking on top of BM25. Without a configured or reachable endpoint, lexical retrieval and MCP recall operate normally.

<details>
<summary>Endpoint environment variables, instruction prefixes, and sidecar storage</summary>

```sh
export DEJA_EMBED_URL='https://api.openai.com/v1/embeddings'
export DEJA_EMBED_MODEL='text-embedding-3-small'
export OPENAI_API_KEY='sk-...'
deja embed
```

When `DEJA_EMBED_URL` is unset, `deja embed` probes `localhost:11434` and `localhost:1234` unless `DEJA_EMBED_OFF=1` or `DEJA_EMBED_URL=off`. Use `DEJA_EMBED_KEY` for custom authenticated endpoints (`OPENAI_API_KEY` is only sent to `https://api.openai.com`). Prefix models accept `DEJA_EMBED_QUERY_PREFIX` and `DEJA_EMBED_PASSAGE_PREFIX`.

Vectors live beside `index.db` in `.vectors.bin`. Float32 vectors cost roughly 4 MB per 1k messages for a 1,024 dimension model. Redacted text only (truncated to ~2k chars) is sent during embedding.

</details>

## Benchmarks

88.9% hit@1 on the 470-question LongMemEval-S cleaned set (`88.2% hit@1`, `97.2% R@5` on all 500 questions), LoCoMo `71.9% hit@1`, `58%` token reduction on repeated repository tasks, and `0.7–0.8 ms` in-process lookups (`deja bench recall`). Reproducible drivers ship in the repository ([benchmarks guide](https://vshulcz.github.io/deja-vu/guide/benchmarks.html)).

```sh
deja bench recall     # 100-query bilingual ranking regression gate
deja bench context    # 30 seeded task chains + negative controls
deja bench block      # compaction & session-start conclusion survival
deja bench prompt     # per-prompt trigger precision/false-positive suite
deja bench ingest     # incremental append, rewrite, and rename cost
deja bench read       # SQLite store parser scaling benchmark
```

<details>
<summary>Measurements and architectural comparison</summary>

- **LongMemEval-S / LoCoMo:** Checked-in JSON artifacts under [`docs/benchmarks/`](docs/benchmarks/) record `88.9% hit@1` (470-question), `88.2% hit@1` / `97.2% R@5` (500-question), and LoCoMo `71.9% hit@1`.
- **Task token cost (`Bench` A/B):** 53,558 vs 126,222 tokens without memory; 52,815 vs 103,443 in alternated 11-run trials (`58%` fewer tokens).
- **Measured store latency (2,419–2,754 sessions, 179k–358k messages, 1.9–5.7 GB):** 0.7–0.8 ms median in-process lookup (`~15 ms` on LongMemEval-S haystacks), `~0.2–0.25 s` CLI end-to-end (including store freshness check), `~50 ms` no-op freshness check, `4%` index footprint (232 MB on 5.7 GB; 185 MB compressed on 19k sessions).

| Model | History before install | Capture step | Runtime dependency | File recovery |
| --- | --- | --- | --- | --- |
| **deja-vu** (transcript index) | Full existing stores across 52 harnesses | None | Single Go binary | `deja restore <path>` |
| Record-forward MCP servers | Starts empty from install | Explicit writes / observer hooks | Background worker / LLM calls | No |
| Raw transcript grep | Full logs | None | Manual search, high noise | No |

Details in the [comparison methodology](https://vshulcz.github.io/deja-vu/guide/compare.html).

</details>

## Configuration & FAQ

<details>
<summary><b>Configuration files under ~/.config/deja</b></summary>

- `policy.json` (`DEJA_POLICY_FILE`): origin activation rules (`activations` for `search`/`mcp`/`auto` across `local`/`imported`/`repo`), `ignore` path globs, `auto_index`, `search_only`.
- `exclude`: per-line project names, path patterns, or `harness:<name>` stores to skip (`DEJA_EXCLUDE_PROJECTS`, `DEJA_EXCLUDE_HARNESSES`).
- `projects`: `<path> = <name>` mappings unifying multiple worktrees under one project.
- `rules.md`: standing instructions synced across installed agent rules files via `deja rules sync`.
- Hook verbosity: `DEJA_RECALL=safe` (default, 2 KB / 3 sessions), `aggressive` (4 KB / 6 sessions), or `off`.

</details>

<details>
<summary><b>Multi-checkout projects & full uninstall</b></summary>

Group checkouts in `~/.config/deja/projects` (`~/work/repo = work`) and run `deja index --rebuild`. To remove all state and hooks:

```sh
deja uninstall --all
rm -rf ~/.cache/deja ~/.local/share/deja ~/.config/deja
```

</details>

## Documentation

- [Getting started](https://vshulcz.github.io/deja-vu/guide/getting-started.html) · [Architecture](docs/ARCHITECTURE.md) · [CLI & configuration reference](https://vshulcz.github.io/deja-vu/guide/commands.html)
- [Compaction recovery](docs/compaction.md) · [Security model](docs/SECURITY-MODEL.md) · [Session format registry](https://vshulcz.github.io/deja-vu/registry/README.html)
- [Where sessions are stored](https://vshulcz.github.io/deja-vu/guide/where-sessions-are-stored.html) · [Benchmarks](https://vshulcz.github.io/deja-vu/guide/benchmarks.html)

## Contributing & Support

Run `make build test lint` before opening a pull request; see [CONTRIBUTING.md](CONTRIBUTING.md) and [ROADMAP.md](ROADMAP.md). Adding a new harness starts at [`docs/ARCHITECTURE.md#source-parsers`](docs/ARCHITECTURE.md#source-parsers).

Report bugs in [GitHub Issues](https://github.com/vshulcz/deja-vu/issues) and security issues via [SECURITY.md](SECURITY.md).

MIT © [Vladislav Shulcz](https://github.com/vshulcz)
