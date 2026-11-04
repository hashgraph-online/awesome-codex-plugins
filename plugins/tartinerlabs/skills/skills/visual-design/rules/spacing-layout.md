---
title: Spacing and Layout
impact: HIGH
tags: spacing-scale, grid, alignment, screen-template, rhythm
---

**Rule**: Space everything from one scale, align to a small number of edges, and give every screen in a flow the same template so only the content changes.

**Evidence**: The Gestalt law of proximity (Wertheimer 1923) holds that nearby items are seen as related, so spacing is how a layout shows groups. Apple's HIG and Material 3 both define layout margins and a 4 or 8 point base grid.

### When Building

- **A 4 or 8 point scale** (4, 8, 12, 16, 24, 32, 48, 64). Every gap, padding, and margin uses one of its steps.
- **Spacing shows grouping.** Related items sit closer together than unrelated ones. Space between groups should be noticeably bigger than space within them, at least about 1.5×.
- **Set spacing through gaps.** Use `gap`, stack spacing, or `Arrangement.spacedBy` rather than margins on individual children, so spacing stays consistent when items change.
- **Few alignment edges.** Content shares the screen's leading margin. Avoid centring body content unless the screen is a single centred moment (welcome, success, empty state).
- **One screen template per flow.** Onboarding steps, setup screens, and paywall pages share the same slots: progress at the top, headline, content, and the primary action at the bottom in the same position. Only the content changes between steps.
- **Generous outer margins** on showcase screens, at least the platform margin (16–20pt on phones). Dense data screens can be tighter inside, but keep the outer margin.
- **Respect safe areas.** Nothing interactive sits under the home indicator, notch, or system bars.

### When Auditing

- Gaps off the scale (13, 18, 22) or several near-identical values
- Equal spacing everywhere, with no grouping
- The primary button moving between steps of a flow
- Content aligned to several different left edges
- Body content centred across a whole screen
- Padding set per child, causing uneven gaps

### Incorrect

```tsx
<View>
  <Text style={{ marginBottom: 13 }}>Title</Text>
  <Text style={{ marginBottom: 18 }}>Subtitle</Text>
  <Button style={{ marginTop: 22 }} />
</View>
```

### Correct

```tsx
<View style={{ gap: space[2] }}>
  <Text style={type.title}>Title</Text>
  <Text style={type.body}>Subtitle</Text>
  <View style={{ marginTop: space[6] }}><Button /></View>
</View>
```

### Why This Matters

Inconsistent spacing reads as unfinished even when users cannot say why. When the button jumps between onboarding steps, the flow feels like separate screens instead of one sequence, and users have to find the button again on each step.

### Alternatives

Editorial and marketing layouts may break the grid on purpose, with an offset image or an oversized headline. Make it clearly deliberate, not off by a few points. Optical adjustments, such as nudging an icon so it looks centred, are fine.
