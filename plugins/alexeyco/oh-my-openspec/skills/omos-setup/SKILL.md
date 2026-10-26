---
name: omos-setup
description: "Install the oh-my-openspec Codex host pieces: the seven ~/.codex/agents/omos-*.toml role agents via the bundled installer, then the openspec MCP-server approval. Invoke via $oh-my-openspec:omos-setup."
---

# omos-setup

Install this plugin's Codex host pieces once per machine: the seven role
agent TOMLs under `~/.codex/agents/`, then the `openspec` MCP-server
approval. Run it after `codex plugin add oh-my-openspec@oh-my-openspec`,
or any time `spawn_agent` reports an unknown `omos-*` agent. This skill
acts directly — it dispatches no roles. You never run git write
commands.

## Flow

### 1. Check current state

List `~/.codex/agents/omos-*.toml`. The seven expected roles:
`omos-critic`, `omos-implementer`, `omos-planner`, `omos-researcher`,
`omos-retrospector`, `omos-reviewer`, `omos-verifier`.

- All seven present and unchanged → already installed; say so and go to
  §4 only if the approval is still missing.
- Any missing → continue with §2.
- Any differing → continue with §2. The installer plans each file as
  copy, skip, update, or conflict: a differing file that carries the
  `# managed-by:` marker is our own and updates silently; a foreign
  differing file is refused — replacing it is the user's explicit
  `--force` choice.

### 2. Locate the marketplace root

Run `codex plugin marketplace list` and read the `oh-my-openspec`
entry's local source path — the on-disk clone of this repository. That
clone is `<root>` for §3.

### 3. Run the installer

Run `node <root>/plugins/oh-my-openspec/assets/install-agents.mjs`.

- It copies the seven TOMLs into `~/.codex/agents/` (created when
  missing), skips byte-identical files — a second run reports seven
  skips, zero copies — and refuses per file to clobber a differing
  target unless the user passed `--force`.
- It prints the §4 approval and restart steps itself.
- Node ≥ 22.18 is required (the bundled MCP server imports `.ts`); the
  installer warns below that floor.

Alternative for users who prefer a fresh clone — read-only, no plugin
install needed:

```
git clone https://github.com/alexeyco/oh-my-openspec /tmp/oh-my-openspec &&
node /tmp/oh-my-openspec/plugins/oh-my-openspec/assets/install-agents.mjs
```

### 4. Approval and restart

- Approve the `openspec` MCP server when Codex prompts — it provides
  `openspec_validate` as `mcp__openspec__openspec_validate`.
- Restart the session so the agents and the MCP server load.

### 5. Verify

- Re-run the §1 check: exactly seven `~/.codex/agents/omos-*.toml`,
  byte-identical to the installer's sources.
- Ask the user to confirm, in a fresh session, that `spawn_agent` can
  name the roles and `mcp__openspec__openspec_validate` answers.

## Guardrails

- Never write `~/.codex/config.toml` — `codex plugin add` owns plugin
  enablement.
- Never overwrite a FOREIGN differing `~/.codex/agents/omos-*.toml` —
  files without the `# managed-by:` marker need the user's explicit
  `--force` choice; marker-carrying files are ours and update silently.
- Never commit, push, or stage anything.
