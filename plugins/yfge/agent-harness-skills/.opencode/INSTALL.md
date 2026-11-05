# Installing Agent Harness Skills For OpenCode

## Prerequisites

- OpenCode installed.
- A local clone of this repository, or a git URL for the repository.

## Installation

For a local clone, add the repository path to the `plugin` array in your global or project-level `opencode.json`:

```json
{
  "plugin": ["/absolute/path/to/agent-harness-skills"]
}
```

For a git-backed install, use the repository URL:

```json
{
  "plugin": ["agent-harness-skills@git+ssh://git@github.com/yfge/agent-harness-skills.git"]
}
```

Restart OpenCode. The plugin injects a compact startup bootstrap into the next chat and registers this repository's `skills/` directory for runtimes that honor plugin config changes.

## Verify

Use OpenCode's native skill tool:

```text
use skill tool to list skills
```

Then load a skill by name, for example:

```text
use skill tool to load repo-harness-assessment
```

## Updating

Pull the repository or update the git-backed plugin source, then restart OpenCode. If OpenCode keeps an old cached copy, clear the OpenCode package cache or reinstall the plugin entry.

## Troubleshooting

- Confirm `opencode.json` points to the repository root, not the `skills/` folder.
- Confirm `package.json` exists at the repository root.
- Confirm your OpenCode version supports `experimental.chat.system.transform` if the startup bootstrap is missing.
- Confirm each skill has a `SKILL.md` file with valid frontmatter.
