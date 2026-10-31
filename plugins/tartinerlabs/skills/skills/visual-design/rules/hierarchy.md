---
title: Hierarchy
impact: HIGH
tags: focal-point, hierarchy, emphasis, text-levels, hero-number
---

**Rule**: Every screen has one focal element: a headline, one key number, or the hero content. Everything else is visibly secondary. Use at most three text levels, separated by size and weight.

**Evidence**: Eye-tracking studies (Nielsen Norman Group, F- and layer-cake scanning patterns) show people land on the largest, highest-contrast element first and scan from there. When there is no clear entry point, they scan the screen instead of reading it. Contrast in size and weight is the strongest cue for where to look.

### When Building

- **Decide the focal element before laying out the screen.** Ask what the user should see in the first second: today's balance, tonight's recipe, the photo being edited. Make that the largest thing on the screen.
- **Three text levels**: primary (headline or hero number), secondary (body, row titles), and tertiary (captions, metadata). A fourth level usually means the screen is doing two jobs.
- **Separate levels by size and weight first**, then by colour. Muted grey alone is a weak difference, and it disappears on low-quality screens and in bright light.
- **Supporting numbers follow the hero.** Put them in a quieter row underneath, not in a stack of equally sized stats above it.
- **Two-line headlines** in showcase screens: a short, heavy headline with one muted subtitle line under it, not two paragraphs.
- **On daily screens, the content is the hero.** The screen title can be the platform's large title; the first piece of content is the focal point.

### When Auditing

- Three or more elements of the same size and weight competing for first look
- A row of four or more equal stat tiles with nothing dominant
- Four or more distinct text sizes on one screen
- Hierarchy carried only by grey versus black
- The most important number shown smaller than its label

### Incorrect

```tsx
<View>
  <Stat label="Balance" value="$9,076" />
  <Stat label="Income" value="$4,210" />
  <Stat label="Spent" value="$1,337" />
  <Stat label="Saved" value="$2,873" />
</View>
```

### Correct

```tsx
<View>
  <Text style={styles.caption}>Spendable</Text>
  <Text style={styles.hero}>$9,076.56</Text>
  <Text style={styles.muted}>$19,176.56 total · $1,337 spent this month</Text>
</View>
```

### Why This Matters

A screen without a focal point makes people work out what matters, and they will often decide wrongly. A clear hierarchy is also most of what people mean when they call a screen "clean" or "premium". It looks calm because their eye knows where to go.

### Alternatives

Comparison screens such as plan pickers, dashboards built to compare peers, and grids of equal items can give their items equal weight on purpose. Even then, the screen title or the selected item becomes the focal point.
