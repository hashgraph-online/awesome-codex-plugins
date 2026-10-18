---
title: Contrast and Colour
impact: HIGH
tags: contrast, colour-blindness, low-vision, dark-mode, status-colours
wcag: 1.4.1, 1.4.3, 1.4.11
---

**Rule**: Text and meaningful graphics have enough contrast against their background, and colour is never the only way information is conveyed.

**Why**: Low vision, colour blindness, ageing eyes, and bright sunlight all reduce what people can distinguish. WCAG sets minimums: 4.5:1 for normal text and 3:1 for large text (1.4.3), 3:1 for interface components and meaningful graphics (1.4.11), and no information by colour alone (1.4.1).

### When Building

- **Text contrast** — at least 4.5:1, or 3:1 for large text (18pt / 24px, or 14pt / about 18.5px bold)
- **Non-text contrast** — 3:1 for input borders, focus indicators, icons that carry meaning, and chart elements users must tell apart
- **Placeholder and disabled-looking text** still needs 4.5:1 if users must read it
- **Check both themes** — light and dark mode, and text over images or gradients (add a scrim)
- **Never colour alone** — errors have an icon and text, not just a red border; links in text are underlined; chart series differ by shape, pattern, or direct labels as well as colour; status uses a word or icon as well as a colour dot
- **Respect platform settings** — increased contrast and "differentiate without colour" where the platform offers them (platform guides)

### When Auditing

- Grey-on-white body text, light placeholders, low-contrast secondary labels
- Input borders and icons below 3:1
- Errors, required fields, or statuses shown only by colour
- Text over photos or video without a scrim
- Dark mode colours that were never checked

### Incorrect

```tsx
<p className="text-gray-400">Your trial ends tomorrow</p>  {/* about 2.5:1 on white */}
<span className="dot bg-red-500" />                        {/* status by colour only */}
```

### Correct

```tsx
<p className="text-gray-700">Your trial ends tomorrow</p>
<span className="status"><AlertIcon aria-hidden="true" /> Payment failed</span>
```

### Alternatives

Logos, purely decorative elements, and disabled controls that users never need to read are exempt from contrast minimums. Brand colours that fail can usually stay as accents while text uses a darker shade.
