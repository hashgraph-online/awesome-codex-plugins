# Arbitrary icons — evaluating convention strength

A working framework for evaluating whether a convention is strong enough to depend on as an icon-only treatment.

## The strength spectrum

Conventions exist on a spectrum from "essentially universal in your audience" to "specialized to a small subgroup."

**Tier 1 — universal:** recognized by virtually all users in the audience. Icon-only treatment is safe. Examples: magnifying glass for search, gear for settings, trash for delete, hamburger menu (in mobile audiences). Recognition rate: 90%+.

**Tier 2 — strong:** recognized by most users. Icon-only is usually safe but pairing with label improves accessibility and helps the long tail of unfamiliar users. Examples: kebab menu, share icon (within platform), bell for notifications. Recognition rate: 75–90%.

**Tier 3 — emerging:** convention is forming but not yet dominant. Some competing conventions exist or recognition varies by audience. Pair with label until convention solidifies. Examples: AI sparkle (as of 2026), some emerging gesture conventions. Recognition rate: 40–75%.

**Tier 4 — domain-specific:** strong within a domain, opaque outside. Use icon-only only if the audience is fully within the domain; otherwise label. Examples: developer-tool icons (diff, pull request, branch), design-tool icons (bezier curve, boolean operations), music-software icons. Recognition rate within domain: 80%+; outside domain: <30%.

**Tier 5 — invented:** custom icon with no external precedent. Recognition is essentially zero on first encounter. Always label; don't expect the icon to communicate alone.

## How to evaluate convention strength

For an icon you're considering, evaluate convention strength by:

**Survey usage in major products in your category.** If most products use a particular icon for the function, the convention is strong in your category. If usage is mixed, the convention is weaker.

**Test recognition with users from your audience.** Show the icon (alone, no context) and ask what it means. The recognition rate is a direct measure of convention strength.

**Check across audience subgroups.** New users vs. experienced users; younger vs. older; international vs. local. Convention strength often varies sharply across these dimensions.

**Look for evidence in design system documentation.** When a convention is strong enough that platform design systems (Apple HIG, Material) document it, it has become near-universal in the platform's audience.

**Watch the trajectory.** Conventions form over years and fade over years. An icon that was universal 10 years ago may be confusing now (the floppy disk); an icon that was niche 5 years ago may be becoming universal (the AI sparkle is on this trajectory).

## Patterns of convention spread

Conventions form when an icon is used:

- **Across many products** (so users encounter it repeatedly).
- **For the same function** (so the meaning is reinforced).
- **In visible places** (toolbars, navigation, onboarding).
- **By influential products** (Apple, Google, the leading product in a category).
- **For long enough** (typically 3–5 years for a strong convention to form).

The pattern is roughly: a couple of products use a form, others copy, the form becomes more common, eventually it's recognized as a convention. The reverse pattern is conventions fading: as fewer products use a form, recognition drops, and it eventually becomes opaque.

You can sometimes contribute to convention spread by being early and visible, but you can't reliably create a convention by yourself. Convention spread is a network effect that requires multiple actors.

## When a convention is conflicting

Some functions have multiple competing conventions. Examples:

- **Share:** Apple uses upward-arrow-from-box; Android uses graph-of-three-dots. Cross-platform products either use the platform-native version (most common) or pick one and label it.
- **Save:** floppy disk (legacy convention) vs. cloud-with-checkmark (newer cloud-storage convention) vs. text label "Save". No clear winner; depends on audience and context.
- **Filter vs. sort:** funnel for filter, up-down arrows for sort, but they're often confused. Pair both with text.
- **Refresh vs. undo:** circular arrows can mean either, depending on the curve direction. Disambiguate visually or label.

When conventions conflict, label the icon. Relying on icon-only with a conflicting convention is a recipe for misclick.

## When to follow a convention you don't love

Designers often want to use a convention they think isn't ideal. The principle: convention strength matters more than icon design merit. A "better" custom icon that nobody recognizes is worse than a "worse" conventional icon that everyone recognizes.

The exceptions:

- The convention is genuinely fading. If it no longer communicates to your audience, switching is justified.
- The convention conflicts with your product's other patterns. If using it would create internal inconsistency, pair it with a label or pick a different approach.
- You have a fundamentally better alternative *and* the resources to popularize it. (This is rare.)

In most cases, follow the convention even if you don't love it. Recognition is what makes icons work.

## When to break a convention deliberately

Sometimes departing from a convention is the right call:

- **The convention is dying** and your audience increasingly doesn't recognize it.
- **The convention conflicts with accessibility** (color-only conventions, conventions that depend on visual detail at small sizes).
- **The convention is misleading in your specific context** (the trash icon for "remove from network" rather than "delete").
- **You're explicitly framing the departure** ("we're reimagining this category" with marketing that sets the expectation).

In all these cases, the departure should be supported by a clear label and (if used in onboarding) explicit teaching. Sneaking in an unconventional icon without acknowledgment hurts users.

## A simple decision tree

For each icon decision:

1. Is there a strong convention for this function in my audience? (Tier 1–2)
   - **Yes:** use the convention, optionally label.
   - **No:** continue to step 2.

2. Is there an emerging convention? (Tier 3)
   - **Yes:** use the most-common emerging convention, pair with label.
   - **No:** continue to step 3.

3. Is the function specific to a domain my audience knows? (Tier 4)
   - **Yes:** use the domain convention, pair with label if mixed audience.
   - **No:** continue to step 4.

4. Is the function distinct enough to need its own icon?
   - **No (or unclear):** use text label only.
   - **Yes:** invent an icon and pair with label always; expect recognition to grow only with consistent use.

## Cross-reference

For the parent principle on iconic communication, see `iconic-representation`. For similar (resemblant) icons, see `iconic-resemblance`.
