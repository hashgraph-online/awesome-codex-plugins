# Try/Fail Cycles and the Five Commandments

Two scene-grain structure tools for pacing the middle of chapters and giving
every scene a checkable shape. Both are widely-published craft concepts;
this is a summary, not a reproduction of any commercial methodology.

## Try/Fail cycles

From Dwight Swain's *Techniques of the Selling Writer*: most scenes in a
chapter should be **attempt scenes** — the POV character tries something and
fails. Escalate across attempts within the chapter:

1. **First attempt fails** — the obvious solution doesn't work.
2. **Second attempt fails worse** — the clever solution backfires, and the
   situation is now worse than before the attempt.
3. **Third attempt leads to a setback or disaster** — partial progress at best,
   or the worst outcome, which forces the next scene.

Rules for planning try/fail chains:

- Each failure must be **caused by the attempt itself**, not by random bad
  luck. The reader should feel the POV character earned the worse situation.
- Never resolve an attempt with a **coincidence that saves** the character
  (deus ex machina). Coincidences may *complicate*, never *rescue*.
- Between failed attempts, insert sequel material (reaction/dilemma/decision —
  see `scene-sequel.md`) so the reader feels the rising cost, not just rising
  noise.
- Track each attempt in the chapter outline as `try-1`, `try-2`, `try-3` with
  its failure and its new complication.

## Scene outcomes

Record each scene's result in the scene file's `outcome` field, using
four answers to "Does the POV character get what they want?". Swain's
scene ends in disaster; the yes-but and no-and outcomes are a later
extension of his scene outcomes, common in current craft teaching, not
Swain's own terms:

| `outcome` | Meaning | Effect on pressure |
|-----------|---------|--------------------|
| `yes` | Goal achieved cleanly | Releases pressure; use sparingly |
| `no` | Goal blocked | Holds pressure |
| `yes-but` | Goal achieved at a cost or with a new problem | Complicates; raises pressure |
| `no-and` | Goal blocked and things get worse | Complicates; raises pressure most |

A try/fail chain usually reads `no`, `no-and`, then `yes-but` or `no-and`.
`story pacing .` lists outcomes per chapter and warns after three or more
consecutive `yes` outcomes, where the story has stopped pushing back.

## The Five Commandments (Story Grid)

Shawn Coyne's *Story Grid* describes every complete story unit — including a
single scene — as moving through five stages (attributed here as a summary of
the widely-discussed framework, not its full methodology):

1. **Inciting incident** — something disrupts the scene's status quo.
2. **Progressive complications** — the situation worsens or the goal gets
   harder to reach (this is where try/fail cycles live).
3. **Crisis** — the POV character faces an irreversible choice between two
   bad options (or a best-bad-choice).
4. **Climax** — the decision, and the action taken on it.
5. **Resolution** — the new state: what changed, what it costs, what the
   character now knows.

## Scene-grain checklist

For each scene in a chapter, verify:

- [ ] An inciting incident opens the scene or the scene opens on its aftermath
- [ ] At least one complication makes the goal harder before the outcome
- [ ] The crisis presents a genuine either/or (no cost-free choice)
- [ ] The climax shows the POV character acting on their decision
- [ ] The resolution states the change: what is different now than at the
      scene's start (record in `state-changes` in the scene file)

If a scene fails the checklist, it is either a transition (keep it short),
a sequel beat (see `scene-sequel.md`), or it needs a complication and a
crisis added before drafting.
