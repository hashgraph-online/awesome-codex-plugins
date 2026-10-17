# Go CLI Terminal Experience Guidelines

Load only the files needed for the current task.

## Workflows

| Task | Workflow |
|---|---|
| Define human, plain, and structured behavior | `workflows/design-output-modes.md` |
| Add prompts, progress, color, or sensitive credential entry | `workflows/add-safe-interaction.md` |
| Build a full-screen terminal application | `workflows/build-terminal-dashboard.md` |

## By Problem

| Symptom | Load |
|---|---|
| JSON is polluted by progress or color | `references/terminal-experience/rules.md` |
| CI hangs waiting for input | `references/terminal-experience/rules.md`, `workflows/add-safe-interaction.md` |
| Piped output exits as an error | `references/terminal-experience/knowledge.md` |
| Dashboard corrupts redirected output | `workflows/build-terminal-dashboard.md` |
| Secret appears in process listings or logs | `references/terminal-experience/examples.md` |

## Decision

```text
Was a mode explicitly requested?
├─ yes → honor it or return an unsupported-mode error
└─ no
   ├─ machine-readable output requested → structured
   ├─ relevant streams are terminals → human
   └─ otherwise → plain, noninteractive
```

## File Index

| File | Purpose |
|---|---|
| `references/terminal-experience/knowledge.md` | Modes, streams, capabilities, cancellation |
| `references/terminal-experience/rules.md` | Implementation and review rules |
| `references/terminal-experience/examples.md` | Go patterns and failure examples |
