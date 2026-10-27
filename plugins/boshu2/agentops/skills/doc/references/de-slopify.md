# De-Slopify — Docs Prose Pass

> Make documentation read like a careful human wrote it. This is a **docs
> quality** method under [`doc`](../SKILL.md), not a general writing skill and
> not a standalone AgentOps skill.

Use it from `doc` when a substantial README or other repo doc is generated or
rewritten, so it stays concrete, scannable, and free of LLM prefab. It is
optional guidance, not a completion gate.

> **Core insight #1:** You cannot do this with regex or a script. It requires a
> manual, line-by-line read. A linter catches a fraction; the rest is judgment.
>
> **Core insight #2:** Slop is a thinking defect wearing a fluent surface.
> Alignment trains models toward the *mode* of human preference, so prose goes
> prefab. Lexical diversity can rise while conceptual diversity falls. Swapping
> blacklist words is necessary and not sufficient. A real pass removes the
> prefab *and* checks that something specific is still present (the additive
> floor below).

## THE PROMPT — full

```
Read the complete text line by line and remove AI-slop tells. You MUST do this
manually, recasting only the lines that show a tell — not with regex or
find-replace. Leave every other line exactly as written.

WORD-LEVEL TELLS (recast on sight):
- Prefabricated phrases / dying metaphors: "move the needle," "navigate the
  landscape," "at its core," "unlock," "delve," "tapestry," "testament to,"
  "in today's fast-paced world." Cut or re-image with something concrete.
- Verbal false limbs: "make contact with" → meet, "give rise to" → cause,
  "has the ability to" → can.
- Zombie nouns on light verbs: "make a decision" → decide, "the implementation
  of X" → we built X. Judgment, not a ban.
- Copula avoidance: "serves as / boasts / features" where plain "is/are" works.
- Lead-ins: "Here's why," "Here's the thing," "It's worth noting," "Let's dive
  in" — just say it.
- Hidden actor and stacked hedges: "the token is refreshed" when the source says
  who refreshes it; "might possibly." Name the actor; keep one hedge, and only
  where the source is uncertain.

STRUCTURAL TELLS:
- Explicit contrast "it's not X, it's Y" / "not only X but also Y." Worst on the
  headline. Cap ≤1 per piece, at an earned mid-body pivot. Prefer two facts the
  reader collides.
- Reflexive rule of three ("fast, simple, and powerful"). Cap ~1 per 500 words.
- Manufactured punchy fragment: short contentless beat ("It isn't new."
  "Simple."). Fold or cut. A short sentence with a real claim stays.
- Manufactured cadence: 3–4 same-shape sentences stacked. Break the symmetry.
- Elegant variation: "notes → explains → observes." Force-repeat the plain word.
- Inflated importance + trailing "-ing" tail: cut to the quiet specific claim.

THE DEEP ONE:
- Each paragraph needs one concrete particular (name, number, path, command),
  taken from the source and never invented, and at least one non-obvious idea.
  Fluent generality is still slop.

Then re-read the whole text for rhythm. Fix every drone, stumble, and run-on.
```

## THE PROMPT — quick

```
Remove AI-slop: prefab phrases, verbal false limbs, zombie nouns, copula
avoidance, "here's why"/"dive in" lead-ins, explicit "not X, it's Y" (≤1, never
on the headline), reflexive rule-of-three, stacked same-shape sentences, elegant
variation, hidden actors, stacked hedges. Each paragraph needs one concrete
particular from the source, never an invented one. Re-read for rhythm. Recast only the
lines with a tell, manually — no regex.
```

## Subtractive pass

1. Prefab phrases and dying metaphors → concrete subject-specific wording.
2. Verbal false limbs → live verbs.
3. Zombie nouns → verbs where it restores a live verb.
4. Copula avoidance → plain is/are.
5. Metadiscourse / signposting ("Moreover," "In this section," "In conclusion") → cut.
6. Lead-ins and forced enthusiasm → delete; say the thing.
7. Explicit contrast cap (never on the headline).
8. Rule-of-three cap.
9. Manufactured fragment and manufactured cadence.
10. Elegant variation → repeat the plain word; vary ideas.
11. Lower rhetorical temperature ("pivotal," "transformative," "groundbreaking").
12. Vague attribution ("studies show") → name the source or cut.
13. Mechanical formatting tells (gratuitous bold, optimistic "despite challenges" closers).
14. Passive voice that hides who acts ("the cache is cleared") → name the
    component or person when the source says; leave it passive when the actor
    is unknown or beside the point.
15. Stacked hedges ("could potentially") → one hedge, only where the source is
    uncertain; trimming never makes the claim stronger than its source.

### Em-dash: use-pattern, not frequency

Do not count dashes and call frequency the signal (it flips by model generation).
Flag the *mechanical append* — a clause fused with a dash where a comma, colon,
period, or two sentences would do. Recast that pattern.

### Dictation sources

Strip filler (um, like, you know), verbal runways, and false starts. Keep the
resolved claim. Do not rebuild a self-repair as "not X, it's Y."

## Additive floor

After cuts, confirm:

- One concrete particular per paragraph, taken from the source, the repository
  or the caller. With none, cut the general sentence or name the missing fact as
  a gap; never invent a name, number, example or source to meet the floor.
- Muddy sentences rewrite the thought (clutter is unfinished thinking)
- One non-obvious idea per section
- Sentence-length variance (build long, land short)
- A last re-read for rhythm

Subtraction alone yields clean, bloodless prose that still reads generated.

## Before / after

**Prefab + inflation**
Before: `Our platform serves as a comprehensive solution that unlocks transformative value.`
After: `The platform turns raw logs into a weekly report.`

**Contrast on the headline**
Before: `It's not a linter — it's a complete code-quality system.`
After: `This checks types, lint, complexity, and the build on every push.`

**Lead-in**
Before: `We chose Rust for this component. Here's why: performance matters.`
After: `We chose Rust because the hot path runs 40M times a day and GC pauses showed up in the p99.`

## Density, not brevity

"Omit needless words" means every word tells — not that every sentence is short.
Do not chop a long sentence that earns its length into stubs.

## Check or rewrite

A question about a draft ("does this read generated?") asks for a check: list
each tell with its quoted line and a short suggested fix, and leave the text
unchanged. Report patterns, never a guess about who or what wrote the text.

A request to fix or polish asks for a rewrite. Change only the sentences that
show a tell and leave the rest as written, so a second pass finds nothing left
to change. In the caller's own prose keep their word choice and voice; in a
repository document match the surrounding idiom.

## What not to "fix"

- Technical accuracy
- Necessary headers and lists
- Thoroughness (being complete is not slop; padding is)
- Code examples (focus on prose)

## When to run

- Before publishing a README, doc, or release note
- After any AI-assisted writing session
- When `doc` generates or rewrites a substantial README, or checks one without
  rewriting it (flag findings)

## README work in Doc

When you run it on a written or rewritten `README.md`, run the full prompt above
on the exact file before the deterministic checks (Step 5 of
[README craft](readme-craft.md)). On a check-only request, report residual slop
tells as evidence; do not silently rewrite unless the caller asked for a rewrite.
