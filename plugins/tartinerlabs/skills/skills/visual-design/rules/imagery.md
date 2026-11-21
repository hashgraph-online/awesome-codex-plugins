---
title: Imagery
impact: MEDIUM
tags: hero, illustration, mascot, onboarding, empty-states, store-assets
---

**Rule**: Make the product's own content the signature visual (its data, artwork, map, or real interface) and draw it the same way everywhere. When illustration is needed, use one imagery mode in one style.

**Evidence**: Studies of product pages and onboarding (Nielsen Norman Group on decorative versus informative images) find that users ignore generic stock imagery and look closely at images that show the actual product or content. A consistent visual style is also what makes a brand recognisable from a single screenshot.

### When Building

- **Find the signature visual.** Every product has something only it can show: a route on a map, a balance trend, a week of meals, the album art of a playlist, a chart of the user's sleep. Use it as the hero on onboarding, empty states, widgets, and store assets.
- **Real interface pieces beat illustrations of the interface.** For showcase screens, use actual components (rotated, overlapping, scaled) rendered with real-looking data, not a drawing of a phone.
- **One imagery mode per product**: real UI pieces, photography, flat illustration, 3D, or a mascot. Mixing modes looks assembled.
- **A mascot is a set of states, not one sticker.** Give it a pose for welcome, success, empty, error, and waiting at minimum, all drawn by the same hand.
- **Empty states show the content to come**: a faded example of the filled screen or the signature visual, with the action that fills it.
- **Placeholder data looks real.** Use plausible names, dates, and amounts in showcase imagery, not "Lorem ipsum", "$0.00", or "John Doe".
- **Store assets follow the app.** App Store and Play Store screenshots use the same direction, headline style, and signature visual as onboarding.

### When Auditing

- Generic stock photos or unrelated 3D blobs as hero images
- Several imagery styles mixed (flat illustration on one screen, 3D on the next)
- A mascot with one pose reused for every state
- Empty states with an icon and a sentence but no hint of the filled screen
- Placeholder text or zero values in showcase screenshots
- Store screenshots that look like a different product from the app

### Incorrect

```tsx
<EmptyState
  image={require("./assets/stock-team-laptop.png")}
  title="Nothing here yet"
/>
```

### Correct

```tsx
<EmptyState
  image={<FadedPreview items={sampleItems} />}
  title="Your first recipe shows up here"
  action={<Button>Add a recipe</Button>}
/>
```

### Why This Matters

Imagery is what people remember and what makes a product recognisable in a store listing. When it shows the product itself, every image explains what the app does. Generic imagery explains nothing and could belong to any app.

### Alternatives

Editorial and lifestyle products may lead with photography when the photographs are the content (food, travel, fashion). Restrained products can skip imagery entirely and let the data be the visual.
