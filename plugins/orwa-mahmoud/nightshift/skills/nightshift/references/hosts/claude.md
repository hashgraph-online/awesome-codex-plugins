# Start on Claude Code

Frictionless permissions come from `$TASK_ROOT/.claude/settings.local.json` or
`$TASK_ROOT/.claude/settings.json` — a `bypassPermissions` default mode, or an allowlist covering
the gates' commands. Settings on disk are what a headless revival inherits; a mode picked at launch
dies with the process. A live conversation is handed back with `claude --resume <id>` for a
terminal, or `vscode://anthropic.claude-code/open?session=<id>` for the IDE; `claude agents --json`
lists ids. Claude Code records clean session ends and Esc, and its watchman stands down for either
rather than resuming.
