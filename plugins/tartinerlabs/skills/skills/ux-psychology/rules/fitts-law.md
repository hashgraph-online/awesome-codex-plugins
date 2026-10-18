---
title: Fitts's Law
impact: HIGH
tags: targets, touch, buttons, distance, size, destructive-actions
---

**Rule**: The time to hit a target grows with its distance and shrinks with its size. Make frequent and primary targets large and close; keep destructive targets away from common ones.

**Evidence**: Fitts 1954 (*Journal of Experimental Psychology*) — movement time depends on distance over target width. MacKenzie 1992, "Fitts' law as a research and design tool in human–computer interaction" (*Human–Computer Interaction*) — the formulation used for pointing and touch. Minimum sizes: 44×44 pt (Apple HIG), 48×48 dp (Material Design), 24×24 CSS px (WCAG 2.2 SC 2.5.8, AA).

### When Building

- **Minimum target size** per platform, measured as the hit area, not the visible icon — pad small icons rather than shrinking the target
- **Spacing** between adjacent targets so a slightly-off tap does not hit the neighbour
- **Primary action close to where attention already is** — at the end of the form, in the thumb zone on mobile (`references/mobile.md`)
- **Make the whole thing clickable** — the full row, card, or label of a checkbox, not just the text or the tiny box
- **Desktop edges and corners** are effectively infinite targets for a mouse — menus and toolbars at screen edges are fast to hit
- **Destructive actions** physically separated from frequent ones, and not in the spot the user's thumb or pointer lands by habit

### When Auditing

- Icon buttons with a hit area below the platform minimum
- Checkboxes and radio buttons whose label is not clickable
- "Delete" or "Cancel subscription" adjacent to "Save" or "Continue"
- Primary actions far from where the preceding task ends (top-right submit on a long mobile form)

### Incorrect

```tsx
<Pressable onPress={onClose}>
  <Icon name="x" size={16} />
</Pressable>
```

### Correct

```tsx
<Pressable onPress={onClose} hitSlop={14} accessibilityLabel="Close">
  <Icon name="x" size={16} />
</Pressable>
```

### Why This Matters

Small and distant targets slow everyone down and cause mis-taps — the most common touch error, and the most damaging when the wrong target is destructive.

### Alternatives

Making a target deliberately small or far away is legitimate friction for rare, dangerous actions. Dense expert desktop tools can use smaller targets than touch guidance suggests, as long as the WCAG minimum holds.
