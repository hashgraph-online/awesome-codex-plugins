# Human Dashboard and TUI Surfaces

These surfaces are for humans, not agents trying to automate NTM.

## Primary Commands

```bash
ntm dashboard myproject
ntm palette myproject
ntm bind
ntm view myproject
```

- `dashboard`: live operator overview
- `palette`: fuzzy searchable command launcher
- `bind`: install convenience bindings such as the palette keybinding
- `view`: quick way to tile and attach

## Command Palette

```bash
ntm palette myproject
```

Useful keys:

| Key | Action |
| --- | --- |
| `↑/↓` or `j/k` | Navigate |
| `1-9` | Quick select |
| `Enter` | Execute |
| `?` | Help |

## Dashboard Notes

The dashboard is useful when:

- you are tending a swarm manually
- you want pane-level visual status
- you need a fast operator overview of sessions, activity, history, and focus

It is the wrong tool when:

- another agent or script needs deterministic state
- you need replayable automation
- you are trying to integrate with external systems

In those cases, use `--robot-*` or `ntm serve`.

## Useful Internal Notes for NTM Contributors

If you are working on NTM itself, these dashboard architecture notes are still useful:

| File | Purpose |
| --- | --- |
| `model.go` | Model structs, types, constants |
| `lifecycle.go` | Init, cleanup, subscriptions |
| `keymap.go` | Keymap and help bindings |
| `messages.go` | Messages and refresh intervals |
| `popup.go` | Popup / overlay rendering |
| `run.go` | Entry points |
| `dashboard.go` | Core update/view path |
| `focus.go` | Focus management |

The TUI stack also leans heavily on Bubble Tea and the Charmbracelet ecosystem.
That is useful context when changing dashboard behavior or trying to trace a rendering issue.
