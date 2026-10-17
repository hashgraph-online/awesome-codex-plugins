---
name: hierarchy
description: 'Use this skill whenever a design has more than one element competing for the viewer''s attention — which is essentially every design. Trigger when laying out a screen, page, slide, poster, dashboard, or any composition where you must decide what gets seen first, what supports it, and what recedes. Trigger when reviewing a design and the user says "everything looks the same," "I don''t know where to look," "the page feels flat," or "what''s the most important thing here?" Trigger when picking type sizes, when deciding which actions to emphasize among many, or when an MVP screen has gone from one button to ten and the screen has lost its focal point. Hierarchy is the most decisive visual principle; this skill teaches how to construct it deliberately, and routes to sub-aspect skills for typographic, spatial, and color/tone hierarchy.'
---

# Hierarchy

Hierarchy is the ranking of importance among visible elements, made legible to the eye through differences in size, weight, color, contrast, position, density, and surrounding space. It is the single most decisive principle in visual design: when hierarchy is well-constructed, the rest of the layout almost designs itself; when it is missing, no amount of polish recovers the page.

## Definition (in our own words)

A composition has *visual hierarchy* when the viewer can, at a glance and without instruction, identify a primary focal element, secondary supporting elements, and recessive background elements. Hierarchy is created by introducing **deliberate differences** along one or more visual dimensions (size, weight, color, position, density, motion). It is destroyed by making everything the same — and equally by making everything different at maximum intensity. Hierarchy is a *contrast* principle: emphasis is meaningful only against a quieter background.

## Origins and research lineage

The deliberate construction of visual hierarchy is one of the oldest practices in graphic communication. Its modern theoretical grounding draws from several lines of work:

- **Gestalt psychology** (Wertheimer, Köhler, Koffka, c. 1910–1930) established that perception groups stimuli into wholes whose structure precedes their parts. The Gestalt laws (figure/ground, proximity, similarity, continuation) are the mechanisms by which hierarchy is read.
- **Information design** (Bertin's *Sémiologie graphique*, 1967; Tufte's *Visual Display of Quantitative Information*, 1983) formalized the visual variables (position, size, value, texture, color, orientation, shape) that encode rank and difference.
- **Cognitive load theory** (Sweller, 1988 onward) explains why hierarchy reduces effort: a well-ranked composition lets the viewer offload sequencing decisions onto the perceptual system.
- **Eye-tracking studies** (Pernice, Nielsen, Pelli, and many others) have repeatedly shown that viewers fixate first on elements that are larger, brighter, higher-contrast, or positioned at common entry points (top-left in left-to-right scripts), before sweeping the rest of the page.

The takeaway: hierarchy is not an aesthetic preference; it is a structural property that determines whether the composition will be readable at all.

## Why hierarchy matters

When you scan a page, your eye is doing two things in rapid alternation: detecting *salient* features (high-contrast, isolated, unusual) and predicting *meaningful* features based on prior knowledge of the layout type. Hierarchy aligns those two: the salient features are the meaningful ones. Without that alignment, the viewer's eye is pulled to whatever is loudest (a stray red icon, a bold word, a big image) regardless of whether that thing is important.

The cost of weak hierarchy compounds: every visit, every screen, every interaction, the viewer pays a small tax to figure out what to look at. Multiply by daily users and the tax is significant.

## When to apply

- **Every composition with more than one element.** Even a "minimal" page with three elements is making hierarchy decisions, intentionally or otherwise.
- **When your first draft "feels flat."** Flatness is almost always a hierarchy problem, not a color or whitespace problem.
- **When users report not knowing where to look or what to do next.** This is hierarchy diagnosing itself.
- **At the start of a layout pass, before pixel-perfect adjustments.** Hierarchy decisions cascade; tweak them after the fact and the cascade reverses.

## When NOT to apply (or when to be careful)

- **In neutral-comparison contexts.** Pricing tables, side-by-side feature comparisons, equal-weight survey options — these *want* equivalence. Adding hierarchy here biases the user. Distinguish "neutral comparison" from "recommended option" deliberately.
- **In dense data tables where every row has equal status.** Adding hierarchy *between rows* is wrong; reserve hierarchy for the chrome (header, footer, totals) and let the rows be uniform.
- **When you don't know what's most important yet.** Don't fake hierarchy by making something arbitrarily bigger. Hierarchy only works when it tracks real importance.

## How hierarchy is constructed: the visual dimensions

Hierarchy is built by varying one or more visual dimensions across elements. Each dimension has different strengths and trade-offs:

| Dimension | What it does well | Cost / risk |
|---|---|---|
| **Size** | Strongest single signal; reads at any distance. | Cheap to overdo; gigantic headlines crowd context. |
| **Weight** | Strong, subtle, additive to size. | Bold-fatigue when overused; loses meaning if everything is bold. |
| **Color (hue)** | Carries categorical meaning; high attention pull. | Accessibility and cultural pitfalls; never the only signal. |
| **Tone (value/contrast)** | Most universal; works in monochrome and accessibility modes. | Subtle; needs other dimensions for headline-level emphasis. |
| **Position** | Top, center, leading edge — privileged by reading habits. | Real estate is finite; not every important thing fits at the top. |
| **Whitespace / isolation** | Gives an element room to breathe; reads as importance. | Costs space; can leave a layout thin if overused. |
| **Density / repetition** | Items repeated together read as a system; the lone item reads as primary. | Backfires if the "system" items become noise. |
| **Motion** | Strongest attention pull; cannot be ignored. | Easily overwhelming; accessibility (vestibular triggers, motion sensitivity); use sparingly. |

The competent use of hierarchy is **stacking** these dimensions: a primary heading is larger *and* heavier *and* darker *and* further from neighbors. A secondary action is medium-sized *and* outlined *and* placed left of the primary. Stacking compounds the signal; relying on a single dimension makes the hierarchy fragile.

## The three-tier rule

A workable default for most compositions: aim for **three** levels of hierarchy.

1. **Primary** — the focal element. There should usually be exactly one per visible region. (More than one fights for attention.)
2. **Secondary** — supporting elements that contextualize the primary. There may be several at this level.
3. **Tertiary** — recessive background elements: navigation chrome, metadata, fine print, captions.

Too few levels (everything primary, or everything tertiary) is flat. Too many levels (5+) blur into one another and the eye treats them as a continuous gradient rather than discrete ranks.

## Worked examples

The examples below are framework-agnostic — written in plain HTML/CSS to make the principle decisions visible. Apply them to any framework.

### Example 1: a page header with title, subtitle, and metadata

A common case where weak hierarchy makes the page feel flat. Three elements; we want one to dominate.

**Anti-pattern (flat):**

```html
<header class="page-header">
  <h1 style="font-size: 1.25rem; font-weight: 500;">Invoices</h1>
  <p style="font-size: 1.25rem; color: #555;">Sent and overdue, this quarter.</p>
  <p style="font-size: 1.25rem; color: #555;">Last updated 3 minutes ago</p>
</header>
```

Three lines all roughly the same size, weight, and color. The eye finds no focal point.

**Right (three tiers):**

```html
<header class="page-header" style="display: grid; gap: 0.25rem;">
  <h1 style="font-size: 1.875rem; font-weight: 600; line-height: 1.2;">Invoices</h1>
  <p style="font-size: 0.95rem; color: #555;">Sent and overdue, this quarter.</p>
  <p style="font-size: 0.8rem; color: #888; margin-top: 0.25rem;">Last updated 3 minutes ago</p>
</header>
```

Now the title dominates by size + weight + tone. The subtitle supports it (smaller, mid-tone). The metadata recedes (smaller still, lower contrast). Three clear tiers, one focal point.

### Example 2: a button row with primary, secondary, and tertiary actions

A frequent case in modal footers, form submissions, and toolbars. The wrong distribution of weight here is one of the most common UI mistakes.

**Anti-pattern (all equal, eye doesn't know which to pick):**

```html
<div class="actions">
  <button class="btn">Cancel</button>
  <button class="btn">Save draft</button>
  <button class="btn">Publish</button>
</div>
```

Three same-styled buttons. The user must read all three labels and decide; primary intent is invisible.

**Right (one primary, two recessive):**

```html
<div class="actions" style="display: flex; gap: 0.5rem; justify-content: flex-end;">
  <button class="btn-ghost">Cancel</button>      <!-- tertiary: text-only, low weight -->
  <button class="btn-outline">Save draft</button> <!-- secondary: bordered, neutral -->
  <button class="btn-primary">Publish</button>    <!-- primary: filled, high contrast -->
</div>
```

```css
.btn-primary { background: #111; color: white; padding: 0.5rem 1rem; border-radius: 0.375rem; }
.btn-outline { background: transparent; border: 1px solid #d1d5db; padding: 0.5rem 1rem; border-radius: 0.375rem; }
.btn-ghost   { background: transparent; border: 0; color: #555; padding: 0.5rem 1rem; }
```

The primary action wins on color and weight. The secondary is recognizably a button (bordered) but quiet. Cancel is a soft escape — necessary but never the focal point.

### Example 3: a dashboard tile grid

Twelve KPI tiles, all the same. The eye gives up. Pick a primary KPI, make it dominate, let the rest recede.

```html
<section class="dashboard" style="display: grid; gap: 1rem; grid-template-columns: repeat(4, 1fr);">
  <article class="tile primary" style="grid-column: span 2; grid-row: span 2;">
    <p class="label">Monthly revenue</p>
    <p class="value" style="font-size: 3rem; font-weight: 600;">$48.2k</p>
    <p class="delta" style="color: #16a34a;">+12% vs last month</p>
  </article>
  <!-- 8 secondary tiles, smaller, recessed -->
  <article class="tile"><p class="label">Active users</p><p class="value">12,481</p></article>
  <article class="tile"><p class="label">Churn</p><p class="value">2.1%</p></article>
  <article class="tile"><p class="label">NPS</p><p class="value">42</p></article>
  <!-- ... -->
</section>
```

The primary tile spans 2x2 grid cells, has a 3rem value, includes a delta, and dominates the composition. The secondary tiles are smaller, single-line values, no delta. The eye reads the dashboard in seconds.

### Example 4: a form with required and optional sections

Even forms have hierarchy: the required path is primary; optional fields are secondary; help text is tertiary.

```html
<form>
  <fieldset class="primary">
    <legend>Account</legend>
    <label>Email <input type="email" required /></label>
    <label>Password <input type="password" required /></label>
  </fieldset>

  <details class="secondary">
    <summary>Profile (optional)</summary>
    <label>Display name <input /></label>
    <label>Bio <textarea></textarea></label>
  </details>

  <p class="tertiary" style="font-size: 0.8rem; color: #888;">
    By signing up you agree to the Terms of Service.
  </p>

  <button class="btn-primary">Create account</button>
</form>
```

Required fields are visible and primary. Optional fields are tucked behind a `<details>` disclosure (secondary). Legalese is tertiary in size and tone. The user's eye lands on the necessary path first.

## Anti-patterns

- **The "hierarchy of bold."** Every label is bold, every heading is bold, every number is bold. Bold has lost all meaning; the page is noisy and flat at the same time. Fix: reserve bold for one or two roles.
- **Color as the only signal.** Important things are blue; everything else is grey. Works for sighted, non-colorblind users in good lighting; fails everywhere else. Fix: stack color with size and weight.
- **The aspirational primary.** Designer makes the "Sign up" CTA gigantic on a settings page where 99% of users are signed in. The primary action should be the *most likely* action on this surface, not the one the business wishes were primary.
- **Hierarchy through volume.** "Important" things are wrapped in colored boxes with thick borders and exclamation icons. Reserve heavy treatments for genuinely critical UI — destructive confirmations, errors, system warnings.
- **No primary at all.** Every element is "secondary" because the designer didn't want to play favorites. Result: equal-weight noise. Fix: pick a primary even if it feels arbitrary; you can always change it after a usability test.

## Heuristics and measurement

A few quick checks for whether hierarchy is working:

1. **The squint test.** Squint at the design (or blur it in Photoshop / via a CSS `filter: blur(8px)`). Can you still see one element dominating? If not, hierarchy is too weak.
2. **The eye-trace.** Show the design to someone for 3 seconds, hide it, ask them what they remember. The thing they remember should be your primary. If it isn't, hierarchy is wrong.
3. **The grayscale test.** Convert to grayscale. If the hierarchy collapses, you were leaning on color alone; restore it through size and weight.
4. **The five-tier check.** Count the distinct visual ranks in your composition. More than 4–5? You probably have too much hierarchy and it's blurring.

## Related principles

- **`alignment`** — hierarchy operates *along* a grid; misalignment fights hierarchy.
- **`proximity`** — proximity establishes *grouping*; hierarchy establishes *ranking* between groups.
- **`signal-to-noise-ratio`** — strong hierarchy increases SNR by making one thing carry the message.
- **`highlighting`** — emphasis works only when sparse; hierarchy is the systemic version.
- **`von-restorff-effect`** — the deliberately-different element is remembered; primary action of a composition leverages this.
- **`gutenberg-diagram`** — when hierarchy is *absent*, the eye falls back to the Z-pattern.

## Sub-aspect skills (read these for specific applications)

- **`hierarchy-typographic`** — type-scale, weight ladders, and how to construct hierarchy entirely through typography.
- **`hierarchy-spatial`** — using position, size, and whitespace to establish hierarchy.
- **`hierarchy-color-and-tone`** — using color, value, and contrast as a hierarchy dimension without sacrificing accessibility.

## Final caution

Hierarchy is one of the few principles where "more is more" is genuinely a trap. The temptation is always to make the primary *more* primary — bigger, brighter, redder. This works once, briefly. After two or three uses the eye desensitizes and you're back where you started, but with a louder page. Restraint preserves the dimension you're spending. Spend it on the things that earn it.
