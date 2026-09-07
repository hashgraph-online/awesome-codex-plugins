# Go Language Correctness Guidelines

Load only the smallest reference set that answers the question.

## By Task

| Task | Primary | Secondary |
|---|---|---|
| Review agent-generated Go | `workflows/review-language-correctness.md` | `references/language-correctness/checklist.md` |
| Validate numeric parsing or arithmetic | `references/language-correctness/rules.md` | `references/language-correctness/examples.md` |
| Diagnose slice or map surprises | `references/language-correctness/knowledge.md` | `references/language-correctness/rules.md` |
| Review range-loop mutation | `references/language-correctness/rules.md` | `references/language-correctness/examples.md` |
| Review Unicode or string handling | `references/language-correctness/knowledge.md` | `references/language-correctness/checklist.md` |

## By Symptom

| Symptom | Load |
|---|---|
| Negative value became a large unsigned value | `references/language-correctness/rules.md` |
| Appending changed another slice | `references/language-correctness/knowledge.md`, `references/language-correctness/examples.md` |
| Small result retains a large input | `references/language-correctness/rules.md` |
| Map-backed output changes order | `references/language-correctness/checklist.md` |
| Range mutation has no effect | `references/language-correctness/examples.md` |
| Unicode input is truncated or miscounted | `references/language-correctness/knowledge.md` |
| Resource use grows inside a loop | `references/language-correctness/rules.md` |

## Boundary

- Use `go-cli-command-design` for user-facing grammar and diagnostics.
- Use `go-idiomatic-api-design` for exported compatibility and method sets.
- Use `go-concurrency-pipelines` when aliasing crosses goroutines.
- Use `go-cli-testing` to implement the resulting tests.
- Use `go-performance-testing` for measured allocation or retention work.

## File Index

| File | Purpose |
|---|---|
| `references/language-correctness/knowledge.md` | Guarantees, ownership, and version semantics |
| `references/language-correctness/rules.md` | Actionable implementation and review rules |
| `references/language-correctness/examples.md` | Compact bad/good Go patterns |
| `references/language-correctness/checklist.md` | Completion and code-review checks |
