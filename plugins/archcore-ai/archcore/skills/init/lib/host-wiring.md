# Host wiring and CLI pre-flight

Flow reference for `/archcore:init`. `SKILL.md` loads this file at its pre-flight step and again when a confirmed plan carries the Host wiring line. Host wiring writes the same files `archcore init` writes (`host-wiring-parity.adr`), so the repository works for teammates who use the CLI without this plugin.

## Pre-flight: CLI availability check

Before any init step, verify that the Archcore CLI is available on PATH. The canonical installer is documented at https://docs.archcore.ai/start/install/ — use it as the single source of truth; do **not** suggest other channels (`brew`, `go install`, etc.) even if the user mentions them.

1. Run: `archcore --version` (via Bash tool)
2. If it **succeeds** → check the host-wiring version gate with the deterministic helper (never compare versions yourself — lexical comparison breaks on double-digit fields). Resolve `$d` **in this same Bash call** (each Bash invocation is a fresh shell — nothing persists from a later step), exactly as the host probe below does: run `d="${CLAUDE_SKILL_DIR:-<absolute dir of this SKILL.md>}"; "$d/../../bin/cli-gte" 0.7.0`. It prints exactly one token:
   - `yes` → return to step 2 of `SKILL.md` (host wiring enabled).
   - `__NO_CLI__` (unexpected here — `--version` just succeeded) → treat as `no`.
   - `no` → the seed still works, but the host-wiring step (see "Host wiring" below) needs a newer CLI. Ask the user once:
     > Archcore CLI `<version>` is older than v0.7.0 — host wiring (project MCP config, SessionStart hook, usage hint) will be skipped. Update now via `archcore update`? (y/N)
     - On `y` → run `archcore update` (Bash), re-run the `cli-gte 0.7.0` check, and return to step 2 of `SKILL.md` (host wiring enabled on `yes`, disabled otherwise).
     - On `N` / silence → return to step 2 of `SKILL.md` with host wiring **disabled**: omit the Host wiring line from the preview, skip the Execution cascade below entirely (the cascade never runs — its manual-fallback leg is NOT a substitute for this note), and in the closing message note: *"Host wiring skipped (CLI < v0.7.0) — update with `archcore update`, then run `archcore init --agent <host> --project "<root>"` in a terminal to make this repo self-contained for CLI-only teammates."* (`<host>`/`<root>` come from the host probe below, which runs regardless of the gate.)
3. If it **fails** (command not found):
   - Detect the platform via `uname -s` (Bash). `Darwin`/`Linux` → POSIX path. Anything else (Windows native) → instruct-only path.
   - **POSIX path** — ask the user once:
     > Archcore CLI not found. The official installer runs:
     >
     > ```
     > curl -fsSL https://archcore.ai/install.sh | bash
     > ```
     >
     > Run it now? (y/N)
   - On `y` → execute the command exactly as shown (Bash tool). After it returns, re-run `archcore --version`.
     - Success → print: *"Archcore CLI installed (`<version>`). Proceeding with init."* → apply the same v0.7.0 comparison from item 2 (a fresh install is normally current, so host wiring is enabled) → return to step 2 of `SKILL.md`.
     - Still failing → print the install message below and **stop**.
   - On `N` / silence / **instruct-only path** → print and stop:
     > Archcore CLI required. Install it, then re-run `/archcore:init`:
     >
     > - macOS / Linux / WSL: `curl -fsSL https://archcore.ai/install.sh | bash`
     > - Windows (PowerShell 5.1+): `irm https://archcore.ai/install.ps1 | iex`
     > - Verify: `archcore --version`
     > - Full docs: https://docs.archcore.ai/start/install/

Do **not** attempt `brew install`, `go install`, package-manager wrappers, or any other install command — they are not the supported path and will produce a CLI that is not version-compatible with the plugin.

## Host and project root probe

**Host + project root for wiring** — always run this probe, even when host wiring is disabled by the pre-flight version gate (it is one cheap Bash call, and the disabled-path closing message still needs `<host>`/`<root>`). One Bash call:

```sh
d="${CLAUDE_SKILL_DIR:-<absolute dir of this SKILL.md>}"; host=$("$d/../../bin/detect-host"); root=$(git rev-parse --show-toplevel 2>/dev/null || pwd); printf '%s\n%s\n' "$host" "$root"
```

`${CLAUDE_SKILL_DIR}` is set by Claude Code only. On other hosts (Cursor, Codex, GitHub Copilot CLI) substitute the absolute directory of this skill file — you know it from having read this file; `bin/detect-host` is two directories up from it (`<plugin-root>/bin/detect-host`).

`bin/detect-host` resolves the current host from environment only (never cwd or stdin — Cursor guarantees neither) and prints exactly one token: `claude-code` | `cursor` | `codex-cli` | `__UNKNOWN__`. **A GitHub Copilot CLI session always lands on `__UNKNOWN__`** — Copilot sets no environment marker in the shell commands it runs, so it is resolved by the question below rather than by the probe (rationale in `bin/detect-host`). If the probe returns `__UNKNOWN__` **or anything else than the three host tokens** (empty output, a path error — treat all the same), ask one `AskUserQuestion` — "Which AI host is this session running in?" with options Claude Code / Cursor / Codex (CLI or desktop app) / GitHub Copilot CLI — and map the answer to the agent id (`claude-code` / `cursor` / `codex-cli` / `copilot`). The Codex option names both surfaces on purpose: they share one binary, one `~/.codex/config.toml` and one plugin install, so `codex-cli` is the agent id for the desktop app too and there is no `codex-desktop` (`codex-adapter.spec`). Remember `host` and `root` for the Preview line and the Execution cascade; do not re-run the probe.

`init_project` initializes only `.archcore/` — host wiring (MCP config, hook, usage hint) is planned in the preview and executed by the Execution cascade below, never here. Do not run `archcore init` yourself at this step; the terminal path is the cascade fallback for the user, not a pre-flight action.

## Empty route

`SKILL.md` step 4 sends a repository with no manifest, no source, and no authored source here. No content seed — but host wiring still applies (an empty repo is exactly where a teammate going CLI-only needs the configs).

When host wiring is **disabled** by the pre-flight version gate, reply with exactly this and stop (no writes):

> Archcore is ready at `.archcore/`. No source code detected yet — no content to seed. Host wiring skipped (CLI < v0.7.0) — update with `archcore update`, then re-run `/archcore:init`. The SessionStart empty-state nudge will keep pointing here until then.


Otherwise show a mini-preview:

> Archcore is ready at `.archcore/`. No source code detected yet — no content to seed.
>
> One thing worth doing now — host wiring, same files `archcore init` writes (makes the repo work for teammates using the CLI without this plugin):
>
> ```
> Host wiring (<host>) → <root>
>   • <per-host file list — e.g. for claude-code: .mcp.json · .claude/settings.json (SessionStart hook) · CLAUDE.md + AGENTS.md (managed block)>
> ```
>
> `confirm` to write these, `cancel` to leave the repo untouched. Re-run `/archcore:init` after the first manifest or source file lands — the SessionStart empty-state nudge will keep pointing here until then.

On `confirm` → execute the Execution cascade below and stop. On `cancel` → stop with no writes. Either way, **do NOT** create placeholder documents — they have no practical value, cost roundtrips and tokens, and suppress the SessionStart empty-state nudge that is the user's breadcrumb back here.

## Preview line

The **Host wiring line** of a preview (omit when disabled by the pre-flight version gate) names the detected host, the resolved project root **explicitly** (the user must see WHERE files will land — Cursor can misroute cwd, and this line is the check against it), and the per-host file list: claude-code → `.mcp.json` + `.claude/settings.json` (SessionStart hook) + `CLAUDE.md` + `AGENTS.md` managed blocks (CLAUDE.md is what Claude Code actually reads; AGENTS.md is the shared standard block — one write, both files; the CLI also deletes the legacy nudge file under `.claude/rules/` left by pre-v0.6.1 CLIs); cursor → `.cursor/mcp.json` + `.cursor/hooks.json` + `AGENTS.md` managed block; codex-cli → `.codex/config.toml` + `AGENTS.md` managed block; copilot → `.mcp.json` + `.github/hooks/archcore.json` (sessionStart) + `AGENTS.md` managed block. **On copilot the Host wiring line is never optional** — the plugin ships no MCP server for that host (Copilot launches a plugin's MCP in the plugin's own directory, github/copilot-cli#4234), so without wiring the session has skills and hooks but no document tools at all. If the version gate disabled wiring, say so plainly in the closing message rather than seeding silently. `edit → hosts: all` widens the install to every agent auto-detected in the repo; `edit → skip wiring` drops the line. These files live **outside** `.archcore/` — they are written only after `confirm`, like everything else.

## Execution cascade

Run the cascade first in the create phase, when the preview carried the Host wiring line and it survived `edit`. Deterministic cascade, first available path wins:
   1. **MCP tool** — if `install_host_config` is among the available archcore MCP tools, call `install_host_config(host=<host>)` (add `all_detected=true` on `hosts: all`). The server's project root is correct by construction; relay the returned report (files ensured / errors) in the closing message.
   2. **CLI fallback** — tool absent (older server still running, or a Cursor day-one session where no archcore MCP is connected yet): run via Bash `archcore init --agent <host> --project "<root>"` (repeat `--agent` per host on `hosts: all`), with `<root>` exactly the path shown in the preview. Non-interactive by contract: no prompts, artifacts land under `--project` regardless of cwd.
   3. **Manual fallback** — the CLI turns out too old for `--agent` at execution time (reachable only when the version check passed at pre-flight but the CLI is stale/broken when the cascade runs — e.g. a concurrent downgrade; a user who declined the update never reaches this cascade, their channel is the closing-message note from the pre-flight gate): print the ready-to-run command *`archcore update && archcore init --agent <host> --project "<root>"`* for the user's terminal and continue with the content seed — wiring failure never aborts the seed.
   On partial failure inside a path (e.g. one host errored), report per-artifact results and continue; do not retry a different path for artifacts that succeeded.

   **On `copilot`, verify the result instead of assuming it.** Everywhere else a failed wiring costs convenience — the plugin's own MCP server still answers. On this host it costs the entire document surface (`copilot-mcp-architecture.adr`), and the user discovers that a session later, as "the plugin is broken". So after the cascade, check the artifact that carries the tools, in one Bash call: `grep -q '"archcore"' "<root>/.mcp.json"`. On a match, report wiring as done. On no match — including a zero-exit CLI that wrote nothing — report it as **failed**, name `<root>/.mcp.json` as the missing file, and give the user the ready-to-run `archcore init --agent copilot --project "<root>"`. Either way continue with the content seed: wiring failure never aborts it.

## Closing outcome lines

When host wiring ran, lead the closing message with its one-line outcome — e.g. *"Host wiring (claude-code): .mcp.json, SessionStart hook, CLAUDE.md + AGENTS.md managed block — repo now works for CLI-only teammates."* — or the per-artifact errors if any failed.

**On `copilot` the outcome line MUST end with the restart requirement**, e.g. *"Host wiring (copilot): .mcp.json, .github/hooks/archcore.json, AGENTS.md — now restart the Copilot session to connect the Archcore MCP document tools. This host reads .mcp.json at session start, so they are not available in this one."* Copilot is the only host where wiring is the sole route to those tools, and they do not appear in the session that wrote the file. A user who is not told this sees a green report followed by an agent that cannot read or create a single document — which reads as a broken plugin, not as a pending restart. `bin/session-start` gives the same instruction in its own Copilot messages; keep the two in step.

**On `codex-cli` the outcome line MUST name the two consents the wiring waits on.** Codex loads a project `.codex/` layer — `.codex/config.toml` and `.codex/hooks.json` alike — only for a project marked `trust_level = "trusted"`, and runs a non-managed command hook only after the user reviews and trusts it under `/hooks`. Neither is granted by writing the files. So the line reads e.g. *"Host wiring (codex-cli): .codex/config.toml, .codex/hooks.json, AGENTS.md — Codex applies them once you trust this project and approve the hooks in `/hooks`; both surfaces (CLI and desktop app) read the same files."* Without that sentence a teammate sees green wiring and a session with no Archcore MCP and no hooks, and `codex exec` skips untrusted hooks without printing why.
