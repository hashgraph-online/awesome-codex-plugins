---
name: archive
description: Use at ship time to merge the spec into the living documentation, delete the staging spec and plan, and ask how to finish.
---
# Living documentation

Always in sync with code. Current ground truth only — atemporal, no history, no plans.

- `README.md` — for users: what it is, who for, how to use
- `docs/tech-spec.md` — for developers/agents: current system state (core backbone, ≤300 lines)
- `docs/specs/<topic>.md` — modular subsystem/protocol details; referenced by path
- `docs/ROADMAP.md` — direction (≥3 milestones or long-term)
- `CHANGELOG.md` — version history (`ship` maintains)
- `docs/decisions/` — architectural rationale (`context / choice / ruled-out`), append-only

## Living doc North Star

> **Standard**: Zero history, maximum truth density, instant scannability.
> - **The Razor**: Past rationale belongs in `docs/decisions/` or `CHANGELOG.md`; `docs/tech-spec.md` holds exclusively active ground truth.

1. **Atemporal**: Describes exclusively current ground truth. No version/milestone headers, changelog deltas, or supersession notes. Mutate in-place.
2. **Modular (Progressive disclosure)**: Bulky subsystem specs (>15 lines, schemas, complex state machines) live in `docs/specs/<topic>.md`, referenced by a one-line declaration in `tech-spec.md`.
3. **Structured & concise**: Atomic declarations (≤25 words per sentence). Multi-attribute contracts use structured bulleted lists or tables; no dense text blocks.

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

`<gate>` Before proceeding: (1) verify `tdd`/`subagents` have completed all tasks listed in the plan; (2) user has approved shipping/archiving this change (ship disposition or an explicit archive go-ahead). `</gate>`

1. **Merge** staging spec into living doc:
   - Integrate in-place into existing declarations; overwrite modified contracts rather than appending new sections.
   - Subsystem details >15 lines go to `docs/specs/<topic>.md`.
   - Maintain concise, structured formatting (lists/tables, no text walls).

2. **Roadmap** (if spec contains `## Roadmap`): update roadmap independently; do not duplicate into tech-spec.

3. **Decisions** (if spec or working notes contain a knowledge artifact — protocol spec, RE findings, architectural rationale): save to `docs/decisions/YYYY-MM-DD-<topic>.md` as `context / choice / ruled-out`.

`<gate>` Before deleting staging spec/plan, verify Living Doc North Star: (1) Atemporal (zero history/dates/supersessions)? (2) Truth-dense (binding facts only)? (3) Modular (subsystems >15 lines in docs/specs/)? (4) User approved merged living-doc. `</gate>`

4. **Delete** `docs/staging/specs/YYYY-MM-DD-<topic>.md` — content absorbed; Git has the history.
5. **Delete** `docs/staging/plans/YYYY-MM-DD-<topic>.md` — plans don't belong on `main`.
