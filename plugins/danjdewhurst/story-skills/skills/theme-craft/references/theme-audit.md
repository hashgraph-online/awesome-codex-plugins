# Theme Audit

A revision-time audit that checks whether the story *dramatizes* its theme —
through choices, consequences, and the ending's verdict — rather than merely
declaring it. Run this after a complete draft exists, as part of a
developmental revision pass (see the `revision-continuity` skill).

## Audit procedure

1. **Recover the working premise.** Read `premise:` and `counter-premise:`
   from `story.md` frontmatter. If `premise: tbd-discovery`, draft the
   premise the manuscript *actually argues* (value + cause, one sentence —
   see `controlling-idea.md`) before auditing. Record the recovered premise
   in `story.md`.
2. **Trace the value through the draft.** For each act (or each third of the
   chapters), note one scene where the protagonist's choice engages the
   value continuum, and whether the scene *cost* the protagonist something.
   Theme without cost is theme stated, not dramatized.
3. **Check the ending against the opening.** The opening poses the
   value-question (usually unknowingly: the protagonist acts on the lie).
   The ending must *engage* that question — not necessarily answer it
   cleanly, but the climax must stage premise vs. counter-premise and deliver
   a verdict the preceding story earned.
4. **Check the antagonist.** Re-read `antagonist-design.md`'s checklist
   against the draft: did the antagonist's counter-premise get a fair
   hearing? Did they win scenes? Is their climax defeat a *thematic* defeat?
5. **Check the motifs.** Every row in the motif ledger (see
   `motif-symbolism.md`) must be `paid-off`, or have a recorded reason for
   being left open.
6. **Check the arcs.** For each significant character with an `arc-type`
   (see `lie-truth.md`), verify the turning points contain what the arc type
   requires — growth beats for change-positive, refused truths for
   change-negative, escalating tests of steadfastness for flat.

## The five audit questions

Answer each in one or two sentences, with chapter references:

1. **Does the ending engage the opening's value-question?** Quote the
   opening's implicit question and the ending's verdict. If the ending
   resolves a different question, either the premise or the ending is wrong.
2. **Is theme dramatized through consequence, not commentary?** List the
   three most expensive choices the protagonist makes. If the theme is
   mostly delivered in dialogue speeches, narration summaries, or a mentor's
   lecture, flag it: move the theme into choices with costs.
3. **Is the motif paid off?** Every planted motif needs its ending
   resonance; see the motif ledger.
4. **Does the climax stage premise vs. counter-premise?** The final
   confrontation must be *about* the value, not adjacent to it. A climax
   won by superior firepower after a thematic story is a broken promise.
5. **Would the story collapse without the theme?** If you can remove the
   premise and the plot still works, the theme is decoration — wire the
   value into the protagonist's decisions or cut the pretense.

## Recording findings

Write the audit as `continuity/theme-audit.md` (one file per project,
updated each revision round) with the premise, the five answers, and a
**verdict**: `theme-holds` (minor fixes) or `theme-broken` (structural
revision needed, with the specific scenes to rework listed). If the audit
changes the premise, update `story.md`'s `premise:` field and the theme
tracking in `plot/_index.md`, then run `story reindex .`,
`story wordcount . --write`, and `story check .`.
