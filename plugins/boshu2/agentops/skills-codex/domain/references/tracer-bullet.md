---
name: Tracer Bullet
kind: concept
status: tracer
see-also: [slice, primitive, entry, index-primitive, citation, anti-pattern]
---
# Tracer Bullet

The thinnest possible Slice that touches every layer of Primitive the larger
feature will eventually need, shipped as one Entry so the architecture
proves itself before any layer thickens.

## Definition

A Tracer Bullet is a Slice (see `slice.md`) constrained by three additional
rules:

1. It must traverse **every** Primitive type the eventual feature touches —
   one Entry per Primitive type, not one per Primitive instance.
2. It must produce a single artifact that can be cited (see `citation.md`)
   by every subsequent Slice in the feature, so growth happens by
   thickening, not by re-architecting.
3. The Index (see `index-primitive.md`) for the feature's corpus surface
   must be updated by the Tracer Bullet itself; new Entries added later
   register against the existing Index, not a new one.

If any of those three rules cannot be satisfied, the work is not a Tracer
Bullet — it is a regular Slice, and the architecture has not yet been
proven.

## When to use

- When starting a new domain area in the repo: design the corpus, the
  retrieval surface, the schema, and the consumer all together, but at
  minimum depth, in one Slice.
- When the operator and the agent do not yet share vocabulary for a
  feature: the Tracer Bullet doubles as the first Entry set
  (see `entry.md`) that future sessions cite.

## Anti-pattern

- **Tracer bullet that skips a Primitive type** (see `anti-pattern.md` for
  the corpus shape). If the Tracer Bullet covers skills + CLI + docs but
  omits a hook layer the eventual feature needs, the omitted layer's
  architecture is unproven and the next Slice has to back-fill from a
  position of weakness.
- **Tracer bullet without a registered Index update.** The shape works in
  isolation but is not discoverable, so the corpus does not actually
  compound. Identical-in-effect to no Tracer Bullet at all.
- **Multiple Tracer Bullets ahead of one consumer.** Architecting three
  parallel domain corpuses before any one has a citing skill is just
  speculation — pick one and prove a citation path through it first.

## Example in this codebase

This Entry is the Tracer Bullet for the `skills/domain/` corpus itself.
It traverses every structural Primitive of the corpus:

- `entry.md` (the Entry primitive — this file is one)
- `index-primitive.md` (the Index — this file is registered there)
- `citation.md` (every `see-also` and every backtick-slug in this file is a
  Citation)
- `primitive.md` (this Entry was composed by treating each prior Entry as a
  Primitive)
- `slice.md` (this Entry IS a Slice, scoped to the domain skill creation)
- `anti-pattern.md` (the Anti-pattern section above cites it by slug)

If you can read this file end-to-end and reconstruct what a Tracer Bullet
is using only the linked Entries, the corpus architecture has cleared its
first proof. If you cannot, one of the six primitives is wrong or missing
and we revise before writing any further Entries.

## See also

- `slice.md` — Tracer Bullets are a constrained Slice
- `primitive.md` — what the Tracer Bullet must traverse
- `entry.md` / `index-primitive.md` / `citation.md` — the corpus structure
  the Tracer Bullet proves
- `anti-pattern.md` — failure modes specific to the Tracer Bullet shape
