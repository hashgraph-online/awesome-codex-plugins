# Rust Bevy State Flow Guidelines

Use this router to choose the right reference before changing Bevy state code.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Adding a new game phase | `workflows/add-state-flow.md`, `references/state-flow-patterns.md` |
| Reviewing plugin boundaries | `references/state-flow-patterns.md` |
| Fixing duplicated UI or entities after transitions | `references/state-flow-patterns.md` |
| Making pause/loading/menu logic reusable | `workflows/add-state-flow.md` |

## By Symptom

| Symptom | Load |
|---------|------|
| Systems run in the wrong game phase | `references/state-flow-patterns.md` |
| Menu entities remain after starting the game | `references/state-flow-patterns.md` |
| Transition logic is hidden inside many systems | `workflows/add-state-flow.md` |
| Plugins depend on setup order by accident | `references/state-flow-patterns.md` |

## Decision Tree

```text
Adding state flow?
|
+-- Is it a user-visible phase? -> AppState
+-- Is it a subsystem mode? -> Feature-specific state or resource
+-- Are entities spawned only for that phase? -> add cleanup marker
+-- Does logic run only in that phase? -> add run condition
+-- Does a transition have side effects? -> make transition explicit
```

## File Index

| File | Purpose |
|------|---------|
| `references/state-flow-patterns.md` | State, plugin, cleanup, and transition rules |
| `workflows/add-state-flow.md` | Step-by-step state implementation process |
