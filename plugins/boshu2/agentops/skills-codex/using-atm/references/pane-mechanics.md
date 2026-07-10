# ATM pane mechanics — peer duels and raw tmux key injection

> **Provenance.** Extracted verbatim from `skills/using-atm/SKILL.md`
> (payload-diet, age-verification-economics-ebec.8 / age-skills-audit-fable-l6ic.8).
> This is genuinely ATM-substrate-specific pane/tmux mechanics (spawn/send/goal
> lifecycle and raw key injection), not tending doctrine — it stays owned by
> `using-atm`. For the tending decision layer see [`../../ntm/SKILL.md`](../../ntm/SKILL.md).

## Fresh Claude/Codex Peer Duels

When the operator asks for "a fresh Claude and Codex", "fresh peer models", a
"duel", or a cross-family opinion, the default substrate is **ATM panes**, not
headless one-shot CLIs. Spawn exactly the requested model families, give both
the same bounded prompt, verify engagement, collect pane output, and kill the
temporary session when done. Do **not** use `claude -p` / `claude --print` for
this shape; use an interactive Claude pane. Use headless `codex exec` only when
the operator explicitly asks for headless execution or there is no pane/TUI
requirement.

Minimal bounded pattern:

```bash
atm spawn agentops --label navi-duel --no-user --cc=1:opus --cod=1:gpt-5.5 \
  --no-cass-context --ready-timeout=2m --json

# Claude pane: direct prompt is fine.
atm send agentops--navi-duel --pane=1 --file prompt.md \
  --no-cass-check --force-non-interactive --json

# Codex pane: use the goal lifecycle and prove engagement.
atm codex preflight --session agentops--navi-duel --pane 2 --json
atm send agentops--navi-duel --pane=2 --codex-goal --file prompt.md \
  --no-cass-check --force-non-interactive --json
atm codex wait-goal-engaged --session agentops--navi-duel --pane 2 --json

# After collecting outputs, do not leave idle duel panes around.
atm kill agentops--navi-duel --json
```

If the requested model alias resolves to a nearby available runtime (for
example `opus` resolving to the installed Opus build), report the actual pane
model in the closeout instead of silently claiming the requested alias.

## Raw tmux Key Injection (Last Resort)

Prefer `atm send`, `atm codex ...`, or NTM robot send surfaces for dispatch. Use
raw `tmux send-keys` only for direct TUI/menu control, emergency pane relay, or
when the robot surface cannot express the action.

When you do use raw tmux, **submit with `C-m` and verify it landed**. Do not rely
on a trailing literal `Enter` token in automation; in live pane relay it can
leave text sitting in the input buffer. The safe pattern is:

```bash
tmux send-keys -t <target-pane> -- "<message>"
tmux send-keys -t <target-pane> C-m
tmux capture-pane -pt <target-pane> -S -30
```

The capture must show that the input line cleared and the pane started reacting
(thinking/working indicator, echoed command output, or new prompt movement). If
the message is still visibly parked in the input box, send another `C-m` and
capture again. Codex-family TUIs may need two or three `C-m` submits after a
large paste; never fire-and-forget a raw tmux relay.

For gate/unblock replies, a capture that only shows text sitting in the input
box is not delivery. The answer must be visible as accepted pane input/output or
recorded in a durable artifact the peer can inspect (bead note or PR comment).
