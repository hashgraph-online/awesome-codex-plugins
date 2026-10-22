# flow audit

Use only the section relevant to the current operation. Inline `scripts/` and `references/` paths are relative to this skill’s directory unless a link says otherwise. Existing authorization and the entrypoint contract govern these recipes.

## Cross-screen flow

For a NEW SCREEN write (not an edit), after the per-screen checks, answer these before the write:

1. Which flow the screen belongs to.
2. Which CTA of which existing screen brings the user here: a real node-id, or a "predecessor to
   build" stated in your reply so it stays in the transcript. A screen with no entry is born
   unreachable: refuse it.
3. Every interactive element on the new screen has a destination (node-id), a "plan to build"
   stated in your reply, or "out of scope" with a specific reason.

### Audit mode

Read-only. Use it on requests such as "audit the flow", "is there an orphan screen?", "where does
this button lead?".

Build the graph of the scope:

- device-sized frames = nodes
- `reactions[]` = wired edges
- CTA text = implicit edges. For example "Filter" implies a Filter screen and "See all" implies a
  list screen. Match the CTA text in whatever language the file uses, ignoring case and
  diacritics.

Emit a punch list. Never mutate the canvas.

- ORPHANS: a screen with no incoming edge (unreachable).
- DEAD ENDS: a screen that has CTAs but zero outgoing wired edges.
- DANGLING CTAs: an interactive element whose text implies a destination that is missing in the
  scope. Always quote the CTA text.
- WIRED-BUT-BROKEN: a reaction that points to a deleted or missing node.
- SEMANTIC MISMATCH: a wired reaction, inside the scope, whose target does not match the CTA text.
- CYCLES: informational, not a bug.

### Hard rules (paid for in production)

- NEVER auto-create a missing screen: half of the "missing" ones are out of scope on purpose.
  Surface it, list the candidates, the human decides. After that, the build belongs to your
  project's own build skill or workflow, if any.
- A wire that leads to a screen that does not match its CTA text is a SEMANTIC MISMATCH, not a
  "misroute". Check the project's product documentation (spec, flow map, handoff doc), if any,
  before you recommend a re-wire (field note, 2026-05: on one project a session reverted a wire
  based on a doc claim and the designer had to undo it).
- A project's glossary of implicit destinations (product terms that imply a specific screen)
  lives in the project's repo, not here. Apply it only inside that project's file.
- Back-navigation cycles are healthy. Do not report them as a problem.
