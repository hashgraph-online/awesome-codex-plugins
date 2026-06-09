---
name: Anti-Pattern
kind: primitive
status: tracer
see-also: [entry, citation, slice]
---
# Anti-Pattern

An Entry whose subject is a specific failure mode of agent-assisted work,
named so that future sessions can recognize and refuse it.

## Definition

An Anti-Pattern is an Entry with `kind: anti-pattern` whose body contains:

- a **Signature** — the surface symptom an agent or operator would see
- a **Cost** — what gets lost or broken when the pattern is allowed to run
- a **Cause** — the upstream confusion or missing primitive that produces it
- a **Refusal** — the concrete sentence or action an agent should take when
  it detects the signature
- at least one **incident citation** anchored in this repo's history
  (commit SHA, `bd` issue, learning under `.agents/learnings/`)

Anti-Patterns are first-class citizens in the corpus, not afterthought
warnings. The lesson belongs in the vocabulary, not in scattered comments.

## When to use

- When a failure mode has been observed twice or more and the next session
  is at risk of repeating it.
- When a Slice has been corrupted by a recurring discipline gap and the
  cheapest fix is to name the pattern so future Slices can cite the
  refusal.

## Anti-pattern (yes, recursive)

- **The unnamed Anti-Pattern.** A failure described in chat or in a commit
  message but never written down as an Entry. Future sessions will repeat
  it because the lesson lives in a non-indexed surface.
- **The Anti-Pattern without an incident citation.** "Don't do X" with no
  link to a specific cost paid. Without evidence it gets tuned out as
  generic advice.
- **The Anti-Pattern that overlaps a Primitive Entry without distinguishing
  itself.** Anti-Patterns describe how primitives go wrong; they should
  not redefine the primitives themselves.

## Example in this codebase

- `.agents/learnings/2026-04-19-orchestrator-compression-anti-pattern.md`
  names the orchestrator-compression failure with signature, cost, and
  refusal. It is referenced by `skills/discovery/SKILL.md` directly. This
  is the shape Anti-Pattern Entries should match (current `.agents/`
  learnings are operator-local — the corpus equivalent here is the
  in-repo shipping copy).

## See also

- `entry.md` — the shape an Anti-Pattern Entry follows
- `slice.md` — what an Anti-Pattern damages when triggered
- `citation.md` — how Anti-Patterns get applied during Slices
