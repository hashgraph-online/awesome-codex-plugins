---
name: memory-setup
description: Use when the user explicitly invokes `/memory-setup` or explicitly asks to initialize Wingman memory files in the current repository. Do not use for ordinary work, memory loading, memory syncing, or setup of unrelated tools.
---

# Memory Setup

Initialize the Wingman memory workflow for the current repository. Create files on disk; do not merely print templates.

This is an explicit workflow skill. Only proceed when the user directly asks for Wingman memory setup.

## Paths

Use `.wingman/` as the platform-neutral data root.

Create:

- `.wingman/memory/`

Seed:

- `.wingman/memory/brief.md`
- `.wingman/memory/context.md`

Do not create `domains/` or `history/` during initial setup. Those areas are created on demand when durable domain truth or history events first need to be written.

If `.wingman/memory/` already exists, treat setup as a repair operation: create missing core files, but never overwrite existing user-authored memory files.

## Brief Template

Write `.wingman/memory/brief.md`:

```markdown
# Memory Brief

## 0. Memory Settings
- **Language**: `auto`

## 1. Architecture Decisions (ADR - Global Rules)
> Record global rules that affect the whole project. Each rule must include `[WHY]`.
> ADR status values: `proposed | accepted | deprecated | superseded`.

## 2. Domain Registry
| Domain | Read When | Current File | History Domain Index | History Topics | Aliases | Related Domains | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |

Registry status values describe whether a domain is still used for routing: `current | deprecated | superseded`.
`Current File` is the authoritative current-truth file or folder index. `History Domain Index` and `History Topics` are lookup indexes for historical context, not current truth. `Related Domains` are read only when relevant to the task.

## 3. Memory Layout
- `brief.md`: global rules, ADRs, memory settings, and the Domain Registry.
- `context.md`: hot task context, pending work, and recent high-signal logs. It is not a long-term knowledge base.
- `domains/`: current durable domain truth, created on demand.
- `history/events/`: event bodies, created on demand.
- `history/domains/`: domain projection indexes for feature-time lookup.
- `history/topics/`: topic projection indexes for feature and problem-cluster lookup.
- `history/months/`: date projection indexes for date-based lookup.
- Context logs should preserve the reason for non-trivial short-term changes. Durable rules with binding force belong in `domains/` or `brief.md`; historical explanation belongs in `history/`.

## 4. Authority Order
Current rules override old events:

1. `brief.md` global rules and current ADRs.
2. `domains/` current domain truth.
3. `context.md` hot working context.
4. `history/` past events and audit trail.
```

Set `Language` to the user's preferred memory language when clear, such as `zh-CN` or `en`. Use `auto` when unclear. Future memory updates should follow this setting.

## Context Template

Write `.wingman/memory/context.md`:

```markdown
# Memory Context

## Pending Tasks
- [ ] To be planned

## Current Work
- None yet.

---
## Recent Logs
### [Init] Wingman memory enabled
- **Goal**: Enable repository-scoped Wingman memory so agents can load current project context before work and sync important outcomes afterward.
- **Reason**: Establish a lightweight default-read memory root; prevents future sessions from relying only on chat history.
- **Core Files**:
  - `.wingman/memory/brief.md`: [Memory Brief] - Stores global ADRs, memory settings, and the Domain Registry.
  - `.wingman/memory/context.md`: [Memory Context] - Stores short-term progress, pending tasks, and recent work context.
- **Verification / Notes**: `domains/` and `history/` are created only when durable domain truth or history events emerge.
```

## On-Demand Domain Shape

When durable domain knowledge first appears, create either `.wingman/memory/domains/<domain>.md` for a small domain or a folder domain for a large domain:

```text
domains/<domain>/index.md
domains/<domain>/<topic>.md
```

Use `.wingman/memory/domains/<domain>/index.md` as the authoritative current-truth index for a folder domain and keep focused topic files beside it.

Use this shape when no stronger local format exists:

```markdown
# <Domain> Domain

## When To Read This Domain
- <task signal>

## Current Truths
- `<rule>` [WHY]: `<reason>`
  - **Evidence**: `<user statement | docs/schema/tests/spec | implementation>`
  - **Applies When**: `<future task condition>`
  - **Status**: `current | deprecated | superseded`
  - **Since**: `YYYY-MM-DD`
  - **Supersedes**: `<old rule or None>`
  - **Related Domains**: `<domain list or None>`
  - **History**: `<history/events/YYYY/MM/YYYY-MM-DD-<event-slug>.md or None>`

## Subfiles
- `topic.md`: when this file should be read
```

Only `current` truths are binding. `History` is an optional backlink; do not invent events just to fill the field.

## On-Demand History Shape

When historical event retention is needed, create:

```text
.wingman/memory/history/
  index.md
  domains/
    <domain>.md
  topics/
    <topic>.md
  months/
    YYYY-MM.md
  events/
    YYYY/
      MM/
        YYYY-MM-DD-<event-slug>.md
```

History stores past events, not current rules. Event bodies stay under `events/YYYY/MM/` and are the single source of truth for historical events. `domains/`, `topics/`, and `months/` under history are projection indexes containing links and short summaries only. Current implementation constraints belong in `brief.md` or `domains/`.

## Finish

Report the created or updated paths.
