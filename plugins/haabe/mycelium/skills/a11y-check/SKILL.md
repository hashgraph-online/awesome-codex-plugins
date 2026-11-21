---
name: a11y-check
description: "Accessibility audit, scoped to the surfaces a product actually has. Detects web / rendered_markdown / terminal / native_app / video_audio / document / headless, then applies only the criteria that bind. WCAG 2.1 AA in full for web; not at all for headless."
metadata:
  instruction_budget: "26"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Accessibility Audit

Evaluate user-facing work against the criteria that BIND TO ITS SURFACES. Accessibility is a design
constraint, not a polish step (Downe Principle 11) — and an instrument aimed at a surface the product
does not have measures nothing while looking like a failure.

## STEP 1 — SURFACE GATE. Run this BEFORE the checklist, every time.

**The checklist below is written for web pages. Most products are not web pages.** Detect which
user-facing surfaces this product actually has, from the repository, and evaluate ONLY the criteria
that bind to them. Profiles and detection hints: `engine/canvas-guidance.yml#surfaces` —
`web` · `rendered_markdown` · `terminal` · `native_app` · `video_audio` · `document` · `headless`.
A product commonly has several. State which you found and how, in the output.

**THE RULE THAT DECIDES EVERY RATING:**

| situation | rating |
|---|---|
| the surface is ABSENT | **`n/a`** — and say which surface is missing |
| the surface is PRESENT and you measured it | `pass` / `partial` / `fail` on the evidence |
| the surface is PRESENT and you did NOT measure it | `not-assessed` — a real gap, it could have been measured |

**MARKING A CRITERION `fail` BECAUSE ITS SURFACE DOES NOT EXIST IS A CATEGORY ERROR.** It
manufactures a defect out of a product's shape, and a done-bar built on it fails for a reason no
work can fix.

**MEASURED, WHICH IS WHY THIS SECTION EXISTS.** On 2026-09-03 this skill's checklist was applied to
Mycelium — a terminal product with markdown docs — and Downe principle 11 was rated **fail**, with
the entry stating plainly: *"NOT TESTED, which is this principle's own fail criterion... WCAG 2.1 AA
is largely the wrong instrument for a terminal product."* **A delivery bar failed on an instrument
that could not bind.** Re-run 2026-09-04 under the surface gate: every applicable criterion passed,
and the rest were `n/a` by absence of surface rather than unmeasured.

**THREE CONSTRAINTS, OR THIS GATE BECOMES A WAIVER MACHINE.** Declaring a surface costs work;
declaring its absence costs a word, and accessibility has a long history of being waived on exactly
such grounds.
1. **Detect from artifacts and RECORD THE EVIDENCE** — say what you looked for and where. An `n/a`
   whose basis is "the agent decided" is not a finding and cannot be falsified later.
2. **`n/a` must never read as `pass` in a total.** "6 pass / 3 n/a" is honest; "9 of 15 clear" is
   the thing this rule exists to stop.
3. **FLOOR: every shipped product has at least one human surface — its docs, at minimum. A
   fully-`n/a` accessibility result is a DETECTOR BUG, not a clean bill.** Treat that run as broken.

**AND SURFACES SCOPE THE SUB-CHECKS, NEVER THE PRINCIPLE.** Downe P11 "Be usable by everyone" is
broader than perceptual access: it covers cost, language, literacy, required prior knowledge and
availability. **A terminal product may be `n/a` on keyboard navigation and still FAIL P11 on
jargon that gates a newcomer.** Bind WCAG's sub-checks to surfaces; never hand the principle itself
an `n/a`.

**HEADLESS IS THE SHARP CASE.** An API or library has no human surface, so WCAG does not bind at
all. What binds instead — error-message clarity, documentation quality — lives under other Downe
principles. Do not rate a headless product on interface criteria.

## STEP 2 — WCAG 2.1 AA Checklist by Principle

**Applies in full to `web`. Partially to `rendered_markdown`, `native_app`, `document`. Barely to `terminal`. Not at all to `headless`.**

### 1. Perceivable
- [ ] All images have meaningful alt text (or alt="" for decorative)
- [ ] Video has captions; audio has transcripts
- [ ] Color is never the sole indicator of meaning
- [ ] Color contrast: 4.5:1 normal text, 3:1 large text
- [ ] Content is readable at 200% zoom without horizontal scroll
- [ ] Text spacing can be adjusted without loss of content

### 2. Operable
- [ ] All interactive elements reachable via keyboard (Tab/Shift+Tab)
- [ ] Visible focus indicators on all focusable elements
- [ ] No keyboard traps (can always Tab away)
- [ ] Skip navigation link for repetitive content
- [ ] Page titles are descriptive and unique
- [ ] Focus order matches visual order
- [ ] Touch targets are at least 44x44 CSS pixels

### 3. Understandable
- [ ] Language of page is declared (lang attribute)
- [ ] Form inputs have associated labels
- [ ] Error messages identify the field and describe the fix
- [ ] Instructions don't rely solely on sensory characteristics
- [ ] Navigation is consistent across pages

### 4. Robust
- [ ] Valid HTML (no duplicate IDs, proper nesting)
- [ ] ARIA used correctly (roles, states, properties)
- [ ] Custom components expose name, role, value to assistive tech
- [ ] Status messages use aria-live regions

## Automated Testing Tools (by stack)

| Stack | Tool | Command |
|-------|------|---------|
| React/Web | axe-core | `npx axe <url>` or axe-core in tests |
| Any web | Lighthouse | `npx lighthouse <url> --only-categories=accessibility` |
| Any web | pa11y | `npx pa11y <url>` |
| CI/CD | axe-linter | Add to CI pipeline |

## Common Violations and Fixes

| Violation | Fix |
|-----------|-----|
| Missing alt text | Add descriptive alt or alt="" for decorative |
| Low color contrast | Increase contrast ratio to 4.5:1 minimum |
| Missing form labels | Add `<label for="id">` or aria-label |
| No focus indicator | Add `:focus-visible` styles, never `outline: none` |
| Non-semantic buttons | Use `<button>` not `<div onclick>` |
| Missing heading hierarchy | Use h1-h6 in order, don't skip levels |
| Auto-playing media | Add pause/stop controls, respect prefers-reduced-motion |

## When to Run
- During development: after every UI component
- Before PR: full automated scan
- Before release: manual screen reader test of critical journeys
- After design changes: re-audit affected components

## Sensitive Context Note
For products handling sensitive user contexts (health, finance, domestic violence, government services), also review trauma-informed design principles in `${CLAUDE_PLUGIN_ROOT}/domains/quality/CLAUDE.md`. Source: Hussain (Chayn), built on SAMHSA's 6 Principles (2014).

## Neurodiversity Considerations
For information-dense or learning-oriented products, supplement WCAG with the Neurodiversity Design System (neurodiversity.design, Soward). Its 8 principle categories with neurotype-to-UI-element matrix address cognitive accessibility needs that WCAG does not fully cover (e.g., font shapes for dyslexia, number formatting for dyscalculia, animation controls for ADHD).
