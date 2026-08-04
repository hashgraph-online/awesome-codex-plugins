---
name: archive
description: Use at ship time to merge the spec into the living documentation, delete the staging spec and plan, and ask how to finish.
---
# Living documentation

Always in sync with code. Facts only — no plans, no interpretation.

- `README.md` — users: what it is, who for, how to use; links to tech-spec
- `docs/tech-spec.md` — developers/agents: current system state (see format below)
- `docs/specs/*.md` — split-out details when tech-spec grows too large; referenced by path
- `docs/ROADMAP.md` — direction (exists when ≥3 milestones or long-term)

Project artifacts — not merged into living docs:
- `CHANGELOG.md` — version history (`ship` maintains)
- `docs/decisions/` — architectural decisions, append-only

## tech-spec format

Declarations only.

```
purpose:      <what problem this solves — one sentence>
user:         <who uses this>
use-case:     <key scenarios, one line each>
architecture: <structural shape — one line, or see docs/architecture.md>
stack:        <language, runtime, frameworks, key deps>
entry:        <where execution starts>
contract:     <public APIs / interfaces that must not break — stability set; full surface by doc-coverage>
flow:         <name>: <trigger> → <steps> → <output>
              (complex — branching/async/multi-actor: one-line summary here, diagram in docs/specs/<flow>.md)
invariant:    <what must always hold>
constraint:   <limits, warnings from code>
convention:   <naming, file structure, test patterns, lint/format/typecheck tools, error-handling, security baseline>
milestone:    <current milestone> (see docs/ROADMAP.md)
```

# Archive

If `topology=multi-module` (triage announcement or coordinator spec/plan declaration), read `../references/multi-module.md`. Merge each module's artifacts in its own repository first. Then merge shared contracts and integration facts in the coordinator, record the revision set, and archive it last. Keep module-local facts in module repos.

`<gate>`Before proceeding: (1) verify `tdd`/`subagents` have completed all tasks listed in the plan; (2) confirm the user has provided explicit written approval.`</gate>`

1. **Merge** staging spec (minus roadmap) into living doc. Not copy-paste — integrate, preserve existing structure.

2. **Roadmap** (if spec contains `## Roadmap`): do not re-copy — roadmap updates independently.

3. **Decisions** (if spec or working notes contain a knowledge artifact — protocol spec, RE findings, architectural rationale): save to `docs/decisions/YYYY-MM-DD-<topic>.md` as `context / choice / ruled-out`.

`<gate>`  confirm the merged content with the user before deleting staging spec and plan. ` </gate>`

4. **Delete** `docs/staging/specs/YYYY-MM-DD-<topic>.md` — content absorbed; Git has the history.
5. **Delete** `docs/staging/plans/YYYY-MM-DD-<topic>.md` — plans don't belong on `main`.
