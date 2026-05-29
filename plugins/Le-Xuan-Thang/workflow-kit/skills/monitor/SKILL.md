---
name: monitor
description: Use to open the full live dashboard — Rich TUI in the terminal or web dashboard at localhost:7860. Also triggers when the user says "show live progress", "open workflow dashboard", "watch the dispatcher", or "monitor in browser". Pass --web for browser mode.
argument-hint: "[--web]"
allowed-tools: Bash
---

# Workflow Monitor

Launch the live monitoring dashboard. TUI by default, web with `--web`.

## Step 1: Check dispatcher

```bash
cat workflow/dispatcher.pid 2>/dev/null | xargs -I{} kill -0 {} 2>/dev/null && echo "running" || echo "stopped"
```

If stopped: warn "Dispatcher not running — dashboard shows current state only. Start with /workflow-kit:execute."

## Step 2: Choose mode

- `--web` or user says "browser" / "web dashboard" → Web mode
- Sandboxed environment (Codex App, CI — no terminal control) → Web mode
- Otherwise → TUI mode

## TUI mode

```bash
python -m workflow_kit monitor
```

Rich terminal dashboard: task queue, in-review panel, live log, footer command bar.
Commands: `/pause`, `/resume`, `/skip <id>`, `/retry <id>`, `/quit`

## Web mode

```bash
python -m workflow_kit dashboard &
```

Tell user: "Dashboard at http://localhost:<dashboard_port from workflow.yaml, default 7860>"

Features: task cards with reviewer status, live log stream, goals viewer, pause/resume/retry buttons.
