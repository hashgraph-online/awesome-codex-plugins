---
name: tree-ring-memory
description: Use when Codex needs local-first recall, durable project decisions, privacy-safe memory capture, evidence records, audit, consolidation, or explicit forgetting through Tree Ring Memory.
---

# Tree Ring Memory

Use Tree Ring Memory as a lifecycle-aware memory layer, not as a transcript
dump.

Tree Ring Memory preserves meaningful agent learning:

- fresh work stays detailed
- older learning compresses into stable rings
- important warnings remain visible as scars
- durable truths become heartwood
- speculative future work stays as seeds
- sensitive data is blocked, redacted, or kept out by default

## First Check

If the current project contains Tree Ring files, read them before using global
assumptions:

```bash
.tree-ring/SKILL.md
.tree-ring/CLI.md
```

If the CLI is not installed, use the canonical project install guide:
<https://github.com/TerminallyLazy/Tree-Ring-Memory#install>

On macOS ARM64:

```bash
brew tap TerminallyLazy/tree-ring
brew install tree-ring
```

## When To Recall

Recall before:

- starting or resuming a project
- changing architecture, storage, security, privacy, or release behavior
- repeating a workflow where prior failures may matter
- responding to a user correction
- making a decision that depends on previous preferences or constraints
- closing meaningful work and deciding what should be remembered

Use narrow queries with project scope when possible. Prefer source-linked,
high-confidence, non-superseded results.

```bash
tree-ring recall "release behavior" --project example-service
```

## When To Remember

Store a memory only when the information is likely to help future work:

- the user states a durable preference
- the user corrects the agent
- a decision is made and should survive the current session
- a lesson is validated by tests, review, or production behavior
- a failed approach should not be repeated
- a security, privacy, release, or data-loss warning appears
- a useful project convention is discovered
- a future idea should be revisited later

Keep memory concise. Store the lesson, decision, warning, or evidence summary,
not the full conversation.

```bash
tree-ring remember "Use project-scoped recall before changing release behavior." \
  --event-type lesson \
  --scope project \
  --project example-service \
  --tag release \
  --tag workflow
```

Use `tree-ring evidence` when the lesson comes from an evaluation, checkpoint,
experiment, branch, incident, or reviewed run artifact.

```bash
tree-ring evidence "Migration smoke test passed with project-local memory." \
  --outcome promoted \
  --evidence-ref "runs/migration-smoke-001" \
  --score 0.91
```

Evidence outcome mapping:

- `promoted`: durable heartwood from supported evidence
- `rejected`: scar for reusable failed or rolled-back approaches
- `deferred`: seed for promising unresolved options
- `observed`: outer-ring evaluation result

## Ring Selection

Use these rings:

- `cambium`: active or recent task context
- `outer`: recent decisions and task lessons
- `inner`: older compressed project knowledge
- `heartwood`: durable, high-confidence truths and user preferences
- `scar`: failures, regressions, rejected approaches, and warnings
- `seed`: unresolved ideas, hypotheses, follow-ups, and future work

Do not promote to `heartwood` from weak evidence. Prefer `outer` or `seed`
unless the user confirms durability or the evidence is strong.

## Privacy And Forgetting

Do not store:

- secrets
- credentials
- tokens
- private keys
- raw chain-of-thought
- temporary scratchpad notes
- unverified claims as durable truth
- private health, financial, legal, or personal identifier details without
  explicit user instruction
- copyrighted source text beyond short allowed snippets

If memory is wrong, private, stale, or superseded:

- redact it when the durable shape is useful but details are unsafe
- delete it when it should not be retained
- supersede it when a newer decision replaces it
- include explicit reasons for every forget operation

```bash
tree-ring forget mem_example --mode delete --reason "example cleanup"
tree-ring audit --audit-type sensitive
tree-ring consolidate --period-type manual --dry-run
tree-ring maintain --apply-expired --repair-fts
```

## Source Adapters

Run adapter commands with `--dry-run` first. Sync only concise, source-linked
summaries; never treat imported memory as more authoritative than the source
`AGENTS.md`, Revolve record, evaluation, PR, issue, or test artifact.

```bash
tree-ring dox sync --source-root . --dry-run
tree-ring revolve sync --source-root revolve --dry-run
tree-ring integrations scan --source-root .
```

## Closeout Habit

At the end of meaningful work, ask:

- What did we decide?
- What did we learn?
- What should future agents avoid repeating?
- Did the user state a durable preference?
- Is there a future seed worth revisiting?
- Is any memory sensitive and better left unstored?

Only remember the answers that will materially improve future work.

Canonical project:

```text
https://github.com/TerminallyLazy/Tree-Ring-Memory
```
