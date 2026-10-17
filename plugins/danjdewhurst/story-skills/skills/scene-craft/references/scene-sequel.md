# Scene Sequel Mechanics

Scene/Sequel is Dwight Swain's scene-unit framework from *Techniques of the
Selling Writer*. chapter-writing covers Swain's **Scene** half
(goal → conflict → outcome/setback). This reference covers the missing
**Sequel** half: reaction → dilemma → decision. The sequel is where character
interiority, motivation repair, and theme processing happen. Without it, a
chapter becomes a string of incidents with no breathing room.

## When a scene needs a sequel

Not every scene gets a sequel. Write one when:

- The scene outcome was a **setback or disaster** the POV character must process
- The POV character learned something that **changes their understanding** of the lie they live by (see `theme-craft`)
- The next scene needs a **decision** with stakes — the sequel manufactures it
- The pacing needs **breathing room** between action beats (see `try-fail.md`)

Skip the sequel when the outcome was a clear victory with a self-evident next
step, or when the following scene opens mid-action and the reaction can happen
on the move.

## The four beats

**1. Reaction (emotional).** The POV character's immediate, visceral response to
the scene's outcome. Sensory, involuntary, in-the-body: nausea, shaking hands,
laughing when they shouldn't. Keep it short — two beats of prose, not a page
of wallowing.

**2. Dilemma (rational).** The character tries to think their way out. A dilemma
is not a problem with one right answer; it is a choice between two bad
options, or a situation with no good path visible. Frame it as an explicit
question with explicit stakes: "Give up the map and lose the one advantage she
has, or keep it and let the person she promised to protect walk into the
ambush?" Record the dilemma in the scene record's `dilemma` field.

**3. Decision (act of will).** The character commits to a course of action. The
decision must be *theirs* — made from who they are, not imposed by the plot —
and it must cost something. A decision that costs nothing is not a decision.

**4. Action (optional, launches the next scene).** Some writers count the action
taken on the decision as part of the sequel; treat it as the bridge beat that
ends the sequel and opens the next scene.

## Scene record fields

The scene template (`chapter-writing/references/scene-template.md`) carries
`sequel: {true|false}` and `dilemma:` frontmatter plus a `## Sequel` body
section. For scenes with sequel content:

```yaml
sequel: true
dilemma: "{The explicit no-good-options question}"
```

And in the `## Sequel` section, record the three beats:

- **Reaction:** the POV character's emotional processing (one or two beats
  of prose, not a page).
- **Dilemma:** the impossible choice restated with its stakes.
- **Decision:** what the POV character commits to, what it costs, and the
  goal that launches the following scene.

For pure action scenes with no sequel, set `sequel: false` and omit the
rest.

## Planning workflow

1. Read the scene's outcome from the chapter outline or scene record.
2. Write the reaction as **one specific physical detail** — the body's answer
   before the mind's.
3. Draft the dilemma as a single question. If you can find an easy answer,
   sharpen it until both options cost something the character values.
4. Make the decision **reveal** character: a brave character may choose the
   cautious path if it protects what they love; that contradiction is where
   theme lives.
5. Check the dilemma against the character's lie (see
   `theme-craft/references/lie-truth.md`): the lie should be fighting the
   decision. If the lie plays no part, the sequel is skimming the surface —
   deepen it.
