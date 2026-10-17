# Visual Critique

A dimensional critique instrument. Score a screen across seven dimensions, each rated **pass / minor issue / major issue**. Lead with the AI-slop verdict (from `avoid-ai-slop.md`). End with the highest-severity finding.

---

## How to Run a Visual Critique

1. **Form your own verdict first.** Look at the screen, name the primary feeling and the primary failure before opening this checklist. The checklist confirms or refutes — it doesn't generate your opinion.
2. **Rate each dimension** (pass / minor issue / major issue).
3. **Report shape:** AI-slop verdict → first impression → 2–3 things working (be specific) → 3–5 priority issues by severity, each with observation / problem / fix → provocative close question.
4. **Anchor discipline:** distinguish genuine design opinion ("the hierarchy collapses because X") from preference ("I'd use a different font"). State which is which.

---

## 1. Visual Hierarchy

**Entry point** — the first element that captures the eye. It must be the *most important* thing on screen.
- Is there a single dominant element, or does attention scatter across competing primaries?
- Does size, contrast, or position establish the entry point unambiguously?
- Does the entry point match the primary user goal for this screen?

**Eye flow** — the path a user's eye travels after landing.
- Does the layout follow F-pattern (left-aligned lists, tables) or Z-pattern (hero + CTA) for its context?
- Are there dead ends, visual loops, or confusing jumps in the flow?
- Does the flow lead naturally to the primary CTA?

**Weight distribution** — relative visual importance of each element.
- Size differentials at least 1.5× between hierarchy levels?
- Bold and heavy type used sparingly so it retains signal value?
- Background fill, stroke weight, and iconography adding to hierarchy or fighting it?

**Emphasis** — specific elements that demand extra attention.
- Exactly one primary emphasis zone per view?
- Color, contrast, or motion used with restraint — or overused to the point where they cancel out?
- Does the highest-emphasis element match actual user and stakeholder priority?

**Common failures:**
- Multiple competing primaries — nothing reads as most important.
- Hierarchy flattening — too similar in size, weight, or color across levels.
- False emphasis — decorative elements outweigh functional ones in visual weight.
- Buried CTA — the action is visually quieter than surrounding content.

---

## 2. Composition

**Balance** — distribution of visual weight across the layout.
- Symmetrically or asymmetrically balanced? Is the choice intentional?
- Heavy elements (dark fills, large images, dense text blocks) offset by lighter ones?
- Clear visual centre of gravity, or does the layout tip — top-heavy, bottom-heavy, left-leaning?

**Whitespace** — negative space as an active design element.
- Sufficient macro whitespace between major sections?
- Micro whitespace consistent (between labels, icons, and adjacent elements)?
- Whitespace guiding attention, or fragmenting the layout into disconnected islands?
- Areas over-compressed or padded inconsistently?

**Rhythm** — repetition, pattern, and visual cadence.
- Spacing intervals consistent and derived from a spacing scale?
- Repeated elements (cards, list items, form rows) maintaining uniform sizing and gaps?
- Visual variety without chaos; repetition without monotony?
- Section breaks and dividers creating a legible page cadence?

**Gestalt principles:**
- **Proximity:** Related elements close together; unrelated elements clearly separated.
- **Similarity:** Elements sharing a function share a visual treatment.
- **Figure/Ground:** Foreground content clearly distinct from the background.
- **Continuity:** Alignment and flow lines lead the eye smoothly through the composition.
- **Closure:** Incomplete shapes or groups still perceived correctly.

**Common failures:**
- Equal-weight two-column layout with no primary/secondary split.
- Inconsistent padding (some components 16px, others 20px with no system).
- Orphaned elements floating without proximity to their related group.
- Overcrowded sections adjacent to empty ones — visual cliffs.
- Competing dividers multiplying without adding structure.

---

## 3. Color

**Contrast:**
- Body text meets WCAG AA (4.5:1)? Large text (18px+ regular, 14px+ bold) meets 3:1?
- Interactive components (buttons, inputs, focus rings) meet 3:1 against adjacent surfaces?
- Placeholder text and disabled states failing contrast in ways that impede use?
- Flag every failing pair with its measured ratio and the minimum required.

**Palette coherence:**
- Limited to defined token values, or arbitrary colors present?
- Neutrals, primaries, and accents applied according to their intended roles?
- Adjacent or overlapping elements creating unintended visual noise or color vibration?
- Overall palette register (warm/cool/neutral) appropriate for the context?

**Semantic use:**
- Color used as the sole indicator of state (error, success, warning)? Must pair with icon or text label.
- Status colors (red=error, green=success, amber=warning) applied consistently across the screen?
- Interactive color (links, button fills) clearly distinct from non-interactive color?
- Decorative color being mistaken for actionable elements?

**Accessibility beyond contrast:**
- Common color vision deficiencies (deuteranopia, protanopia) — does the interface hold up?
- Windows High Contrast mode / forced-color environments considered?
- Decorative color interfering with content legibility?

**Common failures:**
- Link color failing 4.5:1 when underline is removed.
- Error states in red only, with no supporting icon or label.
- Placeholder text at 40% opacity failing contrast on light surfaces.
- One-off hex values outside the token system introduced over time.
- Interactive and non-interactive elements sharing the same color treatment.

---

## 4. Typography

**Scale usage:**
- Only defined scale steps in use (display, h1–h4, body-lg, body, body-sm, caption)?
- Each step used for its intended purpose — headings as headings, labels as labels?
- Intermediate or arbitrary sizes present (someone nudged a font-size 2px off-scale)?
- Sufficient contrast between hierarchy levels (≥1.25× ratio per step recommended)?

**Readability:**
- Body text ≥ 16px on desktop; ≥ 14px on mobile minimum.
- Line-height: 1.1–1.3 for headings; 1.4–1.6 for body.
- Line length (measure): 45–75 characters for body copy.
- Letter-spacing: not over-tracked or compressed to the point of friction.
- Text/background contrast: 4.5:1 for body, 3:1 for large text (WCAG AA).

**Consistency:**
- Semantically equivalent elements (all card titles, all form labels) using the same type style?
- Alignment choices consistent and intentional — not randomly mixed?
- Font weights consistently applied — not randomly varied across similar components?
- Orphaned styles — one-off type treatments not used elsewhere?

**Token compliance:**
- Font-family, font-size, font-weight, line-height, letter-spacing set via tokens?
- Hardcoded CSS values present that should reference a token?
- List every non-compliant value with its correct token name.

**Common failures:**
- Scale drift — nudging sizes 1–2px instead of moving to the next defined step.
- Line-height mismatches — display sizes with body line-height, or body with heading line-height.
- Centred headings above left-aligned body text without intentional justification.
- Over-use of bold — more than two active weight levels on a single screen dilutes contrast.

---

## 5. Affordance

**Clickability signals:**
- Buttons, links, and controls visually distinct from static content through color, shape, underline, or elevation?
- False affordances: elements that look interactive but aren't?
- Missing affordances: elements that are interactive but look static?
- Interactive area ≥ 44×44px on mobile?

**State visibility:**
- Default, hover, active, focus, disabled, and selected states visually distinct?
- Focus state visible and high-contrast — not just the suppressed browser default ring?
- Loading and skeleton states present where async content is expected?
- Disabled states communicated without relying on color alone?

**CTA clarity:**
- Single dominant CTA per view, or multiple actions competing at the same visual weight?
- Primary CTA: filled/solid style. Secondary: ghost or text. Never equal visual weight.
- CTA label specific and action-oriented ("Save changes" not "OK", "Create account" not "Submit")?
- CTA positioned where users expect it?

**Action discoverability:**
- Actions hidden behind hover states that mobile users cannot access?
- Contextual actions (edit, delete, share) visible or indicated — not completely hidden until hover?
- Empty states actionable — do they tell the user what to do next?
- Destructive actions visually distinguished from constructive ones?

**Common failures:**
- Ghost buttons in low-contrast contexts where the border becomes invisible.
- Focus rings suppressed with `outline: none` and no replacement provided.
- Multiple filled CTAs leaving users unsure which to press.
- Edit and delete actions hidden behind hover — inaccessible on touch devices.
- Empty states that explain nothing and offer no path forward.

---

## 6. Information Density

**Cognitive load:**
- How many distinct decisions or pieces of information must the user process for the primary task on this screen?
- Unrelated elements competing for attention simultaneously?
- Page serving multiple user goals when it should be focused on one?
- Elements present that don't serve the current user task (decoration, secondary metadata, noise)?

**Content priority:**
- Primary information above the fold?
- Supporting information (context, explanation, metadata) visually subordinate to primary content?
- Elements with equal visual weight that don't have equal user importance?
- Critical information buried in tooltips, collapsed sections, or low-contrast secondary text?

**Scanning pattern:**
- Content structure matches F-pattern (left-aligned lists, tables) or Z-pattern (hero + CTA) for its context?
- Labels left-aligned and consistent so users can scan vertically without reading every word?
- Numbers, dates, and status values aligned and formatted consistently in lists and tables?
- Content breaks into scannable chunks — short paragraphs, headers, bullets — not dense prose?

**Progressive disclosure:**
- All available information shown at once, or detail appropriately deferred?
- Expandable sections, tabs, and modals hiding genuinely secondary content (not primary actions)?
- Advanced options and edge-case content separated from the primary flow?
- Clear starting point, or ambiguous entry because too much is visible at once?

**Common failures:**
- Dashboards showing every available metric instead of the most actionable ones.
- Detail pages inlining all related objects instead of linking to them.
- Tables with 10+ columns where 3 columns do 90% of the user's work.
- Forms showing all fields at once when a multi-step flow would reduce perceived complexity.
- Content-heavy onboarding that front-loads explanation before the user has done anything.

---

## 7. Brand Consistency

Requires project reference files: `PRODUCT.md` (personality, aesthetic direction) and `DESIGN.md` (visual system, tokens). If either is absent, skip this dimension — do not invent brand rules from scratch.

**Mood alignment:**
- Visual language (imagery style, illustration, iconography, color feel) matches the brand personality keywords in `PRODUCT.md`?
- Any elements tonally off — a playful brand using cold, corporate styling?
- Overall emotional register of the screen matches what the product definition prescribes?

**Voice alignment:**
- Tone matching the voice guidelines (direct vs. conversational, formal vs. friendly)?
- Prescribed vocabulary rules followed — forbidden words avoided, required patterns used?
- CTAs, labels, error messages, and microcopy consistent with the voice guidelines?

**Token compliance:**
- Hardcoded hex values where a color token should apply?
- Spacing, radius, or shadow values deviating from the token definitions in `DESIGN.md`?
- Typography tokens applied correctly, or raw font-size/weight values in use?
- List every non-compliant value with its correct token equivalent.

**Common failures:**
- Hardcoded values drifting from tokens over time, component by component.
- Copy written without consulting voice guidelines, defaulting to generic UI language.
- Inconsistent radius or shadow values across components on the same screen.
- Imagery or illustration sourced outside the brand mood reference.

---

## Output Format

For each dimension, provide:
1. **Observation** — what you see (neutral, factual).
2. **Problem** — what is broken and why it matters to the user.
3. **Fix** — specific, actionable change (include ratio, token name, or exact value where applicable).

Rate each: `pass` / `minor issue` / `major issue`.

Report shape: AI-slop verdict → first impression → 2–3 things working → 3–5 priority issues (highest severity first) → provocative close question.
