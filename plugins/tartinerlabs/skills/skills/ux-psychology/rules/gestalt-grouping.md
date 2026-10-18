---
title: Gestalt Grouping
impact: MEDIUM
tags: proximity, similarity, common-region, layout, grouping
---

**Rule**: People see elements that are close together, look alike, or share a container as one group. Use spacing and containers to show what belongs together — before reaching for labels and dividers.

**Evidence**: Wertheimer 1923 — the Gestalt laws of perceptual grouping (proximity, similarity, continuity, closure). Palmer 1992, "Common region: a new principle of perceptual grouping" (*Cognitive Psychology*) — elements inside a shared boundary are grouped, overriding proximity.

### When Building

- **Proximity** — space within a group smaller than space between groups. A label sits closer to its own field than to the previous one; a heading closer to its section than to the one above
- **Similarity** — things that work the same look the same (all links one style, all destructive actions one style); things that differ look different
- **Common region** — cards, panels, and list sections group related content and actions; an action inside a card applies to that card
- **Alignment** — a shared edge reads as a relationship; misaligned elements read as unrelated
- **Form structure** — group related fields (name, address, payment) with a heading and extra space between groups

### When Auditing

- Uniform spacing everywhere, so labels float between fields and headings between sections
- Actions placed outside the container they act on, or inside one they don't
- Similar-looking elements that behave differently (a styled label that looks like a button)
- Long forms or settings with no visible grouping

### Incorrect

```tsx
<VStack spacing={16}>
  <Label>Email</Label>
  <Input />
  <Label>Password</Label>
  <Input />
</VStack>
```

### Correct

```tsx
<VStack spacing={24}>
  <Field label="Email" gap={6} />
  <Field label="Password" gap={6} />
</VStack>
```

### Why This Matters

Grouping is processed before reading. Correct grouping lets people understand a screen's structure at a glance; wrong grouping makes them read everything to work out what relates to what.

### Alternatives

Gestalt grouping always applies — the choice is which cue. Prefer spacing first, then similarity, then containers; stacking borders and cards everywhere adds clutter and weakens each container's meaning.
