# Restraint — checklist for application

A practical checklist for applying wabi-sabi restraint to existing designs.

## Audit your design system

**How many colors are in active use?**
- Goal: 5–7 colors with clear semantic roles.
- If more: consolidate. Some colors should be variants; some should be eliminated.

**How many typefaces?**
- Goal: 2–3 typefaces (or weights of one).
- If more: pick the strongest and eliminate the rest.

**How many type sizes?**
- Goal: 5–8 sizes on a clear scale.
- If more: collapse to scale values; remove ad-hoc sizes.

**How many shadow / elevation levels?**
- Goal: 5–7 levels.
- If more: consolidate.

**How many corner radii in use?**
- Goal: 2–3 (sharp, slight, rounded).
- If more: consolidate.

**How many animation durations / easings?**
- Goal: 3–4 each.
- If more: consolidate.

Each consolidation is an act of restraint. The result is a more cohesive, more maintainable design system.

## Audit your screens

**Is there a single focal point on each screen?**
- One primary action, one primary message, one primary visual emphasis.
- If multiple competing focal points: pick one and demote the rest.

**Is every visible element earning its place?**
- For each element, ask: what does this do? If "decoration" or "fills space," consider removing.
- Especially: badges, callouts, animated highlights, gradient overlays.

**Is whitespace generous?**
- Margins around content, padding inside containers, vertical breathing room between sections.
- Crowded screens benefit from more space, almost always.

**Are there elements added "to fill space"?**
- These are the easiest to remove. Empty space is fine.

**Is there visual noise that doesn't carry information?**
- Decorative borders, drop shadows on every element, gradient backgrounds, textures applied uniformly.
- Each adds visual weight; each should be justified.

## Audit your features

**How many features does the product have?**
- The exact number isn't the point; the question is whether each earns its place.

**Which features have low usage?**
- See `ockhams-feature-pruning` for the audit process.
- Features that don't serve users well are candidates for removal.

**Which features overlap in function?**
- Multiple ways to accomplish the same task. Consolidate to one.

**Which features were added for one customer?**
- These often outlive their original purpose. Re-evaluate.

## Audit your settings

**How many user-configurable settings exist?**
- Each setting is a decision the user has to make (or default they may not love).
- Question whether each setting needs to be configurable.

**Which settings are rarely changed from default?**
- These could probably just be defaults; remove the configurability.

**Which settings does the team forget the meaning of?**
- A sign that the setting has accumulated past its usefulness.

## Audit your copy

**Is the copy concise?**
- Every word should serve. Cut filler.

**Is the tone consistent?**
- Mixed registers (formal in some places, casual in others) reduce coherence.

**Are there places where less text would be clearer?**
- Often, yes.

**Is there UI text that just states the obvious?**
- "Click here to..." when the button is clearly clickable.
- "This is the X section..." when the heading already says X.

## Audit your animations

**Do all the animations serve communication?**
- Each animation costs render time and user attention. If it doesn't communicate, it's noise.

**Are animations consistent in timing and easing?**
- Inconsistent animation reads as patched.

**Are there animations that frequent users would want to skip?**
- Honor reduced-motion preferences; consider whether the animations should be quicker.

## Process restraint

**Are decisions made deliberately, or accumulated?**
- Restraint requires saying no. Build the muscle for that.

**Is feature addition harder than feature removal?**
- It should be roughly symmetrical. If addition is easy and removal is hard, complexity will accumulate.

**Is there a regular pruning cadence?**
- Quarterly or semi-annual review of features, settings, complexity.

**Are designers and engineers held to restraint principles?**
- A team value that's articulated and reinforced.

## A practical exercise

Pick one screen of your product. Open it. Apply this exercise:

1. List every visible element on the screen.
2. For each element, identify what it does and why it's there.
3. Identify the elements you can't articulate the value of.
4. Consider removing those elements.
5. Look at the result. Is it cleaner? Does it still work? If yes, ship the simpler version.

This exercise often reveals that 10–30% of visible elements aren't earning their place. Removing them produces immediate improvement.

## Anti-patterns to avoid

**Restraint at the cost of usability.** Don't strip affordances; users need to know what's clickable. Don't lower contrast; text needs to be readable. Don't remove labels; users need to know what things do.

**Restraint by reflex.** Stripping things just because stripping feels virtuous. Verify that what you're removing wasn't earning its place.

**Inconsistent restraint.** Stripping some sections and not others. The product feels patched together.

**Cold restraint.** Pure minimalism without warmth or character. Combine with selective imperfection.

**Restraint as a one-time event.** Restraint is a discipline, not a project. The pressure for additions is constant; restraint has to be ongoing.

## Cross-reference

For the imperfection half of wabi-sabi, see `wabi-sabi-imperfection`. For the parent principle, see `wabi-sabi`. For pruning accumulated complexity, see `ockhams-feature-pruning`.
