---
name: Citation
kind: primitive
status: tracer
see-also: [entry, index-primitive]
---
# Citation

The mechanism by which one Entry references another, and by which an agent
records "I applied this Entry to this work."

## Definition

A Citation is an explicit, traceable mention of an Entry slug from one of:

- another Entry's `see-also` frontmatter or body
- a skill SKILL.md, hook script, or CLI doc
- a commit message, PR description, or `bd` issue body
- an `.agents/` artifact (plan, findings, post-mortem)
- the output an agent emits during a session

## Shape

Two forms:

1. **Entry-to-Entry** — in `see-also` frontmatter (a slug list) or inline as
   `` `entry-slug.md` `` in prose. Always slug, never concept name in prose
   citations.
2. **Application** — a session/agent claims it used an Entry by writing
   "applied: `entry-slug`" (or equivalent) somewhere durable (commit body,
   `bd` notes, `.agents/learnings/<date>-<topic>.md`). This is the **only**
   way the corpus compounds value over time.

## When to use

- Always cite when you apply a corpus Entry to a decision. Without Citations,
  the corpus accumulates entries but generates no evidence of utility.
- Cite from one Entry to another via `see-also` when concepts are
  conjoined-meaning (e.g. an Entry on a tracer bullet must cite the Entry on
  vertical slice).

## Anti-pattern

- **Loading without citing.** An agent that reads an Entry but does not record
  the application makes the corpus look unused and starves the maturity-
  weighting signal that future retrieval depends on.
- **Citing by concept name in prose, not by slug.** "We followed the Tracer
  Bullet principle" is unverifiable; `` `tracer-bullet.md` `` is.
- **Citing deprecated Entries** without a forward pointer to the canonical
  replacement.

## Example in this codebase

Every `see-also:` line in this corpus's frontmatter is a Citation. The
deprecated `ao inject` command (`cli/cmd/ao/inject.go:153`) records citation
events to `.agents/ao/citations.jsonl` — the same idea applied to the
existing learnings/patterns corpus.

## See also

- `entry.md` — what gets cited
- `index-primitive.md` — how Citations resolve to actual files
