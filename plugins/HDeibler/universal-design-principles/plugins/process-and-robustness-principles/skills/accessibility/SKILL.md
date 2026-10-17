---
name: accessibility
description: 'Use this skill on every design task that produces a user-facing surface. Trigger on every screen, component, prototype, or design review — accessibility isn''t a phase, it''s a property each surface either has or doesn''t. Trigger when the user mentions accessibility, a11y, WCAG, screen readers, keyboard navigation, contrast, motion sensitivity, ARIA, color blindness, "section 508," "EAA," or compliance. Also trigger when the user is *not* asking about accessibility — because most of the highest-impact accessibility decisions are made silently when no one was asking. Routes to sub-aspect skills for the four WCAG sub-principles: perceivable, operable, understandable, robust.'
---

# Accessibility

Accessibility is the property of a design that lets it be used by the widest plausible range of people, including people with permanent, temporary, and situational impairments. It is not "compliance polish"; it is structural. A design that is bolted on top of an inaccessible foundation will always be partially accessible at best, and the cost to retrofit climbs quickly.

## Definition (in our own words)

A design is accessible to the extent that people can perceive its content, operate its controls, understand what it tells them, and rely on it across the assistive technologies they use. The four verbs — *perceive, operate, understand, robust* — are not arbitrary; they are the four sub-principles of the Web Content Accessibility Guidelines (WCAG), and they cover the full surface area of what can fail when a person who isn't a designer's idealized user encounters a design.

## Origins and research lineage

- **WCAG 1.0 (1999)** was the first formal web accessibility specification, published by the W3C's Web Accessibility Initiative (WAI).
- **WCAG 2.0 (2008)** introduced the four-principle framework (Perceivable, Operable, Understandable, Robust) that grounds modern web accessibility practice.
- **WCAG 2.1 (2018)** and **WCAG 2.2 (2023)** added criteria for mobile, low-vision, and cognitive disabilities.
- **Section 508** (US, 1998 onward) and the **European Accessibility Act** (EAA, full effect 2025) make accessibility a legal requirement for many public-facing software products in their jurisdictions.
- **Inclusive Design** (Microsoft Inclusive Design Toolkit; the work of Kat Holmes, Susan Goltsman, Annie Jean-Baptiste) reframes accessibility as designing for the spectrum of human diversity rather than for "users with disabilities" as a separate category.

The takeaway: accessibility is a four-decade discipline with established principles, measurable criteria, and increasingly serious legal teeth.

## Why accessibility matters

The business case is often presented as either ethical ("it's the right thing to do") or compliance ("we'll get sued"). Both are real. But the deeper case is that accessibility is **good design that's been measured against the hardest cases**.

The user with a screen reader is the user who needs your label-input pairing to be programmatically associated. *Every* user benefits when it is. The user with low vision is the user who needs your contrast ratio to clear 4.5:1. *Every* user benefits when contrast is good. The user with a motor impairment is the user who needs your hit targets to be 44×44. *Every* user — including users on a phone in motion, in glare, with a cracked screen, or one-handed — benefits.

Accessibility raises the floor for everyone. The disabled user is the canary; if the design works for them, it works under the broader range of conditions everyone occasionally faces.

The numbers in any modern audience:

- ~15% of any population has a long-term disability (WHO).
- ~8% of men have red-green color blindness; ~0.5% of women.
- ~25% of adults over 65 have meaningful vision loss.
- 100% of users will eventually be in some form of degraded condition (sun glare, motion, fatigue, distraction, broken finger).

## When to apply

- **Every design task.** Yes, every one.
- **Most pointedly: at the start.** Bake accessibility into the design phase rather than retrofit at the end. Retrofitting is 2–10x the cost of building it in.
- **At every design review.** Add an accessibility check to the review template.
- **In component design (design system).** Get the primitives right and every consumer of them inherits the accessibility for free.

## When NOT to apply

There is no surface on which accessibility doesn't apply. The relative weight of different criteria varies (a marketing landing page is mostly Perceivable + Operable; a complex form is mostly Operable + Understandable), but no surface is exempt.

## The four sub-principles (WCAG framework)

WCAG organizes accessibility into four categories. Each gets its own sub-aspect skill in this plugin; this section is the overview.

### Perceivable

Users must be able to *perceive* the content via at least one of their senses. The system must not present information in a way that requires a sense the user doesn't have access to.

Decisions in scope:

- **Text alternatives** for images, icons, video, audio.
- **Color and contrast** between text and background, between meaningful UI elements.
- **Color is never the only signal** for meaningful information.
- **Text scaling** without breaking the layout.
- **Reflow** on small screens or zoomed displays.
- **Captions and transcripts** for audio/video.

### Operable

Users must be able to *operate* the controls — including users who don't use a mouse or finger. Keyboards, switch devices, voice control, eye-tracking, and screen-reader gestures all need to work.

Decisions in scope:

- **Keyboard reachability** — every interactive element must be focusable and operable with `Tab`, `Enter`, `Space`, `Esc`, and arrow keys as appropriate.
- **Visible focus indicators** so the user can see where they are.
- **Skip links** so keyboard users don't tab through 50 nav items to reach content.
- **No keyboard traps** — focus must always be able to leave a region.
- **Motion sensitivity** — respect `prefers-reduced-motion`; provide pause/stop for any auto-moving content.
- **Touch target size** — at least 24×24 px (WCAG 2.5.8 AA); 44×44 strongly preferred.
- **No timing-out failures** without warning and extension.

### Understandable

Content and behavior should be predictable and recoverable. Error messages explain what went wrong and what to do. Labels describe what they label. Navigation is consistent across pages.

Decisions in scope:

- **Language** declared (`<html lang="en">`) so screen readers pronounce correctly.
- **Predictable behavior** — components don't change context unexpectedly (e.g., selecting a `<select>` shouldn't auto-submit a form without warning).
- **Error identification** — when an input is invalid, explain why in text, near the field, with `aria-describedby`.
- **Labels and instructions** — every input has a label; complex inputs have clear instructions.
- **Consistent navigation** — same nav in the same place across pages.

### Robust

The markup should work with current and future assistive technologies. Use semantic HTML where possible; use ARIA correctly when you need to extend semantics; never invent UI primitives that strip the accessibility from the underlying elements.

Decisions in scope:

- **Semantic HTML first** — `<button>`, `<a>`, `<nav>`, `<main>`, `<form>`, `<label>`. Use them for what they're for.
- **ARIA second, only when needed** — `aria-label`, `aria-labelledby`, `aria-describedby`, `role`, `aria-expanded`, `aria-current`. Wrong ARIA is often worse than no ARIA.
- **Status messages** — use `aria-live="polite"` (or `assertive`) for dynamic content that screen readers should announce (toasts, validation, search results).

## A practical accessibility checklist (for any design)

Run through this for every screen:

```
PERCEIVABLE
  [ ] Every image has alt text (or alt="" if decorative).
  [ ] Every icon-only button has aria-label.
  [ ] Color contrast ≥ 4.5:1 for body text, ≥ 3:1 for large/UI elements.
  [ ] Color is never the only signal for status, required fields, or meaning.
  [ ] Layout survives 200% browser zoom without horizontal scroll.
  [ ] Page has a single <h1>; heading levels are nested (h1 → h2 → h3), not skipped.

OPERABLE
  [ ] Every interactive element is keyboard-reachable via Tab.
  [ ] Visible focus ring on every focusable element (don't outline:none without a replacement).
  [ ] Esc closes any open overlay (Dialog, Sheet, Popover, Combobox).
  [ ] Focus is trapped inside open modals; focus returns to the trigger when closed.
  [ ] Skip-to-main link present, visible on focus.
  [ ] Touch targets ≥ 44×44 (or ≥ 24×24 with adequate spacing).
  [ ] prefers-reduced-motion is respected (no critical motion).

UNDERSTANDABLE
  [ ] Every input has a programmatically associated <label> (or aria-label / aria-labelledby).
  [ ] Errors are inline, named, and offer a fix.
  [ ] Form behavior doesn't change context unexpectedly on input change.
  [ ] Required fields are marked with both a visual indicator and aria-required.
  [ ] <html lang> is set.

ROBUST
  [ ] Use <button>, <a>, <input>, etc. for what they're for.
  [ ] If you need a custom interactive element, give it the right role, tabindex, and keyboard handlers.
  [ ] Live regions (aria-live) used for dynamic announcements (toast, validation, search).
  [ ] Screen-reader test with NVDA / VoiceOver / TalkBack on critical flows.
```

## Worked examples

### Example 1: an icon-only "search" button

**Anti-pattern:**

```html
<div onclick="search()" style="cursor: pointer;">
  <SearchIcon />
</div>
```

Not focusable, no role, no label, not a button. Screen readers say nothing useful; keyboard users can't reach it.

**Right:**

```html
<button onclick="search()" aria-label="Search">
  <SearchIcon aria-hidden="true" />
</button>
```

Native `<button>` (focusable, keyboard-operable, has button role). `aria-label` provides the accessible name. The icon is `aria-hidden` because the label already describes the action.

### Example 2: an inline form error

**Anti-pattern:**

```html
<input type="email" />
<!-- after submit -->
<p style="color: red;">Invalid</p>
```

The error isn't programmatically associated with the input. Screen readers announce the input without the error; sighted users with low vision may not see "Invalid" if it's small or low-contrast.

**Right:**

```html
<div class="field">
  <label for="email">Email</label>
  <input
    id="email"
    type="email"
    aria-invalid="true"
    aria-describedby="email-error"
  />
  <p id="email-error" class="field-error">
    Please enter a valid email address (e.g., name@example.com).
  </p>
</div>
```

`aria-invalid` flags the input as in error; `aria-describedby` ties the message to the input so screen readers announce both together. The message text is specific and offers a fix.

### Example 3: a dialog (modal)

**Anti-pattern:**

```html
<div class="modal">
  <h2>Confirm</h2>
  <button>OK</button>
</div>
```

No role, no labelling, no focus management. Keyboard users can tab out into background content; screen readers don't know it's a dialog.

**Right:**

```html
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-description"
>
  <h2 id="dialog-title">Discard changes?</h2>
  <p id="dialog-description">Your unsaved edits will be lost.</p>
  <button>Discard</button>
  <button>Cancel</button>
</div>
```

Plus JavaScript that:

- Moves focus into the dialog when it opens (typically the first focusable element, or a "primary" focus target).
- Traps focus inside while open (Tab cycles through the dialog's focusable elements only).
- Restores focus to the triggering element when closed.
- Closes on `Esc`.

Most accessible UI libraries (Radix UI, React Aria, headless component sets, shadcn) handle this automatically. If you build modals from scratch, you must do all of it yourself — this is why the strong recommendation is *don't*.

### Example 4: respecting reduced motion

```css
.toast { transition: transform 200ms ease-out; }

@media (prefers-reduced-motion: reduce) {
  .toast { transition: none; }
}
```

Or, more globally:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Users with vestibular disorders, migraine triggers, or motion sensitivity have already told the OS they don't want motion. Honor it.

### Example 5: a status badge that doesn't rely on color alone

**Anti-pattern:**

```html
<span style="background: red; padding: 2px 6px;"></span>
<span style="background: green; padding: 2px 6px;"></span>
```

Color is the only signal. Useless to color-blind users and to anyone in a screenshot or print.

**Right:**

```html
<span class="badge badge-destructive">
  <AlertIcon aria-hidden="true" /> Overdue
</span>
<span class="badge badge-success">
  <CheckIcon aria-hidden="true" /> Paid
</span>
```

Color, icon, and text together. Each user reads the channel that works for them.

## Anti-patterns

- **Outline-none on focus.** The most common accessibility crime. `:focus { outline: none; }` removes the only visual indicator keyboard users have. If you must restyle the focus ring, *replace* it with a custom one (`:focus-visible { outline: 2px solid var(--ring); outline-offset: 2px; }`), don't remove it.
- **Custom-built primitives that strip semantics.** A `<div onclick>` that "looks like a button" but isn't one. Use `<button>`. If you absolutely must use a div, add `role="button"`, `tabindex="0"`, and keyboard handlers — and you'll have rebuilt 80% of what `<button>` already does.
- **ARIA misuse.** `role="button"` on something that's already a `<button>`. `aria-label` on a `<label>` element. Conflicting `aria-labelledby`. Wrong ARIA is worse than no ARIA — it can mislead screen readers actively.
- **Color-only required indicators.** Red asterisk with no text "required" or `aria-required`. Color-blind users perceive nothing.
- **Mouse-only interactions.** Drag-and-drop with no keyboard alternative. Hover-revealed menus with no focus equivalent. Right-click menus with no Shift+F10 access.
- **The "we'll add accessibility later" plan.** Adding accessibility to a finished product is at best painful and at worst impossible. The right time is the first day of the project.
- **Treating accessibility as a checklist instead of a property.** A WCAG-compliant page can still be confusing, slow, or hostile. Compliance is a floor, not the goal.

## Heuristics and tools

1. **Keyboard-only test.** Unplug your mouse. Navigate the entire flow. Anything you can't reach, anything you can't operate, anything where focus disappears is a bug.
2. **Screen-reader test.** Use VoiceOver (macOS, iOS), NVDA (Windows), or TalkBack (Android) to walk a critical flow. Listen for: missing labels, announced as "blank" / "unlabeled," redundant announcements, important state not announced.
3. **Contrast checker.** Browser DevTools, the WebAIM Contrast Checker, or Stark plugin. Body ≥ 4.5:1, large/UI ≥ 3:1.
4. **Zoom to 200%.** Test the layout. Reflow on mobile-width breakpoints; no horizontal scroll for body content.
5. **Color-blind simulators.** Chrome DevTools → Rendering → Emulate vision deficiencies. Or the Sim Daltonism / Color Oracle apps. Status systems that lean on red/green collapse here.
6. **axe DevTools / WAVE / Lighthouse.** Automated audits catch ~30% of accessibility issues — useful as a floor, not a ceiling. Manual testing finds the rest.

## Trade-offs and warnings

- **Accessibility is not a substitute for usability.** A page can pass every WCAG criterion and still be confusing, slow, or hostile. Compliance is necessary; not sufficient.
- **Aria-rich is not always better.** Excessive `aria-*` attributes can over-narrate the UI to screen reader users. Use the minimum needed; rely on semantic HTML when possible.
- **Don't outsource accessibility to a single team.** Designers, engineers, content writers, QA — everyone owns part of it. A central "accessibility champion" can advise; a central "accessibility team" can review; but accountability has to be distributed.
- **Test with real users.** Disabled users have lived experience that no checklist captures. Periodic testing with disabled participants — including diverse impairments — is the only way to find the issues automated tools miss.

## Related principles

- **`color`** (perception) — color decisions are accessibility decisions; build for both.
- **`legibility`** and **`readability`** (perception) — typography choices that aid screen-reading also aid sighted users with low vision and cognitive impairments.
- **`fitts-law`** (interaction) — target size for motor accessibility.
- **`affordance`** (interaction) — affordance + ARIA = accessible affordance.
- **`feedback-loop`** (interaction) — feedback loops must be perceivable in any modality.
- **`error`** and **`forgiveness`** (interaction) — accessible error recovery means errors are *announceable* and *recoverable* by all users.

## Sub-aspect skills

- **`accessibility-perceivable`** — alt text, color/contrast, captions, text scaling.
- **`accessibility-operable`** — keyboard, focus management, motion, target size.
- **`accessibility-understandable`** — labels, error copy, predictable behavior.
- **`accessibility-robust`** — semantic HTML, ARIA, screen-reader compatibility.

## Final note

Accessibility, more than any other principle in this plugin set, is one where doing it well is invisible and doing it badly is sometimes invisible too — until a real user encounters it and quietly leaves. The job of the accessibility-aware designer is to test the things you can't see *yourself* failing on, and to build the structural habits that make accessibility the default rather than the exception. The investment is repaid every day, by users you may never meet.
