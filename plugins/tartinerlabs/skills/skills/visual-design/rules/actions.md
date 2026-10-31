---
title: Actions
impact: MEDIUM
tags: buttons, cta, selection, primary-action, button-system
---

**Rule**: Use one button system: a filled primary, quieter secondary and tertiary styles, and the same shape and position across a flow. The primary action uses ink or the accent, whichever does not collide with the content's colours.

**Evidence**: The von Restorff isolation effect (1933) and Fitts's law (1954) explain why one distinct, reachable primary action works. This rule covers their visual side; whether an action belongs on the screen at all is `ux-psychology`'s call.

### When Building

- **Three levels**: primary (filled), secondary (tinted or outlined), and tertiary (text only). One primary per screen or section.
- **One shape for the system**: pill or rounded rectangle, from the radius scale. Keep the height constant across a flow. Make phone primaries full-width or close to it, at the bottom within thumb reach.
- **Ink or accent for the primary.** An ink (near-black) primary works in any direction and never collides with category colours. Use the accent when it is reserved for actions. A small accent element inside an ink button (an arrow, an icon) carries the brand without using an accent fill.
- **Selection uses the same logic.** Show selected chips, tabs, and segments with ink or the accent, not with a category colour, and add a second cue (weight, check mark, fill).
- **Pressed, disabled, and loading states** are part of the system. Disabled stays legible and does not look like a secondary style.
- **Destructive actions** use the status red, separated from the primary, and are never the default.
- **Use platform buttons where the platform expects them**: system alerts, toolbars, and navigation bars keep native styling.

### When Auditing

- Two or more filled primaries competing on one screen
- Button height, radius, or position changing between steps of a flow
- Selection shown in a colour that also marks a category or status
- Several one-off button styles across the app
- Disabled styling indistinguishable from secondary
- A custom-styled button inside a system alert or toolbar

### Incorrect

```swift
Button("Continue") { next() }
  .buttonStyle(.borderedProminent)
  .tint(.green) // green also marks the "Groceries" category
```

### Correct

```swift
Button { next() } label: {
  Label("Continue", systemImage: "arrow.right").labelStyle(.titleAndIcon)
    .frame(maxWidth: .infinity)
}
.buttonStyle(.borderedProminent)
.buttonBorderShape(.capsule)
.tint(Color.ink) // asset-catalog colour
```

### Why This Matters

Users learn the primary button within a screen or two and then look for it in the same place, with the same shape. A consistent button system makes a flow feel fast and confident. Changing styles make every step feel like a new product.

### Alternatives

Products whose brand is the accent colour (a single-colour fintech, for example) can use the accent for every primary as long as no category colour sits near it. Platform-native apps may keep the system's default prominent button and tint it with the accent.
