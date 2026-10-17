# Figure-ground cues — elevation systems

Practical guidance on building consistent elevation systems that maintain figure-ground separation across a product.

## What an elevation system does

An elevation system formalizes figure-ground cues into a small set of named levels, each with a specific shadow recipe (and possibly other cues). All elements in the product use one of the named levels rather than ad-hoc shadow values.

The benefits:

- Consistency across the product (all modals look like modals; all popovers look like popovers).
- Easier to maintain (changing the elevation scale changes all instances).
- Clearer communication (designers and engineers can talk about "elevation 8" rather than describing shadows).
- Better accessibility (consistent visual hierarchy is easier to navigate).

## A starter elevation scale

A working scale with 6 levels:

| Level | Use case | Shadow recipe |
|---|---|---|
| 0 | Surface (no elevation) | none |
| 1 | Subtle card elevation | 0 1px 2px rgba(0,0,0,0.05) |
| 2 | Card hover, subtle popover | 0 2px 4px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04) |
| 4 | Floating action button, dropdown | 0 4px 8px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04) |
| 8 | Sidebar drawer, sticky header | 0 8px 16px rgba(0,0,0,0.10), 0 4px 8px rgba(0,0,0,0.05) |
| 16 | Modal, dialog | 0 16px 32px rgba(0,0,0,0.12), 0 8px 16px rgba(0,0,0,0.06) |

These are starting points. Adjust the values based on your design's overall feel.

Material Design's elevation system uses a similar (though more elaborate) approach. Apple's Human Interface Guidelines use distinct treatments for different layer types (popovers, sheets, modals).

## Combining elevation with other cues

Shadow alone is sometimes insufficient for clear figure-ground. Combine with:

**Background color.** Elevated elements often have a slightly different background — usually slightly lighter than the surface (in light mode) or slightly elevated-feeling (in dark mode).

**Scrim.** For high-elevation elements (modals, lightboxes), a scrim over the page makes the separation explicit.

**Border.** A subtle 1px border can reinforce a card's edge when shadow alone is too soft.

**Background blur.** iOS uses background blur extensively for elevated elements (sheets, popovers). The blurred background makes the elevated element stand out crisply.

**Animation.** Elements that animate to their elevated position (a modal sliding up; a popover appearing with a subtle scale-in) reinforce the elevation perceptually.

## Dark mode considerations

In dark mode, the typical "elevated = lighter background" pattern reverses. Elevated elements in dark mode usually have:

- Slightly lighter background (because lighter feels closer to the user in dark UI).
- Reduced shadow opacity (shadows are less visible against dark backgrounds).
- Sometimes a subtle inner glow or border to suggest the edge.

Define your elevation tokens with dark-mode variants. Don't just invert light-mode values.

## Application patterns

**Cards:** elevation 1 by default, elevation 2 on hover.

**Sticky headers:** elevation 4 to 8 when scrolled (so they appear to lift off the page).

**Dropdowns and popovers:** elevation 4 to 8.

**Floating action buttons:** elevation 4 to 6 with hover bumping to slightly higher.

**Side panels:** elevation 8 to 12 (significant separation from main content).

**Modals:** elevation 16 to 24, often paired with a scrim.

**Toasts and notifications:** elevation 8 to 16 (clearly above other content but not as dominant as modals).

## Hierarchy of layers

A useful mental model is the z-axis hierarchy:

- Surface (the page itself).
- Cards and contained content.
- Sticky elements (headers, sidebars).
- Floating UI (FABs, dropdowns).
- Side panels and drawers.
- Modals and dialogs.
- Toasts and snackbars.
- Tooltips (highest, very transient).

Each layer has its own elevation. Within a layer, elevation can differ between resting and hovered states.

## Common failures

**No system, ad-hoc shadows.** Each card uses a different shadow. The product feels inconsistent.

**Too many elevation levels.** A 12-level scale is too many to apply consistently. 5–7 levels is usually enough.

**Elevation that doesn't match conceptual layering.** A modal at lower elevation than a popover. Users get confused about what's "in front."

**Heavy shadows that look outdated.** Shadows from 5 years ago tended to be heavier and more dramatic than current style. Subtle, low-opacity shadows are more current. Refresh your shadow values periodically.

**Different elevation cues for the same concept.** Modals use shadow in one part of the product; modals use border in another part. Pick one and apply consistently.

**Elevation cues failing in dark mode.** Light-mode cues that don't translate. Always define dark-mode equivalents.

## Building an elevation system into a design system

Define elevation as design tokens:

```
shadow.0: none
shadow.1: 0 1px 2px rgba(0,0,0,0.05)
shadow.2: 0 2px 4px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)
shadow.4: 0 4px 8px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)
shadow.8: 0 8px 16px rgba(0,0,0,0.10), 0 4px 8px rgba(0,0,0,0.05)
shadow.16: 0 16px 32px rgba(0,0,0,0.12), 0 8px 16px rgba(0,0,0,0.06)
```

And dark-mode variants:

```
shadow-dark.0: none
shadow-dark.1: 0 1px 2px rgba(0,0,0,0.30)
shadow-dark.2: 0 2px 4px rgba(0,0,0,0.35), 0 1px 2px rgba(0,0,0,0.25)
... etc.
```

Components reference the named tokens; switching between light and dark mode swaps the underlying values. The named system is the contract; the values can evolve over time.

## Cross-reference

For modal/overlay-specific patterns, see `figure-ground-overlays-and-modals`. For the parent principle, see `figure-ground-relationship`.
