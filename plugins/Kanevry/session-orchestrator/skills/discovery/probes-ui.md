> See probes-intro.md for confidence scoring reference.

## Category: `ui`

### Probe: accessibility-gaps

**Activation:** React/Vue/HTML files exist (`.tsx`, `.jsx`, `.vue`, `.html`).

**Detection Method:**

```bash
# Images without alt text
Grep pattern: <img(?![^>]*\balt\s*=)[^>]*>
  --glob "*.{tsx,jsx,vue,html}"

# Buttons without accessible text
Grep pattern: <button(?![^>]*aria-label)[^>]*>\s*<(?!span|text)
  --glob "*.{tsx,jsx,vue,html}"

# Links without accessible text
Grep pattern: <a\s(?![^>]*aria-label)[^>]*>\s*<(?!span|text)
  --glob "*.{tsx,jsx,vue,html}"

# Inputs without labels
Grep pattern: <input(?![^>]*aria-label)(?![^>]*aria-labelledby)[^>]*>
  --glob "*.{tsx,jsx,vue,html}"
# Cross-check: is there a <label for="..."> matching this input's id?

# Missing lang attribute
Grep pattern: <html(?![^>]*\blang\s*=)
  --glob "*.html"
```

**Evidence Format:**
```
File: <path> Line: <n>
Violation: img-no-alt | button-no-label | link-no-label | input-no-label | html-no-lang
Element: <matched_element>
WCAG Level: A | AA
```

**Default Severity:** Medium. High for WCAG Level A violations (img-no-alt, html-no-lang).

---

### Probe: responsive-issues

**Activation:** CSS/SCSS/Tailwind files exist.

**Detection Method:**

```bash
# Fixed widths on containers (>99px)
Grep pattern: width:\s*\d{3,}px
  --glob "*.{css,scss,less,sass}"

# Absolute positioning patterns (potential responsive issues)
Grep pattern: position:\s*absolute
  --glob "*.{css,scss,less,sass}"
# Cross-reference: check if parent has position:relative and explicit dimensions

# Missing viewport meta tag
Grep pattern: <meta[^>]*viewport
  --glob "*.html"
# Flag HTML files WITHOUT this pattern
```

**Evidence Format:**
```
File: <path> Line: <n>
Issue: fixed-width | absolute-position | missing-viewport
Code: <matched_text>
Value: <dimension if applicable>
```

**Default Severity:** Medium.

---

### Probe: design-drift

**Activation:** Pencil MCP configured in Session Config (`pencil` path provided, e.g. `pencil: designs/app.pen`).

**Detection Method:**

Use Pencil MCP tools to compare design specifications against implementation:
1. `get_editor_state` -- check current design file
2. `batch_get` -- retrieve design node properties (colors, spacing, typography)
3. `get_screenshot` -- capture design frames for visual comparison

Compare against:
- CSS custom properties / design tokens in codebase
- Component prop values
- Layout dimensions

**Evidence Format:**
```
Component: <component_name>
Design Value: <expected>
Implementation Value: <actual>
Property: color | spacing | typography | layout
Drift: <description>
```

**Default Severity:** High.

---

### Probe: frontend-slop

**Activation:** Frontend source files exist (`.css`, `.scss`, `.sass`, `.less`, `.html`, `.astro`, `.vue`, `.svelte`, `.jsx`, `.tsx`).

**Detection Method:**

Invoke `skills/discovery/probes/frontend-slop.mjs` directly via `node`. Unlike the grep-pattern probes above, this is a deterministic detector module (`scripts/lib/frontend-detect/`) — **no LLM, no network, no browser**. It walks the repo (skipping `node_modules`, `dist`, `.next`, etc.), runs the regex-tier rule set over each scannable file, and returns `{ probe, findings, summary }`.

```bash
node -e 'import("./skills/discovery/probes/frontend-slop.mjs").then(m => m.default({ repoRoot: process.cwd() }).then(r => console.log(JSON.stringify(r, null, 2))))'
```

Detects AI-generated design tells + quality issues, each tied back to a prose rule via `ruleRef` (the "Disziplin statt Mechanik" pattern):

| Rule | Severity | Catches |
|---|---|---|
| `gradient-text` | high | `background-clip:text` + gradient (incl. Tailwind `bg-clip-text`) |
| `side-stripe-border` | high | `border-left/right` ≥ 2px colored accent (incl. `border-l-4`) |
| `overused-font` | medium | Inter / Roboto / Arial / Helvetica as the **primary** family |
| `bounce-easing` | medium | bounce/elastic keywords + overshoot `cubic-bezier` |
| `ai-purple-gradient` | medium | purple→blue / two-purple gradients (high FP-risk if brand-purple) |
| `pure-black-ink` | low | `color:#000 / black` body text (always tint) |
| `arbitrary-z-index` | low | `z-index: 999 / 9999` magic numbers |
| `layout-property-transition` | low | animating width/height/margin/padding |

**Evidence Format:**
```
File: <path> Line: <n>
Rule: <rule-id>  Category: ai-slop | quality
ruleRef: <prose-guidance anchor it enforces>
Snippet: <offending source line>
fpRisk: low | medium | high
```

**Default Severity:** Per-rule (high for the absolute-ban tells, low for advisory quality nits). `fpRisk` is reported so triage can weight high-FP rules (`ai-purple-gradient`) more skeptically.

> **Precision boundary (honest):** this regex tier cannot resolve CSS cascade, so `side-stripe-border` flags any ≥2px side accent even when the element is unrounded — `.claude/rules/frontend.md` bans those (>1px accent), but a cascade-aware detector would narrow further. The heavier static-HTML + browser tiers are deliberately omitted (cost ≫ value for a probe/hook). See `scripts/lib/frontend-detect/rules.mjs`.

---
