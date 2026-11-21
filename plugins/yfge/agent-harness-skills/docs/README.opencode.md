# Agent Harness Skills For OpenCode

Use this guide when installing Agent Harness Skills in OpenCode.

## What The OpenCode Plugin Does

The OpenCode plugin injects a compact startup bootstrap through OpenCode's chat transform hook so agents immediately see the Agent Harness Skills routing index. It also registers this repository's `skills/` directory through OpenCode's config hook for runtimes that honor plugin config changes.

The bootstrap is intentionally small: it points agents to `INDEX.md`, the native OpenCode skill tool, and the packaged `skills/` directory. It does not run commands or change project files.

## Installation

Use a local clone:

```json
{
  "plugin": ["/absolute/path/to/agent-harness-skills"]
}
```

Or use a git-backed plugin entry:

```json
{
  "plugin": ["agent-harness-skills@git+ssh://git@github.com/yfge/agent-harness-skills.git"]
}
```

Restart OpenCode after changing `opencode.json`. The next chat should receive the startup bootstrap automatically.

## Usage

List available skills:

```text
use skill tool to list skills
```

Load a skill:

```text
use skill tool to load repo-harness-assessment
```

Start with `repo-harness-assessment` for an existing repository, then use `INDEX.md` for routing across the other harness skills.

## Troubleshooting

- If no skills appear, confirm the plugin path points to the repository root.
- If the startup bootstrap does not appear, confirm your OpenCode version supports `experimental.chat.system.transform`.
- If the plugin does not load, confirm `package.json` points to `.opencode/plugins/agent-harness-skills.js`.
- If a skill fails to load, run the repository validation commands from the root README.
