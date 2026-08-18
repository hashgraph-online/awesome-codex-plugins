# Agent Guard

Agent Guard is a local-by-default, no-telemetry secret-leak guardrail for AI
coding agents. Its hooks inspect supported tool-call inputs and outputs in every
enabled session, block common credential exposure paths before execution, mask
secret-like output, and scan changed files after mutations and before stop.

It is a defense-in-depth control, not a vault, DLP system, credential rotator,
or replacement for GitHub Secret Scanning and Push Protection.

## Install in Claude Code

```text
/plugin install agent-guard@claude-plugins-official
/reload-plugins
```

The official-marketplace command above applies only after Anthropic lists the
plugin. Until then, install from the project's marketplace:

```text
/plugin marketplace add JeongJaeSoon/agent-guard
/plugin install agent-guard@agent-guard
/reload-plugins
```

After installation, SessionStart reports `DEGRADED` protection whenever `jq`,
`git`, gitleaks, or a bundled policy is unavailable. The warning names the
host-appropriate skill: `$setup-agent-guard` in Codex or
`/agent-guard:setup-agent-guard` in Claude Code. You can also run the
plugin-local `agent-guard setup` directly. Dependency installation always
requires explicit approval. Then verify:

```text
/agent-guard:verify
```

Optional Claude shell command wrapping requires an explicit shell-rc change:

```text
/agent-guard:setup-shell
```

The slash command uses Claude's Bash tool so a sandboxed session can request
approval before changing the shell rc. If the host cannot grant that approval,
run the plugin-local `agent-guard setup-shell` command directly in a terminal.
Restart the shell and Claude Code after setup. Dependency downloads never run
from a lifecycle hook. Until wrapping is loaded, SessionStart repeats the
`/agent-guard:setup-shell` instruction. The guided setup path asks before
installing software and requires the published SHA-256 for the selected
gitleaks archive.

Plugin executions maintain a version-independent sibling path at
`current/bin/agent-guard`; hook manifests and `setup-shell` use it and can fall
back to the newest installed version directory after a cache upgrade. Scanner
infrastructure failures use `AGENT_GUARD_INFRA_FAILURE_MODE=open|closed`
(`open` by default) and warn once per session. Secret detections always block.

## Hooks and data scope

The Claude plugin registers:

- `PreToolUse` for supported read, search, write, shell, web, patch, and MCP
  tools. It inspects paths and proposed tool input before execution.
- `PostToolUse` for supported tools. It scans output for secret-like values and,
  after mutations, scans changed files in the current Git work tree.
- `Stop` to scan changed files in the current Git work tree.
- `SessionStart` to report missing dependencies and, on Claude Code,
  shell-integration version drift. It never installs software.

Recognized checksum fields in `go.sum`, `package-lock.json`, `yarn.lock`,
`Cargo.lock`, and `uv.lock` are allowlisted only when both their path and exact
hash-line shape match. Other content in those files remains subject to normal
secret detection. Output masking likewise replaces assignment values, not
secret-like key names or surrounding prose.

Environment templates are readable only with an explicit final
`.example`/`.sample`/`.template`/`.dist` marker, or a leading
`example`/`sample`/`template` marker directly before `.env` or `.envrc`.
Runtime forms such as `.env.local`, `local.env`, `env.local`, `.flaskenv`, and
`.dev.vars.production` remain blocked. Source modules such as `config.env.ts`
stay readable, while environment data forms such as `schema.env.json` remain
protected. A template name cannot override a non-environment deny rule, a
deny-listed ancestor, or an operator-supplied `AGENT_GUARD_DENY_READ_PATHS`
policy, and template-named symlinks are checked against their resolved target.
Template contents still undergo normal secret scanning on writes.

Default processing is local, ephemeral, and has no telemetry. PII hook handling
is off by default. Selecting the experimental `http` PII adapter sends
the text described in [PRIVACY.md](PRIVACY.md) to the user-configured endpoint.
Compatibility with a specific external service is not guaranteed.

## Requirements and platforms

Supported platforms are macOS and Linux on x64 and arm64. Windows is not
currently supported. Runtime requirements are `sh`, `awk`, `git`, `jq`, and
gitleaks 8.30 or newer (recommended).

## Commands

- `/agent-guard:verify` — scan staged, unstaged, and untracked work-tree data.
- `/agent-guard:checksum [VERSION]` — print published gitleaks checksums.

## Skills

- `/agent-guard:setup-agent-guard` — resolve the plugin-local binary, diagnose
  `jq`/gitleaks, and guide approved installation. Codex invokes the same skill
  as `$setup-agent-guard`; the skill selects the correct host verification path
  and runs live probes through that host's normal command surface.
- `/agent-guard:setup-shell` — install or refresh the optional shell integration
  through the plugin-local binary with approval before changing the shell rc.
  Codex invokes the same skill as `$setup-shell`.

## Policies and support

- [Privacy and data handling](PRIVACY.md)
- [Security reporting](SECURITY.md)
- [Support and platform policy](SUPPORT.md)
- [License](LICENSE)
- [Third-party notices](THIRD_PARTY_NOTICES.md)
- [Full documentation and known limitations](https://github.com/JeongJaeSoon/agent-guard)
