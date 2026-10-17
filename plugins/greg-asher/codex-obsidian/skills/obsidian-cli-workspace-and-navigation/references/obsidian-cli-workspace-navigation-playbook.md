# Obsidian CLI Workspace and Navigation Playbook

Use the Codex-safe wrapper in Codex Desktop on macOS:

```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian <command>'
```

## Read-only inspection first

```bash
obsidian vault info=path
obsidian vaults verbose
obsidian workspace ids
obsidian workspaces total
obsidian tabs ids
obsidian recents total
obsidian wordcount path="Projects/Plan.md" words
```

## Navigation actions

```bash
obsidian open path="Projects/Plan.md" newtab
obsidian tab:open file="Projects/Plan.md"
obsidian random folder="Projects"
obsidian random:read folder="Projects"
obsidian unique name="Capture" content="# Capture"
obsidian web url="https://example.com" newtab
```

## Workspace layout mutations

```bash
obsidian workspace:save name="Daily Review"
obsidian workspace:load name="Daily Review"
obsidian workspace:delete name="Old Layout"
```

Treat workspace load/delete as high-impact state changes and summarize effects before execution.
