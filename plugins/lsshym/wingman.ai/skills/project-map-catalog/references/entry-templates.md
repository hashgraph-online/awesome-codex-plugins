# Project Map Entry Templates

Use these templates when creating or updating entries. Keep content concise and evidence-based. Use `None known` or `Unknown` when evidence is missing.

## Contents

- [Shared Fields](#shared-fields)
- [Feature Entry](#feature-entry)
- [Flow Entry](#flow-entry)
- [Surface Entry](#surface-entry)
- [Component Entry](#component-entry)
- [Module Entry](#module-entry)
- [Utility Entry](#utility-entry)
- [Pattern Entry](#pattern-entry)
- [Contract Entry](#contract-entry)
- [Domain Entry](#domain-entry)
- [Glossary Term Entry](#glossary-term-entry)
- [Index Row](#index-row)

## Shared Fields

All entries should include:

```markdown
# [Name]

## Kind

`feature | flow | surface | component | module | utility | pattern | contract | domain | glossary-term`

## Status

`Preferred | Stable | Experimental | Legacy | Deprecated | Unknown`

## Last Verified

- Date: `YYYY-MM-DD`
- Evidence:
  - `[path or user-confirmed context]`: [what was verified]

## Evidence Level

`Source-Verified | User-Confirmed | Inferred | Stale`

## Tags

- `[tag]`

## Summary

[1-3 sentences. What this is and why it matters.]

## Entry Points

- `[path, route, command, or trigger]`: [how users/agents reach it]

## Key Files

- `[path]`: [role]

## Related Entries

- `[entry path]`: [relationship]

## Use When

- [Concrete fit.]

## Do Not Use When

- [Concrete mismatch.]

## Notes For Agents

[Decision guidance for future AI agents.]
```

## Feature Entry

Add these sections when the kind is `feature`:

```markdown
## User-Facing Behavior

[What the user can do. Use business language.]

## Business Meaning

[Why this feature exists and what domain concept it belongs to.]

## Data And Contracts

- `[contract entry or source]`: [request/response/type meaning]

## Reusable Parts

- `[component/module/utility/pattern]`: [what can be reused or referenced]

## Similar Features

- `[feature entry]`: [how it differs]

## Known Constraints

- [Permissions, state assumptions, domain rules, data shape limits.]
```

## Flow Entry

Add these sections when the kind is `flow`:

```markdown
## Trigger

[What starts the flow.]

## Steps

1. [Step]
2. [Step]

## State And Transitions

- `[state]` -> `[state]`: [condition]

## Failure Modes

- [Error or edge case]: [handling]

## Reusable Parts

- [What can be reused or referenced.]
```

## Surface Entry

Add these sections when the kind is `surface`:

```markdown
## Route Or Entry

- `[route/menu/modal trigger]`

## User Tasks

- [Task]

## Key Components

- `[component entry/source]`: [role]

## Backing Features

- `[feature entry]`

## Permissions

- [Permission or role assumptions]
```

## Component Entry

Add or emphasize:

- Used By
- Domain Assumptions
- Visual / Interaction Traits
- Extension Points

## Module Entry

Add or emphasize:

- Owns Responsibility
- Inputs
- Outputs
- Side Effects
- State Dependencies
- Related Contracts

## Utility Entry

Add or emphasize:

- Signature
- Return Shape
- Purity / Side Effects
- Error Behavior
- Used By

## Pattern Entry

Add or emphasize:

- Problem
- Pattern
- Example Implementations
- Tradeoffs
- Avoid When

## Contract Entry

Add or emphasize:

- Producer
- Consumer
- Fields
- Required / Optional
- Semantic Meaning
- No-Substitute Fields

## Domain Entry

Keep lightweight. Answer:

- Which features belong here?
- Which terms matter?
- Which surfaces/modules are primary?
- Which old implementations should be avoided?

## Glossary Term Entry

Use:

```markdown
## Meaning

[Business meaning.]

## User Phrases

- [What users may say]

## Code Names

- `[symbol/path/keyword]`: [meaning]

## Search Hints

- `[rg pattern]`
```

## Index Row

Top-level and section indexes should use short rows:

```markdown
| [Name] | `[section]/[slug].md` | [Status] | `[tag1, tag2]` | `[route/source]` | [Best For] |
```
