# Bindry plugin for Codex CLI

Compiles a bound Bindry Binder into Codex skills — one skill per Skill — so instructions load only when a
task actually matches them, instead of sitting in context on every turn. Same idea as the Claude Code plugin
in this repo, ported to Codex's actual plugin/skill mechanics.

## Install

This plugin runs local Node.js scripts. It needs a local executor and is intended for Codex or local
threads in the ChatGPT desktop app; installing it does not make those scripts run in web-only chats.

```bash
codex plugin marketplace add bindryai/Plugins
codex plugin add bindry@bindry-plugins
```

Verified working end-to-end against the real `@openai/codex` CLI: both commands complete successfully and
`codex plugin list` shows `bindry@bindry-plugins` as `installed, enabled`, with all three skills and both
scripts present under the installed plugin's cache path.

## Directory package

The plugin manifest includes directory presentation metadata and the desktop-only declaration. From the
repository root, run `node scripts/package-codex.mjs <new-absolute-output-directory>` to build a standalone
bundle with its scripts, skills, icon, security policy and license at the package root. Stage newly added
source files first: the packager copies only Git-tracked files and excludes marketplace configuration.
ZIP the contents of that output directory for the OpenAI submission portal. Publisher verification and
directory review remain separate from building the bundle; a ZIP alone is not a published listing.

The marketplace manifest lives at `codex/.agents/plugins/marketplace.json` — this is the actual, confirmed
location (found by testing several guesses against the real CLI; **not** `.codex-plugin/marketplace.json`,
which is what a naive port from Claude Code's layout would suggest). The plugin manifest itself,
`.codex-plugin/plugin.json`, points its `skills` field at `./skills/`.

To try a local checkout instead of the published repo, point `marketplace add` at the repo root on disk
(`/path/to/Bindry.Plugins`) — same two commands otherwise.

## Use

Bindry ships three skills, each a near-direct port of the Claude Code plugin's equivalent command — same logic,
adapted to Codex's skill-only invocation model (Codex plugins have no separate "commands" concept; skills,
triggered by description-matching or `$name`, are the only invokable action a plugin can expose):

- **`bindry-sync`** — compile a Bindry Binder into `.agents/skills/` (Codex's project-local skills directory,
  the equivalent of Claude Code's `.claude/skills/`). Supports the same `--mode pinned|live` split described
  below.
- **`bindry-check`** — read-only drift report against the already-compiled skills. Never edits or re-syncs.
- **`bindry-connect`** — one-time, per-machine setup connecting Codex to the Bindry MCP server for live mode.

## Live mode

Same design as the Claude Code plugin: `--mode pinned` (default) compiles a static snapshot; `--mode live`
compiles a pointer skill whose body tells the agent to call the Bindry MCP server's `bindry.skills.get` tool
for current content instead of trusting anything cached. A live skill never goes stale, so `bindry-check`
reports it as "live (always current)."

Connecting to the MCP server is a deliberate, explicit opt-in via the `bindry-connect` skill — not a bundled
`mcpServers` entry in the plugin manifest. Codex, like Claude Code, has no way to conditionally load a
plugin-declared MCP server; bundling one would put a permanent "not connected" status in front of every
pinned-only installer who hasn't set up an API key.

```bash
codex mcp add bindry --url <api-base>/api/mcp --bearer-token-env-var BINDRY_API_TOKEN
```

Any key generated from the workspace's team page in Bindry works here — there's no separate permission to
grant for MCP access, and no separate token needed from pinned-mode sync. Verified live end-to-end: registered
a real API key this way against a real running Bindry API, confirmed `codex mcp get bindry` reports it enabled,
and confirmed (via a real independent MCP client) that `Authorization: Bearer <key>` against `/api/mcp` returns
real tool results — this required a small fix upstream in IBeam's default JWT scheme, which was previously
intercepting any non-JWT Bearer value before the API-key scheme got a chance; see the Bindry-API changelog for
that fix's own verification.

## Try it right now, without Codex

The compiler is the same plain, dependency-free Node script as the Claude Code plugin, just defaulting to a
different output directory:

```bash
# from a local export file
node scripts/compile-binder.mjs examples/git-flow-command-center.binder.json

# a Skill with an attachment (logo file)
node scripts/compile-binder.mjs examples/brand-guidelines.binder.json

# live, from a running Bindry API
node scripts/compile-binder.mjs <binder-id> --api-base http://localhost:5160 --token <api-key> --out .agents/skills
```

Verified against a real running Bindry API: output for the bundled examples is byte-identical to what the
Claude Code compiler produces for the same input (frontmatter, pin/live comment, body, assets — only the output
directory differs), and a full live round-trip (seed a Binder + Skill, compile pinned and live, edit the
Skill's content, re-fetch live and see the new content immediately) was verified the same way it was for the
Claude Code plugin.

## Current limitations

- `--mode live` requires real GUID Skill ids from a live-fetched Binder — the bundled
  `examples/*.binder.json` files use illustrative ids (e.g. `bnd_git_branch_pr_hygiene`), not real GUIDs, so
  those Skills are skipped with a warning rather than compiling a skill that would always fail.
- Attachments are still downloaded and pinned to disk at compile time even in live mode — the live MCP tool
  returns a Skill's text content only, not its file attachments.
- `/api/binders/{id}/export` is workspace-scoped, same as the Claude Code plugin — "sync your own Binders," not
  "install someone else's published Binder."
- Codex skills have no structured "prefer tool X" mechanism beyond the prose in the skill body itself (confirmed
  against a real OpenAI-authored plugin already installed on this machine) — a live skill's instruction to call
  the MCP tool is exactly that: an instruction, not an enforced constraint.

## Compiled skills need to be readable, and a failure here is nearly silent

Codex reads each `SKILL.md` **twice**, and both reads have to succeed for a skill to do anything:

1. **At session start**, Codex itself reads every `.agents/skills/**/SKILL.md` to build the list of skills the
   model is offered — name, description, path.
2. **During a turn**, the model reads the body of the skill it chose, with an ordinary shell command
   (`Get-Content` / `cat`) against that path. There is no skill tool in Codex's event stream; the body arrives
   this way or not at all.

So a compiled skill is unavailable if **either** Codex cannot read the file at startup, **or** the agent's shell
is sandboxed such that it cannot read the workspace during the turn. `codex exec -s read-only` is sufficient —
read-only permits reads — but a stricter sandbox would not be.

**The failure is almost invisible.** Observed directly (BIND-0264): with one `SKILL.md` made unreadable, Codex
emitted a single line to **stderr** —

```
ERROR codex_core::session::session: failed to load skill …\bulletin-protocol\SKILL.md: failed to read file: Access is denied. (os error 5)
```

— and then ran the turn normally. The skill was simply absent: it was never offered, never mentioned, and the
answer was written from general knowledge. Nothing in the response, and nothing on stdout, indicated that a
skill had been expected and lost. If you redirect or ignore stderr, there is no signal at all.

**The always-on block is unaffected.** In the same run the `AGENTS.md` preamble was still honoured in full, so
a Binder can be half-working — persona applied, skills silently missing — which looks like the Binder working.

If skills seem to be doing nothing on Codex, check stderr for that line before anything else. A malformed
`SKILL.md` fails the same way, for the same reason, with `missing YAML frontmatter delimited by ---`.
