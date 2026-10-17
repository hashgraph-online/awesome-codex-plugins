---
name: snr-emphasis-economy
description: 'Use this skill when deciding *how* to spend emphasis — color, weight, size, motion — across a design so that each instance lands. Trigger when picking the primary action among many CTAs, when status-color usage has multiplied across the app and lost meaning, when the brand color appears in too many places, or when a designer asks "should this also be highlighted?" and the answer is almost always no. Sub-aspect of `signal-to-noise-ratio`; read that first if you haven''t already.'
---

# Emphasis economy

Emphasis is a finite resource. Every time you use color, bold, size, or motion to call attention to something, you're spending some of the user's *attentional bandwidth*. Spend too freely and the bank empties — emphasis stops registering. Spend deliberately and each instance lands.

## The core idea

Emphasis works through *contrast against a quieter background*. A red badge in a sea of white badges shouts; a red badge among twenty other red badges is invisible. The job of emphasis economy is to keep the background quiet so the emphasized things stand out.

The rough budget per surface:

- **One** primary action per visible region.
- **One or two** instances of the brand-emphasis color (logo, primary CTA).
- **One or two** instances of destructive color (an "overdue" badge, a delete button — never both on the same row).
- **Zero or one** "new!" / highlight callouts.

Above this, emphasis dilutes.

## How emphasis dilutes

A page starts with one bold word, one colored badge, one underlined link. The eye picks them out instantly. Add a second bold word — the eye now sweeps both. Add a third — they're a category, not emphasis. By the seventh bold word, "bold" no longer means "important"; it means "this UI uses bold a lot."

The same dilution happens with:

- **Color emphasis:** brand-color buttons everywhere → brand color stops registering.
- **Status color:** every row marked "active" green → green stops meaning anything specific.
- **Size emphasis:** every section heading at 24px → no section dominates.
- **Motion:** loading spinners, animated badges, hover rotations on every card → page feels jittery and nothing reads as primary.

## Practical rules

### One primary action per region

A region (toolbar, card, modal footer, page header) gets exactly one filled / colored / dominant button. Everything else is `outline`, `ghost`, or text-only.

```html
<!-- Right -->
<div class="actions">
  <button class="ghost">Cancel</button>
  <button class="outline">Save draft</button>
  <button class="primary">Publish</button>
</div>

<!-- Wrong: three primary buttons fight; user can't pick -->
<div class="actions">
  <button class="primary">Cancel</button>
  <button class="primary">Save draft</button>
  <button class="primary">Publish</button>
</div>
```

If you genuinely have two equally-primary actions (rare), the layout should make the choice obvious through framing, not weight: "Continue without saving" / "Save and continue" — both visually equal, both labeled to clarify the consequence.

### Reserve destructive color for actually destructive

"Destructive red" should appear in a UI in proportion to how often the user faces a destructive action. On most surfaces, that's zero or one places. If your app has red on every row (because "delete" is in every row's menu), the destructive signal is now ambient and won't activate when it actually matters.

Better: keep "delete" as a neutral menu item until the user *opens* the confirmation, then the dialog goes red. Stress saved for the moment.

### Reserve status color for genuine status variation

A list of items where every item is the same status doesn't need a color-coded badge — the column is constant. Use status color only when status varies meaningfully.

### Reserve bold for one or two roles

Pick what bold means in your design:

- Headings (most common)
- Primary numbers in tables / dashboards
- "Now" or "live" markers

Three bold roles is the maximum. If labels, values, headings, table headers, button text, and metadata are all bold somewhere, bold no longer encodes anything.

### Reserve motion for state changes

A button glows on hover (state). A toast slides in (state). A new item lifts into a list (state). These all earn their motion. A page-load fade-in cascade across every element is theater — restraint serves the user better.

## How to spend emphasis well

Once you've quieted the background, you have a budget to spend on the moments that matter.

### The single hero moment

A pricing page can have *one* "Recommended" tier highlighted. Not three "popular" tiers; not every tier with a color. One.

```html
<div class="pricing-grid">
  <article class="plan">…Starter…</article>
  <article class="plan featured">…Pro (highlighted)…</article>
  <article class="plan">…Enterprise…</article>
</div>
```

The featured plan gets: a slightly different background, a "Recommended" chip, a brighter border, a slightly lifted shadow. Stack the cues.

### The single first-time moment

A new feature gets a "New" badge for two weeks. Not forever. Not on every feature simultaneously. Spend the badge on the most important new thing, retire it after users have seen it.

### The single high-stakes confirmation

A destructive `AlertDialog` gets the full red + warning icon + type-to-confirm treatment because *this is the moment it earns those cues*. The button to open the dialog can stay neutral.

## Worked example: a noisy toolbar, economized

**Before (emphasis everywhere):**

```html
<header class="toolbar" style="background: hsl(220 90% 95%);">
  <button class="primary">New</button>
  <button class="primary" style="background: hsl(142 70% 35%);">Sync</button>
  <button class="primary" style="background: hsl(38 90% 50%);">Reports</button>
  <button class="primary" style="background: hsl(280 70% 50%);">AI</button>
  <span class="badge new" style="background: hsl(0 80% 50%);">NEW</span>
  <span class="badge new" style="background: hsl(0 80% 50%);">BETA</span>
  <button class="primary danger">Delete all</button>
</header>
```

Five colored buttons, two red badges, one tinted background. Eye finds nothing.

**After (emphasis economized):**

```html
<header class="toolbar">
  <button class="primary">New</button>
  <button class="ghost">Sync</button>
  <button class="ghost">Reports</button>
  <button class="ghost"><SparklesIcon /> AI <span class="badge">New</span></button>
  <div style="margin-left: auto;">
    <button class="ghost danger" aria-label="Delete all"><TrashIcon /></button>
  </div>
</header>
```

One primary action. One "New" badge on the genuinely new feature. The destructive action is iconified and tucked at the right margin. The eye finds "New" instantly.

## Anti-patterns

- **Promotional creep.** Marketing wants every available feature to have a "callout"; over time everything's highlighted and nothing reads.
- **Brand-color CTA inflation.** Every link, every action, every chip in brand color. Brand color now means "interactive in general," not "do this thing."
- **Status-everywhere syndrome.** Every row has a colored status badge, every column has an icon, every value has a delta indicator. Real status changes get lost in the texture.
- **Animation inflation.** Page loads with cascading entrance animation, scrolls trigger reveals, hovers spin, badges pulse. Total visual fidget; cognitive cost is high.

## Heuristics

1. **Count the highlights.** On any given screen, how many things are highlighted (colored, bold, badged, animated)? More than 3–4? Cut.
2. **Cover-the-emphasis test.** Cover the most-emphasized element. Does anything *else* now read as primary? If yes, you have multiple primaries fighting.
3. **The "what's new here?" test.** Glance at the page for 1 second. What's the first thing you noticed? If it was an accidental ornament rather than your intended primary, the economy is broken.

## Related sub-skills

- **`signal-to-noise-ratio`** (parent).
- **`snr-decoration-removal`** — the audit method for stripping noise; clears space for emphasis to land.
- **`snr-densification`** — the opposite move when over-pruned.
- **`hierarchy`** — emphasis economy is the operational expression of hierarchy: the budget you spend to make the rank visible.
- **`von-restorff-effect`** — the perceptual basis for why economized emphasis works.
- **`red-effect`** — the specific case for the destructive color budget.
