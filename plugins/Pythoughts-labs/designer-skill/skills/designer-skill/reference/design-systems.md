# Design Systems

The specification and governance layer. Read this when building, extending, or auditing a design system — tokens, component specs, naming conventions, motion, theming, and pattern library. These govern *how to systematize* design decisions so they scale. The other reference files cover *how to design*; this covers *how to make those decisions durable*.

---

## Token Architecture

Design tokens are the single source of truth for visual decisions. Two-layer hierarchy is the minimum viable structure.

**Layer 1 — Global (primitive) tokens:**
Raw values. No semantics — just named constants.
```css
/* Color */
--color-blue-500: oklch(60% 0.2 260);
--color-neutral-100: oklch(95% 0.003 260);
--color-neutral-900: oklch(18% 0.005 260);

/* Spacing */
--space-4: 4px;
--space-8: 8px;
--space-16: 16px;
--space-32: 32px;
```

**Layer 2 — Semantic (alias) tokens:**
Reference global tokens by *purpose*. Themes override this layer, not the primitives.
```css
--text-primary: var(--color-neutral-900);
--text-secondary: var(--color-neutral-600);
--surface-default: var(--color-neutral-50);
--surface-card: var(--color-neutral-100);
--action-primary: var(--color-blue-500);
--border-subtle: var(--color-neutral-200);
```

**Layer 3 — Component tokens (optional):**
Scoped to a specific component. Add only when a component needs a value that doesn't fit any semantic token.
```css
--button-color-primary: var(--action-primary);
--button-radius: var(--radius-md);
--input-border-error: var(--status-error);
```

**Naming pattern:** `{category}-{property}-{concept}-{variant}-{state}`
Examples: `color-surface-overlay`, `space-inset-sm`, `border-width-input-focus`, `color-text-disabled`

**Rules:**
- Name by role, not value: `--text-body` not `--font-size-16`. A token named after its current value becomes misleading the moment the value changes.
- No hardcoded colors in components — always reference a semantic token.
- Declare new colors in OKLCH; never add a hex value outside the global token layer.
- CSS variable inheritance warning: changing a token on a parent recalculates all children. Set transforms directly on the element when you need to avoid cascade side effects.
- Themes override semantic tokens, not component tokens or global tokens.

---

## Token Categories

| Category | Global examples | Semantic examples |
|---|---|---|
| **Color** | `color-blue-500`, `color-neutral-900` | `text-primary`, `surface-card`, `action-primary`, `status-error` |
| **Spacing** | `space-4`, `space-8`, `space-16` | `inset-sm`, `inset-md`, `stack-md`, `inline-lg` |
| **Typography** | `font-size-14`, `font-weight-600`, `line-height-normal` | `text-body`, `text-heading-sm`, `text-caption` |
| **Border** | `border-width-1`, `radius-4`, `radius-full` | `border-default`, `radius-sm`, `radius-pill` |
| **Shadow / elevation** | `shadow-sm-values`, `shadow-lg-values` | `elevation-card`, `elevation-modal`, `elevation-tooltip` |
| **Motion** | `duration-100`, `duration-300`, `ease-out-expo` | `transition-interactive`, `transition-enter`, `transition-exit` |
| **Z-index** | Semantic scale only | `z-dropdown: 100`, `z-sticky: 200`, `z-modal-backdrop: 300`, `z-modal: 400`, `z-toast: 500`, `z-tooltip: 600` |

---

## Motion System

Define motion as a token layer, not a collection of one-off animations. Without a system, each component invents its own duration and easing; transitions feel inconsistent; design and engineering have no shared language.

**Duration scale (4–6 values is enough):**

| Token | Value | Use |
|---|---|---|
| `duration-instant` | 50ms | Checkbox tick, toggle — changes that must feel immediate |
| `duration-fast` | 100ms | Tooltip appear, chip dismiss, small element transitions |
| `duration-normal` | 200ms | Default UI transitions: dropdown open, focus ring, tab switch |
| `duration-moderate` | 300ms | Modal entry, panel slide, medium element transitions |
| `duration-slow` | 400ms | Page-level transitions, complex choreography |
| `duration-deliberate` | 600ms | High-emphasis, intentionally paced moments (onboarding reveal) |

Don't create more tokens than distinct use cases. Add a new one only when nothing in the existing scale fits.

**Easing scale:**

| Token | Curve | Use |
|---|---|---|
| `ease-standard` | `cubic-bezier(0.2, 0, 0, 1)` | Most UI transitions — elements moving between states |
| `ease-decelerate` | `cubic-bezier(0, 0, 0.2, 1)` | Elements entering the screen |
| `ease-accelerate` | `cubic-bezier(0.3, 0, 1, 0.3)` | Elements leaving the screen |
| `ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Playful or tactile interactions (FAB expand, drawer bounce) |
| `ease-linear` | `linear` | Looping animations only — progress spinners, shimmer |

**Choreography rules:**
- Stagger: related elements entering together stagger 30–50ms; lead with the most important.
- Total staggered sequence: under 500ms.
- Direction consistency: elements sliding in from the right → related outgoing elements slide out to the left.
- Coordination: elements in the same semantic group use the same duration and easing.

**Reduced motion — apply at the system level:**
```css
@media (prefers-reduced-motion: reduce) {
  :root {
    --duration-instant: 0ms;
    --duration-fast: 0ms;
    --duration-normal: 0ms;
    --duration-moderate: 0ms;
    --duration-slow: 0ms;
    --duration-deliberate: 0ms;
  }
}
```
Preserve animations that convey essential state (loading spinners, progress bars). Opacity-only fades are generally acceptable under reduced-motion. Remove sliding, scaling, and rotation.

---

## Component Specification

Every component needs a spec before implementation. The spec is the contract between design and engineering.

**Required sections:**

1. **Overview** — name, one-sentence description, when to use, when NOT to use.
2. **Anatomy** — visual breakdown with labels for each sub-element; required vs. optional parts.
3. **Variants** — size (sm/md/lg), style (primary/secondary/ghost), layout variations.
4. **States** — default, hover, focus, active, disabled, loading, error, success. Every state must have a visual representation.
5. **Props/API** — name, type, default, description, required flag. One row per prop.
6. **Behavior** — interaction sequence, animation (duration + easing tokens), responsive behavior, edge cases.
7. **Accessibility** — ARIA role, keyboard navigation sequence, screen reader behavior, focus management.
8. **Usage guidelines** — do/don't examples, content rules (max label length, icon requirements), related components.

**State rule:** never implement a component without specifying all eight interaction states. A component with a loading state that wasn't designed gets a default browser spinner in a random location. A component with no error state silently fails.

---

## Naming Conventions

Predictable names are the most underrated design system feature. If a contributor can guess the name before looking it up, the system is working.

**Principles:** Predictable. Consistent. Scalable. Unambiguous. Names describe purpose, never appearance.

**Patterns by artifact:**

| Artifact | Pattern | Example |
|---|---|---|
| Component (Figma / file) | `[Category]/[Name]/[Variant]/[State]` | `Form/Input/Default/Error` |
| Token | `{category}-{property}-{concept}-{variant}-{state}` | `color-text-primary`, `space-inset-sm` |
| CSS class | `kebab-case` | `.button-primary`, `.input-error` |
| JS/TS component | `PascalCase` | `<ButtonPrimary />`, `<InputField />` |
| Props | `camelCase` | `isDisabled`, `onSubmit`, `labelText` |
| Icon asset | `icon-{name}-{size}` | `icon-chevron-right-16` |
| Illustration | `illust-{scene}-{variant}` | `illust-empty-state-default` |

**Common pitfalls:**
- Abbreviations only the author understands (`btn-pri-hov` vs. `button-primary-hover`).
- Inconsistent separators (`__` in some places, `-` in others).
- Names based on appearance (`color-blue`) instead of purpose (`color-action-primary`) — the name becomes misleading when the value changes.
- Using numbers that depend on the current value (`gray-200`) instead of the role (`neutral-subtle`).

---

## Theming Architecture

One component library, multiple visual themes through token mapping. Themes are layer-2 overrides; the components never change.

**Three-layer override model:**
- **Layer 1 (global tokens):** Never change between themes — these are the raw palette.
- **Layer 2 (semantic tokens):** Themes override here. Light mode, dark mode, brand variant, high-contrast — all expressed as semantic token overrides.
- **Layer 3 (component tokens):** Inherit from semantic tokens; rarely need to be themed directly.

**Theme types:**
- **Color modes:** light (default), dark, high-contrast, dimmed.
- **Brand themes:** primary brand, sub-brand, white-label, seasonal campaign.
- **Density:** comfortable (default), compact (data-heavy views), spacious (reading/editorial).

**Dark mode design:**
- Never just invert — reduce brightness thoughtfully.
- Use lighter surfaces for elevation rather than shadows (drop shadows don't read in dark mode).
- Desaturate colors 10–20% — saturated colors vibrate against dark backgrounds.
- Text: use off-white (e.g. `oklch(87% 0.01 260)`) not pure white.
- Surface hierarchy: each elevation step is 2–4% lighter: background → surface-1 → surface-2 → surface-3 → overlay.
- Test every component in dark mode; never assume it just works.

**Implementation:**
```css
/* Light mode (default) */
:root {
  --surface-default: var(--color-neutral-50);
  --text-primary: var(--color-neutral-900);
  --action-primary: var(--color-blue-500);
}

/* OS-level dark mode detection */
@media (prefers-color-scheme: dark) {
  :root {
    --surface-default: var(--color-neutral-950);
    --text-primary: var(--color-neutral-100);
    --action-primary: var(--color-blue-400);
  }
}

/* Manual toggle — takes precedence over OS detection */
[data-theme="dark"] {
  --surface-default: var(--color-neutral-950);
  --text-primary: var(--color-neutral-100);
  --action-primary: var(--color-blue-400);
}
```
Provide both `prefers-color-scheme` detection and a manual `[data-theme]` attribute toggle.

---

## Pattern Library

A pattern library documents reusable solutions to recurring problems — not just component appearance, but the interaction patterns that span multiple components.

**Pattern entry structure:**
1. **Problem** — what recurring need does this address, and in what contexts?
2. **Solution** — the pattern; key principles; visual + interaction description.
3. **Anatomy** — constituent components, layout, required vs. optional elements.
4. **Variants** — context-specific implementations, responsive adaptations.
5. **Behavior** — user flow, state changes, error handling.
6. **Examples** — good implementations + anti-patterns with explanations.
7. **Accessibility** — inclusive design considerations, assistive tech support.
8. **Related patterns** — similar patterns, commonly combined patterns, patterns this builds upon.

**Common pattern categories:** Navigation, Data entry (forms), Data display (tables, lists, cards), Feedback (toasts, banners, inline), Onboarding, Empty states, Error states, Search, Dialogs / overlays.

**Quality bar:** a pattern entry is not complete until it includes at least one anti-pattern (what NOT to do) with a specific explanation of why it fails. Patterns without anti-patterns teach the solution without teaching the failure mode.

---

## Accessibility Integration

Accessibility is integrated into component development, not added as a post-hoc audit.

**WCAG 2.2 POUR framework:**
- **Perceivable:** text alternatives for non-text content, captions, adaptable content, color contrast.
- **Operable:** keyboard access, no seizure-inducing content, navigation, input modalities.
- **Understandable:** readable, predictable, input assistance.
- **Robust:** assistive technology compatibility, semantic markup, correct ARIA.

**Severity for triage:** Critical (blocks access entirely) → Major (significant difficulty) → Minor (workaround available) → Enhancement (beyond compliance improvement).

**Minimum checks per component:**
- Contrast ratios: 4.5:1 for body text, 3:1 for large text and UI components against adjacent surfaces.
- All interactive elements keyboard-reachable and operable with Enter/Space.
- Focus ring: visible, 2–3px, 3:1 contrast against the surrounding surface, offset outside the element.
- Labels programmatically associated with inputs (`<label for>` or `aria-label` or `aria-labelledby`).
- Error messages associated with their field via `aria-describedby`.
- No color-only information — always pair color with a text label or icon.
- Dynamic state changes announced via `aria-live` region or role-based announcement.

**Rule:** automated checks catch ~30–40% of WCAG 2.2 issues. Never certify WCAG 2.2 AA compliance from automated output alone. Manual keyboard navigation and screen reader testing are required.

---

## Color System Architecture

Build in three layers: raw palette → semantic role mapping → component-specific tokens.

**Step 1 — Generate tonal scales:**
For each hue (primary, secondary, accent, neutrals, semantics: error/success/warning/info), generate a tonal scale from lightest (50) to darkest (950). Use OKLCH for perceptually uniform steps across the scale.

```css
--color-brand-50:  oklch(97% 0.02 260);
--color-brand-100: oklch(93% 0.04 260);
--color-brand-300: oklch(78% 0.12 260);
--color-brand-500: oklch(60% 0.20 260);
--color-brand-700: oklch(42% 0.15 260);
--color-brand-900: oklch(25% 0.08 260);
--color-brand-950: oklch(18% 0.06 260);
```

**Step 2 — Map semantic roles:**

| Semantic token | Purpose |
|---|---|
| `color-text-primary` | Primary body text |
| `color-text-secondary` | Secondary / supporting text |
| `color-text-disabled` | Disabled text (must still pass 3:1) |
| `color-surface-default` | Page background |
| `color-surface-card` | Card and panel backgrounds |
| `color-surface-overlay` | Modal / dialog backgrounds |
| `color-action-primary` | Primary interactive color (buttons, links) |
| `color-action-secondary` | Secondary interactive color |
| `color-status-error` | Error state backgrounds and icons |
| `color-status-error-text` | Error state text (must pass 4.5:1 against its background) |
| `color-status-success` | Success states |
| `color-status-warning` | Warning states |
| `color-border-default` | Standard border color |
| `color-border-strong` | Emphasized / focus border |

**Step 3 — Validate all pairings:**
Every foreground/background semantic pair in use must be verified for contrast. A color system is not complete until every combination used in components has been checked. Document failing pairs — don't ship them as known issues.

---

## Typography Scale

A mathematical ratio generates harmonic size relationships. Pick one ratio and apply it consistently.

**Common ratios:** Major Third (×1.25), Perfect Fourth (×1.333), Augmented Fourth (×1.414).

**Example scale using Major Third from a 16px base:**

| Token | Size | Line-height | Use |
|---|---|---|---|
| `text-caption` | 12px | 1.4 | Fine print, timestamps, metadata |
| `text-body-sm` | 14px | 1.5 | Secondary body, dense UI |
| `text-body` | 16px | 1.5 | Primary body text (floor for desktop) |
| `text-body-lg` | 20px | 1.5 | Lead / intro paragraphs |
| `text-heading-sm` | 24px | 1.3 | Card titles, subsection headings |
| `text-heading-md` | 32px | 1.2 | Section titles |
| `text-heading-lg` | 40px | 1.15 | Page titles |
| `text-display` | 48–64px | 1.1 | Hero headings |

**Paired dimensions per token:** `font-size`, `line-height`, `letter-spacing`, `font-weight`. Define all four for each scale step; don't let components set them ad hoc.

**Letter-spacing guide:** tight (−0.02em) for large display headings; 0 for body; wide (+0.05em) for uppercase labels and captions only.

**Rules:**
- Body minimum: 16px on desktop, 14px on mobile.
- Line length (measure): 45–75 characters for body. Apply with `max-width: 65ch` on prose containers.
- Limit to 4–5 active sizes in regular UI; display / hero are supplementary.
- Test with real content — lorem ipsum hides length and line-break edge cases.

---

## Spacing System

A base unit multiplied into a scale. 4px or 8px base. Never use arbitrary values in components.

**4px base scale:**

| Token | Value | Typical use |
|---|---|---|
| `space-1` | 4px | Minimal gap: icon + label, badge padding |
| `space-2` | 8px | Tight internal padding: chip, tag |
| `space-3` | 12px | Input vertical padding, small component gap |
| `space-4` | 16px | Default padding, standard gap between siblings |
| `space-6` | 24px | Component-to-component gap, card padding |
| `space-8` | 32px | Large component gap, section breathing room |
| `space-12` | 48px | Section-to-section spacing |
| `space-16` | 64px | Major section dividers |
| `space-24` | 96px | Hero padding, page-level vertical rhythm |

**Spatial types:**
- **Inset (padding):** equal `inset-sm: 8px`; squish `inset-squish-sm: 4px 8px` (tighter top/bottom than left/right); stretch `inset-stretch-sm: 12px 8px` (taller than wide).
- **Stack:** vertical gap between stacked elements.
- **Inline:** horizontal gap between inline or flex-row elements.
- **Grid gap:** gap between grid / flex children.

**Density modes:** compact (reduce each spacing value one step down), comfortable (default), spacious (increase one step up). Never mix modes within a component.

**Rules:**
- Related items: smaller spacing (`space-1`, `space-2`).
- Distinct sections: larger spacing (`space-8`, `space-12`).
- Minimum padding in bordered or contained components: 8px (`space-2`).
- Consistent within a component; larger between unrelated groups.
