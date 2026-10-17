# Scene Cards

A scene card is the planning unit between a plot beat and a chapter draft:
one card per scene, each recording what changes. Use cards when a chapter
has multiple POV lines or timelines to braid, or when scenes need reordering
before drafting. They are the cheapest place to fix structure — reordering
cards costs minutes; reordering drafted scenes costs days.

## Card contents

One card per scene, with exactly these fields:

- **Scene id:** `chapter-{NN}-scene-{NN}` (matches the `scenes/` record id)
- **POV:** who carries the scene
- **Location:** where
- **Start state:** the situation, the POV character's emotional state, and
  the open question at the scene's beginning — one line each
- **Change:** what shifts by the scene's end (plot fact, relationship,
  knowledge, or emotional state). If nothing changes, the card has no reason
  to exist — cut, fold, or combine it.
- **End state:** the new situation and the new open question
- **Type:** Scene (goal → conflict → outcome) or Sequel (reaction → dilemma
  → decision); see `scene-sequel.md`
- **Try/fail position:** `try-1`, `try-2`, `try-3`, or `setback` when part
  of an escalation chain; see `try-fail.md`
- **Arcs advanced:** which arcs move in this scene (kebab-case ids)

Store the card in the scene's `scenes/` file under a `## Scene Card` section,
or as a block at the top of the chapter outline. Keep the format identical
everywhere so a later agent can read them.

## Reordering

Lay the cards out and check:

1. **Causality:** each card's start state must follow from the previous card's
   end state. Gaps are plot holes; contradictions are continuity errors.
2. **Escalation:** across the chapter, stakes, pressure, or emotional cost
   rise. A card that lowers tension after the midpoint needs a reason.
3. **Rhythm:** alternate scene types. Two pure action scenes back-to-back
   flatten; a sequel between them deepens both.
4. **Reader knowledge vs character knowledge:** mark cards where the reader
   learns something the POV character doesn't (or vice versa). Unplanned
   dramatic-irony gaps are continuity bugs; planned ones are logged in
   `continuity/questions/`.

## Braiding POV lines

When a chapter or sequence alternates POV characters:

1. Write one card stack per POV line.
2. Interleave so each line's cliffhanger resolves at least two of its own
   cards later — never cut away at a resolution, always at an unresolved
   question.
3. Record the interleave order in the chapter outline and mirror it in the
   `scenes/` card stack.

## When to ask the user

Reordering changes story shape. Present the proposed new order as a card list
(start state → change → end state per card) and get approval before rewriting
scene files or the chapter outline. Do not reorder silently.
