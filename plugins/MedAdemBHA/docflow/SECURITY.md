# Security

docflow is a local documentation scaffold and AI-agent workflow helper. It does not run a server, open network connections, or collect telemetry.

## Supported Versions

| Version | Status |
|---------|--------|
| `main` | Active development |
| `0.1.x` | Initial public release line |

## Hook Behavior

The Claude plugin registers one `SessionStart` hook:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/hooks/docflow-context.sh
```

The hook is designed to be read-only:

- It changes into the current project directory.
- It reads `docflow.json` if present.
- It reads the docs index and newest non-template changelog file.
- It prints a truncated context block.
- It exits `0` and stays silent when docflow is not configured.

It does not write files, invoke package managers, call network APIs, inspect secrets, or execute repository code.

## Before Installing

Review these files before enabling the plugin in a repository:

- `.claude-plugin/plugin.json`
- `.codex-plugin/plugin.json`
- `hooks/docflow-context.sh`
- `scripts/scaffold.sh`

For CI or shared use, run:

```bash
shellcheck scripts/*.sh hooks/*.sh
bash scripts/test-scaffold.sh
```

## Reporting a Vulnerability

Open a private GitHub security advisory if available. If not, open an issue with:

- affected version or commit
- operating system and shell
- exact command or hook path involved
- expected vs actual behavior
- minimal reproduction steps

Do not include secrets or private repository content in public issues.
