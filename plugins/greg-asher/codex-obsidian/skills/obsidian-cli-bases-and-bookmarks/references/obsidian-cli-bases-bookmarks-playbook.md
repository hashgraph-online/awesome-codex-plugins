# Obsidian CLI Bases and Bookmarks Playbook

Use the Codex-safe wrapper in Codex Desktop on macOS:

```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian <command>'
```

## Read-only discovery

```bash
obsidian bases
obsidian base:views path="Projects.base"
obsidian base:query path="Projects.base" view="Roadmap" format=json
obsidian bookmarks verbose format=json
```

## Mutating operations

```bash
obsidian base:create path="Projects.base" view="Roadmap" name="Q3 Plan" content="# Q3 Plan"
obsidian bookmark file="Projects/Q3 Plan.md" title="Q3 Plan"
obsidian bookmark folder="Projects"
obsidian bookmark search="status:blocked"
obsidian bookmark url="https://example.com" title="Reference"
```

Use explicit targets and structured output for automation-friendly workflows.
