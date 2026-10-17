# Obsidian CLI Sync and Publish Playbook

Use the Codex-safe wrapper in Codex Desktop on macOS:

```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian <command>'
```

## Read-first release gate

```bash
obsidian sync:status
obsidian help publish:status
```

If publish support is detected, continue with publish status checks:

```bash
obsidian publish:status
obsidian publish:list total
```

## Inspect and restore sync history

```bash
obsidian sync:history path="Projects/Plan.md" total
obsidian sync:read path="Projects/Plan.md" version=2
obsidian sync:restore path="Projects/Plan.md" version=2
```

## Publish changes intentionally

```bash
obsidian publish:add path="Projects/Plan.md"
obsidian publish:add changed
obsidian publish:remove path="Archive/OldPlan.md"
obsidian publish:open path="Projects/Plan.md"
```

Run publish commands only when the publish support probe succeeds.
Prefer status + explicit scope before mutating publish or restore actions.
