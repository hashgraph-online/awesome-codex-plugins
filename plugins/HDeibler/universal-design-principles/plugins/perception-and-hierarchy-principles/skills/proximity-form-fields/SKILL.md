---
name: proximity-form-fields
description: 'Use this skill when laying out a form, fixing a confusing form, or building a form layout convention for a design system. Forms are where proximity failures are most visible: ambiguous label-input pairing, sections that bleed into each other, help text that orphans from its field. Trigger when designing sign-up, sign-in, settings, profile, billing, checkout, multi-step, or any structured-input surface. Sub-aspect of `proximity`; read that first if you haven''t already.'
---

# Proximity in form layout

Forms are the canonical proximity case. A form with poor proximity produces ambiguous label-input pairings, orphaned help text, sections that don't read as sections, and a general feeling that the user must "decode" the layout before they can fill it in. A form with good proximity reads as a structured set of pairs and groups; the user fills it in without thought.

## The form proximity ladder

Use four nested levels of spacing — each level visibly tighter than the level above it:

```
Level 1: gap-1   (4px)    inside a label-input pair
Level 2: gap-3   (12px)   between fields in a group
Level 3: gap-6   (24px)   between groups within a section
Level 4: gap-10  (40px)   between sections
```

Each level should be at least 2× the level inside it. Don't use `gap-2` and `gap-3` for different roles — they look identical.

## The label-input pair

The single most important proximity decision in a form: the **label belongs with the input it labels**. Every other proximity issue cascades from this.

### Top-aligned labels (default for vertical forms)

```html
<style>
  .form { display: grid; gap: 1.5rem; max-width: 400px; }     /* Level 3 between groups */
  .field { display: grid; gap: 0.25rem; }                      /* Level 1 inside pair */
  .field-help { font-size: 0.8rem; color: hsl(0 0% 45%); }     /* tone reduction for tertiary */
</style>

<form class="form">
  <div class="field">
    <label for="email">Email address</label>
    <input id="email" type="email" required />
    <p class="field-help">We'll send a verification link.</p>
  </div>
  <div class="field">
    <label for="password">Password</label>
    <input id="password" type="password" required />
  </div>
  <button type="submit">Sign up</button>
</form>
```

The label, input, and help text are bound by tight (4px) spacing. The fields are separated by loose (24px) spacing. Pairing reads instantly.

### Inline labels (left-aligned, common in admin and settings)

```html
<style>
  .form-grid {
    display: grid;
    grid-template-columns: 10rem 1fr;          /* fixed label column */
    gap: 0.75rem 1rem;                          /* row gap, column gap */
    max-width: 600px;
  }
  .form-grid label { padding-top: 0.5rem; text-align: right; }
  .form-grid .field-help { grid-column: 2; font-size: 0.8rem; color: hsl(0 0% 45%); }
</style>

<form class="form-grid">
  <label for="display-name">Display name</label>
  <input id="display-name" />

  <label for="email">Email</label>
  <input id="email" type="email" />
  <p class="field-help">Used for login and notifications.</p>

  <label for="role">Role</label>
  <select id="role">…</select>
</form>
```

Note how the help text appears in the right column under its input — proximity binds it to the field, not to the label across the row.

### Section grouping

When a form spans more than ~5 fields, group them. Sections get **distinctly larger** spacing than between fields, plus a heading.

```html
<form style="display: grid; gap: 2.5rem; max-width: 480px;">
  <section style="display: grid; gap: 1rem;">
    <h2 style="margin-bottom: 0.25rem;">Profile</h2>
    <div class="field"><label>Display name</label><input /></div>
    <div class="field"><label>Bio</label><textarea></textarea></div>
  </section>

  <section style="display: grid; gap: 1rem;">
    <h2 style="margin-bottom: 0.25rem;">Notifications</h2>
    <div class="field"><label>Email frequency</label><select>…</select></div>
    <div class="field"><label>Quiet hours</label><input /></div>
  </section>

  <section style="display: grid; gap: 1rem;">
    <h2 style="margin-bottom: 0.25rem;">Security</h2>
    <div class="field"><label>Two-factor</label><div>…toggle…</div></div>
  </section>
</form>
```

Three ranks of spacing (1rem within a section, 2.5rem between sections, plus the tight 0.25rem inside each field). The heading is *slightly* closer to its first field (0.25rem) than to neighbors (1rem) so it groups with what it labels.

### Required indicators

A common proximity question: where does the asterisk go? Right next to the label text, with no space:

```html
<label>Email <span class="required" aria-hidden>*</span></label>
```

Not:

```html
<label>Email</label> <span class="required">*</span>     <!-- detached, looks like body content -->
```

The asterisk is part of the label, not a separate element. Proximity confirms.

### Inline error messages

Errors should appear *below* the field they reference, with tight spacing:

```html
<div class="field" data-state="error">
  <label for="email">Email</label>
  <input id="email" type="email" aria-invalid="true" aria-describedby="email-error" />
  <p id="email-error" class="field-error">Please enter a valid email.</p>
</div>

<style>
  .field-error {
    font-size: 0.8rem;
    color: hsl(0 75% 35%);
    margin-top: 0.25rem;     /* same as label-input gap */
  }
</style>
```

The error sits inside the field group's tight cluster, so the user reads it as part of the field, not as page-level content.

## Multi-column forms

Sometimes density requires placing fields side-by-side (first name / last name; city / state / zip). Proximity-friendly multi-column layout:

```html
<style>
  .field { display: grid; gap: 0.25rem; }
  .row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }   /* same as field gap */
</style>

<form style="display: grid; gap: 1rem; max-width: 480px;">
  <div class="row">
    <div class="field"><label>First name</label><input /></div>
    <div class="field"><label>Last name</label><input /></div>
  </div>
  <div class="row" style="grid-template-columns: 1fr auto auto;">
    <div class="field"><label>City</label><input /></div>
    <div class="field"><label>State</label><select>…</select></div>
    <div class="field"><label>ZIP</label><input style="width: 6rem;" /></div>
  </div>
</form>
```

The horizontal gap (`gap: 1rem`) within a row matches the vertical gap between rows. Each field is a tight pair internally. The user reads "first name + last name as a paired row," distinct from the row above.

## Anti-patterns

- **Equal vertical spacing.** Label, input, label, input all separated by the same gap. Pairing is ambiguous; users read carefully.
- **Help text outside the pair.** Help text in a sidebar or above the section heading. The user has to look elsewhere to understand the field. Place help text under its input, tightly bound.
- **Section heading equally spaced above and below.** The heading should be tighter to its own section than to the previous section.
- **Border-as-section.** Wrapping each section in a card with a 1px border because the spacing isn't doing the work. First fix the spacing; the borders may not be needed.
- **Mobile mush.** A form that's nicely grouped on desktop collapses on mobile because the responsive layout reduced all gaps to one value. Maintain the proportional ladder at every breakpoint.

## Heuristics

1. **Cover and pair.** Cover all but two adjacent elements. Can you tell if they're a pair or two separate items? If not, the gap is wrong.
2. **The 'gap audit'.** List every distinct gap value used in the form. There should be 3–5, each visibly different. Many distinct gaps near each other (8px, 10px, 12px, 14px) signal accidental spacing.
3. **Mobile line-up test.** At 320px viewport, the form should still read as discrete groups. If it becomes a single column of evenly-spaced rows, proximity has collapsed.

## Related sub-skills

- **`proximity`** (parent) — the principle in full.
- **`proximity-data-tables`** — applying the same idea to tabular data.
- **`hierarchy-spatial`** — spatial hierarchy *between* groups; complementary to proximity *within* groups.
