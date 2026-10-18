---
title: Signifiers
impact: HIGH
tags: affordances, discoverability, gestures, hover, interactive-states
---

**Rule**: Anything interactive must look interactive, and anything that looks interactive must be. Hidden gestures and hover-only controls need a visible alternative.

**Evidence**: Norman, *The Design of Everyday Things*, revised edition (2013) — signifiers are the perceivable cues that tell people what actions are possible and where; affordances alone are invisible on a flat screen. NN/g 2017, "Flat UI Elements Attract Less Attention and Cause Uncertainty" (eyetracking) — pages with weak clickability cues made users work harder to find what they could click.

### When Building

- **Buttons look like buttons** — shape, fill, or border, and a label or a recognisable icon; links look like links (colour plus underline or position)
- **States** — default, pressed/active, focused, disabled, and on the web hover; disabled states explain why when it isn't obvious
- **Gestures have a visible twin** — swipe-to-delete also reachable from a menu or edit mode; long-press actions also in a "…" menu
- **Hover is an enhancement** — row actions revealed on hover also reachable by keyboard and touch (`references/web.md`)
- **Non-interactive things don't look interactive** — no button styling on labels, no underlines on plain text, no pointer cursor on static cards
- **Scroll cues** — partially visible items at the edge show that more content exists

### When Auditing

- Clickable `div`s and text with no visual cue
- Actions reachable only by swipe, long-press, or hover
- Disabled-looking controls that work, or active-looking ones that do nothing
- Icon-only buttons with unfamiliar icons and no label or tooltip

### Incorrect

```tsx
<div onClick={openProject}>{project.name}</div>
```

### Correct

```tsx
<button type="button" onClick={openProject} className="project-link">
  {project.name}
  <ChevronRight aria-hidden />
</button>
```

### Why This Matters

If users cannot see that something is possible, for them it does not exist. Features hidden behind invisible gestures go unused, and support tickets ask for features the product already has.

### Alternatives

Expert shortcuts (keyboard, gestures) can stay invisible as long as a visible path exists and the shortcut is discoverable from it — e.g. shown in a menu next to the action. OS-standard gestures users already know (swipe back, pull to refresh) need no extra cue.
