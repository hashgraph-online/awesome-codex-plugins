---
name: color-semantic-systems
description: 'Use this skill when building or auditing a color system that encodes meaning — status colors (success / warning / error), category colors (department, product line, user segment), brand-role colors (primary, secondary, tertiary). Trigger when designing status badges, picking chart palettes, building a design-system color spec, or fixing inconsistent color use across surfaces. Sub-aspect of `color`; read that first.'
---

# Building semantic color systems

A semantic color system encodes meaning through color: green means success, red means error, blue means primary brand. Done well, users learn the system once and read every surface fluently. Done poorly, the same color means different things in different places, and users learn nothing reliably.

## What semantic colors should encode

Three useful categories:

### Status / state

Conveys the condition of a thing:

- Success / completed / passed
- Warning / pending / caution
- Error / failed / overdue
- Info / neutral / draft

Status colors map to specific outcome semantics. Use sparingly: every visible status badge is attention spent.

### Category

Conveys what kind of thing this is:

- Project tags (a small palette of distinct hues for project labels)
- Department or team
- Product line
- User segment

Categories should use perceptually distinct hues; for ≤ 7 categories, color works well. Beyond that, the user can't reliably remember which color means which.

### Brand role

Conveys importance or role within the design:

- Primary brand color → primary CTA
- Secondary / accent → recommended option, focused state
- Tertiary → light emphasis (informational badges)

Role colors are about hierarchy more than meaning per se.

## Building a status palette

A workable status set:

```
success:    hsl(142 70% ...)   green
warning:    hsl(38 90% ...)    amber
destructive: hsl(0 75% ...)    red
info:       hsl(220 90% ...)   blue
neutral:    hsl(0 0% ...)      grey
```

For each, define multiple lightness stops:

- `*-50` — tinted background (used for badges, alerts, subtle treatments)
- `*-300` — border or icon
- `*-500` — primary use (badge color, button color)
- `*-700` — text color (dark, used on tinted backgrounds)
- `*-900` — text on dark backgrounds

The pairing rule: `*-50` background + `*-700` text gives WCAG AA contrast at body size; `*-50` + `*-500` gives AA for large text only.

## Consistency rules for semantic colors

A semantic color system breaks the moment a color means different things in different places. Rules:

- **One color per role.** Don't have "two reds" for "destructive" and "important emphasis." Pick one role per color.
- **Status colors stay status.** Don't use the destructive red for marketing emphasis. The user reads it as error.
- **Category colors stay categorical.** Don't reuse a project-tag color for a status badge.
- **Document the system.** A color-system spec page that lists every color and its role keeps the team honest.

## Building a category palette

For project tags, departments, or chart series:

- **5–7 hues maximum** for memorability; beyond that, users can't recall what means what.
- **Distribute around the color wheel** so adjacent items are visually distinct.
- **Match lightness and saturation** across the set so no one color dominates.
- **Test with colorblind simulation** to ensure each hue remains distinct.

A workable 7-color category palette:

```
hsl(220 70% 55%)    blue
hsl(160 60% 45%)    teal
hsl(40 90% 55%)     amber
hsl(310 60% 55%)    pink
hsl(10 70% 55%)     red-orange
hsl(270 50% 55%)    violet
hsl(85 50% 45%)     olive
```

Each at similar lightness and saturation; each visually distinct from neighbors.

## Brand role palette

The minimum useful set:

- **Primary**: filled CTA, focused state, brand emphasis. One hue, used sparingly.
- **Secondary**: optional alternative emphasis (often used for "recommended" highlight).
- **Accent / tertiary**: micro-emphasis (informational icons, soft highlights).

Most products need only primary plus neutrals; secondary and accent are optional.

## Worked example: a complete semantic system

```css
:root {
  /* Brand */
  --brand-primary: hsl(220 90% 50%);
  --brand-primary-fg: white;
  --brand-primary-hover: hsl(220 90% 45%);

  /* Neutrals (tinted toward brand) */
  --neutral-50: hsl(220 6% 98%);
  --neutral-100: hsl(220 6% 96%);
  --neutral-200: hsl(220 6% 92%);
  --neutral-300: hsl(220 6% 85%);
  --neutral-400: hsl(220 6% 65%);
  --neutral-500: hsl(220 6% 50%);
  --neutral-600: hsl(220 6% 40%);
  --neutral-700: hsl(220 6% 27%);
  --neutral-800: hsl(220 6% 18%);
  --neutral-900: hsl(220 6% 9%);

  /* Status */
  --success-bg: hsl(142 70% 95%);
  --success-fg: hsl(142 70% 22%);
  --success-border: hsl(142 60% 70%);

  --warning-bg: hsl(38 95% 95%);
  --warning-fg: hsl(38 90% 25%);
  --warning-border: hsl(38 80% 70%);

  --destructive-bg: hsl(0 80% 95%);
  --destructive-fg: hsl(0 75% 32%);
  --destructive-border: hsl(0 60% 70%);

  --info-bg: hsl(210 80% 95%);
  --info-fg: hsl(210 80% 30%);
  --info-border: hsl(210 60% 70%);
}
```

Every status pair (bg + fg) clears WCAG AA contrast. The neutrals are tinted toward the brand for cohesion.

## Anti-patterns

- **Brand color reused as primary semantic.** If the brand is red and red also means "destructive," every CTA looks dangerous.
- **Decorative status color.** A red border around a card with no actual error. Users learn to dismiss the cue.
- **Inconsistent saturation across statuses.** Bright green success, muted yellow warning, vivid red error. The visual hierarchy jumps; nothing reads coherently.
- **Too many statuses.** A system with 8 distinct status colors no user can remember.
- **Categories that compete with statuses.** A "project" category color happens to be the same red as your destructive status. Users get confused.

## Heuristics

1. **The "what does each color mean?" audit.** List every color in your design system. Can you name a single specific role for each? If yes, the system is coherent. If a color has multiple roles, conflicts are inevitable.
2. **The grayscale test.** Convert to grayscale. Does the visual hierarchy still work? If yes, color is enhancing, not carrying. If no, you're depending on color alone.
3. **The colorblind test.** Simulate deuteranopia. Are status colors still distinct? Categories?
4. **The cross-surface check.** Open three different pages of the product. Does the same status look the same color across all three?

## Related sub-skills

- **`color`** (parent).
- **`color-accessibility-and-mode`** — accessibility and dark-mode considerations for semantic systems.
- **`hierarchy-color-and-tone`** — color as a hierarchy axis.
- **`consistency`** (cognition) — semantic color is a consistency discipline.
