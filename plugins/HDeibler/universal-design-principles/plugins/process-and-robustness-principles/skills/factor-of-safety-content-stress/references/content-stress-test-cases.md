# Content stress: test-case reference

A reference complementing `factor-of-safety-content-stress` with concrete test cases and worst-case content samples.

## Sample worst-case test data

A reusable test set for stress-testing layouts. Pull these into your test environment and render every component against them.

### Names

```
Short:    Li
Typical:  Maria Mendoza
Long:     Pierre-Auguste Renoir III
Very long: María-José Esperanza Sánchez de Bermúdez y Fernández
Multi-script: 田中太郎 (Tanaka Tarō)
With emoji: 🎉 Maya Chen
RTL:      محمد عبد الرحمن
```

### Currency

```
$0.01
$1.50
$1,234.50
$1,234,567.89
$999,999,999.99
-$1,234.50
€1.234,50  (German format)
¥1,234,567 (no decimals)
```

### Email addresses

```
a@b.co (5 chars)
maria@acme.com (typical)
maria.mendoza+filter@long-subdomain.example.com (long)
verylonglocalpart-with-allowed-special.chars+filter@very.long.subdomain.example.com (near max)
```

### Multi-line content

```
Single word: Hello
Single sentence: This is a typical short message.
Paragraph: A longer paragraph that wraps to multiple lines and contains enough content
to exercise text-wrapping behavior in the layout.
Multi-paragraph: ...

(Add 2-3 paragraphs of placeholder text)
```

### Numbers (counts and metrics)

```
0
1
12
1,234
1,234,567
1,234,567,890
12.5%
-12.5%
+999.9%
```

### Dates

```
Today
Yesterday
2 hours ago
Mar 5
March 5, 2026
2026-03-05
2026-03-05 14:32:01 UTC
```

## Internationalization stress test

Translate UI strings to:

- **German** — typically 30% longer than English; tests horizontal expansion.
- **Russian** — similar length; Cyrillic alphabet rendering.
- **Chinese (Simplified)** — typically 30% shorter; vertical baseline differs.
- **Arabic** — RTL direction; tests bidirectional layout.
- **Hindi** — Devanagari script; line height is different.

Render each and screenshot. Layouts that depended on English-length assumptions break visibly.

## Image stress test

Test image-handling with:

- **Missing image** (404 / no src). Should fall back gracefully.
- **Wrong aspect ratio** (a square image in a landscape slot). Crop, fit, or letterbox?
- **Very large image** (8K resolution). Lazy-load and downsample.
- **Tiny image** (16×16). Don't upscale unless deliberate.
- **Animated GIF / video** in a static slot. Should still load.

## Empty and edge states

For every list, table, dashboard, or content area:

- **Empty (zero items)**: deliberate empty-state design.
- **Single item**: layout should still feel intentional.
- **Maximum items**: pagination, virtualization, or scrolling kick in.
- **Loading**: skeleton or spinner.
- **Error**: explanation + recovery path.
- **Stale data**: indication of staleness.

## Accessibility stress test

Test with:

- **Browser zoom at 200% and 400%** — does layout reflow?
- **Reduced motion** — do animations disable correctly?
- **Forced colors mode** — do critical signals survive?
- **Screen reader** — does the page narrate sensibly?
- **Keyboard only** — can you reach everything?
- **Touch only** — are targets ≥ 44×44?

## Performance stress test

- **Slow network throttling** — Chrome DevTools "Slow 3G."
- **Slow CPU throttling** — DevTools "6x slowdown."
- **Cold cache** — first-visit rendering.
- **Many records** — lists with 1000, 10000 items.
- **Heavy concurrent operations** — multiple panels loading.

## Resources

- **Storybook** — render every component against every state, including stress states.
- **Playwright / Cypress** — automate visual regression on stress-test data.
- **Percy / Chromatic** — visual-diff tools that catch unintended layout changes.
- **Real user monitoring** — track real-world content distribution to inform what you should design for.
