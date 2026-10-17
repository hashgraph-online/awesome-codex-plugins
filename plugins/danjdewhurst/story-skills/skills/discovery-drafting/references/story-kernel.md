# The Story Kernel

A story kernel is a one-paragraph starting point for discovery drafting —
enough to write from, not enough to be an outline. It replaces the beat
sheet as the draft's seed. Write the kernel before chapter one, then let the
chapters discover the rest.

## Kernel contents

One paragraph, 3–6 sentences, containing:

1. **A character in a situation** — who, and what unstable position they're in.
2. **A want** — what the character wants badly enough to act on.
3. **An obstacle or pressure** — what stands in the way, or what will go
   wrong if they don't act.
4. **A tone/genre signal** — one phrase that sets the register (noir,
   wonder, dread, farce).

What the kernel deliberately omits: plot beats, an ending, a theme statement,
a cast list, worldbuilding. Those get discovered (and reconciled later — see
`reconcile-loop.md`).

Example (original, for illustration):

> A retired cartographer who falsifies maps for smugglers discovers her
> latest commission describes a city that shouldn't exist — and someone is
> paying in real gold to reach it. She wants the money and wants to know if
> she drew something true by accident. The client is lying about why they
> need the route, and her old guild contacts are watching. A tense,
> low-magic caper with the unease of a ghost story.

## Recording the kernel

Store the kernel in `story.md` under a `## Story Kernel` section, and mark
the project as discovery-drafted in frontmatter:

```yaml
draft-mode: discovered
```

This tells every later skill and audit that chapters were written without a
pre-planned outline, so the reconcile loop (not the outline) is the source
of truth for what happened.

## Using the kernel

- **Starting a session:** re-read the kernel, then ask "what's the most
  interesting thing that could happen next?" Write that.
- **When stuck:** cycle back a few hundred words and try a different choice
  (the canonical discovery-writer recovery). Do not stop to outline forward.
- **When the kernel stops generating:** the kernel has done its job when
  chapters have their own momentum. Promote discovered elements into the
  bible via the reconcile loop; the kernel itself never needs updating.
- **Kernel vs. premise:** the kernel is a situation, not a theme. If a
  working premise emerges during drafting (see the `theme-craft` skill),
  record it as `premise:` in `story.md` — but do not force the draft to
  serve a premise that arrived late.

## When discovery mode is wrong

Use the outline-first `chapter-writing` workflow instead when: the story has
hard external constraints (a mystery whose fair-play clues must be planted —
see `genre-craft`), the user explicitly wants a beat sheet, or repeated
reconcile loops show the draft wandering without deepening. Discovery is a
method, not an identity — switch modes per project, and mark the switch in
`story.md` (`draft-mode: outlined` for chapters written outline-first;
mixed-mode projects are fine, tracked per chapter).
