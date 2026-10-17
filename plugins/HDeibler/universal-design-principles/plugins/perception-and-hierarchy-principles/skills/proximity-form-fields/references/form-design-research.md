# Form-design research and patterns

A reference complementing `proximity-form-fields` SKILL.md with research findings and patterns from the broader form-design literature.

## Empirical findings

The most-cited form-design research:

- **Caroline Jarrett & Gerry Gaffney**, *Forms that Work* (2008). The reference work for form usability. Key finding: label-input *association* (proximity, alignment, semantic clarity) accounts for the majority of form usability differences across designs.
- **Luke Wroblewski**, *Web Form Design: Filling in the Blanks* (2008). Compiles empirical studies on label position, alignment, error placement, and other form decisions.
- **NN/g studies on form completion** (multiple) — consistently show that top-aligned labels outperform left-aligned for completion speed when the form is single-column; left-aligned labels outperform when fields are extensively scanned (e.g., a profile review).

Key empirical results worth remembering:

- **Top labels are 50% faster to complete on average** than left-aligned labels (Penzo, 2006), because the eye moves vertically without scanning sideways.
- **Right-aligned labels** (label flush right against input flush left) are tied for speed with top-aligned but read as less friendly.
- **Inline labels (placeholder-only)** test 30%+ slower than visible labels and have highest error rates, especially after the user starts typing and the placeholder vanishes.
- **Required-field markings as `*` are widely understood** but should be paired with text for accessibility ("required").

## Form-layout patterns by use case

### Sign-up / sign-in (fast completion priority)

Single column, top labels, generous gaps between fields, primary CTA at bottom-right or full-width.

### Long settings (scanning priority)

Two-column with right-aligned labels — the eye scans the left column for the setting it wants, then values are aligned in a second column for quick review.

### Multi-step wizard (progress priority)

Single column per step. Stepper at top showing progress. Each step is short (≤ 5 fields). Primary CTA progresses; secondary CTA returns.

### Edit-in-place (proximity to context priority)

Inline editing where each field is bound to the data it represents (no labels needed; the data itself is the label). Hover or focus reveals editing affordance.

### Conversational form (one-question-at-a-time priority)

Each field on its own screen with a question and an input. Reduces Hick's Law pressure but multiplies clicks.

## Cross-domain examples

### Government forms

Government forms (tax returns, immigration, benefits) are the bottom of the form-design barrel and the highest-stakes. They violate proximity routinely (labels and inputs separated by half-pages of instructions), and the cost is measurable in failed applications and call-center burden.

A few governments have invested in form modernization (UK GOV.UK, US 18F) and seen large completion-rate gains from applying basic proximity, single-column layout, and progressive disclosure.

### Paper forms

Paper forms have proximity built in by physical reality — there's a line for "Name" right next to the empty space to write it. Translating these to digital and *losing* the proximity is the failure mode.

### Survey research

Academic survey design (Couper, Tourangeau) studies how question grouping affects responses. Questions grouped together by topic show more correlated answers (acquiescence bias); spreading them out reduces that bias. Proximity changes the *answers*, not just the speed.

## Edge cases

### Mobile two-column layouts

Two-column layouts collapse on mobile. The same form needs to read sensibly at 375px wide and 1280px wide. Practical pattern:

- Default to single column.
- Use two columns only for paired fields where the pairing is genuinely tight (first/last name, city/state).
- At mobile breakpoint, collapse paired columns to single column.

### Conditional fields

Fields that appear/disappear based on prior input (e.g., "Are you a US citizen?" → "Visa type") need proximity that *remains* clear when the conditional fields appear. Insert them in place; don't reflow the whole form.

### Multi-language forms

Label length varies wildly across languages (German labels are often 2× English; Chinese can be 0.5×). Form layouts that work in English break in German. Test at multiple languages.

## Resources

- **Jarrett, C. & Gaffney, G.** (2008). *Forms that Work*.
- **Wroblewski, L.** (2008). *Web Form Design: Filling in the Blanks*.
- **GOV.UK Design System** (gov.uk/design-system) — form patterns for high-stakes government use.
- **WCAG 1.3.1, 3.3.1, 3.3.2** — relevant success criteria for form accessibility.

## Closing

Form design is one of the most-studied corners of UX, and the findings consistently elevate proximity above other variables. If a form is failing, the first thing to audit is the spacing and pairing — long before the wording or the visual style.
