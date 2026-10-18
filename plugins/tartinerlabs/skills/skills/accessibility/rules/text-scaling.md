---
title: Text Scaling and Reflow
impact: HIGH
tags: dynamic-type, font-scale, zoom, reflow, responsive, low-vision
wcag: 1.4.4, 1.4.10, 1.4.12
---

**Rule**: Text scales with the user's settings and layouts adapt instead of clipping, overlapping, or scrolling sideways.

**Why**: Many people raise their text size; on phones it is one of the most used accessibility settings. WCAG requires text that resizes to 200% without loss (1.4.4), content that reflows at a 320 CSS px width without horizontal scrolling, or 256 CSS px height for horizontally scrolling content (1.4.10), and layouts that survive increased line, letter, and word spacing (1.4.12).

### When Building

- **Scalable units** — `rem`/`em` on the web, Dynamic Type text styles on Apple platforms, `sp` on Android, `allowFontScaling` left on in React Native
- **No fixed heights on text containers** — let rows, buttons, and cards grow with their text
- **Layouts switch at large sizes** — side-by-side becomes stacked; horizontal button rows wrap; truncation is a last resort and the full text stays reachable
- **Scale non-text sizes that sit with text** — icons and spacing next to text scale too (`@ScaledMetric` in SwiftUI)
- **Web zoom** — pages work at 200% zoom and at 320 px wide; never disable pinch zoom (`user-scalable=no` or `maximum-scale=1`)
- **Respect user text spacing** — don't rely on exact line heights that clip when spacing increases

### When Auditing

- Font sizes in `px` on the web, fixed `.font(.system(size:))` in SwiftUI, `dp` for text on Android, `allowFontScaling={false}` in React Native
- Fixed-height containers holding text
- Viewport meta that disables zoom
- Truncated labels that hide essential information at large sizes

### Incorrect

```html
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
```

### Correct

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

### Alternatives

Content that genuinely needs two dimensions — data tables, maps, diagrams, editors — may scroll horizontally; the rest of the page must still reflow. A capped maximum size for a few decorative display titles is reasonable when body text still scales fully.
