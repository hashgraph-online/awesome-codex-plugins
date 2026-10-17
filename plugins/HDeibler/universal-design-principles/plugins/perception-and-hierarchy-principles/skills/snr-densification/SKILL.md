---
name: snr-densification
description: 'Use this skill when a design has *too much* whitespace — when the SNR pendulum has swung from cluttered all the way to sparse, sterile, or "empty-feeling," and you need to add signal density without adding noise. Trigger when reviewing a UI that "feels thin," "feels under-built," or where users complain "I''m scrolling forever to get to anything." Also trigger when designing power-user surfaces (admin panels, IDEs, data tools) that need higher density than consumer defaults. Sub-aspect of `signal-to-noise-ratio`; read that first if you haven''t already.'
---

# Densification: adding signal without adding noise

The opposite failure mode of "noisy UI" is "sterile UI" — a design so subtractively-edited that it loses the affordances and richness users actually need. SNR is a *ratio*; you can improve it either by removing noise or by adding signal. This skill covers the latter.

## When sterility is the problem

Symptoms:

- Power users tell you they "miss" features that are present but tucked away.
- The page contains 3 things on a 1440px screen and feels under-built.
- Common workflows require navigating away and back; the current surface doesn't show enough.
- The empty state doesn't feel empty — the *populated* state feels empty.
- A/B testing shows users hesitating because there's not enough information to decide.

## What signal-density looks like

Densification means **more meaningful information per visible region**, with the meaning still clearly readable. Done well, it looks like a Bloomberg terminal in restraint mode: many numbers, but every number labeled, ranked, and scannable.

Approaches:

### 1. Replace navigation steps with adjacent context

A common low-density mistake: a list view shows only names; the user clicks through to see details. Densify by showing critical detail inline.

```html
<!-- Sparse: name only, click for detail -->
<li><a href="/projects/acme">Acme Q4 Refresh</a></li>

<!-- Dense: name + status + owner + due date inline -->
<li>
  <a href="/projects/acme">Acme Q4 Refresh</a>
  <span class="meta">In review · Maria · Due May 12</span>
</li>
```

The signal-per-line jumped 4x with no added noise.

### 2. Use compact data primitives

Replace large cards with rows. Replace giant icons with small ones. Replace verbose labels with shorter conventional ones.

```html
<!-- Sparse: each KPI in a 200x200 card with icon and gradient -->
<div class="card-grid">
  <div class="card">…1 number…</div>
  <div class="card">…1 number…</div>
  <div class="card">…1 number…</div>
</div>

<!-- Dense: KPIs as a single row of stat blocks -->
<dl class="stat-row">
  <div><dt>Revenue</dt><dd>$48.2k <span class="delta-up">+12%</span></dd></div>
  <div><dt>Users</dt><dd>12,481 <span class="delta-up">+3%</span></dd></div>
  <div><dt>Churn</dt><dd>2.1% <span class="delta-down">-0.4%</span></dd></div>
  <div><dt>NPS</dt><dd>42</dd></div>
</dl>
```

### 3. Inline action affordances

Don't make users open a row's menu to see what they can do. Show the actions inline (icon-buttons in the row).

```html
<tr>
  <td>Acme Q4 Refresh</td>
  <td>In review</td>
  <td class="actions">
    <button aria-label="Open"><EyeIcon /></button>
    <button aria-label="Comment"><MessageIcon /></button>
    <button aria-label="Archive"><ArchiveIcon /></button>
  </td>
</tr>
```

### 4. Smaller default sizes

The default shadcn/Material density is calibrated for general use. Power surfaces benefit from `text-sm` body, `text-xs` metadata, `py-1.5` row padding instead of `py-3`. Just tune one notch denser, not five.

### 5. Allow user-controlled density

Offer a "Compact" mode in settings, or per-table density toggles, so users can pick their preferred ratio.

## How densification differs from noise

The line between dense and noisy is whether the additional content is **task-relevant**.

- **Dense:** more numbers, more labels, more rows, more context — all serving the user's reason for being here.
- **Noisy:** more borders, more shadows, more illustrations, more decoration — none of which advance the task.

A correctly densified UI looks like more information; a noisy UI looks like more decoration around the same information.

## Worked example: a sparse dashboard, densified

**Before (sparse):**

```html
<main style="padding: 4rem; max-width: 800px; margin: 0 auto;">
  <h1>Welcome back</h1>
  <p>You have 3 things to review.</p>
  <button>Go to inbox</button>
</main>
```

A "welcome dashboard" of this kind feels like a placeholder. The user came to *do something*; they shouldn't have to click through.

**After (densified):**

```html
<main style="padding: 1.5rem; max-width: 1200px; margin: 0 auto;">
  <header style="display: flex; justify-content: space-between; align-items: end;">
    <div>
      <h1 style="font-size: 1.5rem;">Today</h1>
      <p style="color: hsl(0 0% 45%); font-size: 0.875rem;">3 to review · 2 due this week</p>
    </div>
    <div style="display: flex; gap: 0.5rem;">
      <button>Inbox</button>
      <button class="primary">New</button>
    </div>
  </header>

  <section style="margin-top: 2rem; display: grid; gap: 1rem; grid-template-columns: 2fr 1fr;">
    <div>
      <h2 style="font-size: 1rem; margin-bottom: 0.5rem;">To review</h2>
      <ul class="dense-list">
        <li><a href="/r/1">Acme Q4 contract</a> <span class="meta">Maria · 2h</span></li>
        <li><a href="/r/2">Brand book v3</a> <span class="meta">Lin · yesterday</span></li>
        <li><a href="/r/3">2026 hiring plan</a> <span class="meta">You · 3d</span></li>
      </ul>
    </div>
    <aside>
      <h2 style="font-size: 1rem; margin-bottom: 0.5rem;">This week</h2>
      <dl class="stat-list">
        <div><dt>Open tickets</dt><dd>14</dd></div>
        <div><dt>Closed</dt><dd>52</dd></div>
        <div><dt>Avg response</dt><dd>2h 14m</dd></div>
      </dl>
    </aside>
  </section>
</main>
```

Same page region, ~10× the actionable signal, no added noise.

## Anti-patterns

- **Densification by adding decoration.** "It feels empty, let me add a hero illustration." That's the opposite move; you've added noise, not signal.
- **Densification by adding all features.** Every product feature gets a tile on the dashboard regardless of relevance. That's noise too — only the user's actually-needed features should be present.
- **Density without alignment.** Cramming many elements without a strict grid produces clutter, not density. Strong alignment is what allows high density to remain readable.

## Heuristics

1. **Squint test in reverse.** Squint at the page. Is there *any* dominant content? If you see only mass background and a few dots, the page is empty.
2. **The "What can I do here?" test.** Land on the page cold. Within 2 seconds, can you identify 3 actions you might take? If no, density is too low.
3. **The information audit.** Count the distinct pieces of useful information visible without scrolling. Compare to similar surfaces in well-designed competitors. If you're at half their count and the page feels light, densify.

## Related sub-skills

- **`signal-to-noise-ratio`** (parent).
- **`snr-decoration-removal`** — the *subtraction* side of SNR; complementary to this skill.
- **`hierarchy-spatial`** — densification needs strong spatial hierarchy or it becomes visual mush.
- **`propositional-density`** (cognition) — closely related: meaning per mark, signal per pixel.
