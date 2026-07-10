# Agent-friendly pages — audit reference (May 2026)

The next wave of AI search is not summarization — it's **agents** acting on the
user's behalf (search, compare, buy, book). Google's AI optimization guide and
the linked web.dev article describe three channels through which agents
interpret your site:

1. **Screenshots + vision model** — interprets visual hierarchy, button
   prominence, layout. Slow and token-expensive.
2. **Raw HTML / DOM** — nesting, IDs, classes, data attributes.
3. **The accessibility tree** — the browser-native semantic distillation
   (roles, names, states). The cleanest signal of the three.

Modern agents combine all three. Optimizing for the **accessibility tree** is
the single highest-leverage move; if your accessibility tree is broken, no
amount of visual polish saves you.

**Primary sources:**
- Google AI optimization guide:
  https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- web.dev (referenced from the guide above): article on building
  agent-friendly websites

## Audit checklist

### 1. Use real interactive elements

| Pass | Fail |
|---|---|
| `<button>` for actions | `<div onclick="...">` |
| `<a href="...">` for navigation | `<div onclick="window.location...">` |
| `<input>` / `<select>` / `<textarea>` | Custom `contenteditable` widgets |

If you cannot use a real interactive tag, supply ARIA: `role="button"`,
`role="link"`, `tabindex="0"`, plus key handlers for `Enter` and `Space`.

**Why it matters:** the accessibility tree exposes real interactive elements
with their roles. Custom div widgets often appear in the tree with no role at
all — agents skip them.

### 2. Label associations

Every form input must have an associated label:

```html
<label for="email">Email</label>
<input id="email" type="email" name="email">
```

Or use `aria-label` / `aria-labelledby` where a visible label isn't possible.
Agents that read the accessibility tree get the field purpose directly from
the associated label — without it, the input is a void.

### 3. Interactive target size

Visual-analysis pipelines filter out interactive elements smaller than **~8
square pixels** of unobscured area. Tap-target accessibility minimums (24×24
WCAG AA, 44×44 Apple HIG) are stricter and pass the agent gate by default.

Audit: any clickable element below 24×24px is a candidate for agent
invisibility, in addition to the WCAG failure.

### 4. Don't cover interactive nodes with transparent overlays

Vision models discard covered nodes when computing what's "interactive at this
position". Common offenders:

- Full-card click handlers that overlay every child link.
- Transparent cookie-consent layers persisting beyond consent.
- Modal portals with `pointer-events: auto` left on after dismiss.
- "Ghost" tracking pixels with `position: absolute; inset: 0`.

### 5. Layout stability

If "Add to cart" lives in different positions on `/category/shoes` vs
`/category/bags`, screenshot-based agents have to relearn the page each
visit. Keep functionally identical actions in the same screen quadrant across
templates.

Cross-reference: this overlaps with **CLS** (Cumulative Layout Shift) in Core
Web Vitals, but the agent-UX concern is broader — it covers page-to-page
stability, not just within-page shift.

### 6. `cursor: pointer` as a legitimate signal

Vision models read `cursor: pointer` (set by default on `<a>` / `<button>`) as
a hint that an element is actionable. Do not override it to `cursor: default`
on truly interactive elements just for visual minimalism.

Inverse: do not apply `cursor: pointer` to non-interactive elements — that
makes agents click things that do nothing.

### 7. Stable, meaningful selectors

Agents that fall back to DOM parsing rely on:

- Real semantic tags (`<nav>`, `<main>`, `<article>`, `<section>`, `<aside>`)
- Stable `id` attributes on top-level layout containers
- `data-*` attributes that describe purpose, not implementation

Avoid auto-generated class names like `__sc_a4b7d9e2` as the only handle on a
critical interactive element — agents can target them but cannot tell what
they mean.

## Forward-looking: WebMCP

Google's AI optimization guide name-drops **WebMCP**, a proposed standard for
direct site-to-agent interaction (analogous to MCP in the Claude / Anthropic
ecosystem, but operating at the page level). There is an early preview
program; broad adoption is not expected before 2027.

**Audit posture:** mention WebMCP in reports as a forward-looking signal worth
tracking. Do not flag the absence of WebMCP support as a finding — the
standard is not yet stable.

## Quick-audit one-liner

For a fast smoke check, capture the accessibility tree via Lighthouse or
Chrome DevTools and look for:

- Any interactive element with `role="generic"` → broken semantics.
- Any input without an `accessible name` → missing label.
- Any `<div>` with `onclick` and no `role` / `tabindex` → custom widget that
  agents won't see.

`scripts/render_page.py --mode auto` already loads pages headlessly; extending
it with an accessibility-tree dump (`page.accessibility.snapshot()` in
Playwright) is the natural place to land an automated agent-UX check in a
future iteration.

## Last verified

2026-05-18. Update when:

- WebMCP graduates from preview to stable.
- Google publishes a separate agent-UX scoring framework.
- web.dev publishes a follow-up article with revised criteria.
