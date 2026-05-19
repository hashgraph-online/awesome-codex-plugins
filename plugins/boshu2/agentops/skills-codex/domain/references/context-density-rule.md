---
name: Context Density Rule
kind: concept
status: canonical
see-also: [citation, slice, primitive, tracer-bullet]
---
# Context Density Rule

Every context token should carry one of six payloads: intent, boundary,
evidence, decision, constraint, or next action.

## Definition

The Context Density Rule is the CDLC compression rule for agent work. A prompt,
packet, handoff, plan, verdict, or skill section earns its place in the context
window only when it changes what the agent can safely do next.

This is a rule for context units, not tokenizer math. One paragraph, table row,
or bullet can be dense when it carries a payload; a long explanation is sparse
when it only restates background.

## When to use

- Before adding prose to a prompt, packet, handoff, plan, or skill.
- When trimming context for a phase-specific agent window.
- When deciding whether a learning should promote into a skill, template, gate,
  or doctrine doc.
- When reviewing an orchestrator skill such as `rpi`, `discovery`, `plan`,
  `crank`, or `validation`.

## Payloads

| Payload | Meaning |
|---|---|
| Intent | What behavior, outcome, or user-visible change matters |
| Boundary | What bounded context, write scope, non-goal, or adapter seam applies |
| Evidence | What test, verdict, citation, metric, or artifact proves the claim |
| Decision | What was chosen, rejected, deferred, or escalated |
| Constraint | What must hold, must not regress, or must not be touched |
| Next action | What the agent or operator should do next |

## Anti-pattern

- **Context filler.** Prose that sounds useful but does not change intent,
  boundaries, evidence, decisions, constraints, or next actions.
- **Packet stuffing.** Adding every adjacent fact because it might help,
  instead of linking to a discovery surface and loading it only if needed.
- **Evidence-free doctrine.** Promoting a slogan into a skill or gate without a
  citation, test, incident, or operator decision behind it.

## Example in this codebase

`docs/cdlc.md` states the rule at the product-doctrine level. `$rpi` applies it
at the orchestration boundary: phase handoffs should preserve the objective
spine, bounded context, validation evidence, decisions, constraints, and next
action without carrying phase-local chat history forward.

## See also

- `citation.md` - how applied entries leave evidence
- `slice.md` - how dense context becomes a vertical work unit
- `tracer-bullet.md` - the thinnest proof-bearing slice
