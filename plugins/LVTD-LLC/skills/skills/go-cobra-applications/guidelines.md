# Go Cobra Applications Guidelines

Use this file to route Cobra and Viper application work to focused references.

## Workflows

| Task | Workflow |
|---|---|
| Build or restructure a testable Cobra command tree | `workflows/build-cobra-command-tree.md` |

## By Task

| Task | Load |
|---|---|
| Design a command tree | `references/cobra-applications/knowledge.md`, `references/cobra-applications/rules.md` |
| Implement root and subcommands | `references/cobra-applications/examples.md`, `references/cobra-applications/patterns.md` |
| Add flags, configuration, or environment binding | `references/cobra-applications/rules.md`, `references/cobra-applications/patterns.md` |
| Review a Cobra application | `references/cobra-applications/checklist.md` |

## By Code Element

| Element | Primary | Secondary |
|---|---|---|
| `cobra.Command` tree | `references/cobra-applications/rules.md` | `references/cobra-applications/examples.md` |
| `RunE`, arguments, and business logic | `references/cobra-applications/patterns.md` | `references/cobra-applications/checklist.md` |
| persistent/local flags and Viper binding | `references/cobra-applications/rules.md` | `references/cobra-applications/patterns.md` |
| completion and generated docs | `references/cobra-applications/knowledge.md` | `references/cobra-applications/checklist.md` |

## By Problem or Symptom

| Symptom | Load |
|---|---|
| Command constructors mutate package globals | `references/cobra-applications/patterns.md`, `references/cobra-applications/checklist.md` |
| Configuration precedence is surprising | `references/cobra-applications/knowledge.md`, `references/cobra-applications/rules.md` |
| Tests cannot isolate command output or arguments | `references/cobra-applications/examples.md`, `references/cobra-applications/patterns.md` |
| Generated setup differs from current Cobra tooling | `references/cobra-applications/rules.md`, `references/cobra-applications/checklist.md` |
| Parsed value may narrow, overflow, alias, or mishandle Unicode | Use `go-language-correctness` after Cobra binding |

## Decision Tree

```text
What are you changing?
├─ Command hierarchy → knowledge.md + rules.md
├─ Command implementation → examples.md + patterns.md
├─ Flags or configuration → rules.md + patterns.md
└─ Tests, completion, docs, or review → checklist.md
```

## File Index

| File | Purpose |
|---|---|
| `references/cobra-applications/knowledge.md` | Cobra architecture, lifecycle, configuration, completion, and docs |
| `references/cobra-applications/rules.md` | Current Cobra/Viper design rules |
| `references/cobra-applications/examples.md` | Original command-tree and testable-constructor examples |
| `references/cobra-applications/patterns.md` | Dependency injection, configuration, and command composition patterns |
| `references/cobra-applications/checklist.md` | Build and review checklist |

## Common Combinations

| Scenario | Files |
|---|---|
| New Cobra application | `knowledge.md` + `rules.md` + `examples.md` |
| Add a testable subcommand | `patterns.md` + `examples.md` |
| Audit configuration behavior | `rules.md` + `checklist.md` |
