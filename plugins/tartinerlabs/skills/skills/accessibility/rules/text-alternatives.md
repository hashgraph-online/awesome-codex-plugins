---
title: Text Alternatives
impact: HIGH
tags: alt-text, images, icons, charts, maps, decorative
wcag: 1.1.1
---

**Rule**: Every non-text element that carries meaning has a text alternative that conveys the same meaning. Decorative elements are hidden from assistive technology.

**Why**: Screen readers cannot see images, icons, charts, or maps. WCAG 1.1.1 (Non-text Content) requires a text alternative that serves the equivalent purpose — describing what the image *means in context*, not what it looks like.

### When Building

- **Informative images** — alt text with the information the image gives ("Revenue rose 12% in March"), not "chart" or the filename
- **Functional images** (icon buttons, image links) — describe the action or destination ("Search", "Go to home"), not the picture ("magnifying glass")
- **Decorative images** — empty alt (`alt=""`), `aria-hidden`, or the platform's decorative option, so they are skipped
- **Icons next to text** that says the same thing are decorative
- **Charts and maps** — a summary of the key insight plus access to the data (a table, a list of places, or per-point labels); a map of visits can also be a list of visits
- **Complex images** — a short alt plus a longer description nearby
- **Text in images** — avoid; when unavoidable, the alt contains the same text

### When Auditing

- `<img>` without `alt`; SwiftUI `Image` without a label or `decorative:`; Compose `Image` with a missing or meaningless `contentDescription`
- Alt text that repeats nearby text, describes appearance, or contains "image of"
- Charts and maps with no text summary or data alternative
- Icon fonts and SVG icons used as buttons without an accessible name

### Incorrect

```tsx
<img src="/q3.png" />
<img src="/divider.svg" alt="divider" />
```

### Correct

```tsx
<img src="/q3.png" alt="Q3 revenue: up 12% on Q2, led by the Team plan" />
<img src="/divider.svg" alt="" />
```

### Alternatives

When the same information is already in adjacent text, the image is decorative — hide it rather than duplicating the announcement.
