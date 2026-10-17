# Obsidian CLI Runtime Admin Playbook

Use the Codex-safe wrapper in Codex Desktop on macOS:

```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian <command>'
```

## Read-only inventory first

```bash
obsidian plugins filter=community versions format=json
obsidian plugins:enabled filter=community versions format=json
obsidian themes versions
obsidian snippets
obsidian snippets:enabled
obsidian commands filter=app:
obsidian hotkeys format=json
```

## Runtime mutation examples

```bash
obsidian plugin:install id=dataview enable
obsidian plugin:disable id=calendar
obsidian plugins:restrict on
obsidian theme:set name=Minimal
obsidian snippet:enable name=custom-snippet.css
obsidian command id=app:open-settings
```

For mutating commands, summarize side effects before execution and report the changed runtime entities.
