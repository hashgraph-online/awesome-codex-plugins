<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/vshulcz/deja-vu/main/assets/logo-dark.svg">
    <img src="https://raw.githubusercontent.com/vshulcz/deja-vu/main/assets/logo.svg" width="280" alt="deja-vu">
  </picture>
</p>

<p align="center"><b>Your coding agents stop re-debugging what you already fixed.</b></p>

<p align="center">Claude Code, Codex, Cursor, OpenClaw, Gemini CLI, OpenCode, Hermes and 36 more agents already save every session to disk.<br>
deja indexes all of it locally and hands the relevant history back over MCP and hooks — no LLM, one Go binary.</p>

<p align="center">English | <a href="docs/readme/README.zh.md">简体中文</a> | <a href="docs/readme/README.zh-TW.md">繁體中文</a> | <a href="docs/readme/README.ja.md">日本語</a> | <a href="docs/readme/README.ko.md">한국어</a> | <a href="docs/readme/README.es.md">Español</a> | <a href="docs/readme/README.pt.md">Português</a> | <a href="docs/readme/README.fr.md">Français</a> | <a href="docs/readme/README.de.md">Deutsch</a> | <a href="docs/readme/README.ru.md">Русский</a> | <a href="docs/readme/README.tr.md">Türkçe</a> | <a href="docs/readme/README.hi.md">हिन्दी</a></p>

<p align="center">
  <a href="https://trendshift.io/repositories/83640"><img src="https://trendshift.io/api/badge/trendshift/repositories/83640/daily?language=Go" alt="#1 Go Repository Of The Day" style="width: 250px; height: 55px;" width="250" height="55"></a>
</p>

<p align="center">
  <a href="https://github.com/vshulcz/deja-vu/stargazers"><img src="https://img.shields.io/github/stars/vshulcz/deja-vu?style=flat&color=f59e0b" alt="GitHub Stars"></a>
  <a href="https://github.com/vshulcz/deja-vu/actions/workflows/ci.yml"><img src="https://github.com/vshulcz/deja-vu/actions/workflows/ci.yml/badge.svg?branch=main&event=push" alt="CI"></a>
  <a href="https://github.com/vshulcz/deja-vu/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/coverage-88%25-brightgreen" alt="Coverage"></a>
  <a href="https://github.com/vshulcz/deja-vu/releases"><img src="https://img.shields.io/github/v/release/vshulcz/deja-vu" alt="Release"></a>
  <a href="https://mcptoplist.com/server/io.github.vshulcz%2Fdeja-vu"><img src="https://mcptoplist.com/badge/io.github.vshulcz%2Fdeja-vu.svg" alt="MCP Toplist"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
</p>

<p align="center"><a href="https://vshulcz.github.io/deja-vu/"><b>Website &amp; interactive search</b></a> &middot; <a href="https://vshulcz.github.io/deja-vu/view/"><b>Live browser demo</b></a> &middot; <a href="https://vshulcz.github.io/deja-vu/guide/getting-started.html">Docs</a> &middot; <a href="https://vshulcz.github.io/deja-vu/guide/benchmarks.html">Benchmarks</a> &middot; <a href="https://vshulcz.github.io/deja-vu/guide/compare.html">How it compares</a> &middot; <a href="docs/INTEGRATING.md">Building it into your tool</a></p>

<p align="center"><img src="https://raw.githubusercontent.com/vshulcz/deja-vu/main/assets/demo.gif" width="720" alt="The same question put to the same agent twice: without memory it has no record of it, with deja it answers with the decision from eight months earlier"></p>

```sh
curl -fsSL https://raw.githubusercontent.com/vshulcz/deja-vu/main/install.sh | sh
deja install --auto
```

<p align="center"><sub>Or with Homebrew: <code>brew install deja-vu &amp;&amp; deja install --auto</code> &middot; Claude Code plugin: <code>claude plugin marketplace add vshulcz/deja-vu &amp;&amp; claude plugin install deja-vu@deja-vu</code> &middot; Agent Skills: <code>npx skills add vshulcz/deja-vu</code><br><a href="#install">Windows (Scoop / winget), Codex, OpenCode, OpenClaw and more</a> &middot; Try without installing: <code>npx @vshulcz/deja-vu sources</code> &middot; <a href="https://vshulcz.github.io/deja-vu/view/">Live demo →</a></sub></p>

<table align="center">
<tr>
<td align="center" width="33%">Recall<br><b>97.2% R@5</b> on LongMemEval-S<br><sub>MemPalace publishes 96.6%, agentmemory 95.2%</sub></td>
<td align="center" width="33%">Tokens<br><b>half the tokens</b> of agentmemory<br><sub>on a task this machine had already solved</sub></td>
<td align="center" width="33%">Index time<br><b>13.6 s</b> to index 19,195 sessions<br><sub>the next of seven tools takes 72 s</sub></td>
</tr>
</table>

<p align="center"><sub>Every driver, corpus and scoring rule is in this repository: <a href="https://vshulcz.github.io/deja-vu/guide/day-zero.html">head-to-head</a> &middot; <a href="https://vshulcz.github.io/deja-vu/guide/benchmarks.html">all benchmark runs</a></sub></p>

## Search it yourself

`deja` with no arguments opens a terminal search across every agent's history — starting with
the sessions behind your uncommitted changes, then recent work in the current project.

<p align="center"><img src="https://raw.githubusercontent.com/vshulcz/deja-vu/main/assets/tui.gif" width="720" alt="Typing a search in the deja screen, reading the session it found, and continuing that session in another agent"></p>

- **Navigate:** `↑↓` picks a session, `↵` opens at the match, `/` searches inside a session, `]` `[` jump between turns, `^s` toggles date/relevance sort (`deja search --sort date`).
- **Filter:** by agent (`codex:`), time (`today`, `yesterday`, `week`, `month`), or project (`in:<project>`).
- **Resume or hand off:** `r` reopens the session in its native agent; `o` continues it in another agent with its goal, decisions and open work.
- **Recover deleted chats:** `tab` switches between this project, all projects, and **Deleted** (sessions an agent purged that deja still holds); `R` restores one, `D` deletes (`deja delete <id>`), `?` lists all keys.

Prefer a browser? `deja view` exports the store — sessions, the recall audit trail, and promoted notes — into one local HTML file ([try the live demo](https://vshulcz.github.io/deja-vu/view/)). With `DEJA_TUI=0` (or `deja brief`), `deja` prints a plain-text summary.

## Highlights

- **Starts full on day one.** Months of existing transcripts across all [forty-three agents](#supported-harnesses) are searchable immediately — fix a bug in Codex and Claude Code, Cursor or OpenCode recalls it.
- **Automatic recall via hooks & MCP.** Surfaces prior sessions at session start, before a file edit or command runs, and when a command fails.
- **Survives compaction.** Over 43 measured compactions, summaries kept 77% of decisions and 0.2% of commands; deja hands back the rest ([how](docs/compaction.md)).
- **Indexes code changes, not just chat.** Tracks opened files, commands with exit codes, and exact `Edit` spans (`deja blame <file>:<line>`, `deja restore <path>`).
- **Tracks decision lifecycle & staleness.** `deja promote <id> --state rejected` marks a reverted approach so later hits warn why it was dropped (`--state accepted` takes the mark back), and hits report when files touched by a session have changed since.
- **Travels with the repository.** `deja repo add` commits the decisions and dead ends you pick into `.deja/memory.jsonl`; a teammate's agent recalls them after a clone ([repo memory](#memory-in-the-repository)).
- **Local and private by default.** Zero LLM calls, no cloud account, and automatic credential redaction at index time ([privacy](#privacy)).

### Your own work, wrapped

`deja stats --card` draws your yearly agent activity in the terminal or writes an SVG for your GitHub profile ([convert to PNG in browser](https://vshulcz.github.io/deja-vu/card/)).

<p align="center"><img src="https://raw.githubusercontent.com/vshulcz/deja-vu/main/docs/assets/stats-card-demo.svg" width="600" alt="deja stats card: a year of agent sessions as a heatmap, the agents they came from, and the longest one"></p>

## Install

`install.sh` places the `deja` binary in `~/.local/bin`, and `deja install --auto` wires MCP recall and hooks into every detected agent and builds the initial index (~10s).

<p align="center"><img src="https://raw.githubusercontent.com/vshulcz/deja-vu/main/assets/banner.png" width="700" alt="What deja prints after the first index: the mark, the agents it found, and a query taken from your own history"></p>

Open a new session in any wired agent and it already knows what you solved in that repository — or ask it directly (`have we dealt with jwt refresh rotation before?`).

<details>
<summary><b>Homebrew, Windows (Scoop / winget), npm, plugin marketplaces, and binary-only setup</b></summary>

`brew install deja-vu`, `nix run github:numtide/llm-agents.nix#deja-vu`, `go install github.com/vshulcz/deja-vu/cmd/deja@latest`,
or `npx @vshulcz/deja-vu "query"` to try it without installing anything. Desktop apps that
take MCP servers as bundles can open the `.mcpb` from the
[latest release](https://github.com/vshulcz/deja-vu/releases/latest); it carries the binary.

Codex CLI, opencode, Claude Code, Qwen and OpenClaw can also install the plugin
bundle directly from their own marketplaces or registries (see
[Harnesses with a package of their own](#harnesses-with-a-package-of-their-own),
plus [`cursor-plugin/`](cursor-plugin/) for Cursor and [`antigravity-plugin/`](antigravity-plugin/) for Antigravity). Copilot CLI installs the
marketplace bundle too, though it takes only the skill there — use
`deja install copilot-auto` for hooks and MCP:

```sh
codex plugin marketplace add https://github.com/vshulcz/deja-vu && codex plugin add deja-vu@deja-vu
opencode plugin opencode-deja
claude plugin marketplace add vshulcz/deja-vu && claude plugin install deja-vu@deja-vu
```

On Windows the install script exits with `unsupported OS` — it is a shell script. Use
Scoop, from the main bucket every Scoop install already has, or winget, which ships with Windows:

```powershell
scoop install deja-vu
winget install vshulcz.deja-vu
```

Or take `deja-vu_<version>_windows_amd64.zip` from the
[latest release](https://github.com/vshulcz/deja-vu/releases/latest) and put `deja.exe` on
your `PATH`, e.g. in `%USERPROFILE%\.local\bin`.

The binary alone is a complete install for searching: index, search, `show`, `ctx`, `blame`,
`--json` and redaction need nothing else. `deja install` is what wires MCP into your agents
and turns on session-start recall — worth having, and optional. On a binary-only setup
`deja doctor` reports every MCP target as `config missing`, or `not-wired` where the agent
is installed, which is that setup working as intended. `deja warmup` also leaves a skill at `~/.agents/skills/deja-search/SKILL.md`
that teaches an agent the CLI contract — `deja recall`, `ctx`, `blame`, how to read the
recall page and ask for the next one — so it knows history is searchable without MCP. The copy in the repo is
[`skills/deja-search/SKILL.md`](skills/deja-search/SKILL.md).

`deja install --all` is `--auto` without the session-start recall: agents answer from memory
when they decide to call it, rather than starting each session with it. The
[agent setup guide](https://vshulcz.github.io/deja-vu/guide/agents.html) covers what each
harness supports, aider's read-only context file, and the Windows `cmd /c deja mcp` wrapper.

</details>

<details>
<summary>What gets written into each agent's own guidance file</summary>

Install also writes user-level guidance for the harnesses it detects: Claude Code, Codex, opencode, Gemini CLI, Antigravity, Qwen, Kimi Code, pi, Senpi, Copilot, VS Code Copilot Chat, Goose, OpenClaw, Hermes, Roo Code, omp, Amp, prime-agent, DeepSeek Harness, Continue, Crush, CodeBuddy Code, WorkBuddy, Zed, TRAE CLI, TRAE IDE, Muse Code, CodeWhale, ZCode and Junie each get it in their own guidance file (or under the configured `XDG_CONFIG_HOME`). Re-run rewrites deja's skill or marked block without changing surrounding user content. Use `deja install --all --no-guidance` to opt out; Grok Build and Devin CLI get the shared skill in `~/.agents/skills`, which is what they read; the `~/.grok/GROK.md` written beside it is for the unrelated community CLI that shares that directory. Cursor has no user-level instructions file, so it gets the shared skill in `~/.agents/skills` — one of the four places Cursor reads skills from — read only when something looks relevant rather than every session. Kilo Code, gajae-code, Kimchi, Command Code, Cherry Studio and Reasonix get the skill, MiniMax Code gets it inside the plugin package, and Kiro the skill and a steering file, from their own install target.

</details>

## Memory in the repository

Sync moves history between your own machines. To hand the people you work with the
few things your agents learned the hard way, put them in the repository:

```text
$ deja repo candidates
4cd7e7bb9c rejected Reverted the retry with jitter: it broke idempotency because the sender re-signs each attempt with a new delivery id.  (session s1, claude 2026-08-03)
$ deja repo add 4cd7e7bb9c
added 1 entry to .deja/memory.jsonl
nothing is committed: review with `git diff .deja/` and commit it like code
```

Candidates come from this project's history in every agent: promoted and remembered
notes, reversals reported in a session, and what sessions settled. Nothing is written
until you pick, every entry is redacted on the way in, and one that still matches a secret
rule is refused. The file is JSON lines sorted by a content hash, with a
`merge=union` attribute beside it, so parallel additions merge; deleting a line removes
an entry. After a clone, the entries come back at session start and in recall, in any agent
deja is wired into, marked as from the repository and framed as untrusted like the rest.
`{"activations":{"auto":{"repo":false}}}` in the trust policy keeps them out of the hooks.
[More](https://vshulcz.github.io/deja-vu/guide/repo-memory.html).

## Privacy

Indexing and search are local. The network is used only by `deja update`, `deja sync ssh`,
the version check in `deja doctor`, `deja embed` against an endpoint you configure (and,
once it has built the semantic sidecar, each search, which sends the query to that
endpoint), and a once-a-day look at the latest release from an interactive command. That look sends no
session data; `DEJA_OFFLINE=1` turns it off, and so does `DEJA_NO_UPDATE_NOTICE` set to any
value, which also hides the note a new version prints on its first run.

Credentials are stripped as the index is built: cloud and provider keys, tokens and JWTs,
PEM blocks, passwords in URLs or stated in prose. Each becomes `[redacted:<kind>]` and the
text around it stays searchable. The source transcripts still hold them
([one machine had 84 in 42 sessions](https://vshulcz.github.io/deja-vu/guide/credentials-in-transcripts.html)):
`deja secrets` names those sessions without printing a value, and `deja secrets --scrub`
rewrites the ones it can, keeping the original beside the file.

`deja forget` drops sessions and keeps them dropped across rebuilds. `~/.config/deja/exclude`
skips a project per line, or a whole store with `harness:opencode`. The
[security model](docs/SECURITY-MODEL.md) has the data flows and what redaction cannot catch.

## CLI

Bare `deja` in a terminal opens [the search screen](#search-it-yourself). With a query,
or any command below, it prints and exits:

```text
$ deja "jwt refresh token"
[claude] api        · Jul 8 · 8f31c0a9 — 2 matches
  login started failing after refresh token rotation; jwt kid mismatch in tests
  fixed by reloading jwks cache after rotateKey and adding a clock-skew test
[codex]  web        · Jul 1 · b77d91e2 — 1 match
  refresh token cookie needed SameSite=Lax in local callback flow
```

**Ask your history**

| Command | What it does |
| --- | --- |
| `deja <query>` | Search every history. Multi-word is AND and quoted phrases require contiguous text; a query with no exact match then tries word forms and close spellings, which is where a substring reaches its word (`code` finds `opencode`). `--sort date` lists the newest match first. |
| `deja` | In a terminal, the full-screen search above. `deja brief` prints the text summary instead: today's sessions, what deja served, recent work and a search to try. |
| `deja wip` | What the last session in this directory was doing: the task, what it settled, the files in flight, the last command and whether it failed — derived from the transcript, not from a note someone remembered to write. |
| `deja blame <path>[:line]` | Which sessions discussed a file, what was decided, and why. With a line: the commit that last changed it, and the session that wrote that line or the text the commit replaced. `--attribution` prints the line answer alone, as JSON with `--json`, and `--git-note` records it in `refs/notes/deja`. |
| `deja origin [rev\|range]` | Which session and user turn produced a commit or commit range, matched against recorded edit spans (`attributed`, `uncertain`, or `unknown`). |
| `deja review [rev\|range]` | Prior sessions and settled notes (`.deja/notes.jsonl` and personal notes) for the files changed in a working-tree diff, commit, or range. |
| `deja files <topic>` | The other direction: which files the work on a subject actually touched. |
| `deja how <tool>` | How this machine actually runs a thing, with the real flags, from what agents ran before. |
| `deja fix <error>` | What this machine ran after that same error before, when the error did not come back. Never a merge, a force push or a deletion. |
| `deja friction` | Errors that hit three or more separate sessions, with the harnesses named. |

When the first word of a bare query has at least four characters and is one
edit from a command name, deja names that command on stderr and then searches
as usual. `deja search <query>` skips the suggestion.

<details>
<summary>Using what it finds, and moving it between machines</summary>

**Use what it finds**

| Command | What it does |
| --- | --- |
| `deja ctx <query>` | Markdown digest of the best match, with the code it changed, ready to pipe into a prompt. |
| `deja recall <words>` | The page the MCP recall tool gives an agent: about 4 KB, this project first (`DEJA_RECALL_GLOBAL=1` ranks every project the same). For skills and scripts that run deja through the shell. |
| `deja resume <id>` | Reopen a found session in its native harness. `--app` opens a Codex session in the ChatGPT desktop app. |
| `deja restore <path>` | Hand back a span an agent replaced, from the `old_string` its edit recorded. Never writes over the original. |
| `deja promote <id>` | Distill a session into a curated note with provenance, tags and a lifecycle state (`--repo` writes to `<repo>/.deja/notes.jsonl` for the team). Notes outrank raw transcripts. |
| `deja share <id>` | A sanitized session digest for a colleague, with secrets already scrubbed. |

**Move it and check it**

| Command | What it does |
| --- | --- |
| `deja sync export/import/ssh` | Move memory between machines. Watermarked, append-only, idempotent. |
| `deja repo candidates`, `deja repo add <id>` | Move memory between people: write the decisions and dropped approaches you pick into the repository's `.deja/memory.jsonl`, redacted, for review and commit. Whoever clones it gets them in recall. |
| `deja view` | Your whole memory as one local HTML file ([live demo](https://vshulcz.github.io/deja-vu/view/)). No server, and the file never leaves the machine. |
| `deja stats` | Your agent work, wrapped. `--card` draws it in the terminal, `--card <file>.svg` writes one for a profile, `--html` a browsable timeline. |
| `deja secrets [--scrub]` | Which sessions' source transcripts carry credentials, and what kind. Never prints a value. `--scrub` rewrites the ones it can, original kept beside the file. |
| `deja rules [sync]` | Keep your standing rules in `~/.config/deja/rules.md`; `sync` copies them as a marked block into every installed agent's global rules file. |
| `deja rules candidates [--json] [--limit n] [--since 90d] [--project name] [--repo]` | The turns where you corrected an agent, across every tool (or scoped to `--repo` / `--project`), numbered with their session. Ask your agent to suggest rules and it groups them; nothing is written until you pick. |
| `deja doctor [--deep]` | Self-diagnosis, and with `--deep`, proof of the index against the sources. |
| `deja mcp` | The stdio MCP server, which is what `deja install` wires in. |

</details>

Full reference: [commands](https://vshulcz.github.io/deja-vu/guide/commands.html) and
[JSON output](docs/json-output.md).

### MCP tools

The server exposes one tool, `deja`, with a `mode`; `deja install` wires it in. One tool
costs 477 tokens of definitions a turn, against 8,283 for the largest of the seven servers
measured in [day zero](https://vshulcz.github.io/deja-vu/guide/day-zero.html). The six
older tool names (`recall`, `recall_context`, `blame`, `fix`, `how`, `remember`) still answer.
`deja mcp --context-search` is a separate server with a single `context_search` tool, for
Qwen Code's External Context MCP Profile v1 ([Qwen page](docs/registry/qwen.md)).

<details>
<summary>Arguments and return shapes</summary>

| Tool | Arguments | Returns |
| --- | --- | --- |
| `deja` | `mode`, `q`, `harness?`, `project?`, `limit?` | Depends on the mode, below. |

`q` carries whatever the mode asks about. The per-mode names below are still
accepted; they are no longer declared, because the schema is read every turn
whether or not the tool is called.

| Mode | `q` is | Also reads | Returns |
| --- | --- | --- | --- |
| `recall` | 1-3 exact terms: a file path, an error string, a flag or identifier | `harness?`, `limit?`, `offset?` | Dense matching snippets, capped at 4KB. |
| `context` | the same as recall | `harness?` | Markdown digest of the best-matching session, with the code it changed. |
| `blame` | a file path | `harness?`, `project?`, `since?`, `limit?`, `all?` | Sessions that discussed a file. |
| `fix` | the failing output, verbatim | `limit?` | What this machine ran, or changed, after that same error before. |
| `how` | the tool or target, e.g. `go test` | `project?`, `limit?` | The real invocation, from what agents ran here. |
| `orient` | nothing — it asks about the project | `project?`, `limit?` | The commands past sessions ran here and the files they worked in. |
| `remember` | one durable fact or decision | `project?`, `tags?` | Stores a durable decision for later recall. `project` `repo:` (or `repo:rejected`, `repo:gotcha`) writes it into this repository's `.deja/memory.jsonl` instead, uncommitted. |
| `handoff` | a session id or harness name; empty for the newest session here | `harness?` | Another session's goal, standing instructions, latest conclusions, passed checks and where it stopped, to continue it. |

</details>

## Supported harnesses

<!-- matrix:start -->
aider &middot; Amp &middot; Antigravity &middot; Claude Code &middot; Cline &middot; Codex CLI &middot; Copilot CLI &middot; VS Code Copilot Chat &middot; Cursor &middot; DeepSeek Harness &middot; Gemini CLI &middot; Goose &middot; Grok Build &middot; Hermes &middot; Kimi Code &middot; omp (Oh My Pi) &middot; OpenClaw &middot; opencode &middot; Continue &middot; Crush &middot; pi &middot; prime-agent (PrimeIntellect) &middot; Qwen Code &middot; Cherry Studio &middot; Senpi &middot; gajae-code &middot; Kimchi Coding &middot; Command Code &middot; ZCode &middot; Kiro &middot; Kilo Code &middot; Roo Code &middot; Zed &middot; Devin CLI &middot; CodeWhale &middot; Junie &middot; JetBrains AI Assistant &middot; Windsurf / Devin Desktop &middot; CodeBuddy Code &middot; Reasonix &middot; TRAE CLI &middot; Muse Code &middot; MiniMax Code.

<details>
<summary>What each one supports</summary>

| Harness | MCP recall | Auto-recall | Skill | Command | Resume | Handoff | Needs |
| --- | :-: | :-: | :-: | :-: | :-: | :-: | --- |
| aider | ⚠ | ✅ | ✕ | ⚠ | ✕ | ✅ | deja aider |
| Amp | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | threads from 0.0.1774963753 on live on ampcode.com; deja reads those its plugin has written out, and older local ones |
| Antigravity | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Claude Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Cline | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Codex CLI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Copilot CLI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| VS Code Copilot Chat | ✅ | ✅ | ✅ | ✅ | ✕ | ✅ | — |
| Cursor | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 (IDE chats, CLI tool output) |
| DeepSeek Harness | ✅ | ✅ | ✅ | ✅ | ✕ | ✅ | zstd |
| Gemini CLI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Goose | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | deja goose |
| Grok Build | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 (grok-dev store) |
| Hermes | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 |
| Kimi Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| omp (Oh My Pi) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| OpenClaw | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 (2026.8+ store); zstd for .zst archives and compressed events (2026.9.9+) |
| opencode | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 |
| Continue | ✅ | ⚠ | ✅ | ✅ | ✅ | ✅ | — |
| Crush | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 |
| pi | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| prime-agent (PrimeIntellect) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Qwen Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Cherry Studio | ✅ | ✅ | ✅ | ✕ | ✕ | paste | import the server once in Settings -> MCP; enable the skill for the agent |
| Senpi | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| gajae-code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| Kimchi Coding | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| Command Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| ZCode | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 for the CLI database |
| Kiro | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 for the CLI database |
| Kilo Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | sqlite3 for the CLI store |
| Roo Code | ✅ | ✕ | ✅ | ✅ | ✅ | paste | roo CLI (editor tasks reopen in the editor) |
| Zed | ✅ | ✕ | ✅ | ✅ | ✕ | paste | sqlite3 + zstd |
| Devin CLI | ✅ | ✅ | ✅ | ✕ | ✅ | ✅ | sqlite3 |
| CodeWhale | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| Junie | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| JetBrains AI Assistant | ✅ | ⚠ | ⚠ | ⚠ | ✕ | paste | none |
| Windsurf / Devin Desktop | ✅ | ⚠ | ✅ | ✅ | ✕ | paste | none |
| CodeBuddy Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| Reasonix | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | zstd for 1.x sessions |
| TRAE CLI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| Muse Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| MiniMax Code | ✅ | ✅ | ✅ | ✕ | ✅ | ✅ | the MiniMax Code CLI (`mcode`) for `deja resume` and `deja handoff --to mcode --exec`; `sqlite3` for the session's workspace |

✅ works &middot; — possible, not built yet &middot; ✕ the harness has no such mechanism &middot; ⚠ waiting on the harness itself &middot; ? not investigated

</details>
<!-- matrix:end -->

TRAE IDE is wired, not read: its chats are in an encrypted database. `deja install trae-ide`
adds the MCP server and the skill, and `trae-ide-auto` adds hooks, which TRAE IDE runs only
after you turn them on in Settings > Hooks.

Custom store locations go through `DEJA_*_ROOT` variables, and each agent's own relocation
variable is honored too. The
[session format registry](https://vshulcz.github.io/deja-vu/registry/README.html) documents
the observed paths, record schemas and role mapping per harness, with synthetic fixtures
keeping those descriptions checked against the parsers.

### Harnesses with a package of their own

`deja install --auto` wires every one of these like every other harness, and
that stays the shortest path. They also have a package in their own ecosystem,
for people who install extensions there rather than from a CLI:

| Harness | Package | Install |
| --- | --- | --- |
| opencode | npm `opencode-deja` | `opencode plugin opencode-deja` |
| DeepSeek Harness | npm `dsh-deja` | `dsh plugin --profile web add dsh-deja` |
| Zed | `deja-context-server` | Zed → Extensions → deja |
| Kimi Code | plugin `deja` | `/plugins install https://github.com/vshulcz/deja-vu` |
| Gemini CLI | extension `@vshulcz/deja`, in the [Gemini CLI Extensions Gallery](https://geminicli.com/extensions/) | `gemini extensions install https://github.com/vshulcz/deja-vu` |
| Antigravity | plugin `deja-vu` ([`antigravity-plugin/`](antigravity-plugin/)) | `agy plugin install deja-vu` |
| Codex CLI | plugin `deja-vu` | `codex plugin marketplace add https://github.com/vshulcz/deja-vu` then `codex plugin add deja-vu@deja-vu` |
| Grok Build | plugin `deja` | `grok plugin marketplace add vshulcz/deja-vu` then `grok plugin install deja` |
| OpenClaw | ClawHub and npm `@vshulcz/openclaw-deja` | `openclaw plugins install clawhub:@vshulcz/openclaw-deja` |
| pi (and omp) | npm `@vshulcz/pi-deja` | `pi install npm:@vshulcz/pi-deja` |
| Hermes | memory provider `deja-memory`, in the Hermes plugin catalog | `hermes plugins install deja-memory`, or from GitHub: `hermes plugins install vshulcz/deja-vu/extensions/hermes` |
| Magpie | npm `@vshulcz/magpie-deja` | `magpie plugin add @vshulcz/magpie-deja` |
| VS Code / Cursor / Windsurf | status bar extension `vshulcz.deja-status` | `code --install-extension vshulcz.deja-status` |
| Raycast | Raycast extension `deja-vu` | `cd extensions/raycast && npm install && npx ray develop` |
| CC Switch | 1-click MCP &amp; Skill Repo import (`ccswitch://`) | [Add MCP to CC Switch](ccswitch://v1/import?resource=mcp&apps=claude,codex,gemini,opencode&config=eyJtY3BTZXJ2ZXJzIjp7ImRlamEiOnsiY29tbWFuZCI6Im5weCIsImFyZ3MiOlsiLXkiLCJAdnNodWxjei9kZWphLXZ1Iiwic2VydmUiXX19fQ==) · [Switching guide](https://vshulcz.github.io/deja-vu/guide/switch-agents-without-losing-context.html) |

Either path works alone, and both together double nothing: each package reads what
`deja install` already wrote and uses the deja you already have.

In a [Spec Kit](https://github.com/github/spec-kit) project, an extension adds
`/speckit.deja-vu.recall`, which searches past sessions for the feature before you
implement it:

```sh
specify extension add deja-vu --from https://github.com/vshulcz/deja-vu/releases/latest/download/deja-spec-kit.zip
```

The same search is also a skill, for any agent that loads a `SKILL.md`:

```sh
npx skills add https://github.com/vshulcz/deja-vu --skill deja-search   # skills CLI: Claude Code, Cursor, Goose, Copilot…
openclaw skills install @vshulcz/deja-search                            # ClawHub
hermes skills install vshulcz/deja-vu/skills/deja-search                # Hermes
```

The skill drives the `deja` binary from the install step above; it does not bundle one.

## Semantic recall (optional)

Point `deja embed` at a local Ollama, LM Studio or OpenAI-compatible endpoint with
`DEJA_EMBED_URL` and rephrased queries still hit. Without a reachable runtime, lexical
search and MCP recall continue unchanged. OpenAI Platform works with its standard key:

```sh
export OPENAI_API_KEY='sk-...'
export DEJA_EMBED_URL='https://api.openai.com/v1/embeddings'
export DEJA_EMBED_MODEL='text-embedding-3-small'
deja embed
```

<details>
<summary>Local runtimes, other endpoints, and what vectors cost</summary>

With no `DEJA_EMBED_URL` set, deja probes `localhost:11434` and `localhost:1234`,
so a machine already running Ollama or LM Studio is picked up without being asked.
`DEJA_EMBED_OFF=1`, or `DEJA_EMBED_URL=off`, turns that probe off — any other
configured `DEJA_EMBED_URL` still wins.

For another authenticated OpenAI-compatible endpoint, set `DEJA_EMBED_KEY` explicitly:

```sh
export DEJA_EMBED_URL='https://example.com/v1/embeddings'
export DEJA_EMBED_MODEL='embedding-model'
export DEJA_EMBED_KEY='...'
deja embed
```

`DEJA_EMBED_KEY` takes precedence. `OPENAI_API_KEY` is used automatically only for an
HTTPS `api.openai.com` URL; it is never implicitly sent to local or third-party endpoints.

Models trained with instruction prefixes, such as the multilingual E5 family, need them on
both sides. `DEJA_EMBED_QUERY_PREFIX` goes in front of every search query and
`DEJA_EMBED_PASSAGE_PREFIX` in front of every indexed text; both are empty by default:

```sh
export DEJA_EMBED_MODEL='multilingual-e5-small'
export DEJA_EMBED_QUERY_PREFIX='query: '
export DEJA_EMBED_PASSAGE_PREFIX='passage: '
deja embed
```

The passage prefix is part of the sidecar's model name, so changing it embeds everything
again, and search ignores vectors made with another model or prefix (it says so once).

The sidecar sits beside the index as `.vectors.bin`, not inside `index.db`. Float32 vectors
cost roughly 4 MB per 1k messages for a 1,024 dimension model. A remote endpoint receives
the redacted indexed text, truncated to about 2k characters, but never raw source files.
With Ollama or LM Studio, embedding stays local and needs no key.

</details>

## Proof

Millisecond lookups, and on LongMemEval-S 88.9% hit@1 (470-question cleaned set) and 88.2% hit@1 on all 500 questions;
on LoCoMo retrieval, 71.9% hit@1. On a task this machine had already solved, 58% fewer
tokens: eleven runs an arm, 53,558 against 126,222 with nothing wired, and 52,815 against
103,443 on a later build with the arms alternated. Both retrieval harnesses ship in this repo
and run on the public datasets in minutes: [benchmarks](https://vshulcz.github.io/deja-vu/guide/benchmarks.html) ·
[what one task costs](https://vshulcz.github.io/deja-vu/guide/day-zero.html).

The rest is measured by `deja bench`:

```sh
deja bench recall     # ranking floor: 100 queries, half Russian, CI fails if recall drops
deja bench context    # 30 seeded task chains plus five negative controls
deja bench block      # does the answer survive into what deja hands over
deja bench prompt     # what the per-prompt hook fires on, and what it fires on wrongly
deja bench ingest     # what an update costs: unchanged, a turn, a new transcript, a rename, a rewrite
deja bench read       # what it costs to read a database-backed store, and what one long value does to it
```

<details>
<summary>What the in-repo benches measure, and lookup cost on a real store</summary>

`bench block` asks the question the others cannot: with the right session in
hand, does the block carry what that session settled. Eight sessions discuss each
subject and one of them settles it, in the middle of its own transcript rather
than at the end — so the baseline arm, the newest turns of the top hit, scores
zero and an arm above zero had to choose.

| Arm | Carries the answer | Median tokens |
|---|---|---|
| `deja-block` (session-start block) | 1.00 | 665 |
| `deja-digest` (context digest) | 1.00 | 1656 |
| `newest-turn` (baseline) | 0.00 | 289 |
| `cold` | 0.00 | 0 |


The context experiment compares deja-recall against full-history, naive grep and cold
context. With the default seed:

| Arm | Median tokens | Median coverage | Negative-control tokens |
| --- | ---: | ---: | ---: |
| deja-recall | 1,096 | 1.00 | 0 |
| full-history | 80,547 | 1.00 | 78,145 |
| naive-grep | 273,238 | 1.00 | 0 |
| cold | 0 | 0.00 | 0 |

Same fact coverage as grepping the raw logs for about 250x fewer tokens, and about 70x
fewer than replaying the matched sessions in full, while injecting nothing on the chains
where no prior fact is relevant. The corpus generator and the relevance labels are
ordinary reviewed Go. Audit what "relevant" means before trusting any figure, ours
included.

Measured on a real store of 2,419 sessions and 179k messages, 1.9 GB of
transcripts:

| Measurement | Result |
| --- | --- |
| Lookup, in process | **0.7–0.8 ms** median (`deja bench recall`, 100 queries, half of them Russian), ~15 ms on the LongMemEval-S haystacks |
| `deja <query>`, end to end | ~0.2 s median on that store: process start, the freshness check over every store, ranking, printing |
| Freshness check alone | ~50 ms when nothing changed |
| Index size | 200 MB, ~10% of corpus |

The same store has since grown to 2,754 sessions, 358k messages and 5.7 GB.
A cold full build over it takes 71 s and writes a 232 MB index — 4% of the
corpus, because the share falls as transcripts repeat themselves — and the
end-to-end median is unchanged at 0.25 s. Since 0.23.2 records are compressed
from 256 bytes, which takes a 19k-session index from 277 to 185 MB.

The index is incremental. When a session file grows, only that file is re-read. When one is
rewritten, its new records are appended and the old ones zeroed in place. On a
40,000-session store a pass over 20 rewritten transcripts takes 1.7 s and peaks under 1 GB,
and a search for a word most sessions hold takes about a second.

</details>

## How it works

Local inverted index in `~/.cache/deja`: parse the JSONL and SQLite stores, redact
credentials, write an append-only `records.bin` plus token buckets, and track per-file state in
`manifest.gob` so repeat runs only ingest what changed. The MCP server, stats, share and
sync all read that one index. Details in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## FAQ

<details>
<summary><b>How is this different from the other memory tools?</b></summary>

| | deja | Memory platforms<br>(Mem0, Letta, memU) | Session search<br>(cass) |
| --- | :-: | :-: | :-: |
| Knows work from before you installed it | yes | no | yes |
| Capture step | none, the transcripts are the memory | the agent or your code writes facts | none |
| Needs an LLM or embedding key | no | yes | optional |
| Recalls without being asked | at session start and before a tool runs | no | no |

[engram](https://github.com/Gentleman-Programming/engram) is the strongest of the
record-forward tools and worth your time if that model fits you; it still starts empty and
knows only what an agent chose to save. The
[full comparison](https://vshulcz.github.io/deja-vu/guide/compare.html) covers 15 of them.

</details>

<details>
<summary><b>Will it slow my agent down?</b></summary>

A recall is a lexical lookup against a local index:
0.7–0.8 ms median, and nothing waits on a model. A hook adds the process start and a
freshness check over your stores on top of that: about 0.2 s end to end on a 1.9 GB
store. On an index of 19k sessions the per-prompt hook takes 107 ms at the median,
and a recall through `deja mcp` 85 ms.

</details>

<details>
<summary><b>Where is Claude Code session history stored, and can I search it?</b></summary>

Under `~/.claude/projects`, one JSONL file per session; Codex keeps `~/.codex/sessions`, Cursor a
SQLite `state.vscdb`. deja reads them all in place: bare `deja` opens a screen to search
and read them, `deja search` does it from a script, `deja last` lists the recent
sessions of every agent, and `deja view` opens the whole history as one local page. Paths
for each agent: [where sessions are stored](https://vshulcz.github.io/deja-vu/guide/where-sessions-are-stored.html).

</details>

<details>
<summary><b>My Claude Code session history disappeared. Is it gone?</b></summary>

Claude Code deletes transcripts older than 30 days (`cleanupPeriodDays` in `~/.claude/settings.json`), and `claude --resume` lists
only what is left. A session deja indexed before the cleanup stays searchable after the
file is gone, and the weekly note at session start says how many it kept, with an id
`deja resume <id> --write-back` puts back. Details: [session files on disk](https://vshulcz.github.io/deja-vu/guide/session-files-on-disk.html).

</details>

<details>
<summary><b>What files live in ~/.config/deja, and what can I set in them?</b></summary>

Under `~/.config/deja` (or `$XDG_CONFIG_HOME/deja`):

- **`policy.json`** (`DEJA_POLICY_FILE` moves it) — JSON object with four optional keys:
  - `"activations"`: per-surface origin rules for `"search"`, `"mcp"` and `"auto"` (hooks), keyed by `"local"`, `"imported"`, `"imported:<group>"` or `"*"` (`true`/`false`). `DEJA_AUTORECALL_LOCAL_ONLY=1` sets `activations.auto.imported` to `false`.
  - `"ignore"`: array of shell globs matched against session path and project to exclude from recall and `sync` (default `["*/.claude/jobs/*"]`).
  - `"auto_index"`: `false` stops automatic index updates on search, MCP recall and hooks (same as `DEJA_NO_AUTO_INDEX=1`).
  - `"search_only"`: `true` skips mining fixes, commands and co-occurrence, saving ~20% of build CPU (same as `DEJA_SEARCH_ONLY=1`).
- **`exclude`** — one project name or path pattern per line to skip at index time and `sync export`, or `harness:<name>` (e.g. `harness:opencode`) to skip a store (`DEJA_EXCLUDE_PROJECTS`, `DEJA_EXCLUDE_HARNESSES`).
- **`projects`** — one `<path> = <name>` per line to group multiple checkouts or worktrees as one project.
- **`rules.md`** — standing instructions copied into each installed agent's global rules file by `deja rules sync`.
- **State files written by deja** — `peers.json` (`deja sync ssh`), `settled.json` (`deja friction --settle`), `tombstones` (`deja forget`), `wiring.json` and `bin/deja-hook` (`deja install`).

Hook recall mode is set by `DEJA_RECALL`: `safe` (default, 2 KB cap and up to 3 sessions from the current project at session start), `aggressive` (4 KB cap and up to 6 sessions across projects), or `off` (silences all hooks). The `DEJA_INDEX_*` switches and full configuration table are in the [commands guide](https://vshulcz.github.io/deja-vu/guide/commands.html#configuration).

</details>

<details>
<summary><b>One project is spread over several checkouts. Can recall treat them as one?</b></summary>

List the trees in `~/.config/deja/projects`, one `<path> = <name>` per line:

```text
~/work/monorepo = work
~/work/worktrees = work
```

Every directory under a listed path is then that project, for indexing, the hooks and recall alike; the longest matching path wins. Run `deja index --rebuild` to re-file existing transcripts under the new name. The exclude file still wins over project aliases.

</details>

<details>
<summary><b>How do I wipe everything?</b></summary>

```sh
deja uninstall --all
rm -rf ~/.cache/deja ~/.local/share/deja ~/.config/deja
```

The index is under `~/.cache/deja`, your `remember` and `promote` notes in
`~/.local/share/deja`, and the rules, exclude list, project aliases and hook launcher in
`~/.config/deja` (or under `XDG_DATA_HOME` and `XDG_CONFIG_HOME` when set; on
Windows the notes are in `%AppData%\deja`).

</details>

## Guides

- **Context & recovery:** [Does your agent remember previous conversations?](https://vshulcz.github.io/deja-vu/guide/does-my-agent-remember.html) · [The agent lost the context you had](https://vshulcz.github.io/deja-vu/guide/lost-context.html) · [The context window is full](https://vshulcz.github.io/deja-vu/guide/context-window-full.html) · [What compaction drops](https://vshulcz.github.io/deja-vu/guide/after-compaction.html) · [Why agents forget between sessions](https://vshulcz.github.io/deja-vu/guide/forgetting.html)
- **Resuming & finding:** [Resuming yesterday's session](https://vshulcz.github.io/deja-vu/guide/resume-a-session.html) · [Finding the session where you solved it](https://vshulcz.github.io/deja-vu/guide/find-a-session.html) · [The agent repeats a mistake you already fixed](https://vshulcz.github.io/deja-vu/guide/repeated-mistakes.html) · [Switching agents](https://vshulcz.github.io/deja-vu/guide/switching-agents.html)
- **Session files & cleanup:** [Session files on disk](https://vshulcz.github.io/deja-vu/guide/session-files-on-disk.html) · [Where each agent keeps its history](https://vshulcz.github.io/deja-vu/guide/where-sessions-are-stored.html) · [Recovering a deleted Claude Code session](https://vshulcz.github.io/deja-vu/guide/recover-a-deleted-session.html) · [Claude Code: No conversation found with session ID](https://vshulcz.github.io/deja-vu/guide/no-conversation-found-claude-code.html) · [Codex resume session](https://vshulcz.github.io/deja-vu/guide/codex-resume-session.html) · [Deleting old Claude Code sessions](https://vshulcz.github.io/deja-vu/guide/delete-old-claude-sessions.html)
- **Comparisons & operations:** [What each memory tool knows the day you install it](https://vshulcz.github.io/deja-vu/guide/day-zero.html) · [Memory plugins compared](https://vshulcz.github.io/deja-vu/guide/compare.html) · [What memory costs](https://vshulcz.github.io/deja-vu/guide/token-cost.html) · [Auditing an agent](https://vshulcz.github.io/deja-vu/guide/auditing-agents.html) · [Exporting a conversation](https://vshulcz.github.io/deja-vu/guide/export-conversations.html) · [Across machines](https://vshulcz.github.io/deja-vu/guide/sync-across-machines.html)

<details>
<summary><b>Per-harness setup guides (Claude Code, Codex, Cursor, OpenClaw, Hermes…)</b></summary>

[Claude Code](https://vshulcz.github.io/deja-vu/guide/memory-for-claude-code.html) · [Codex](https://vshulcz.github.io/deja-vu/guide/memory-for-codex.html) · [Cursor](https://vshulcz.github.io/deja-vu/guide/memory-for-cursor.html) · [Windsurf](https://vshulcz.github.io/deja-vu/guide/memory-for-windsurf.html) · [opencode](https://vshulcz.github.io/deja-vu/guide/memory-for-opencode.html) · [DeepSeek Harness](https://vshulcz.github.io/deja-vu/guide/memory-for-dsh.html) · [Kimi Code](https://vshulcz.github.io/deja-vu/guide/memory-for-kimi.html) · [Zed](https://vshulcz.github.io/deja-vu/guide/memory-for-zed.html) · [Grok Build](https://vshulcz.github.io/deja-vu/guide/memory-for-grok.html) · [Gemini CLI](https://vshulcz.github.io/deja-vu/guide/memory-for-gemini.html) · [Qwen Code](https://vshulcz.github.io/deja-vu/guide/memory-for-qwen.html) · [OpenClaw](https://vshulcz.github.io/deja-vu/guide/memory-for-openclaw.html) · [Goose](https://vshulcz.github.io/deja-vu/guide/memory-for-goose.html) · [Cline](https://vshulcz.github.io/deja-vu/guide/memory-for-cline.html) · [pi](https://vshulcz.github.io/deja-vu/guide/memory-for-pi.html) · [Hermes](https://vshulcz.github.io/deja-vu/guide/memory-for-hermes.html) · [Copilot CLI](https://vshulcz.github.io/deja-vu/guide/memory-for-copilot.html) · [Copilot Chat](https://vshulcz.github.io/deja-vu/guide/memory-for-copilot-chat.html) · [aider](https://vshulcz.github.io/deja-vu/guide/memory-for-aider.html) · [Amp](https://vshulcz.github.io/deja-vu/guide/memory-for-amp.html) · [Antigravity](https://vshulcz.github.io/deja-vu/guide/memory-for-antigravity.html) · [Continue](https://vshulcz.github.io/deja-vu/guide/memory-for-continue.html) · [Crush](https://vshulcz.github.io/deja-vu/guide/memory-for-crush.html) · [Roo Code](https://vshulcz.github.io/deja-vu/guide/memory-for-roo.html) · [Kilo Code](https://vshulcz.github.io/deja-vu/guide/memory-for-kilocode.html) · [Kiro](https://vshulcz.github.io/deja-vu/guide/memory-for-kiro.html) · [Cherry Studio](https://vshulcz.github.io/deja-vu/guide/memory-for-cherrystudio.html) · [Oh My Pi](https://vshulcz.github.io/deja-vu/guide/memory-for-omp.html) · [prime-agent](https://vshulcz.github.io/deja-vu/guide/memory-for-prime.html) · [Senpi](https://vshulcz.github.io/deja-vu/guide/memory-for-senpi.html) · [Kimchi](https://vshulcz.github.io/deja-vu/guide/memory-for-kimchi.html) · [Command Code](https://vshulcz.github.io/deja-vu/guide/memory-for-commandcode.html) · [ZCode](https://vshulcz.github.io/deja-vu/guide/memory-for-zcode.html) · [gjc](https://vshulcz.github.io/deja-vu/guide/memory-for-gjc.html) · [CodeWhale](https://vshulcz.github.io/deja-vu/guide/memory-for-codewhale.html) · [Reasonix](https://vshulcz.github.io/deja-vu/guide/memory-for-reasonix.html) · [TRAE CLI](https://vshulcz.github.io/deja-vu/guide/memory-for-trae.html)

</details>

## Contributing

`make build test lint`, then [CONTRIBUTING.md](CONTRIBUTING.md). Adding a harness starts in
the [parser registry](docs/ARCHITECTURE.md#source-parsers). Priorities and non-goals are in
[ROADMAP.md](ROADMAP.md). Good first issues are labeled.

## Support

Bugs and questions go to [issues](https://github.com/vshulcz/deja-vu/issues).
Anything you think is exploitable goes through the private advisory link in
[SECURITY.md](SECURITY.md) instead. What deja reads, what it never sends
anywhere, and how to exclude a project or forget a session is under
[Privacy](#privacy). Found it useful? [Star deja-vu on GitHub](https://github.com/vshulcz/deja-vu).

## License

MIT © [Vladislav Shulcz](https://github.com/vshulcz)
