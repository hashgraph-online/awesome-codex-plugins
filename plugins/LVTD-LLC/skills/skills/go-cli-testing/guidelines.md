# Go CLI Testing Guidelines

Use this file to route a CLI testing task to the smallest useful reference set.

## Workflows

| Task | Workflow |
|---|---|
| Build, stabilize, or review a complete command test suite | `workflows/test-cli-command.md` |
| Remove sleeps or diagnose nondeterministic tests | `workflows/stabilize-flaky-test.md` |

## By Task

| Task | Load |
|---|---|
| Plan a test strategy | `references/cli-testing/knowledge.md`, `references/cli-testing/rules.md` |
| Write unit or table-driven tests | `references/cli-testing/examples.md`, `references/cli-testing/patterns.md` |
| Test subprocesses or local integrations | `references/cli-testing/patterns.md`, `references/cli-testing/rules.md` |
| Review test quality and coverage | `references/cli-testing/checklist.md` |
| Benchmark, profile, or compare performance | Use `go-performance-testing` |
| Test inbound HTTP lifecycle | Use `go-http-server-applications` |
| Test SQL adapter behavior | `references/cli-testing/patterns.md`, then `go-cli-sql-storage` |
| Test goroutine lifecycle and backpressure | `references/cli-testing/patterns.md`, then `go-concurrency-pipelines` |

## By Code Element

| Element | Primary | Secondary |
|---|---|---|
| Command runner with injected streams | `references/cli-testing/examples.md` | `references/cli-testing/rules.md` |
| Table-driven test and helper | `references/cli-testing/patterns.md` | `references/cli-testing/examples.md` |
| Interface-backed dependency or fake | `references/cli-testing/patterns.md` | `references/cli-testing/rules.md` |
| Temporary files, env, network, or subprocess | `references/cli-testing/rules.md` | `references/cli-testing/checklist.md` |

## By Problem or Symptom

| Symptom | Load |
|---|---|
| Tests mutate globals or fail in parallel | `references/cli-testing/rules.md`, `references/cli-testing/patterns.md` |
| Tests sleep or intermittently time out | `references/cli-testing/patterns.md`, `references/cli-testing/checklist.md` |
| Stream parser fails only on fragmented input | `references/cli-testing/patterns.md`, then `go-language-correctness` |
| Overflow, aliasing, range, or Unicode case is unclear | Use `go-language-correctness`, then this skill |
| Assertions mirror implementation details | `references/cli-testing/knowledge.md`, `references/cli-testing/checklist.md` |
| External tools or services make tests unreliable | `references/cli-testing/patterns.md`, `references/cli-testing/rules.md` |

## Decision Tree

```text
What test boundary is involved?
├─ Pure command behavior → examples.md + rules.md
├─ Repeated cases or test fixtures → patterns.md
├─ Process, filesystem, environment, or network → patterns.md + checklist.md
├─ Performance benchmark or profile → go-performance-testing
├─ Inbound HTTP semantics → go-http-server-applications
├─ SQL driver, migration, or transaction semantics → go-cli-sql-storage
└─ Reviewing the suite
   ├─ Need acceptance criteria → checklist.md
   └─ Need rationale → knowledge.md
```

## File Index

| File | Purpose |
|---|---|
| `references/cli-testing/knowledge.md` | Testing boundaries, test levels, observability, and isolation |
| `references/cli-testing/rules.md` | Current Go testing rules and constraints |
| `references/cli-testing/examples.md` | Original command and test examples |
| `references/cli-testing/patterns.md` | Reusable test doubles, helpers, subprocess, and integration patterns |
| `references/cli-testing/checklist.md` | Implementation and review checklist |
| `workflows/stabilize-flaky-test.md` | Deterministic async and time-testing workflow |

## Common Combinations

| Scenario | Files |
|---|---|
| Add command tests | `rules.md` + `examples.md` |
| Stabilize flaky tests | `patterns.md` + `checklist.md` |
| Design a full suite | `knowledge.md` + `rules.md` + `checklist.md` |
