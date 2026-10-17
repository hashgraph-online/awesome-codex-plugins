---
name: progressive-disclosure
description: 'Use this skill whenever a design has *more* available than the user needs to see at this moment — settings panels with advanced options, forms with optional fields, dashboards with drill-down detail, navigation with deep IA, dialogs with "More options" affordances, marketing pages with FAQ accordions. Trigger when designing or fixing surfaces that feel "overwhelming," when stakeholders argue about whether to expose every option up front, when novice and expert users have different tolerance for the same surface, or when reviewing a UI cluttered with rarely-used controls. Progressive disclosure is one of the foundational principles in ''Universal Principles of Design'' (Lidwell, Holden, Butler 2003), originally formalized through the Xerox Star user-interface work in the 1970s.'
---

# Progressive Disclosure

Progressive disclosure is the discipline of revealing information and controls in layers — showing only what's needed for the current decision and tucking the rest behind explicit affordances the user can invoke when they need more. It's one of the most decisive cognition principles in software UI: it reduces visible complexity for the 80% case while preserving access to the long tail.

## Definition (in our own words)

Instead of presenting every option, control, and piece of information at once, divide the surface into layers based on usage frequency or relevance. Show the "primary layer" — what the typical user needs in the typical case — and conceal the rest behind disclosure affordances (a "More" button, an accordion, an "Advanced" tab, a menu). Users who need the deeper layers can reach them with one explicit action; users who don't are spared the cognitive cost of looking past them.

## Origins and research lineage

- **The Xerox Star user interface** (Xerox PARC, 1981) is widely credited as the first commercial system to explicitly apply progressive disclosure as a design strategy. Properties dialogs in Star showed common settings by default and offered more-detailed controls behind a "More" button — a pattern adopted by Mac OS, Windows, and most modern UI conventions afterward.
- **Lidwell, Holden & Butler**, *Universal Principles of Design* (2003) articulated the principle as "a strategy for managing information complexity in which only necessary or requested information is displayed at any given time" and noted its application both in software and physical environments (theme park lines that don't expose their full length).
- **Jakob Nielsen** has written extensively on progressive disclosure as a usability technique: it reduces error rates by hiding controls users aren't ready to use, and it eases novice onboarding without penalizing expert use.
- **Cognitive load theory** (Sweller, 1988 and later) explains the underlying mechanism: every visible element imposes some intrinsic and extraneous cognitive load. Hiding the long tail of options removes the extraneous load they impose, freeing working memory for the task at hand.

## Why progressive disclosure matters

Every visible option costs the user something. They must:

1. **Notice** it — perceptual cost.
2. **Read** it — comprehension cost.
3. **Evaluate** whether it's relevant to their task — decision cost.
4. **Decide** whether to use it — Hick's Law cost.
5. **Live with** the consequence if they engaged with it incorrectly — error cost.

For options that are rarely used, the user pays this cost on every visit and almost never gets value from it. The math is brutal: a user visiting a settings page 50 times pays the cost on each of the 47 fields they don't need to see, every time, in service of changing the 3 fields that matter.

Progressive disclosure inverts the math: the 3 frequent fields are visible, the 47 are tucked away with one explicit affordance. Cost-per-visit collapses; access is preserved.

## When to apply

- **Long forms** where some fields are required and others optional.
- **Settings pages** with both common and advanced options.
- **Toolbars** where a few actions cover most use and the rest live in overflow menus or palettes.
- **Filter UIs** with basic and advanced filtering.
- **Pricing pages** with feature lists too long to display in tier cards.
- **Dialogs** with "Show more" / "Advanced" patterns.
- **Documentation** with summary up top and details on demand.
- **Onboarding** that introduces features gradually rather than all at once.

## When NOT to apply

- **When all the disclosed information is essential.** A safety checklist, a legal disclosure, a price breakdown the user must see before buying — hiding these is malpractice.
- **When discovery matters more than density.** A new product surface where users don't yet know what's possible needs to *show* features, not hide them. Progressive disclosure assumes users know what they're looking for or can find it via search.
- **When the disclosure adds confusion.** A "More" button leading to two more buttons leading to a panel — disclosure depth without payoff. If the deeper layers are themselves overwhelming, the principle isn't being applied; it's being deferred.
- **In compliance / accessibility contexts.** Information required by law, by accessibility standards, or by user-trust commitments (privacy disclosures, billing terms) cannot be hidden behind disclosure. They can be *summarized* with a "Read full terms" link, but not concealed.

## The two layers (and sometimes three)

A useful model: think of every surface as having a primary layer and a deeper layer (or two).

### Primary layer

What's visible by default. Should answer:

- The 80% case: what most users need, most of the time.
- The required path: fields, controls, or information without which the task can't be completed.
- The wayfinding chrome: nav, breadcrumb, page title.

### Secondary layer

Visible after one explicit user action. Should answer:

- The 20% case: options used by power users or in unusual situations.
- Optional refinements: filters, settings, customizations.
- Detail / explanation that the primary layer summarizes.

### Tertiary layer (sparingly)

Visible only after deeper navigation. Should be:

- The very-long tail: feature flags, debug tools, edge-case settings.
- "Expert mode" / advanced / "I really want to do something unusual."

Going deeper than 3 layers is rare and usually a sign the IA itself is too dense.

## Disclosure affordances

The mechanism by which the user reveals deeper layers. Patterns:

### "Show more" / "More choices" buttons

The Xerox Star pattern. A button at the edge of the visible content reveals additional fields or options inline.

```html
<form>
  <label>Find: <input name="q" /></label>
  <button type="button" onclick="toggle('advanced')">More choices ▾</button>

  <fieldset id="advanced" hidden>
    <label>Search in: <select>...</select></label>
    <label>Match: <select>...</select></label>
  </fieldset>

  <button type="submit">Find</button>
</form>
```

The toggle is reversible; "More choices" becomes "Fewer choices" when expanded. Users can close back to the simpler view.

### Accordions

Multiple disclosure affordances stacked vertically, each revealing its own deeper content.

```html
<details>
  <summary>Account</summary>
  <div>...account fields...</div>
</details>

<details>
  <summary>Notifications</summary>
  <div>...notification settings...</div>
</details>

<details>
  <summary>Advanced</summary>
  <div>...advanced settings...</div>
</details>
```

Native `<details>` / `<summary>` provides the accessibility scaffolding for free; reach for it before custom accordions.

### Tabs

Different views within the same region, only one visible at a time. Useful when the secondary content is *parallel* to the primary, not deeper.

```html
<nav role="tablist">
  <button role="tab" aria-selected="true">Overview</button>
  <button role="tab">Activity</button>
  <button role="tab">Members</button>
  <button role="tab">Settings</button>
</nav>
```

### Pages and routes

The strongest form of disclosure: a separate page reached by navigation. Use when the deeper content is large enough to warrant its own URL, breadcrumb, and orientation chrome.

### Modals and sheets

A primary surface remains in context while a deeper surface overlays. Useful for editing a single object's detail, configuring something, or reviewing.

### Hover / focus reveals

The lightest disclosure: a tooltip or popover on hover/focus. Reserved for supplementary information that doesn't disrupt the main flow.

```html
<button>
  Free trial
  <span class="info" tabindex="0" aria-describedby="trial-info">ⓘ</span>
</button>
<div id="trial-info" role="tooltip" hidden>
  14 days, no credit card required.
</div>
```

Caveat: hover-only disclosures fail on touch and for keyboard users. Always pair with focus or click.

## Worked examples

### Example 1: a search form with simple and advanced modes

The canonical Xerox Star pattern, still the right answer for most search UIs.

```html
<form action="/search">
  <input name="q" placeholder="Search" autofocus />
  <button type="submit">Search</button>

  <details>
    <summary>Advanced</summary>
    <fieldset>
      <label>In: <select name="in">
        <option>All</option>
        <option>Title</option>
        <option>Body</option>
      </select></label>
      <label>Posted after: <input type="date" name="after" /></label>
      <label>Author: <input name="author" /></label>
    </fieldset>
  </details>
</form>
```

99% of users hit Enter on the search field. The 1% who need scoped search expand Advanced and refine.

### Example 2: a settings page with chunked sections

Long settings pages benefit from accordion-style disclosure: each section is collapsed by default; the user opens the one they want.

```html
<form class="settings">
  <details open>
    <summary><h2>Profile</h2></summary>
    <div>
      <label>Display name <input /></label>
      <label>Bio <textarea></textarea></label>
    </div>
  </details>

  <details>
    <summary><h2>Notifications</h2></summary>
    <div>...notification controls...</div>
  </details>

  <details>
    <summary><h2>Security</h2></summary>
    <div>...security controls...</div>
  </details>

  <details>
    <summary><h2>Advanced</h2></summary>
    <div>...power-user options...</div>
  </details>
</form>
```

The first section is open by default (`open` attribute) so the user lands somewhere; the rest expand on demand.

### Example 3: a filter bar with primary and advanced filters

```html
<form class="filters">
  <input type="search" placeholder="Search" />
  <select><option>Status: Active</option>...</select>
  <select><option>Owner: Anyone</option>...</select>

  <details>
    <summary>+ More filters</summary>
    <fieldset>
      <label>Created after <input type="date" /></label>
      <label>Tag <input /></label>
      <label>Custom field 1 <input /></label>
      <label>Custom field 2 <input /></label>
    </fieldset>
  </details>
</form>
```

Three filters cover most use; the rest are an explicit gesture away.

### Example 4: a marketing FAQ

A marketing page with 25 questions and answers is overwhelming. Show the questions; expand answers on click.

```html
<section class="faq">
  <h2>Common questions</h2>

  <details>
    <summary>How long is the free trial?</summary>
    <p>14 days. No credit card required.</p>
  </details>

  <details>
    <summary>What happens after the trial?</summary>
    <p>You can choose a paid plan or downgrade to our free tier...</p>
  </details>

  <details>
    <summary>Do you support SSO?</summary>
    <p>Yes, on Pro and Enterprise plans...</p>
  </details>
</section>
```

The page reads as 25 questions, not as 25 paragraphs of answers. Users open only the ones they care about.

### Example 5: progressive disclosure in onboarding

A user signs up for a complex product. Showing every feature on day one would overwhelm. Instead:

- **Day 1:** the product introduces itself with one simple flow (create your first object).
- **Days 2–7:** contextual tooltips reveal features as the user encounters surfaces where they apply.
- **Week 2+:** "What's new" or "Tips" surfaces introduce advanced features once the user has the basics.

The complexity is *temporally* disclosed rather than spatially.

## Cross-domain examples

### Theme park lines

A theme park line stretching to the horizon discourages joining. Modern parks use serpentine queues, walls, and visual breaks to disclose only a small segment of the line at a time. Visitors at the front can't see the back; visitors at the back can't see the front; the apparent line length is much shorter than the actual length.

The same logic underlies "infinite scroll" in software (the user only sees the current view; the apparent content depth is limited) and "lazy loading" (only what's needed now is loaded; the rest waits).

### Restaurant menus

A multi-page menu with categories on tabs is progressive disclosure. The user picks a category (Appetizers / Mains / Desserts) and sees only those items. Without the categorization, all 80 items would compete for attention.

A single-page menu by contrast — common at fast-food counters — exposes everything because the order decision happens in seconds and Hick's Law cost is small enough to absorb.

### Print form folding

Government and legal forms often fold the long instructions out of the way until the user reaches a relevant section. Tax forms, insurance applications, and the IRS-style worksheet model all use spatial disclosure to manage a 30-page form's visible complexity.

### Chapter-by-chapter book reading

A book is progressive disclosure of content. The reader doesn't see Chapter 12 while reading Chapter 1; they reach it sequentially. Books that violate this (showing all spoilers up front) frustrate readers; books that respect it (gradual reveal) succeed.

## Anti-patterns

- **Disclosure to nowhere.** A "More options" button that reveals one additional checkbox. The disclosure overhead exceeds the disclosed value.
- **Disclosure stacking.** "More" → "More" → "More" → the actual control. Each click is friction; aggregate clicks compound.
- **Hiding the required.** Required fields tucked behind disclosure. The user submits with the visible fields filled, gets an error, expands the hidden section to find more required fields.
- **Hiding the primary action.** The "Save" or "Buy" button is somehow inside an accordion. Users miss it; conversion drops.
- **Defaults closed when most users need them open.** A FAQ where the most-asked question is collapsed at the same level as a 50-times-rarer question.
- **No memory of disclosure state.** Every page load resets disclosed sections. A power user who reopens "Advanced" every visit will resent it.
- **Using disclosure to bury bad news.** "Total" prominent; "Including taxes and fees" tucked behind disclosure. Users feel cheated when they expand.

## Heuristics

1. **The "what does the typical user need?" test.** For each visible element on the surface, ask: is this in the typical user's path? If no, ask: should it be tucked behind disclosure? Most "yes."
2. **The "click count" audit.** For the most common task on this surface, how many clicks does it take? Disclosure that increases the click count for common tasks is wrong.
3. **The "did they find it?" test.** Watch users perform an uncommon task. Do they find the disclosed control? If they search, miss, and give up, your disclosure affordance isn't visible enough.
4. **The Pareto check.** Look at usage analytics. What percentage of users engage with a given control? <20% is a strong candidate for disclosure. <5% is a strong candidate for *removal* (or moving to a separate "advanced" page).

## Related principles

- **`hicks-law`** — partner principle; progressive disclosure shrinks the visible decision space, reducing Hick's Law cost.
- **`80-20-rule`** — partner principle; tells you which 20% to surface and which 80% to disclose.
- **`chunking`** — disclosure groups items into chunks (sections, accordions); chunking organizes within them.
- **`recognition-over-recall`** — disclosed items must be recognizable; "More options" needs to suggest what's behind it.
- **`mental-model`** — disclosure depth must match the user's mental model; surprise depth confuses.
- **`performance-load`** — progressive disclosure reduces both cognitive load (less to read) and kinesthetic load (less to scroll).
- **`wayfinding`** — disclosure interacts with wayfinding; users must be able to *find* the disclosed content when they need it.
- **`signal-to-noise-ratio`** (perception) — disclosure is the procedural form of SNR discipline applied to time-of-display.

## Sub-aspect skills

- **`progressive-disclosure-defaults-and-tucking`** — how to decide what's primary vs. tucked, and how to default disclosure states.
- **`progressive-disclosure-disclosure-affordances`** — the specific UI patterns (buttons, accordions, tabs, modals) and when each fits.

## Closing

Progressive disclosure is one of the highest-leverage cognition moves in modern UI design. Done well, it creates an experience that feels simple to novices and powerful to experts — the same surface serving both. Done poorly, it hides what users need and surfaces what they don't. The discipline is in the editorial choice: who is this *for*, and what do they need *now*?
