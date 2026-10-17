---
name: hierarchy-color-and-tone
description: 'Use this skill when constructing visual hierarchy through color and tone (value, contrast, saturation) — picking which elements get full-color emphasis and which recede into greys, building a tone ladder, and deciding when color should *be* the hierarchy versus when it should *support* a size/weight hierarchy. Trigger when picking the primary color, building a neutral palette, designing a status badge system, or fixing a UI where color is "too loud" or "too flat." Sub-aspect of the broader `hierarchy` principle; read that first if you haven''t already.'
---

# Hierarchy through color and tone

Color is the most attention-grabbing visual dimension and the most accessibility-loaded. Used well, it can establish a hierarchy of importance at a glance. Used poorly, it creates noisy, fatiguing, or inaccessible UIs. This skill is about using color and tone deliberately, as a *third* hierarchy axis on top of size and weight — almost never as the *only* hierarchy signal.

## When this is the decisive sub-aspect

- You're picking the primary color, accent palette, and neutral ramp for a design system.
- You're designing status badges, semantic colors (success/warning/danger), or a chart palette.
- You have a layout where size and weight hierarchy work but the page still feels "flat" or "monochrome."
- You're trying to fix a "noisy" UI — too many colors, all competing.
- You're checking accessibility and need to keep hierarchy intact while satisfying contrast requirements.

## Core ideas

### Tone (value/contrast) is the universal hierarchy axis

*Value* is how light or dark a color is; *contrast* is the value difference between figure and ground. Tone hierarchy works across hue, theme (light/dark), color blindness, and grayscale rendering. It's the most robust hierarchy dimension you have.

A workable tone ladder for foreground text on a light background:

```
primary text       hsl(0 0% 9%)      contrast 19.9:1   /* near-black */
secondary text     hsl(0 0% 35%)     contrast  9.9:1
tertiary text      hsl(0 0% 50%)     contrast  6.4:1
disabled text      hsl(0 0% 70%)     contrast  3.6:1   /* WCAG AA fails for body */
```

Use this ladder *additively* with size and weight: `display` is large + heavier *and* highest contrast; `caption` is small + light *and* lowest contrast. The three axes compound.

Mirror the ladder for dark themes (light values on a dark ground), tuned for the different perceptual response to light-on-dark.

### Color (hue) carries categorical meaning, not rank

Hue is a categorical signal: red, blue, green are *different kinds*, not different *amounts*. Using hue to rank items ("red is most important, orange is next, yellow is third") fails for colorblind viewers and contradicts cultural expectations.

Use hue to encode **category** or **state**, not rank:

- **Status semantics:** green = success, yellow = warning, red = danger/destructive.
- **Brand emphasis:** the primary brand color marks the action the brand wants you to take.
- **Categorical data:** chart series, tag colors, project labels.

For *ranking*, use tone (value) and saturation, which behave like amounts.

### Saturation distinguishes emphasis from background

Saturated colors call for attention; desaturated colors recede. A useful pattern: full-saturation for emphasis, desaturated/muted for background.

```
primary action       full saturation, full hue       /* "Save" button */
recommended option   medium saturation               /* hover, selected state */
disabled / inactive  desaturated to grey             /* unavailable items */
```

When a brand color appears everywhere at full saturation, it loses meaning — the eye dismisses it as decoration. Reserve saturation for the things you want noticed.

### One primary color, one or two semantic colors, the rest neutral

A common failure mode: the brand has a primary, secondary, tertiary, and accent color, plus warning, error, success, info. Eight colors in active use means the eye can't tell what means what.

A robust default palette has three roles in active color:

1. **Primary** — the brand color, used for primary actions and selection states.
2. **Destructive** — red, used only for destructive actions and errors.
3. **Success / muted positive** — used sparingly for confirmation states and positive deltas.

Everything else lives in the **neutral ramp** (5–10 grey values from background to primary text). Neutrals do most of the work; color is reserved for moments.

### Build a neutral ramp

A useful neutral ramp at 9 stops:

```
neutral-50    background, lightest                hsl(0 0% 98%)
neutral-100   subtle background, hover            hsl(0 0% 96%)
neutral-200   borders, dividers                   hsl(0 0% 92%)
neutral-300   strong borders, disabled inputs     hsl(0 0% 85%)
neutral-400   placeholder text, icons             hsl(0 0% 65%)
neutral-500   muted text, captions                hsl(0 0% 50%)
neutral-600   secondary text                      hsl(0 0% 40%)
neutral-700   primary body text                   hsl(0 0% 27%)
neutral-800   strong text, headings               hsl(0 0% 18%)
neutral-900   highest contrast, display text      hsl(0 0% 9%)
```

For dark themes, invert (but slightly compress, since white-on-black is more glaring than black-on-white).

When you find yourself reaching for a "fourth" colored element on a page, stop. It probably belongs in the neutral ramp.

### Color tinted toward the primary

A subtle move that lifts perceived quality: tint your neutral ramp very slightly toward the primary brand color. Pure-grey neutrals can feel sterile; a 2–4% chroma toward the brand makes the whole UI feel cohesive.

```
/* Pure neutral */
neutral-700: hsl(0 0% 27%);

/* Tinted toward a blue brand */
neutral-700: hsl(220 6% 28%);
```

The difference is invisible side by side and obvious on the whole UI.

## Worked example: a status badge system

Three badges encoding three states. Color carries the category; tone and weight carry the rank.

```html
<style>
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.125rem 0.5rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 500;
    line-height: 1.4;
  }
  .badge-success {
    background: hsl(142 70% 96%);
    color:      hsl(142 70% 22%);   /* dark text on light tint, contrast > 7:1 */
  }
  .badge-warning {
    background: hsl(38 95% 95%);
    color:      hsl(38 90% 25%);
  }
  .badge-destructive {
    background: hsl(0 80% 96%);
    color:      hsl(0 75% 32%);
  }
  .badge-neutral {
    background: hsl(0 0% 96%);
    color:      hsl(0 0% 30%);
  }
</style>

<span class="badge badge-success">●  Paid</span>
<span class="badge badge-warning">●  Pending</span>
<span class="badge badge-destructive">●  Overdue</span>
<span class="badge badge-neutral">●  Draft</span>
```

Each badge uses *both* hue (category) and tone (legibility). The dot icon adds a non-color signal so colorblind users can still differentiate at a glance.

## Worked example: a primary action among secondary actions

```html
<style>
  .btn { padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 500; cursor: pointer; }
  .btn-primary {
    background: hsl(220 90% 50%);
    color: white;
    border: 0;
  }
  .btn-secondary {
    background: white;
    color: hsl(0 0% 27%);
    border: 1px solid hsl(0 0% 85%);
  }
  .btn-tertiary {
    background: transparent;
    color: hsl(0 0% 40%);
    border: 0;
  }
</style>

<button class="btn-tertiary">Cancel</button>
<button class="btn-secondary">Save draft</button>
<button class="btn-primary">Publish</button>
```

The primary uses full saturation + brand hue + white text. The secondary uses neutral-on-neutral (no color emphasis). The tertiary uses no surface, just dimmer text. The eye picks the primary instantly.

## Anti-patterns

- **Color as the only signal.** "Required fields are red." A red asterisk works in conjunction with the word "required" or `aria-required`. Color alone fails ~8% of male users (red-green color blindness) and anyone in glare or with degraded vision.
- **Brand color everywhere.** When every link, every heading, every active state, every illustration is the brand color, the brand color stops registering. Reserve it for moments.
- **Saturated everything.** A page of fully-saturated icons, badges, illustrations, and CTAs is a noise field. Pick which 1–3 things deserve full saturation; mute the rest.
- **Mid-tone trap.** Body text at hsl(0 0% 50%) (mid-grey) on white *just* clears WCAG AA at 18px. It feels elegant in design comps and tires real users in real lighting. Use neutral-700 or darker for body.
- **Decorative status colors.** A red border around a card that has no error, just because it "looks important." Status colors should only carry semantic meaning; otherwise users learn to dismiss them.
- **Ten-color palette.** Every product role gets its own bespoke color. Users can't learn the system; the brand fragments. A workable palette is small.

## Heuristics and accessibility

1. **Grayscale test.** Convert your design to grayscale. Hierarchy that survives is robust. If everything collapses to similar-grey, you were leaning on color alone.
2. **Contrast ratios.** Body text ≥ 4.5:1 (WCAG AA); large text ≥ 3:1; UI components and graphical objects ≥ 3:1. Use any contrast checker. Failing contrast is a hierarchy failure as well as an accessibility one — low-contrast text *literally* recedes from view.
3. **Color-blindness simulation.** View the design through a deuteranopia filter (Chrome DevTools → Rendering → Emulate vision deficiencies). Status that depends on red/green collapse here.
4. **The "first color you notice" check.** Ask someone to glance at the page for 1 second; what color do they remember? It should be your intended emphasis. If it's an accidental detail (a stock photo, an icon), the hierarchy is wrong.

## Trade-offs and warnings

- **Color is non-portable across cultures.** Red signals luck and prosperity in much of East Asia, danger and stop in much of the West. Don't assume your palette transfers.
- **Color is non-portable across themes.** A palette tuned for light theme often fails in dark — saturation perception inverts, contrast ratios change. Test both.
- **Color is non-portable across devices.** OLED vs. LCD vs. e-ink, calibrated vs. uncalibrated, sun vs. dim. Tone ladders are more portable than hue choices.
- **Color is non-portable across abilities.** Build a hierarchy that works in grayscale; add color *on top* of it as enhancement, not as the substrate.

## Related principles

- **`hierarchy`** — parent skill. Read it for full framing.
- **`hierarchy-typographic`** and **`hierarchy-spatial`** — color works best as a third axis on top of these.
- **`color`** — the broader principle of color-as-language; cultural meaning, accessibility.
- **`red-effect`** — red specifically; reserve for genuine urgency.
- **`signal-to-noise-ratio`** — too many colors reduces SNR; restraint multiplies the signal.
- **`accessibility`** (process plugin) — color decisions are accessibility decisions; build for both.
