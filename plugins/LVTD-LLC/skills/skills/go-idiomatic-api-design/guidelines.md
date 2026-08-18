# Go Idiomatic API Design Guidelines

Load only the files needed for the decision at hand.

## By Task

| Task | Primary | Secondary |
|---|---|---|
| Create a package API | `references/api-design/rules.md` | `references/api-design/examples.md` |
| Review an exported change | `workflows/review-public-api.md` | `references/api-design/knowledge.md` |
| Introduce an interface | `references/api-design/rules.md` | `references/api-design/examples.md` |
| Review embedding, receivers, generics, or functional options | `workflows/review-public-api.md` | `references/api-design/knowledge.md` |
| Diagnose compatibility risk | `references/api-design/knowledge.md` | `workflows/review-public-api.md` |
| Change an API to improve performance | This skill, then `go-performance-testing` | `references/api-design/knowledge.md` |
| Write public examples | `references/api-design/examples.md` | `references/api-design/rules.md` |

## By Symptom

| Symptom | Load |
|---|---|
| Names repeat the package name | `references/api-design/rules.md` |
| Tests require a huge fake | `references/api-design/rules.md` |
| Callers mutate internal state | `references/api-design/knowledge.md` |
| A zero value panics or misbehaves | `references/api-design/knowledge.md` |
| A small change breaks many consumers | `workflows/review-public-api.md` |
| Interface compares non-nil on a success path | `references/api-design/knowledge.md`, `references/api-design/examples.md` |
| Slice, map, range, numeric, or Unicode invariant is unclear | Use `go-language-correctness` |

## Boundary

- Use `go-cli-application-architecture` for executable composition and adapters.
- Use `go-cli-errors-observability` for operational classification and presentation.
- Use `go-cli-testing` for general CLI test strategy.
- Use this skill for caller-facing Go package design and compatibility.
