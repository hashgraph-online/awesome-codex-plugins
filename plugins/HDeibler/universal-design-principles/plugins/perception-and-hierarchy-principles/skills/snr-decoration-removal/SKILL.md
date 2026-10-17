---
name: snr-decoration-removal
description: 'Use this skill when the question is *what to delete* — running a structured audit of a UI to remove decorative elements that don''t earn their pixels. Trigger when reviewing an existing UI for noise reduction, when a stakeholder pushback says "this feels too busy" but you don''t know what specifically to cut, or when polishing a design pre-ship. This is the operational counterpart to `signal-to-noise-ratio`; it gives you a checklist and a procedure rather than a principle.'
---

# Decoration removal: an audit procedure

A structured procedure for going through an existing UI and identifying chrome that adds visual weight without serving the user. Run this as a final pass before shipping, or when revising a design that "feels busy."

## The audit

Work through the UI element-by-element. For each candidate, ask: *if I removed this, would the user lose information they need?* If no, it's a candidate for deletion.

### Borders

For every border on the page, ask:

1. Is it separating two regions that would otherwise blur together? *(e.g., a sticky header from the scrolling content beneath it)*
2. Is it the only thing distinguishing an interactive element from non-interactive content? *(e.g., outlined buttons in a low-color UI)*
3. Is it required by the component's role? *(e.g., the border of an input field)*

If none of the above: delete the border. Most card borders, divider lines between sections, container borders around field groups are unnecessary — proximity already does the grouping work.

### Backgrounds and tints

For every tinted region (cards, panels, banners, callouts), ask:

1. Is it grouping content that proximity alone can't?
2. Is it a state (hover, selected, focused, disabled)?
3. Is it semantic (success/warning/destructive)?

If none of the above, the tint is decoration. Common offenders: brand-tinted hero panels with no informational role, "info" boxes that just hold normal content, colored sections that exist "for variety."

### Shadows

For every box-shadow, ask:

1. Does this element actually float above its context (popover, tooltip, modal, dragged element)?
2. Is it a hover-state cue that matters?

If none of the above, drop the shadow. Most card shadows are unwarranted — cards sit *on* the page, not above it.

### Gradients

For every gradient (backgrounds, button fills, illustrations), ask:

1. Does it reinforce a directional cue (e.g., a hero gradient suggesting depth, a button "lift" via subtle gradient)?
2. Is it part of an illustrative element with content meaning?

If neither, replace with a flat color. Decorative gradients age poorly and reduce SNR.

### Icons

For every icon, ask:

1. Is it replacing text in a space-constrained context (toolbar, mobile nav, tab bar)?
2. Does it disambiguate (e.g., sparkle = AI-assisted, lock = encrypted, warning triangle = destructive)?
3. Is it carrying status information (e.g., success check, error X)?

If none, delete the icon. The most common offender is decorative icons next to section headings — "Notifications" with a bell icon, "Account" with a user icon. The label already says what it is.

### Repeated branding

For every brand mark (logo, brand color block, brand pattern), ask: how many times does the brand appear on this screen? Once is right (header). Twice is fine if one is a footer mark. More than that, you're decorating with the logo and the user is tuning it out.

### Animations and transitions

For every animation, ask:

1. Is it signaling a state change (open/close, success, drag)?
2. Is it providing affordance (a button that elevates on hover)?
3. Is it teaching causality (an item slides into a list to show it was added)?

If none of the above, the animation is eye-candy. Particularly suspect: looping animations (drawing the eye repeatedly), entrance animations on every element on page load (delays time-to-content).

### "Polish" effects

The last pass of a design often adds:

- Glassmorphism / backdrop-filter on elements that don't actually overlap content
- Subtle inner shadows on inputs (they fight focus rings)
- Micro-illustrations next to empty states that already have an icon and a sentence
- Brand-color underlines on headings
- Tinted "callout" boxes around quotes or tips

Each of these has a defensible single use; together, on the same surface, they collapse to noise.

## A worked audit

Imagine the following as the visual chrome on a single dashboard tile:

- 1px border + 8% brand-color tint background + 12px shadow + a 32x32 brand-color icon in a tinted square next to the label + a colored top accent stripe + a hover scale effect + a help-tooltip "i" icon that's never been clicked.

Audit results:

- **Border:** keeps the tile distinct from neighbors → keep, but lighten to `hsl(0 0% 92%)`.
- **Background tint:** decorative, not grouping (proximity already separates tiles) → delete.
- **Shadow:** the tile doesn't float; it sits → delete.
- **Brand icon-in-square:** doesn't add information; "Monthly revenue" is unambiguous → delete.
- **Top accent stripe:** decoration → delete.
- **Hover scale:** the tile isn't a primary interaction; users don't expect cards to scale → delete.
- **"i" tooltip:** if it's never been clicked, ask whether the metric needs explanation at all. If it does, surface that explanation in the dashboard's empty/onboarding state, not on every tile → delete.

What remains: the border, the label, the number, the delta, the timestamp. The signal is intact; the chrome is gone. SNR up, perceived quality often up too — restraint reads as competence.

## Common pitfalls in this audit

- **Overcorrection.** Stripping too much produces sterility (see `snr-densification`). After this audit, look at the page again — has it become too sparse for the role?
- **Saved by hover.** A border is fine *because* it appears on hover. Don't delete it.
- **The stakeholder defense.** "But marketing wanted that callout box." If marketing's request didn't survive a signal audit, propose moving the request to a different surface (the marketing site, an onboarding tour) where decoration is appropriate.

## Heuristics

1. **The 25% screenshot test.** Reduce a screenshot to 25%. Things that vanish are probably noise (or weak signal); things that remain visible are likely signal-bearing.
2. **The "after" walk-through.** After removing things, walk through the user's primary task. Did anything become harder? If yes, restore the deleted element.
3. **Versions side-by-side.** Place the cluttered version next to the cleaned version. Most viewers prefer the cleaned one without being able to articulate why.

## Related sub-skills

- **`signal-to-noise-ratio`** (parent).
- **`snr-densification`** — the opposite move; rebalances if you've over-stripped.
- **`snr-emphasis-economy`** — what to do with emphasis once noise is gone.
