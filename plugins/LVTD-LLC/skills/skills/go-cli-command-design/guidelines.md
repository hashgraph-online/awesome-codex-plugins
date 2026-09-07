# Go CLI Command Design Guidelines

Use this file to load only the command-design references needed for the task.

## Workflows

| Task | Workflow |
|---|---|
| Design or substantially change a command interface | `workflows/design-command-interface.md` |

## By Task

| Task | Load |
|---|---|
| Design a command contract | `references/command-interface/knowledge.md`, `references/command-interface/rules.md` |
| Implement flags, streams, or environment inputs | `references/command-interface/rules.md`, `references/command-interface/examples.md` |
| Review an existing command | `references/command-interface/checklist.md` |
| Learn the patterns through code | `references/command-interface/examples.md` |

## By Code Element

| Element | Primary | Secondary |
|---|---|---|
| `main`, `Run`, or command entry point | `references/command-interface/rules.md` | `references/command-interface/examples.md` |
| `flag.FlagSet` and usage output | `references/command-interface/knowledge.md` | `references/command-interface/rules.md` |
| stdin, stdout, and stderr | `references/command-interface/rules.md` | `references/command-interface/examples.md` |
| environment and filesystem dependencies | `references/command-interface/examples.md` | `references/command-interface/checklist.md` |

## By Problem or Symptom

| Symptom | Load |
|---|---|
| Tests depend on process-global flags or streams | `references/command-interface/rules.md`, `references/command-interface/examples.md` |
| Errors and normal output are mixed | `references/command-interface/knowledge.md`, `references/command-interface/checklist.md` |
| Behavior differs across terminals or operating systems | `references/command-interface/rules.md`, `references/command-interface/checklist.md` |
| Usage, exit behavior, or defaults are unclear | `references/command-interface/knowledge.md`, `references/command-interface/rules.md` |
| Numeric width, overflow, aliasing, range, or Unicode semantics are unclear | Use `go-language-correctness` |

## Decision Tree

```text
What are you doing?
├─ Defining behavior → knowledge.md + rules.md
├─ Writing command code
│  ├─ Need a pattern → examples.md
│  └─ Need constraints → rules.md
└─ Reviewing or debugging → checklist.md
   └─ Need rationale → knowledge.md
```

## File Index

| File | Purpose |
|---|---|
| `references/command-interface/knowledge.md` | Command contracts, inputs, outputs, errors, and portability concepts |
| `references/command-interface/rules.md` | Concrete design rules and current Go guidance |
| `references/command-interface/examples.md` | Original implementation examples |
| `references/command-interface/checklist.md` | Design and review checks |

## Common Combinations

| Scenario | Files |
|---|---|
| New command | `knowledge.md` + `rules.md` + `examples.md` |
| Focused review | `checklist.md` + the relevant section of `rules.md` |
