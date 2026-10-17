# Obsidian CLI Devtools Playbook

Use the Codex-safe wrapper in Codex Desktop on macOS:

```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian <command>'
```

## Read-only diagnostics first

```bash
obsidian dev:errors
obsidian dev:console limit=100 level=error
obsidian dev:dom selector=".workspace-tab-header" total
obsidian dev:css selector=".workspace-tab-header" prop="color"
```

## Screenshot capture

```bash
obsidian dev:screenshot path="/tmp/obsidian-debug.png"
```

## Controlled runtime execution

```bash
obsidian eval code="app.vault.getFiles().length"
obsidian dev:cdp method="Runtime.evaluate" params='{"expression":"window.location.href"}'
```

Run `eval` and `dev:cdp` only when explicitly requested and after showing exact code/method params.
