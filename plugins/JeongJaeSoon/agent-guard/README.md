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
`git`, gitleaks, or a bundled policy is unavailable. Follow its prompt to run
`$setup-agent-guard` (or the plugin-local `agent-guard setup`); dependency
installation always requires explicit approval. Then verify:

```text
/agent-guard:verify
```

Optional Claude shell command wrapping requires an explicit shell-rc change:

```text
/agent-guard:setup-shell
```

Restart the shell and Claude Code after setup. Dependency downloads never run
from a lifecycle hook. Until wrapping is loaded, SessionStart repeats the
`/agent-guard:setup-shell` instruction. The guided setup path asks before
installing software and requires the published SHA-256 for the selected
gitleaks archive.

## Hooks and data scope

The Claude plugin registers:

- `PreToolUse` for supported read, search, write, shell, web, patch, and MCP
  tools. It inspects paths and proposed tool input before execution.
- `PostToolUse` for supported tools. It scans output for secret-like values and,
  after mutations, scans changed files in the current Git work tree.
- `Stop` to scan changed files in the current Git work tree.
- `SessionStart` to report missing dependencies and shell-integration version
  drift. It never installs software.

Default processing is local, ephemeral, and has no telemetry. PII hook handling
is off by default. Selecting the optional `pleno` or `http` PII provider sends
the text described in [PRIVACY.md](PRIVACY.md) to the user-configured endpoint.

## Requirements and platforms

Supported platforms are macOS and Linux on x64 and arm64. Windows is not
currently supported. Runtime requirements are `sh`, `awk`, `git`, `jq`, and
gitleaks 8.30 or newer (recommended).

## Commands

- `/agent-guard:verify` — scan staged, unstaged, and untracked work-tree data.
- `/agent-guard:checksum [VERSION]` — print published gitleaks checksums.
- `/agent-guard:setup-shell` — install or refresh Claude command wrapping.

## Policies and support

- [Privacy and data handling](PRIVACY.md)
- [Security reporting](SECURITY.md)
- [Support and platform policy](SUPPORT.md)
- [License](LICENSE)
- [Third-party notices](THIRD_PARTY_NOTICES.md)
- [Full documentation and known limitations](https://github.com/JeongJaeSoon/agent-guard)
