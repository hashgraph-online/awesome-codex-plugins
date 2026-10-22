---
title: Motion, Flashing, and Time
impact: HIGH
tags: reduced-motion, vestibular, carousels, autoplay, flashing, timeouts
wcag: 2.2.1, 2.2.2, 2.3.1, 2.3.3
---

**Rule**: Respect the user's reduced-motion setting, let users pause anything that moves on its own, never flash more than three times a second, and give users control over time limits.

**Why**: Large motion — parallax, zooming transitions, spinning — can trigger dizziness and nausea in people with vestibular disorders. Flashing can trigger seizures. Auto-moving content distracts people with attention difficulties, and time limits shut out slow readers and assistive technology users. WCAG covers these: Timing Adjustable (2.2.1), Pause, Stop, Hide for content that moves for more than 5 seconds (2.2.2), Three Flashes or Below Threshold (2.3.1), and Animation from Interactions (2.3.3, AAA — but the platform settings make it easy to honour).

### When Building

- **Reduced motion** — when the setting is on, replace large movement (slide, zoom, parallax, spring overshoot) with fades or instant changes; keep essential feedback (`prefers-reduced-motion` on the web; platform guides for native)
- **Pause, stop, hide** — carousels, tickers, background video, and animations longer than 5 seconds get a visible pause control; better, don't auto-advance at all
- **No autoplaying audio**; autoplay video starts muted with controls
- **No flashing** more than three times per second
- **Time limits** — warn before a session expires and offer to extend; save progress so a timeout doesn't lose work; avoid limits unless essential (auctions, security)
- **Don't depend on motion for meaning** — a reduced-motion user must still get the same information

### When Auditing

- Animations with no `prefers-reduced-motion` / Reduce Motion branch
- Auto-advancing carousels or banners without pause
- Autoplaying video with sound
- Session timeouts with no warning or extension; forms that lose input on timeout

### Incorrect

```css
.hero { animation: zoom-in 1.2s ease-out; }
```

### Correct

```css
.hero { animation: zoom-in 1.2s ease-out; }
@media (prefers-reduced-motion: reduce) {
  .hero { animation: fade-in 0.2s ease-out; }
}
```

### Alternatives

Reduced motion means less *large or vestibular* motion, not none — small opacity fades, colour changes, and progress indicators can stay. Essential motion (a video the user chose to play, a game whose mechanic is movement) is exempt, but keep a way to pause.
