---
name: Entry
kind: primitive
status: tracer
see-also: [index-primitive, citation]
---
# Entry

The atomic unit of the domain corpus. Every concept, vocabulary noun, and
anti-pattern in this corpus is expressed as exactly one Entry.

## Definition

An Entry is a single markdown file under `skills/domain/references/` with:

- **Frontmatter** declaring `name`, `kind`, `status`, and `see-also`
- A one-line H1 matching `name`
- A **Definition** section (≤3 sentences)
- A **When to use** or equivalent applied section
- An **Anti-pattern** or **What it is not** section
- Optionally an **Example** anchored in this codebase by `file:line`
- A **See also** section listing related Entry slugs

## Shape (frontmatter contract)

```yaml
name: <PascalCase concept name>
kind: primitive | concept | anti-pattern
status: tracer | draft | canonical | deprecated
see-also: [<slug>, <slug>, ...]
```

## When to use

- Adding a vocabulary term that other Entries, skills, or agents will cite.
- Documenting a discipline (do-this) or anti-discipline (do-not-this) for
  agent-assisted work.

## Anti-pattern

- Multi-concept Entries. One Entry per concept; if two need to be referenced
  together, link via `see-also`, do not merge them.
- Long-form Entries (>1 page). If the concept needs more than one page, it is
  probably two concepts or it belongs in `docs/` as a narrative, not in the
  corpus as a definition.

## Example in this codebase

This file (`skills/domain/references/entry.md`) is itself an Entry. It uses
the frontmatter shape above and stays under one page.

## See also

- `index-primitive.md` — how Entries are discovered
- `citation.md` — how Entries reference each other
