---
name: tmux-layout
description: Use this skill when the operator wants a prepared tmux visualization layout for the session's side-channels (STATE.md tail, CI-watch, events.jsonl tail). Renders a 4-pane default layout or debug layout. Read-only side-channel observability — the coordinator chat stays in the operator's original terminal. Trigger phrases: "tmux layout", "split panes for ci watch", "visualize session side-channels", "show me state-md tail and ci".
model: inherit
color: cyan
tools: Read, Bash, Grep, Glob
---

# tmux-layout — Operator-Side Visualization Substrate

> Status: PROPOSED per ADR-0007 (`docs/adr/0007-tmux-visualization-substrate.md`). Opt-in skill — NOT default.
> Project-instruction file resolution: this is `CLAUDE.md` on Claude Code / Cursor IDE; the equivalent on Codex CLI is `AGENTS.md`. See `skills/_shared/instruction-file-resolution.md`.

## Purpose

Render a prepared tmux layout for *operator-side observability* of the session's asynchronous side-channels — STATE.md updates, CI status, events.jsonl wave/gate transitions. NOT a coordinator chat surface, NOT a wave-agent host. The coordinator chat remains in the operator's original terminal, period (per AUQ-001 in `.claude/rules/ask-via-tool.md`).

## When to Use

- During a long deep-session when you want CI status visible alongside Quality-Gate output without polling `glab ci status` manually.
- During `/debug` Phase 2 hypothesis testing (use `--layout debug`).
- Anywhere `tail -F .claude/STATE.md` + a CI watcher would speed up your loop.

## When NOT to Use

- For wave-agent visualization — wave agents are in-process `Agent()` calls; no PID, no TTY, no pane to attach.
- For autopilot multi-story panes — autopilot.jsonl currently shows 11 entries / 8 dry-runs; below the value threshold for a pane-per-story UI.
- As your coordinator chat surface — that stays in the terminal where you invoked /tmux-layout.

## Usage

```
/tmux-layout                        # default layout (4 panes)
/tmux-layout --layout debug         # debug layout (4 panes, /debug companion)
/tmux-layout --json                 # machine-readable output (no attach)
/tmux-layout --session-name my-ws   # custom tmux session name
/tmux-layout --force                # replace existing session (PSA-003 escape hatch)
/tmux-layout --help                 # full CLI usage
```

The skill prints a one-line tmux command. Paste it into a SECOND terminal (do not run it where /tmux-layout was invoked). That second terminal becomes the layout. Your original terminal (the coordinator chat) stays where it is.

## Default Layout (4 panes)

| Pane | Content | Command |
|---|---|---|
| 1 | **Shell** (operator scratch — NOT claude) | `bash` (interactive) |
| 2 | STATE.md tail | `tail -F <state-dir>/STATE.md` |
| 3 | CI watch (poll-loop wrapper) | `while true; do clear; glab ci status --pipeline-id LATEST --output json \| jq ...; sleep 15; done` |
| 4 | events.jsonl wave/gate filter | `tail -F .orchestrator/metrics/events.jsonl \| jq --line-buffered 'select(.event \| test("wave\|gate\|spiral"))'` |

`<state-dir>` is resolved via `resolveStateDir()` from `scripts/lib/platform.mjs` (`.claude/`, `.codex/`, or `.cursor/`).
Pane 3 command is vcs-aware (`glab` for gitlab, `gh pr checks` for github, informational `echo` fallback when no CLI).

## Debug Layout (4 panes — `--layout debug`, depends-on #562)

| Pane | Content | Command |
|---|---|---|
| 1 | **Shell** (operator scratch) | `bash` (interactive) |
| 2 | Hypothesis-test runner | `npm test -- --watch <scope>` (or per-skill-config) |
| 3 | Debug-artifact tail | `tail -F .orchestrator/debug/*.md` |
| 4 | Diff-watch | `watch -n 2 'git diff --stat \| head -30'` |

## Architecture

Three sibling modules under `scripts/lib/tmux-layout/`:

- `layouts.mjs` — `renderDefaultLayout()`, `renderDebugLayout()`, `detectVcsCommand()`.
- `vcs-detector.mjs` — `detectVcsCommand({config, projectRoot})` returns `{bin, args, fallback, blocking}` per vcs key.
- `tmux-shell.mjs` — `detectTmuxVersion()`, session-collision policy helpers.

Entry point: `scripts/tmux-layout.mjs` (parseArgs from `node:util`, dispatcher to layout functions).

## PSA-003 Compliance

Session-collision policy: **refuse + `--force`**. The skill NEVER kills, overwrites, or modifies a tmux session it did not create unless the operator passes `--force` explicitly. See `.claude/rules/parallel-sessions.md` § PSA-003.

## AUQ-001 Compliance

The coordinator chat (where AskUserQuestion fires) stays in the operator's ORIGINAL terminal. Pane 1 of the tmux layout is intentionally a scratch shell, NOT a new `claude` session — there is no second AUQ surface, no decision-authority split. See `.claude/rules/ask-via-tool.md` § AUQ-001.

## Telemetry & Promotion Gate (#563)

This skill emits structured events to `.orchestrator/metrics/events.jsonl`:
- `tmux-layout.invoked`
- `tmux-layout.degraded` (tmux missing, version too old, session collision without --force, etc.)
- `tmux-layout.completed` (when the user closes the tmux session)

Promotion criteria from opt-in skill to default-recommended in session-start banner: invocation count ≥ 5 across ≥ 3 distinct deep sessions over ≥ 2 calendar weeks, layout-completion rate ≥ 80%, zero AUQ-001 / PSA-003 regressions. See ADR-0007 § Follow-ups.

## Troubleshooting

- **tmux not found** → install: `brew install tmux` (macOS) / `apt install tmux` (Linux). Minimum tmux ≥ 3.0.
- **Session already exists** → use `--force` (acknowledges PSA-003) or `--session-name my-other`.
- **CI pane shows nothing** → `glab` or `gh` not installed, or `vcs:` not set in `## Session Config`. Pane will show a clear fallback message.

## See Also

- `docs/adr/0007-tmux-visualization-substrate.md` — design rationale.
- `skills/_shared/monitor-patterns.md` — comparison: tmux-layout vs Monitor vs /loop.
- `skills/debug/SKILL.md` — Phase 2 hypothesis testing (use `--layout debug` as companion).
- GitLab #561 #562 #563.
