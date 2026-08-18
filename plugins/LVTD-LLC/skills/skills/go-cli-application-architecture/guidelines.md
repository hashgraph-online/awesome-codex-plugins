# Go CLI Application Architecture Guidelines

## Workflow

| Task | Workflow |
|---|---|
| Design a new CLI or untangle an existing one | `workflows/design-application-boundaries.md` |
| Review files, pools, bodies, timers, or background tasks | `workflows/review-resource-lifecycle.md` |

## By Symptom

| Symptom | Load |
|---|---|
| Cobra command contains API and storage logic | `references/application-architecture/rules.md` |
| Tests require global mutation | `references/application-architecture/examples.md` |
| Interfaces package imports everything | `references/application-architecture/knowledge.md` |
| Config reload mutates shared globals | `references/application-architecture/rules.md` |
| Repository abstraction has dozens of methods | `references/application-architecture/examples.md` |
| Public package API is difficult to evolve | Use `go-idiomatic-api-design` |
| HTTP handlers own domain behavior | Use this skill, then `go-http-server-applications` |
| SQL pool and transactions have unclear owners | Use this skill, then `go-cli-sql-storage` |
| Application exposes internal worker channels | Use this skill, then `go-concurrency-pipelines` |
| Slice, map, range, or Unicode semantics are unclear | Use `go-language-correctness` |
| A boundary is changing only for speed | Establish evidence with `go-performance-testing` first |

## Decision

```text
Does code describe CLI syntax or rendering?
├─ yes → command adapter
└─ no
   ├─ coordinates a user action → application service
   ├─ enforces core invariant → domain/core package
   └─ talks to network, disk, process, clock → adapter behind a narrow seam
```

## File Index

| File | Purpose |
|---|---|
| `references/application-architecture/knowledge.md` | Layers and dependency direction |
| `references/application-architecture/rules.md` | Package and construction rules |
| `references/application-architecture/examples.md` | Practical Go patterns |
| `workflows/review-resource-lifecycle.md` | Ownership, cleanup, and partial-startup review |
