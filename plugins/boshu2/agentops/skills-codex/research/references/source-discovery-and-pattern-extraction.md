# Source Discovery And Pattern Extraction

Use this reference for codebase archaeology, software-tool research, codebase reports, or mining reusable implementation patterns across one or more repositories.

## Discovery Order

1. Read the docs entry points first.
2. Find executable entry points: commands, handlers, jobs, hooks, or exported APIs.
3. Trace data flow from input to durable side effect.
4. Identify the core types and invariants that survive across layers.
5. Compare at least one working path with one edge path.
6. Only then summarize architecture, patterns, and risks.

## Pattern Extraction

Record a pattern only when it has:

- At least two concrete examples or one canonical implementation.
- A name that describes behavior, not a file location.
- Preconditions that say when the pattern applies.
- Failure modes that say when the pattern should not be reused.
- A pointer to validation evidence.

## Software Research Output

For external tools and libraries, write output in this order:

1. Current stable version and release date.
2. Supported command/API surface.
3. Config files, env vars, and hidden defaults.
4. Migration hazards and known issues.
5. Recommendation for this repo, including "do not adopt" when warranted.

## Report Shape

```markdown
## Summary
## Entry Points
## Core Flow
## Invariants
## Reusable Patterns
## Risks
## Open Questions
```

---

**Source:** Adapted from an external skill corpus / `codebase-archaeology`, `codebase-pattern-extraction`, `codebase-report`, and `research-software`. Pattern-only, no verbatim text.
