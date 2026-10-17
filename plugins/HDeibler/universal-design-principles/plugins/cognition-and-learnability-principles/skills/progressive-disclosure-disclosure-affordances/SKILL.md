---
name: progressive-disclosure-disclosure-affordances
description: 'Use this skill when picking the *mechanism* for revealing tucked content — accordion vs. modal vs. tab vs. separate page vs. tooltip. Trigger when designing the UI for "More options," picking between an inline accordion and a side sheet, deciding whether a wizard step should be a modal or a separate page, or reviewing whether existing disclosure affordances are doing their job. Sub-aspect of `progressive-disclosure`; read that first.'
---

# Progressive disclosure: choosing the affordance

Once you've decided what to tuck, the next decision is how to surface it on demand. Different disclosure affordances suit different relationships between the primary and secondary content. Picking the wrong one is a common subtle UX error.

## The affordance ladder

Ordered roughly from lightest to heaviest:

```
Tooltip / popover         — supplementary info; doesn't disturb flow
Inline expand (accordion) — additional fields/sections within the page
Tab                       — parallel views in the same region
Side sheet / drawer       — detail beside primary content
Modal / dialog            — focused interaction, blocks primary
Separate page             — full context shift, deep-linkable
```

Each level adds friction; pick the lightest affordance that does the job.

## Tooltip / popover

For supplementary information that the user might want but doesn't need to act on.

```html
<button>
  Free trial
  <span tabindex="0" aria-describedby="trial-info">ⓘ</span>
</button>
<div id="trial-info" role="tooltip" hidden>
  14 days, no credit card required. Cancel anytime.
</div>
```

**Use for:**
- Definitions of jargon.
- Format hints for inputs.
- Explanations of UI labels.
- Status / metadata that isn't worth a separate field.

**Don't use for:**
- Required interaction (clicking inside a tooltip is fragile).
- Long-form content (tooltips are for small bits).
- Mobile-primary surfaces (no hover; touch tooltips are awkward).

## Inline expand (accordion)

The classic disclosure pattern: a section header that expands to reveal its content.

```html
<details>
  <summary>Advanced filters</summary>
  <fieldset>
    <label>Created after <input type="date" /></label>
    <label>Tags <input /></label>
  </fieldset>
</details>
```

**Use for:**
- Optional form fields.
- Settings sections that are sometimes relevant.
- FAQ-style content (question = trigger, answer = content).
- Any case where the deeper content makes sense in line with the primary.

**Don't use for:**
- Content that needs more space than the page can give.
- Content the user must engage with for primary task completion.
- Sequenced content (steps in a workflow — use a separate page or modal).

## Tab

Parallel views within the same page region. Switching tabs preserves context (the user is still on the same page; they're just seeing a different facet).

```html
<nav role="tablist">
  <button role="tab" aria-selected="true">Overview</button>
  <button role="tab">Activity</button>
  <button role="tab">Members</button>
  <button role="tab">Settings</button>
</nav>
<div role="tabpanel">...current tab content...</div>
```

**Use for:**
- Parallel views of the same object (overview, activity, members for a project).
- Different cuts of the same data (filter by status: All / Open / Closed).
- Configuration sections grouped by purpose.

**Don't use for:**
- Sequential workflows (tabs imply parallel; use a stepper for sequence).
- Tabs where one is far more important than the others (just show the primary; tuck the rest behind a different affordance).
- Mobile primary nav (mobile bottom-nav is a tab pattern at the global level, but mid-page tabs on mobile are often awkward).

## Side sheet / drawer

A panel that slides in beside the primary content, leaving primary visible. Useful for detail-of-an-item interactions where the user wants to see context while they work.

```html
<aside class="sheet" role="complementary">
  <header>
    <h2>Edit invoice #1284</h2>
    <button aria-label="Close">×</button>
  </header>
  <form>...invoice fields...</form>
  <footer>
    <button>Cancel</button>
    <button class="primary">Save</button>
  </footer>
</aside>
```

**Use for:**
- Editing a row from a table (the table stays visible; the sheet is the editor).
- Detail views in inboxes (Gmail's preview pane).
- Filters or properties for a selected object (Figma's right panel).

**Don't use for:**
- Standalone detail views the user might bookmark (use a separate page).
- Long forms that benefit from full-page focus.
- Modal-required interactions (use a true modal).

## Modal / dialog

A focused surface that blocks the primary. The user can't continue with primary tasks until they close the modal.

```html
<dialog role="dialog" aria-labelledby="dialog-title">
  <h2 id="dialog-title">Confirm deletion</h2>
  <p>Permanently delete "Q4 plan"? This can't be undone.</p>
  <button>Cancel</button>
  <button class="destructive">Delete</button>
</dialog>
```

**Use for:**
- Destructive confirmations.
- Decisions that genuinely block the primary task (you can't continue until you choose).
- Brief, focused interactions (signing in, reviewing a single short form).

**Don't use for:**
- Long flows that would feel claustrophobic in a modal (use a separate page).
- Information the user might want to reference while continuing work (use a side sheet).
- Trivial confirmations the user will dismiss on autopilot (lean on undo instead).

## Separate page

A full URL change. Used when the disclosed content is large enough or important enough to warrant its own context.

**Use for:**
- Deep settings (Account / Security / Billing).
- Configuration UIs that fill the screen.
- Documentation that benefits from its own URL (shareable, bookmarkable).
- Anything the user might link to or return to directly.

**Don't use for:**
- Quick edits that should preserve context.
- Optional fields in an existing form.
- Brief decisions / confirmations.

## Picking the right affordance

A few diagnostic questions:

### Does the user need to keep seeing the primary?

- Yes → tooltip, inline expand, tab, or side sheet.
- No → modal or separate page.

### Will the user return to this disclosed content?

- Yes, frequently → separate page (so they can bookmark / link).
- No, just this once → modal or sheet.

### Does the disclosed content have its own structure (multiple subsections)?

- Yes → separate page or full sheet.
- No → modal, accordion, or tooltip.

### Is the disclosed content a parallel view (vs. a deeper level)?

- Parallel → tab.
- Deeper → accordion or modal.

### Does the disclosed content involve a decision the user must make before continuing?

- Yes → modal.
- No → any other affordance.

## Common mismatches

- **Modal where a tab would do.** A "Filter" modal that pops up to set filters, then closes. Filters belong inline or in a side panel; they're parallel to the main view, not a blocking decision.
- **Accordion where a separate page would do.** Account / billing / security crammed into accordions on a single Settings page. Each is its own context; they deserve their own pages.
- **Tooltip where an inline note would do.** Important explanation hidden in a tooltip the user must hover. Inline help text under the field is more accessible and discoverable.
- **Separate page where a side sheet would do.** Editing a row by navigating to its detail page, then back to the list. Loses scroll position and context. A side sheet preserves both.
- **Tab where progressive disclosure isn't needed.** Two tabs where one has 95% of the relevant content. Just show the primary; the second "tab" can be a link or a smaller affordance.

## Mobile considerations

Mobile compresses the affordance choices:

- **Tooltips** become awkward (no hover); use inline help or a dedicated info screen.
- **Side sheets** typically become full-screen sheets (left or right slide-in).
- **Modals** typically become full-screen presentations.
- **Tabs** stay viable but with smaller labels.
- **Inline accordions** still work well; arguably better on mobile (less screen real estate for everything visible).

When in doubt on mobile, default to inline disclosure (accordion) or full-screen takeover. The middle ground (small popovers, partial overlays) often feels cramped.

## Accessibility notes

- **`<details>` / `<summary>`** is the most accessible inline-expand pattern; native keyboard, semantics, and screen-reader support.
- **`<dialog>`** is the modern modal element with proper focus management when used with `.showModal()`.
- **Tabs** require ARIA: `role="tablist"`, `role="tab"`, `role="tabpanel"`, `aria-selected`, arrow-key navigation.
- **Tooltips** need keyboard activation (focus, not just hover) and proper `aria-describedby` references.
- **Sheets / drawers** need focus trap, Esc to close, focus restoration on close.

Most modern UI libraries (Radix, React Aria, headless component sets) implement these correctly. Custom implementations frequently get focus management wrong; lean on libraries.

## Heuristics

1. **The "lightest viable" rule.** Pick the lightest affordance on the ladder that meets the need. Promoting unnecessarily adds friction.
2. **The deep-link test.** Can users link directly to the disclosed content? If yes, you probably want a separate page (or modal whose state is in the URL). If no, lighter affordance is fine.
3. **The frequency check.** How often does the user open this disclosure? Frequent → light affordance (low friction). Rare → heavier affordance is fine.
4. **The dismiss test.** Can the user always dismiss / close? Esc, click outside, close button — at least two of these should work.

## Related sub-skills

- **`progressive-disclosure`** (parent).
- **`progressive-disclosure-defaults-and-tucking`** — the editorial decisions that produce the choices this skill helps execute.
- **`affordance`** (interaction) — disclosure triggers must look like triggers.
- **`feedback-loop`** (interaction) — opening a disclosure should give immediate visual feedback.
- **`accessibility-operable`** (process) — disclosure affordances must work with keyboard.
