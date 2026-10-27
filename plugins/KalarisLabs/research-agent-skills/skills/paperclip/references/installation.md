# Installing and authenticating Paperclip

Paperclip is distributed by GXL (`https://paperclip.gxl.ai`). There are two ways to reach it: a local
CLI, or a hosted MCP server. The CLI is the richer surface — the virtual filesystem, `grep`, `scan`,
`sql`, repos, and the clipboard all live there — so prefer it unless you are on Windows or cannot
install software.

Commands here were exercised against **paperclip 0.7.14 and 0.7.15** on macOS (darwin 25.5.0). Per-client MCP
configuration is transcribed from `https://paperclip.gxl.ai/install` and is not verified here.

## 1. Install the CLI

### One-line installer (recommended, macOS and Linux)

```bash
curl -fsSL https://paperclip.gxl.ai/install.sh | bash
```

This is the vendor's supported install path, and it executes a remotely-fetched script with the
user's privileges — there is no published checksum or signature to verify it against. Get the user's
go-ahead before running it, and read it first if they want that:

```bash
curl -fsSL https://paperclip.gxl.ai/install.sh | less
```

The same applies after install: the CLI self-updates opportunistically, so the code that runs can
change between invocations. `paperclip --version` tells you what actually ran.

This drops a self-contained CLI in `~/.paperclip/` and a launcher on your `PATH` (on macOS,
`~/.local/bin/paperclip`). It bundles its own interpreter and dependencies under `~/.paperclip/lib/`,
so it will not disturb any project virtualenv.

If `paperclip` is not found afterwards, `~/.local/bin` is not on your `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"      # add to ~/.zshrc or ~/.bashrc to persist
```

### Via uv

Use this when you want the package inside an environment you control — for example to import the
Python SDK alongside your own code.

```bash
uv pip install https://paperclip.gxl.ai/paperclip.whl
paperclip setup        # = paperclip login + paperclip install
```

Two caveats. The wheel URL is unversioned, so it resolves to whatever is current — there is no pinned,
hash-verified release to install instead, and `gxl-paperclip` is not published on PyPI. And the
unrelated `paperclip` package **is** on PyPI: `uv pip install paperclip` installs the wrong software.
Always install from the full URL.

### Windows

The native installer does not support Windows. Use Claude Desktop, claude.ai, or another MCP client
pointed at the hosted server (below).

## 2. Authenticate

**Use an API key from the environment. Treat browser OAuth as the fallback.** A key is
non-interactive, works headless and in CI, is independently revocable, and never blocks on a browser.

### Resolution order

Verified against `cli/app.py` and `client/client.py` in 0.7.14:

| Priority | Source | Notes |
|---|---|---|
| 1 | `--api-key` flag | Works, but exposed in `ps` and shell history — avoid |
| 2 | `PAPERCLIP_API_KEY` env var | **Preferred.** Click reads it via the flag's `envvar` binding |
| 3 | `~/.paperclip/credentials.json` | Written by `paperclip login` |

A key in the environment **short-circuits OAuth completely**: `_ensure_auth()` returns immediately, so
no browser opens and a stored login is not consulted even when one exists. That also means an exported
key silently overrides the account you logged in as — `paperclip config` will show
`Auth: ✓ API key (env)` instead of your email.

The Python SDK's `from_env()` uses a similar order with one extra step in front:
`PAPERCLIP_BEARER_TOKEN` → `PAPERCLIP_API_KEY` → `~/.paperclip/credentials.json`.

### API key from `.env` — the default path

Create a key at `https://paperclip.gxl.ai/keys` (they look like `gxl_...`) and put it in the project's
`.env`:

```bash
# .env  — add to .gitignore
PAPERCLIP_API_KEY=gxl_...
```

**Paperclip has no dotenv support.** There is no `python-dotenv` dependency anywhere in the package;
`config.py` reads `os.getenv("PAPERCLIP_API_KEY", "")` and nothing more. A `.env` sitting next to the
command is invisible to it, so the file has to be exported into the environment first.

Use this exact form, in the directory holding `.env`:

```bash
[ -f .env ] && { set -a; . ./.env; set +a; }; paperclip config
```

`set -a` marks subsequent assignments for export, `.` sources the file, `set +a` restores normal
behavior.

Two things about this form are not stylistic:

**The `[ -f .env ]` guard is mandatory.** A bare `. ./.env` against a missing file is a *fatal* error
in a POSIX shell — it terminates the shell, so everything after the `;` is silently discarded:

```bash
# WRONG — unguarded, run in a directory with no .env
sh -c 'set -a; . ./.env 2>/dev/null; set +a; echo survived; paperclip config'
#   (no output at all — "survived" never prints, paperclip never runs)
```

Guarded, it is safe in all four states, each verified: `.env` present, `.env` absent, key already
ambient in the environment, and under both `sh` and `bash`.

**Every invocation needs it.** Environment variables do not persist between separate shell
invocations, which is exactly how an agent runs commands — one call per tool use. Export in one call
and run `paperclip` in the next and the key is gone, and Paperclip does not complain: it silently
falls back to stored OAuth, a *different identity*:

```bash
# WRONG — split across two tool calls
# call 1
set -a; . ./.env; set +a
# call 2
paperclip config      # → Auth: ✓ someone@example.com   ← the key never loaded
```

```bash
# RIGHT — one self-contained call
[ -f .env ] && { set -a; . ./.env; set +a; }; paperclip config   # → Auth: ✓ API key (env)
```

If the key is already exported — CI secrets, a shell profile, `direnv` — the guard is a harmless
no-op and no prefix is needed.

```bash
export PAPERCLIP_API_KEY='gxl_...'   # ad hoc, current shell only
```

Values containing spaces must be quoted inside `.env` or the shell will try to run them; `gxl_` keys
never contain spaces, so this only matters for other variables sharing the file.

Over HTTP the key travels as an `X-API-Key` header. Never echo it, never commit `.env`, and never
include it in a file you `paperclip upload`.

### The `--api-key` flag

```bash
paperclip --api-key "$PAPERCLIP_API_KEY" search -s pmc "query" -n 5
```

Same mechanism, worse hygiene: the argument shows up in `ps` output and shell history. Use it only to
run two identities in one shell where exporting would collide.

### Fallback: browser OAuth — a human must run this

`paperclip login` opens a browser and waits. An agent cannot complete it; ask the user to run it and
report back. With no TTY it exits cleanly rather than hanging:

```text
[error] Not authenticated. Run: paperclip login
       Or use --api-key flag or PAPERCLIP_API_KEY env var
```

For interactive use on a machine with a browser and no key available:

```bash
paperclip login       # opens a browser
paperclip logout      # sign out, remove stored credentials
```

Credentials land in `~/.paperclip/credentials.json`. Sign-in is also triggered automatically on first
use — which is exactly the blocking behavior an API key avoids, so set the key before the first call
in any non-interactive context.

## 3. Verify

```bash
paperclip config
```

With a key exported, a healthy install prints:

```text
  Paperclip
  Server:  https://paperclip.gxl.ai
           (default)
  Auth:    ✓ API key (env)
  Config:  /Users/you/.paperclip
  Health:  ✓ server reachable
  Sources: PubMed Central, bioRxiv, medRxiv, arXiv
```

Under OAuth the `Auth` line shows your email address instead.

**`Auth: ✓` means a key is present, not that it is valid.** A junk key produces the identical line,
and `Health: ✓ server reachable` is an unauthenticated probe. Only a real query proves the credential:

```bash
paperclip search -s pmc "CRISPR base editing" -n 3
```

You should get numbered results ending in a `[s_xxxxxxxx]` result id. An invalid key instead prints
`[error] Authentication failed (API key invalid).` and exits **1**, which is what to check in a script.

## 4. Install the agent skill files (optional)

`paperclip install` writes Paperclip's own skill files into a project so an agent picks them up
without being told.

**It is interactive** — two prompts, agent and path. Run bare from a tool call it either hangs on a
TTY or aborts without writing anything:

```text
  Select (e.g. 1,2 or all) [1]: Aborted!
```

Answer both prompts on stdin. `1` = Claude Code, `2` = Cursor, `3` = Codex; the empty second line
accepts the `--dir` default:

```bash
printf '1\n\n' | paperclip install --dir /path/to/project
# → writes /path/to/project/.claude/skills/paperclip/SKILL.md
```

Interactively:

```bash
paperclip install                 # prompts for client: Claude Code or Codex
paperclip install --dir ~/work/my-project
```

Installed skills are tracked in `~/.paperclip/installed_skills.json`. This is independent of the
CLI itself — the CLI works fine without it.

## 5. MCP server (no local install)

Universal endpoint:

```text
https://paperclip.gxl.ai/mcp
```

### Claude Code

```bash
claude mcp add --transport http paperclip https://paperclip.gxl.ai/mcp
```

### Codex

```bash
codex mcp add paperclip --url https://paperclip.gxl.ai/mcp
codex mcp login paperclip
```

Codex Desktop: Settings → MCP servers → Custom MCP, with an `X-API-Key` header holding your key.

### Cursor — `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "paperclip": {
      "url": "https://paperclip.gxl.ai/mcp",
      "type": "http"
    }
  }
}
```

Reload the window afterwards.

### Claude Desktop and claude.ai

Customize → Connectors → add a custom connector named "Paperclip" with the MCP URL above. Requires a
Pro, Max, Team, or Enterprise plan.

### Windsurf, Antigravity, ChatGPT

Same URL, configured as a custom MCP server or connector; the first two need the `X-API-Key` header
added by hand in their config file.

**MCP caveat:** the MCP surface is a single `paperclip` tool, not the full CLI. Its own instructions
tell you to run `paperclip skill` first to load the command reference.

## 6. Maintenance

```bash
paperclip update      # upgrade the CLI and refresh installed agent skills
paperclip uninstall   # remove Paperclip from this machine
```

The CLI also self-updates opportunistically. A command may print
`[paperclip] Updated 0.7.14 → v0.7.15` before its output — harmless, but it means a long-running
script can change versions mid-run. Pin behavior by running `paperclip update` up front if that
matters.

## 7. Configuration

```bash
paperclip config                              # diagnostics (default)
paperclip config --show                       # current configuration
paperclip config --url http://localhost:8002  # point at a different server
paperclip config --sources pmc --sources fda  # persistent default source filter
paperclip config --sources-list
paperclip config --sources-clear
```

A persistent source filter narrows *every* subsequent command. If searches come back suspiciously
empty, check `paperclip config --sources-list` before debugging anything else.

Config lives in `~/.paperclip/`:

```text
~/.paperclip/
├── credentials.json      OAuth tokens
├── feature_flags.json
├── installed_skills.json
├── repos/                local repo state
├── cache/
└── lib/                  bundled interpreter + gxl_paperclip package
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `command not found: paperclip` | `~/.local/bin` missing from `PATH` — export it, or re-source your shell rc |
| `Error: search requires a source flag (-s)` | Expected. Every search names a source: `-s pmc` |
| `Auth: ✗` in `paperclip config` | Run `paperclip login`, or export `PAPERCLIP_API_KEY` |
| Searches return nothing across sources | A stale source filter — `paperclip config --sources-clear` |
| Corpus `grep` finds nothing for a rare term | Default scan is time-bounded; retry with `--exhaustive` |
| `head` on `meta.json` prints nothing | `head`/`tail` handle `.lines` files; use `cat` for JSON |
| Version changed mid-session | Opportunistic self-update; re-run `paperclip --version` |
| MCP client cannot authenticate | Add the `X-API-Key` header with a key from `/keys` |
