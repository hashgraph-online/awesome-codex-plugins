# The Controlling Idea

Robert McKee's *Story* frames a story's theme as a **controlling idea**: a
value plus its cause, stated as one sentence — e.g. "Justice triumphs because
the hero is smarter than the criminals" (paraphrased concept, not McKee's
words). Theme *words* ("justice", "redemption") can't guide a scene decision;
a controlling idea can, because it names both the value at stake and what
causes it to triumph or fail.

## The sentence

A controlling idea has this shape:

> **{Value} {triumphs | fails} because {cause}.**

- **Value** — the story's core moral value, phrased as a continuum with a
  positive and negative pole: justice/injustice, love/hate, courage/cowardice,
  honesty/deception.
- **Triumphs or fails** — the ending's verdict. A positive ending argues the
  value triumphs; a negative ending argues it fails (or a counter-value wins).
- **Cause** — the protagonist's action or quality that *produces* the verdict.
  This is what makes the idea usable: every scene can be checked against
  whether the protagonist is moving toward or away from the cause.

Examples (original constructions in the form, not quotations):

- "Mercy triumphs over vengeance because the protagonist refuses the killing blow."
- "Honesty fails because the protagonist protects the lie that keeps them safe."

## The counter-premise

Record the **counter-premise** alongside the premise: the antagonist's (or
the world's) opposing claim, in the same value+cause form:

- Counter-premise: "Vengeance triumphs because the world punishes mercy."

The counter-premise is what the antagonist believes and acts on (see
`antagonist-design.md`). The story's climax stages the two premises against
each other and delivers a verdict — that verdict is the controlling idea's
"triumphs/fails" pole.

## Working-premise workflow

Craft opinion is genuinely split on planning theme up front (King warns
against starting from theme; McKee and Truby plan it). The repo's stance: use
a **working premise**, revisable.

1. **Plan:** at story-init (or when picking up an existing project), draft a
   working premise and counter-premise. Store in `story.md` frontmatter:

   ```yaml
   premise: "{Value} triumphs because {cause}."
   counter-premise: "{Opposing value} triumphs because {opposing cause}."
   ```

   If the user resists planning theme, record `premise: tbd-discovery` and
   let the revision audit (see `theme-audit.md`) build it from what the draft
   actually argues.

2. **Use during drafting:** the premise answers scene-level questions —
   "which choice tests the value?" A scene that never touches the value
   continuum is structurally decorative; flag it for the scene-craft sequel
   (the sequel is where the character's lie confronts the value).
3. **Audit in revision:** run `theme-audit.md`. The working premise is not
   sacred — if the draft argues something truer, rewrite the premise to match
   the draft, then revise the ending so it *delivers* the verdict cleanly.

## Premise quality check

- [ ] One sentence, with a named value and a named cause.
- [ ] The cause is something the *protagonist does*, not something that
      happens to them.
- [ ] The counter-premise is a genuine belief someone could hold (test: can
      you imagine the antagonist defending it?).
- [ ] The climax can plausibly stage both premises and pick a winner.
