# Signifier design decisions: deeper reference

A reference complementing `affordance-signifiers` with patterns and trade-offs around picking signifier strength.

## Norman's signifier framework

Norman's 2008 essay "Signifiers, not affordances" argued that designers should focus on signifiers because:

- Affordances often exist regardless of design (a `<button>` is clickable whether styled or not).
- The design decision is *what to make perceivable* about that affordance.
- Designers don't add or remove the underlying possibility; they add or remove the cues users see.

This shifts the design question from "is this affordable?" to "does the user know it's affordable?" — which is much more answerable from observation.

## The signifier budget

Like emphasis, signifiers spend attention. A page where every element is highly signifier-rich (every "card" has hover, every section has a chevron, every label has a help-icon) reads as noisy.

A useful budget: 3–5 distinct signifier styles per surface, each consistent in role.

```
Primary action      → filled background, brand color, strong hover
Secondary action    → outlined, neutral, medium hover
Tertiary action     → text-only, brand color, light hover
Destructive action  → distinct color (typically red), strong hover, often after confirm
Inert content       → no signifier
```

Five distinct styles, each used for one role consistently across the entire product.

## Signifier consistency across components

The signifier system should hold across all interactive elements, not just buttons:

- A "More" disclosure trigger should use the same chevron icon site-wide.
- Drag handles should use the same six-dot icon site-wide.
- Sortable column headers should use the same arrow indicator.
- Editable fields (when not always editable) should use the same affordance hint.

Inconsistency degrades the system: each variation forces the user to re-learn what the cue means.

## When subtle signifiers are appropriate

Dense expert tools (IDEs, DAWs, trading terminals) sometimes use subtler signifiers because users develop muscle memory and spatial knowledge. They don't *scan* for the signifier; they fly to where they remember the control was.

The trade-off: new users have a much steeper learning curve. Tools intended for daily use by professionals can absorb that curve; tools intended for casual or occasional users can't.

## Mobile-specific signifier challenges

Mobile lacks hover, which is a major signifier channel on desktop. Mitigations:

- **Stronger static signifiers** — bordered, filled, or both.
- **Press-state animations** that confirm taps.
- **Long-press** as a discoverable secondary affordance (often communicated through onboarding or empty-state hints).
- **Iconographic conventions** (hamburger menu, plus FAB) that users recognize across apps.

Mobile bottom-nav and FAB patterns work because they exploit consistent iconography and position — the user learns once across many apps.

## Resources

- **Norman, D.** "Signifiers, not affordances" — jnd.org, 2008.
- **Material Design**, **Apple HIG** — both publicly document signifier patterns for their platforms.
- **NN/g** — many articles on signifier design and the flat-design regression.
