---
name: proximity
description: 'Use this skill whenever the question is how to make a composition feel organized — what belongs with what, where groups end, how related items can be visually bound without resorting to borders or boxes. Trigger when laying out forms, tables, navigation, lists, cards, dashboards, or any composition with multiple distinguishable groups of content. Trigger when a layout "feels disorganized," when users are confused which label goes with which input, when grouping is being attempted with borders that look heavy, or when a designer is reaching for color to encode grouping. Proximity is the cheapest, most powerful grouping tool in design; this skill teaches how to use spacing as the primary grouping mechanism, with sub-aspect skills for forms, tables, and navigation.'
---

# Proximity

Proximity is one of the original Gestalt grouping laws: **elements close together are perceived as belonging together; elements farther apart are perceived as separate.** It is the cheapest grouping mechanism in the designer's toolkit — it requires no ink, no color, no chrome, only the deliberate distribution of space. Used well, proximity makes most other grouping tools (borders, backgrounds, dividers) unnecessary.

## Definition (in our own words)

When the human visual system encounters a set of similar elements, it organizes them into groups based on relative spatial distance. Items that share a small gap are perceived as a unit; items separated by a larger gap are perceived as belonging to different units. This perceptual grouping happens preattentively — before conscious thought, before reading. It is one of the most reliable findings in perception research, observed in infants, across cultures, and across animal species.

## Origins and research lineage

- **Gestalt psychology** (Wertheimer, 1923) formalized the laws of perceptual grouping, of which Proximity (*Gesetz der Nähe*) is the most basic. Wertheimer's original demonstrations used dots arranged at varying distances; the perceived groupings shifted dramatically with small spacing changes.
- **Treisman's feature integration theory** (1980s) and the broader preattentive-processing literature established that grouping by spacing happens within the first ~200ms of viewing — before the user has consciously "looked" at anything.
- **Information design** (Tufte; Krug, *Don't Make Me Think*, 2000) translated proximity from perception research into web/UI practice, particularly in the design of forms and information dense surfaces.
- **Web usability research** (Nielsen Norman Group studies on form perception, label-input pairing) repeatedly shows that label-input ambiguity — usually a proximity failure — is among the top usability issues in form design.

## Why proximity matters

Every layout makes implicit proximity claims. If a label is equidistant from the input above and the input below, the user must read carefully to figure out which it labels. If two cards are visually identical to two surrounding cards, they read as one group of four — even when conceptually they're two pairs.

Proximity failures are silent: users don't report "this label is ambiguous"; they just take longer, make more mistakes, and feel a low-grade frustration they can't articulate. This is why proximity is one of the highest-leverage things to get right in dense interfaces — small spacing decisions determine whether the page feels organized or chaotic.

## When to apply

- **Forms** — every label-input pair, every section, every fieldset. Proximity is the dominant principle in form layout.
- **Lists and tables** — row spacing, column spacing, group separators.
- **Navigation** — clusters of related links, dividers between sections.
- **Cards** — internal layout (title, metadata, body, action) and external layout (cards-in-a-grid).
- **Dashboards** — grouping of related KPIs.
- **Settings pages** — sections, sub-sections, grouped controls.

In short: anywhere you have ≥3 elements and need to communicate which belong together.

## When NOT to apply (or when to be careful)

- **When everything genuinely has equal status.** A list of 100 search results doesn't want sub-grouping; the user is scanning sequentially. Adding proximity-based grouping where there is no real grouping is noise.
- **When grouping must survive responsive reflow.** If your nice 3-column grid wraps to 1 column on mobile, the proximity grouping that worked horizontally may collapse vertically. Plan for both.
- **When proximity conflicts with continuity.** Sometimes elements that share a baseline or column should read as a row, even with internal gaps. Then alignment beats proximity (see Good Continuation).

## How to encode grouping with proximity

The trick is creating a **spacing hierarchy**: gaps inside a group should be smaller than gaps between groups, and the difference should be perceptually obvious. A 4px gap looks roughly like a 6px gap; the eye can't tell. A 4px gap is unmistakably tighter than a 16px gap.

A useful spacing scale (most design systems land somewhere near this):

```
gap-1   = 0.25rem (4px)    inside a tight pair (label/input)
gap-2   = 0.5rem  (8px)    inside a closely related set
gap-3   = 0.75rem (12px)   between fields in a section
gap-4   = 1rem    (16px)   between minor groups
gap-6   = 1.5rem  (24px)   between sections
gap-8   = 2rem    (32px)   between major regions
gap-12  = 3rem    (48px)   between page-level zones
```

Adjacent values in the scale should differ by at least 1.5× — preferably 2× — for the eye to register them as different ranks of grouping. Don't use both `gap-3` and `gap-4` in the same composition for *different* grouping levels; they look identical.

## Worked examples

### Example 1: a label-input pair (the canonical case)

**Anti-pattern (ambiguous):**

```html
<form>
  <label>Email</label>
  <input type="email" />
  <label>Password</label>
  <input type="password" />
</form>
```

With default browser margins, each label sits roughly equidistant from the input above and the input below. The user has to read to figure out the pairing.

**Right (proximity binds the pair):**

```html
<form style="display: grid; gap: 1rem;">                  <!-- gap-4 between fields -->
  <div style="display: grid; gap: 0.25rem;">              <!-- gap-1 between label and input -->
    <label for="email">Email</label>
    <input id="email" type="email" />
  </div>
  <div style="display: grid; gap: 0.25rem;">
    <label for="password">Password</label>
    <input id="password" type="password" />
  </div>
</form>
```

Now the gap inside each pair (4px) is unmistakably tighter than the gap between pairs (16px). Pairing reads instantly without any reading.

### Example 2: a settings page with three sections

```html
<style>
  .settings { display: grid; gap: 3rem; }       /* gap-12 between sections */
  .section  { display: grid; gap: 1rem; }       /* gap-4 between fields */
  .section h2 { margin-bottom: 0.5rem; }        /* heading slightly closer to its fields */
  .field { display: grid; gap: 0.25rem; }       /* gap-1 inside label/input pair */
</style>

<form class="settings">
  <section class="section">
    <h2>Profile</h2>
    <div class="field"><label>Name</label><input /></div>
    <div class="field"><label>Email</label><input /></div>
  </section>
  <section class="section">
    <h2>Notifications</h2>
    <div class="field"><label>Frequency</label><select>...</select></div>
    <div class="field"><label>Channels</label><input /></div>
  </section>
  <section class="section">
    <h2>Security</h2>
    <div class="field"><label>Password</label><input type="password" /></div>
  </section>
</form>
```

Three nested ranks of proximity (4px / 16px / 48px) carry the entire grouping. No borders, no boxes, no dividers, no color — just space.

### Example 3: a card with title, metadata, body, and action

```html
<style>
  .card { display: grid; gap: 1rem; padding: 1.5rem; }
  .card-header { display: grid; gap: 0.25rem; }     /* title + metadata are paired */
  .card-actions { display: flex; gap: 0.5rem; margin-top: 0.5rem; }
</style>

<article class="card">
  <header class="card-header">
    <h3>Q4 financial review</h3>
    <p class="meta">Updated 3 minutes ago · Owner: Maria</p>
  </header>
  <p>This quarter shows record revenue across the SMB segment...</p>
  <div class="card-actions">
    <button>Open</button>
    <button>Share</button>
  </div>
</article>
```

Three groupings: title-metadata (tight pair), body (its own paragraph), actions (their own row). Each cluster reads independently; together they form the card.

### Example 4: a navigation menu with sections

```html
<nav style="display: grid; gap: 1.5rem;">                <!-- gap between sections -->
  <div style="display: grid; gap: 0.25rem;">             <!-- tight gap between links -->
    <a href="/dashboard">Dashboard</a>
    <a href="/projects">Projects</a>
    <a href="/team">Team</a>
  </div>
  <div style="display: grid; gap: 0.25rem;">
    <a href="/settings">Settings</a>
    <a href="/billing">Billing</a>
    <a href="/logout">Sign out</a>
  </div>
</nav>
```

Two clear sections, no dividers needed. The eye reads the gap between them as a section break.

## Anti-patterns

- **The four-equidistant trap.** Label, input, label, input — all spaced the same. Common in browser-default form rendering. Always tighter inside the pair, looser between pairs.
- **Borders as grouping.** Reaching for `border: 1px solid grey` around every group adds visual weight without doing what proximity already does for free. Borders are a fallback for when proximity isn't enough.
- **Inconsistent gaps for the same role.** Three sections on a page, each separated by a different gap. The eye reads inconsistency as accident; settle on one section gap and use it everywhere.
- **Equal gaps top-to-bottom in a card.** Header, body, footer all separated by the same gap. The user has to read to figure out the structure. Vary gaps to encode role.
- **Whitespace orphans.** A heading close to its content, but with so much space below the content that the next heading attaches to the *previous* content rather than its own. Always: heading-tighter-to-its-content; sections-looser-than-fields.

## Heuristics

1. **Squint test for grouping.** Squint until detail blurs. Each visual cluster should be obvious as a cluster, with clear gaps between clusters. If the page is one continuous mass, proximity is too uniform.
2. **Read the cards aloud.** "Title, then metadata, then body, then actions." If you can hear the pauses between groups, proximity is working. If everything runs together, the gaps are equal.
3. **Two-finger test.** With two fingers, can you point at a single group and feel that the boundaries are clear? If your finger keeps drifting into the next group, the boundary is too ambiguous.
4. **Strip the borders.** Remove every border on the page (mentally or actually). If structure collapses, you were leaning on borders to do proximity's job.

## Related principles

- **`uniform-connectedness`** — when proximity isn't enough, a shared background or container creates a stronger group; proximity tried first.
- **`similarity`** — items that look alike are also grouped; combines with proximity.
- **`good-continuation`** — items aligned on an axis read as a row, even with internal spacing.
- **`hierarchy`** — proximity establishes *grouping*, hierarchy establishes *ranking* between groups.
- **`signal-to-noise-ratio`** — proximity reduces noise by replacing chrome (borders, backgrounds) with negative space.
- **`horror-vacui`** — proximity *requires* whitespace; resist filling it.

## Sub-aspect skills

- **`proximity-form-fields`** — applying proximity to form layouts, label-input pairs, sections.
- **`proximity-data-tables`** — row spacing, column spacing, total rows, group separators.
- **`proximity-navigation`** — sidebar groups, top-nav clusters, mobile menus.

## Final note

Proximity is the principle most likely to be invisible when working and noisy when failing. The reward for getting it right is that the page feels organized in a way no one can quite pinpoint — they just don't get confused.
