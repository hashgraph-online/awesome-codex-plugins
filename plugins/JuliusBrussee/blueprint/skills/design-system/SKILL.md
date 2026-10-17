---
name: design-system
description: |
  How to write and maintain a DESIGN.md in the 9-section Google Stitch format.
  Covers the 9-section structure, design token conventions, quality standards,
  integration with kits and build tasks, revision patterns, and collection import.
  Trigger phrases: "design system", "DESIGN.md", "visual design spec",
  "design tokens", "create design system", "import design system",
  "visual identity", "UI spec", "design language"
---

# Design System: DESIGN.md for AI Agents

## Core Principle: DESIGN.md Describes WHAT It Looks Like, Not HOW to Build It

DESIGN.md is the visual equivalent of kits. It defines the project's visual language — colors, typography, spacing, components, responsive behavior — in a format AI agents can read and apply consistently. It is a **parallel constraint layer** that all Hunt phases consult.

| Document | Defines | Audience |
|----------|---------|----------|
| CLAUDE.md | How to build the project | Coding agents |
| Kits | What must be true (behavior) | All agents |
| **DESIGN.md** | **What it looks like (visual)** | **UI-building agents** |
| Plans | How to build it (tasks) | Builder agents |

### Why a Dedicated Design System Document?

Without DESIGN.md, visual decisions scatter across kits, plans, and code:
- Colors get hardcoded differently per component
- Typography choices vary between agents and sessions
- Spacing becomes inconsistent across the UI
- New components reinvent patterns that already exist

DESIGN.md centralizes these decisions. Every agent reads it before writing UI code.

---

## The 9-Section Stitch Format

DESIGN.md follows the [Google Stitch format](https://stitch.withgoogle.com/docs/design-md/overview/) — 9 sections that together define a complete visual language. Every DESIGN.md must contain all 9 sections.

### Section 1: Visual Theme & Atmosphere

The design philosophy, mood, and overall aesthetic. Use evocative, specific language — not generic terms like "clean and modern."

```markdown
## 1. Visual Theme & Atmosphere

This is a warm editorial experience built on natural materials. Think: a well-curated
bookshop with soft overhead lighting and carefully chosen display shelves. The density
is low — generous whitespace signals confidence and clarity. Every element earns its
place; nothing decorative exists without functional purpose.

**Key attributes:** Warm, unhurried, editorial, confident
**Density:** Low — generous whitespace, single-column focus
**Personality:** Thoughtful librarian, not flashy storefront
```

**What good looks like:** A new designer reading this section could sketch a rough layout without seeing any other section.

**Anti-pattern:** "Clean, modern, and professional" — this describes nothing specific.

### Section 2: Color Palette & Roles

Every color needs three things: a semantic name, a hex value, and a functional role.

```markdown
## 2. Color Palette & Roles

### Primary
| Name | Hex | Role |
|------|-----|------|
| Terracotta Brand | #c96442 | Primary CTA, active states, brand anchors |
| Terracotta Hover | #b85838 | Hover/pressed state for primary actions |

### Neutral
| Name | Hex | Role |
|------|-----|------|
| Near Black | #141413 | Primary text, headings |
| Olive Gray | #5e5d59 | Secondary text, captions |
| Parchment | #f5f4ed | Page background, default canvas |
| Ivory White | #ffffff | Card surfaces, overlays |

### Semantic
| Name | Hex | Role |
|------|-----|------|
| Success Green | #2d7d46 | Confirmation, success states |
| Warning Amber | #c27217 | Warnings, attention needed |
| Error Red | #c24132 | Errors, destructive actions |
| Info Blue | #3b6fb5 | Informational states, links |

### Dark Mode (if applicable)
| Light Name | Dark Equivalent | Hex |
|------------|----------------|-----|
| Parchment | Deep Charcoal | #1a1a1a |
| Near Black | Off White | #e8e8e8 |
```

**Rules:**
- Every hex value must be verified against the actual design or live site
- Every color must have a clear functional role — no orphan colors
- Name colors semantically (by role), not by hue ("Primary CTA" not "Orange")
- If dark mode exists, map every light color to its dark equivalent

### Section 3: Typography Rules

Complete type hierarchy with specific values — no "roughly 16px" or "medium weight."

```markdown
## 3. Typography Rules

### Font Stack
- **Display/Heading:** "Anthropic Serif", Georgia, "Times New Roman", serif
- **Body:** "Anthropic Sans", -apple-system, BlinkMacSystemFont, sans-serif
- **Code:** "Anthropic Mono", "SF Mono", "Fira Code", monospace

### Type Scale
| Level | Size | Weight | Line Height | Letter Spacing | Font |
|-------|------|--------|-------------|----------------|------|
| H1 | 48px / 3rem | 500 | 1.10 | -0.02em | Serif |
| H2 | 36px / 2.25rem | 500 | 1.15 | -0.01em | Serif |
| H3 | 24px / 1.5rem | 500 | 1.25 | 0 | Serif |
| H4 | 20px / 1.25rem | 600 | 1.30 | 0 | Sans |
| Body | 16px / 1rem | 400 | 1.60 | 0 | Sans |
| Small | 14px / 0.875rem | 400 | 1.50 | 0.01em | Sans |
| Caption | 12px / 0.75rem | 500 | 1.40 | 0.02em | Sans |

### Principles
- Headings use serif for warmth and authority
- Body text uses sans-serif for readability at small sizes
- Maximum line length: 65ch for body text
- Minimum font size: 14px (never go below)
```

**Rules:**
- Every level in the scale must have all 5 values (size, weight, line-height, letter-spacing, font)
- Use rem alongside px for accessibility
- Include font stack fallbacks

### Section 4: Component Stylings

Concrete styling for common components including interaction states.

```markdown
## 4. Component Stylings

### Buttons
**Primary:**
- Background: Terracotta Brand (#c96442)
- Text: Ivory White (#ffffff), 16px Sans, weight 500
- Padding: 12px 24px
- Border radius: 8px
- Hover: Terracotta Hover (#b85838), translateY(-1px), shadow-sm
- Active: translateY(0), shadow-none
- Disabled: opacity 0.5, cursor not-allowed
- Transition: all 150ms ease-out

**Secondary:**
- Background: transparent
- Border: 1px solid Olive Gray (#5e5d59)
- Text: Near Black (#141413)
- Hover: background Parchment (#f5f4ed)

### Cards
- Background: Ivory White (#ffffff)
- Border: 1px solid rgba(0,0,0,0.06)
- Border radius: 12px
- Padding: 24px
- Shadow: 0 1px 3px rgba(0,0,0,0.04)
- Hover: shadow 0 4px 12px rgba(0,0,0,0.08), translateY(-2px)

### Inputs
- Border: 1px solid #d0d0d0
- Border radius: 8px
- Padding: 10px 14px
- Focus: border Terracotta Brand, ring 2px rgba(201,100,66,0.2)
- Error: border Error Red, ring 2px rgba(194,65,50,0.2)

### Navigation
...
```

**Rules:**
- Include hover, focus, active, and disabled states
- Specify transition durations and easing
- Include touch-target minimum sizes (44x44px)

### Section 5: Layout Principles

Spacing system, grid, containers, and whitespace philosophy.

```markdown
## 5. Layout Principles

### Spacing Scale (base: 4px)
| Token | Value | Usage |
|-------|-------|-------|
| space-1 | 4px | Tight gaps, icon margins |
| space-2 | 8px | Related element spacing |
| space-3 | 12px | Component internal padding |
| space-4 | 16px | Standard gap between elements |
| space-6 | 24px | Section padding, card padding |
| space-8 | 32px | Between major sections |
| space-12 | 48px | Page-level vertical rhythm |
| space-16 | 64px | Hero/banner spacing |

### Grid
- Max content width: 1200px
- Column count: 12
- Gutter: 24px (space-6)
- Margin: 16px mobile, 24px tablet, auto desktop

### Border Radius Scale
| Token | Value | Usage |
|-------|-------|-------|
| radius-sm | 4px | Badges, tags |
| radius-md | 8px | Buttons, inputs |
| radius-lg | 12px | Cards, panels |
| radius-xl | 16px | Modals, dialogs |
| radius-full | 9999px | Avatars, pills |
```

### Section 6: Depth & Elevation

Shadow system and visual layering.

```markdown
## 6. Depth & Elevation

### Shadow Scale
| Level | Value | Usage |
|-------|-------|-------|
| shadow-none | none | Flat elements |
| shadow-sm | 0 1px 2px rgba(0,0,0,0.04) | Subtle lift (cards at rest) |
| shadow-md | 0 4px 12px rgba(0,0,0,0.08) | Hover states, active cards |
| shadow-lg | 0 8px 24px rgba(0,0,0,0.12) | Dropdowns, popovers |
| shadow-xl | 0 16px 48px rgba(0,0,0,0.16) | Modals, dialogs |

### Surface Hierarchy
1. **Base** — page background (Parchment)
2. **Raised** — cards, panels (Ivory White + shadow-sm)
3. **Floating** — dropdowns, tooltips (Ivory White + shadow-lg)
4. **Overlay** — modals, dialogs (Ivory White + shadow-xl + scrim)
```

### Section 7: Do's and Don'ts

Concrete examples with code — not just prose rules.

```markdown
## 7. Do's and Don'ts

### DO: Use semantic color names
```css
/* Good */
.button-primary { background: var(--color-terracotta-brand); }
```

### DON'T: Hardcode color values
```css
/* Bad */
.button-primary { background: #c96442; }
```

### DO: Follow the spacing scale
```css
/* Good — uses scale */
.card { padding: var(--space-6); margin-bottom: var(--space-8); }
```

### DON'T: Use arbitrary spacing
```css
/* Bad — 19px is not on the scale */
.card { padding: 19px; margin-bottom: 37px; }
```

### DO: Include all interaction states
### DON'T: Skip hover/focus states on interactive elements
### DO: Use the type scale for all text
### DON'T: Introduce new font sizes not in the scale
```

### Section 8: Responsive Behavior

Breakpoints, mobile patterns, and adaptation rules.

```markdown
## 8. Responsive Behavior

### Breakpoints
| Name | Width | Target |
|------|-------|--------|
| mobile | < 640px | Phones |
| tablet | 640–1024px | Tablets, small laptops |
| desktop | > 1024px | Laptops, monitors |

### Touch Targets
- Minimum interactive element size: 44x44px
- Minimum spacing between targets: 8px

### Mobile Adaptations
- Navigation collapses to hamburger menu below 640px
- Cards stack single-column below 640px
- Font sizes: H1 reduces to 32px on mobile, H2 to 28px
- Side padding: 16px on mobile, 24px tablet, auto-center desktop

### Behavior Patterns
- Horizontal scrolling: never (use stacking or truncation)
- Images: responsive with srcset, max-width: 100%
- Tables: horizontal scroll wrapper below tablet breakpoint
```

### Section 9: Agent Prompt Guide

How AI agents should use this document when generating UI.

```markdown
## 9. Agent Prompt Guide

### Quick Reference
- Primary CTA color: Terracotta Brand (#c96442)
- Background: Parchment (#f5f4ed)
- Heading font: Serif, weight 500
- Body font: Sans, weight 400
- Standard spacing: 24px (space-6)
- Card radius: 12px (radius-lg)

### How to Use This Document
1. Before writing any UI code, read the full DESIGN.md
2. Reference specific section names when implementing: "Following Section 4: Buttons"
3. Use design token names in CSS (var(--color-terracotta-brand)), not raw hex values
4. Check Section 7 (Do's and Don'ts) before submitting
5. If a component is not covered, create it following existing patterns and flag for DESIGN.md update

### Example Component Prompt
"Create a hero section on Parchment (#f5f4ed) with a headline at H1 scale
(48px Serif weight 500, line-height 1.10). Use Near Black (#141413) text.
Add a subtitle in Olive Gray (#5e5d59) at Body scale (16px Sans, line-height 1.60).
Place a Terracotta Brand (#c96442) primary button with Ivory text, radius-md (8px)."

### Iteration Guide
- Change one component at a time
- Reference specific color names and token values
- Describe the component's state (default, hover, active, disabled)
- Specify responsive behavior for the component
```

---

## Design Token Conventions

Tokens are the bridge between DESIGN.md and code. Consistent naming ensures agents can translate design specs into CSS/Tailwind variables.

### Naming Pattern

```
--{category}-{name}[-{modifier}]
```

| Category | Examples |
|----------|---------|
| `color-` | `--color-terracotta-brand`, `--color-near-black`, `--color-success-green` |
| `space-` | `--space-1`, `--space-4`, `--space-8` |
| `text-` | `--text-h1`, `--text-body`, `--text-caption` |
| `radius-` | `--radius-sm`, `--radius-md`, `--radius-lg` |
| `shadow-` | `--shadow-sm`, `--shadow-md`, `--shadow-lg` |
| `font-` | `--font-serif`, `--font-sans`, `--font-mono` |

### Mapping to CSS Custom Properties

DESIGN.md tokens map directly to CSS custom properties:
```css
:root {
  --color-terracotta-brand: #c96442;
  --space-6: 24px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
}
```

### Mapping to Tailwind

When using Tailwind, DESIGN.md tokens map to `tailwind.config.js` extensions. The builder agent should configure this once and reference throughout.

---

## Integration with Kits

When DESIGN.md exists and kits contain UI requirements, acceptance criteria should reference design tokens by section and name. This creates a traceable chain:

```
DESIGN.md → Cavekit acceptance criterion → Plan task → Implementation
```

### How to Reference

| In Cavekit Acceptance Criteria | Design Reference |
|----------------------------------|-----------------|
| "CTA button uses primary brand styling" | DESIGN.md Section 4: Buttons, primary variant |
| "Headings follow the type hierarchy" | DESIGN.md Section 3: Type Scale |
| "Cards have subtle resting elevation" | DESIGN.md Section 6: shadow-sm |
| "Layout uses the standard grid" | DESIGN.md Section 5: Grid |
| "Colors adapt for dark mode" | DESIGN.md Section 2: Dark Mode mapping |

**Do NOT duplicate DESIGN.md content into kits.** Reference by section/token name only. If a color changes in DESIGN.md, kits should not need updating.

### When No Design Reference Exists

If a cavekit needs a visual pattern not in DESIGN.md, the acceptance criterion should note this:
```markdown
- [ ] Component uses a card-like container [DESIGN.md: pattern not yet defined — flag for design update]
```

This tells the inspect phase to check whether DESIGN.md needs a new pattern.

---

## Integration with Plans (Architect Phase)

When the architect generates task descriptions for UI work, each task should include:

```markdown
**Design Reference:** DESIGN.md Section {N} — {section name}
```

This tells the task-builder which DESIGN.md sections to read before implementing.

---

## Integration with Build Phase

Task-builder agents follow this protocol for UI work:

1. **Before implementing:** Read DESIGN.md (or the specific sections referenced in the task)
2. **During implementation:** Use design tokens, not hardcoded values
3. **In commit messages:** Note which DESIGN.md sections were followed
4. **If a new pattern is needed:** Implement it following existing DESIGN.md conventions and flag for design update

---

## Revision Patterns

When visual fixes are made manually (outside the Hunt loop), `/ck:revise` traces them back to DESIGN.md:

### Visual Fix Classification

| Fix Type | DESIGN.md Action |
|----------|-----------------|
| Color change that should apply globally | Update DESIGN.md Section 2 with corrected value |
| New component pattern not in DESIGN.md | Add to DESIGN.md Section 4 |
| Spacing adjustment revealing wrong scale | Update DESIGN.md Section 5 scale |
| Typography fix | Update DESIGN.md Section 3 type scale |
| Responsive behavior change | Update DESIGN.md Section 8 |

### Revision Protocol

1. Identify the visual change in the diff
2. Check if DESIGN.md covers this pattern
3. If not covered: add the pattern to the appropriate section
4. If covered but wrong: update the token/value
5. Log the change to `context/designs/design-changelog.md`

---

## Collection Import

The [awesome-design-md](https://github.com/VoltAgent/awesome-design-md) repository contains 54+ curated design systems extracted from real products. These serve as starting points.

### Import Workflow

1. **Choose a template:** `vercel`, `claude`, `stripe`, `github`, `linear`, etc.
2. **Fetch the raw DESIGN.md** from the collection
3. **Present to the user** as a starting point — not a finished product
4. **Walk through each section** for customization (brand colors, typography, specific component needs)
5. **Write the customized version** to project root

### After Import

The imported DESIGN.md becomes the project's own. Future updates are made directly — the import is a seed, not a dependency.

---

## Quality Standards

### Completeness Checklist

- [ ] All 9 sections present and non-empty
- [ ] Every color has: semantic name + hex value + functional role
- [ ] Complete typography table (all 5 values per level)
- [ ] Component stylings include hover, focus, active, disabled states
- [ ] Spacing scale is defined with consistent base unit
- [ ] Shadow/elevation scale is defined
- [ ] Breakpoints have specific pixel values
- [ ] Agent Prompt Guide has quick reference and example prompts

### Specificity Requirements

Every value in DESIGN.md must be concrete and unambiguous:

| Too Vague | Specific Enough |
|-----------|----------------|
| "a warm blue" | `#3b6fb5` (Info Blue) |
| "medium spacing" | `24px` (space-6) |
| "slightly rounded" | `8px` (radius-md) |
| "subtle shadow" | `0 1px 2px rgba(0,0,0,0.04)` (shadow-sm) |
| "large heading" | `48px / 3rem, weight 500, line-height 1.10` |

### Consistency Rules

- Tokens used in Section 4 (Components) must exist in Sections 2, 3, 5, 6
- Dark mode mappings must cover every color used in components
- Responsive changes must reference defined breakpoints
- All spacing values must be multiples of the base unit

---

## Anti-Patterns

1. **Generic atmosphere** — "Clean, modern, professional" describes every SaaS app and none
2. **Missing interaction states** — A button without hover/focus is incomplete
3. **Orphan colors** — Colors defined in the palette but never used in components
4. **Arbitrary spacing** — Values that don't follow the spacing scale
5. **Missing dark mode** — If the app supports dark mode, every light color needs a mapping
6. **Hex-only references in components** — Use semantic names, not raw values
7. **No Agent Prompt Guide** — Section 9 is what makes DESIGN.md actionable for AI agents
8. **Duplicating DESIGN.md into kits** — Reference by section/token name only
