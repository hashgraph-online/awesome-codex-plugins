---
title: von Restorff Effect (Primary Action)
impact: MEDIUM
tags: isolation-effect, primary-action, cta, emphasis, hierarchy
---

**Rule**: The item that differs from its surroundings is the one noticed and remembered. Give each screen one clearly primary action, and spend emphasis only where it matters.

**Evidence**: von Restorff 1933 (*Psychologische Forschung*) — the isolation effect: a distinctive item in a list is remembered better than the uniform items around it. WCAG 2.2 SC 1.4.1 (Use of Color) — emphasis must not rely on colour alone.

### When Building

- **One primary action per screen or section** — filled, high-contrast, or larger; secondary actions visibly quieter (outline, text, or ghost style)
- **Emphasis is a budget** — when everything is bold, coloured, or badged, nothing stands out. Reserve accent colour and badges for what needs attention now
- **Distinct by more than colour** — weight, size, position, or an icon as well, for colour-blind users and bright screens
- **Destructive actions are distinct in their own way** (red, separated) but not primary unless deletion is the screen's purpose
- **New or changed items** — a temporary highlight or "New" badge that clears once seen

### When Auditing

- Two or more equally prominent primary buttons on one screen
- Every card or row carrying a badge, accent, or bold label
- Primary state shown only by colour
- The primary action styled the same as secondary ones

### Incorrect

```tsx
<Button variant="primary">Export</Button>
<Button variant="primary">Share</Button>
<Button variant="primary">Save</Button>
```

### Correct

```tsx
<Button variant="primary">Save</Button>
<Button variant="secondary">Share</Button>
<Menu label="More"><MenuItem>Export</MenuItem></Menu>
```

### Why This Matters

The primary action is what most users came to do. When it does not stand out, they search for it; when several compete, they hesitate or pick the wrong one.

### Alternatives

Screens whose purpose is a neutral choice between equal options (two plans, "Sign in" vs "Create account") can present them with equal weight. Constant highlighting fades — a permanent "New" badge stops being seen (banner blindness, `rules/scanning.md`).
