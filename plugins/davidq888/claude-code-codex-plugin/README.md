# Claude Code Plugin for OpenAI Codex

A lightweight local bridge from Codex to the user's authenticated Claude Code CLI. The plugin has
no runtime dependencies and never stores Claude credentials, tokens, API keys, or account data.

## Install

From the repository root, run on Windows, macOS, or Linux:

```bash
node plugins/claude-code/scripts/install.mjs install
```

Windows users can alternatively run:

```powershell
powershell -ExecutionPolicy Bypass -File .\plugins\claude-code\install.ps1
```

Use `update` or `uninstall` with the Node installer to perform those actions. The optional
`--destination-root <path>` flag supports isolated test installations; `--force` explicitly
replaces an existing installation.

The installer copies the plugin to `~/plugins/claude-code`, writes machine-specific MCP paths, and
adds the plugin to the Personal marketplace. Start a new Codex task after installation.

## Use

| Tool | Purpose |
| --- | --- |
| `claude_code_status` | Check local Claude Code installation and account readiness |
| `claude_code_login` | Open the official Claude Code browser sign-in flow |
| `claude_code_prompt` | Run workspace-scoped prompts in safe mode with `manual` or `plan` permissions |

Useful prompts:

```text
Check my Claude Code account status.
Open Claude Code login.
Run Claude Code in plan mode and review this repository.
Ask Claude Code for a second opinion about this implementation.
```

Claude Code owns its authentication state. This plugin only starts the local CLI and receives its
normal command output.
