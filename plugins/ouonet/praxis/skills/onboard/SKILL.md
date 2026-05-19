---
name: onboard
description: Use when taking over an existing codebase that has no living document. Produces a factual record of what already exists.
---
# Onboard

Goal: read the codebase, produce living documentation. No code changes. No plans. No gap analysis.

## living documentation

- `README.md` : project overview, what it is, who it's for, how to use it. Links to the technical specification.
- `docs/tech-spec.md` : main technical specification.
- `docs/specs/*.md` : created by splitting out details from the main spec if they are too bulky or complex. Reference by path from the main spec.

technical specification is declarations only (no narrative), with facts only, no interpretation or plans. 

## Steps

1. **Explore** entry points, public interfaces, key dependencies, test patterns, file structure. Read, don't guess.
2. **Ask the user** about anything ambiguous — never invent architecture.
3. **Write** living documentation .

```
stack:       <language, runtime, frameworks, key deps>
entry:       <where execution starts>
contract:    <public APIs / interfaces that must not break>
convention:  <naming, file structure, test patterns>
invariant:   <what must always hold>
constraint:  <limits, warnings from code or README>
```

   If details are bulky, split into `docs/tech-specs/` and link.

4. **Confirm** with user.

<gate>`docs/tech-spec.md` must contain: `stack` + at least one `contract` + at least one `convention` before done.</gate>

## Don't
- Invent facts not found in code or README.
- Add gap analysis, plans, or code changes.
- Paste large code blocks — reference by path.

## After
`docs/tech-spec.md` on disk → user continues with normal `design → plan → tdd`.
