---
name: color
description: 'Use this skill whenever color decisions matter — picking the brand primary, defining a neutral ramp, designing status semantics (success/warning/error), choosing chart palettes, selecting accent hues, supporting dark mode, ensuring colorblind-safe contrast, or auditing an existing UI for color noise. Trigger when stakeholders argue about palette, when WCAG contrast is in scope, when designing for global audiences (where color symbolism varies), or when a UI feels "too colorful" or "too monochrome." Color is one of the foundational principles in ''Universal Principles of Design'' (Lidwell, Holden, Butler 2003).'
---

# Color

Color attracts attention, groups related elements, signals meaning, and shapes aesthetic response. Used deliberately, it carries information at a glance and unifies a product. Used carelessly, it adds noise, fails accessibility, and means different things to different audiences. Among visual variables, color is the loudest and the most easily abused.

## Definition (in our own words)

Color performs four jobs in design: it draws the eye to elements that matter (attention), it visually unifies elements that belong together (grouping), it carries categorical or semantic information (meaning — green is success, red is danger), and it shapes the aesthetic register of the design (a saturated palette feels energetic; a muted one feels serious). Each color you introduce to a design takes on one or more of these roles; designs that use color promiscuously dilute every role. The discipline is in the restraint: a small palette, used consistently, with each color earning its place.

## Origins and research lineage

- **Josef Albers**, *Interaction of Color* (1963). The foundational treatment of perceptual color relationships — how the same color reads differently against different backgrounds. Required reading for anyone designing color systems.
- **Johannes Itten**, *The Art of Color* (1961). The Bauhaus tradition of color theory; introduced the color wheel still used today.
- **Maxwell, Helmholtz, Hering** — 19th-century color-perception researchers whose work underlies modern color science (trichromacy, opponent-process theory).
- **Lidwell, Holden & Butler** (2003) compactly addressed the design implications under the headings of number of colors, combinations, saturation, and symbolism. The book emphasizes restraint: use color conservatively and never as the only signal.
- **WCAG color-contrast research** (W3C, 2008 onward) provides the empirical basis for accessibility-aware color systems — body text needs 4.5:1 luminance contrast minimum.
- **Modern perceptual color spaces** (CIELAB, OKLCH) provide tools for building color systems that are perceptually uniform across hues.

## The four jobs of color

### 1. Attention

A saturated, distinct color in a sea of neutrals draws the eye. This is the basis for primary CTAs, error states, and emphasis. The mechanism is preattentive: a single colored item among uncolored items "pops out" within ~200ms.

The economy: attention only works when sparse. A page where every element is colored loses the pop-out advantage entirely.

### 2. Grouping

Items that share a color read as related. This underlies status systems (all overdue items in red), category coding (all marketing dashboards in blue), and brand identity (all of this product's surfaces share this hue).

Use this for *meaningful* relationships, not for decoration.

### 3. Meaning

Color carries semantic content when it's used consistently and conventionally. In Western contexts: red = danger / stop / error; green = go / success; yellow = warning. These conventions are partly cultural (red signals luck in much of East Asia; green is unlucky in some contexts), so global products should pair color with non-color signals.

### 4. Aesthetics

Color shapes mood. Saturated palettes feel energetic; muted palettes feel calm or serious. Warm colors (yellow, orange, red) feel active; cool colors (blue, green, purple) feel stable. These associations are partly biological (warm colors attract attention faster) and partly cultural.

## Number of colors: be restrained

A useful rule: limit your active palette to ~5 colors that the user must recognize.

```
Brand primary    — 1 hue
Neutrals         — a ramp from dark to light (~9 stops)
Success          — 1 hue (typically green)
Warning          — 1 hue (typically yellow / amber)
Destructive      — 1 hue (typically red)
```

Beyond this, every additional hue dilutes the system. Charts and data visualizations may need 5–8 categorical colors, but those are exceptions; the *interface chrome* should stay restrained.

## Color combinations: how to compose a palette

Common harmony patterns (from the color wheel):

- **Monochromatic**: variations of one hue (different lightness/saturation). Calm, unified.
- **Analogous**: hues adjacent on the wheel (blue, blue-green, green). Harmonious, low-tension.
- **Complementary**: hues opposite on the wheel (blue + orange). High contrast, high tension.
- **Triadic**: three hues equidistant on the wheel. Balanced, vibrant.
- **Quadratic**: four hues from a square or rectangle on the wheel. Complex; needs careful weighting.

For UI work, monochromatic + neutrals + a few semantic accents is the workhorse. Complementary and triadic palettes look striking but require more care to balance.

## Saturation: the volume knob

Saturation (chromatic intensity) is color's volume knob.

- **Saturated colors** demand attention. Use sparingly: primary CTAs, errors, brand moments.
- **Desaturated colors** recede. Use abundantly: backgrounds, neutrals, secondary states.

A common UI mistake: saturated colors everywhere. The page becomes loud; nothing stands out. The fix: pull saturation down on most surfaces; reserve full saturation for moments.

## Symbolism: cultural variation

Color symbolism is *not* universal. Examples:

- **Red**: danger / stop in Western contexts; luck and prosperity in Chinese contexts; mourning in some African contexts.
- **White**: purity in Western weddings; mourning in some Asian funerals.
- **Black**: formal / authoritative in Western; mourning broadly; rebellion in subcultures.
- **Green**: nature / go in Western; sometimes unlucky or associated with infidelity in specific contexts.
- **Yellow**: caution / warmth in Western; sacred in some Asian contexts; cowardice in others.

For global products: don't rely on color symbolism alone. Pair color with text, icons, and position so the meaning carries across audiences.

## Color is never the only signal

WCAG 1.4.1 codifies what's also a basic usability principle: color must not be the only means of conveying information. About 8% of men have red-green color blindness; achievement of WCAG 1.4.1 requires that any color signal be paired with a non-color signal.

Practical applications:

- **Form errors**: red border + error message + icon, not just red border.
- **Status badges**: color + icon + text, not just color.
- **Required fields**: asterisk + "(required)" or `aria-required`, not just red label.
- **Chart series**: color + pattern (lines: dashed, dotted) or label, not just color.
- **Selected items**: color + checkmark or border, not just color.

This isn't only for color-blind users; it serves anyone in glare, on a printed copy, in low contrast, or with degraded vision.

## Color and accessibility (WCAG)

Foreground/background contrast ratios (relative luminance):

| Content type | Level AA | Level AAA |
|---|---|---|
| Body text (< 18pt regular or < 14pt bold) | 4.5:1 | 7:1 |
| Large text (≥ 18pt regular or ≥ 14pt bold) | 3:1 | 4.5:1 |
| UI components and graphical objects | 3:1 | (no AAA) |

Common failures:

- Light grey body text (`#999` on white = 2.85:1 — fails).
- Brand-color body links (`#1e90ff` on white = 3.4:1 — fails for body, passes for large/UI).
- Placeholder text in inputs (often <3:1 — fails for the field's accessible name).

Test with a contrast checker (WebAIM, Stark, Chrome DevTools). It's faster than guessing.

## Building a color system

A workable system architecture:

### 1. Pick the brand primary

One hue. This is the color users will associate with your product. Choose with awareness of category conventions (banking is often blue; food is often warm; tech is often blue or green).

### 2. Define the neutral ramp

9–11 stops from white to near-black. Tinting the neutrals slightly toward the brand primary (e.g., 4% saturation of the primary hue) makes the whole UI feel cohesive without anyone consciously noticing.

```
neutral-50    background (lightest)
neutral-100   subtle background, hover
neutral-200   borders, dividers
neutral-300   strong borders
neutral-400   placeholder, icons
neutral-500   muted text
neutral-600   secondary text
neutral-700   primary body text
neutral-800   strong text, headings
neutral-900   highest contrast
```

### 3. Define semantic colors

Three to five hues for status:

- **Success** (typically green).
- **Warning** (typically amber / yellow).
- **Destructive / Error** (typically red).
- Optionally: **Info** (typically blue, especially if your primary is *not* blue).

For each, define multiple stops: a tinted background (`green-50`), a darker text color (`green-700`), a focus or border color (`green-500`).

### 4. Test in dark mode

A palette tuned for light mode often fails in dark mode — saturation and contrast perception inverts. Build dark-mode tokens deliberately, not by simple inversion.

### 5. Test for accessibility

Every text-on-background pair you ship must clear 4.5:1 (body) or 3:1 (large/UI). Test with a contrast checker; fix what fails.

## Worked examples

### Example 1: a status badge system

```html
<style>
  .badge { display: inline-flex; align-items: center; gap: 4px;
           padding: 2px 8px; border-radius: 9999px;
           font-size: 12px; font-weight: 500; }
  .badge--success { background: hsl(142 70% 95%); color: hsl(142 70% 22%); }
  .badge--warning { background: hsl(38 95% 95%);  color: hsl(38 90% 25%); }
  .badge--error   { background: hsl(0 80% 95%);   color: hsl(0 75% 32%); }
  .badge--neutral { background: hsl(0 0% 96%);    color: hsl(0 0% 30%); }
</style>

<span class="badge badge--success"><CheckIcon aria-hidden /> Paid</span>
<span class="badge badge--warning"><ClockIcon aria-hidden /> Pending</span>
<span class="badge badge--error"><AlertIcon aria-hidden /> Overdue</span>
<span class="badge badge--neutral"><PencilIcon aria-hidden /> Draft</span>
```

Each badge uses color, icon, *and* text. Color carries category at a glance; icon and text carry it for color-blind users and for any out-of-context display.

### Example 2: a primary action vs. secondary action

```html
<button class="btn-primary">Save changes</button>
<button class="btn-secondary">Cancel</button>
```

```css
.btn-primary {
  background: hsl(220 90% 50%);   /* full-saturation brand */
  color: white;
  /* ...padding, radius... */
}
.btn-secondary {
  background: white;
  color: hsl(0 0% 27%);
  border: 1px solid hsl(0 0% 85%); /* neutral, no color emphasis */
}
```

The primary uses full saturation and the brand hue; the secondary uses neutrals only. The eye picks the primary instantly.

### Example 3: a chart palette

```css
:root {
  --chart-1: hsl(220 70% 55%);
  --chart-2: hsl(160 60% 45%);
  --chart-3: hsl(40 90% 55%);
  --chart-4: hsl(310 60% 55%);
  --chart-5: hsl(10 70% 55%);
}
```

Five hues at similar lightness and saturation, distributed around the wheel. Each is distinct from the others *and* survives most color-blindness simulations. For more series, add patterns (dashed lines, dotted, hatched fills) rather than adding more hues.

## Anti-patterns

- **Saturation overload.** Every CTA, every chart, every badge at full saturation. Page becomes a noise field.
- **Color-only signals.** Red asterisks for required fields with no `*` or "required" text. Color-blind users miss it.
- **Brand color everywhere.** Every link, every heading, every accent in the brand color. Brand stops registering.
- **Light grey body text** (`#999` on white). Fails AA contrast; fatigues all readers.
- **Inconsistent semantic colors.** "Destructive" in one shade of red here, a different shade there. Each instance is a re-learning.
- **Dark-mode by simple inversion.** Saturation perception differs; pure inversion produces glare.
- **Color symbolism assumed universal.** A red Lunar New Year banner reading as "danger" because the design system equates red with errors.
- **Too many colors.** A 12-hue palette where users can't predict what means what.

## Heuristics

1. **The grayscale test.** Convert to grayscale. Does the design still work? If yes, color is supportive but not load-bearing. If no, you're depending on color too much.
2. **The contrast pass.** Every text/background pair, every UI/background pair. AA at minimum.
3. **The colorblind simulation.** Chrome DevTools → Rendering → Emulate vision deficiencies. Status systems that lean on red/green collapse here.
4. **The cultural check.** For global products, check color symbolism with users in target markets.
5. **The dark-mode test.** Switch to dark mode. Does the palette still work? Are contrasts still passing?

## Related principles

- **`hierarchy-color-and-tone`** — color as a hierarchy axis.
- **`highlighting`** — color is the strongest highlighting tool.
- **`signal-to-noise-ratio`** — color discipline is at the core of SNR design.
- **`accessibility-perceivable`** (process) — color decisions are accessibility decisions.
- **`expectation-effect`** (interaction) — color signals shape user expectations.
- **`uniform-connectedness`** — color is one of the strongest grouping signals.
- **`interference-effects`** — mismatched color/meaning (red "go" button) creates Stroop interference.

## Sub-aspect skills

- **`color-semantic-systems`** — building status/category color systems that scale and stay consistent.
- **`color-accessibility-and-mode`** — accessibility-aware color, dark mode, and high-contrast support.

## Closing

Color is the loudest single dimension a designer commands. The discipline is in the restraint: a small palette, used consistently, with each color earning its place. Designs that respect this restraint feel polished; designs that don't feel noisy. Spend color where it earns the volume.
