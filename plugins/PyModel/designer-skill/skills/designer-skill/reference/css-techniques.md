# CSS Techniques

Practical, modern CSS patterns for writing and fixing real stylesheets — the implementation cookbook behind the design decisions. Where `design-principles.md` and `engineering-and-performance.md` say *what* the type ramp, spacing, contrast, and responsive behavior should be, this file says *how* to express it in idiomatic CSS: resets, box-sizing inheritance, centering, `aspect-ratio`, `:is()`/`:not()`, logical properties, container queries, `:has()`, `@layer`, `clamp()`, and more. Reach for it whenever you apply CSS fixes to a site.

Baseline labels (Widely / Newly / Limited available) are a browser-compatibility signal only — still verify accessibility, keyboard behavior, motion preferences, and contrast separately. Source: AllThingsSmitty/css-protips + curated Baseline additions (web.dev/MDN).

Each entry is a self-contained pattern — apply the one that fits the problem in front of you.

---

### Use a CSS Reset

CSS resets help enforce style consistency across different browsers with a clean slate for styling elements. There are plenty of reset patterns to find, or you can use a more simplified reset approach:

```css
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}
```

Now elements will be stripped of margins and padding, and `box-sizing` lets you manage layouts with the CSS box model.

#### [Demo](https://codepen.io/AllThingsSmitty/pen/kkrkLL)

> [!TIP]
> If you follow the [Inherit `box-sizing`](#inherit-box-sizing) tip below you might opt to not include the `box-sizing` property in your CSS reset.


### Inherit `box-sizing`

Let `box-sizing` be inherited from `html`:

```css
html {
  box-sizing: border-box;
}

*,
*::before,
*::after {
  box-sizing: inherit;
}
```

This makes it easier to change `box-sizing` in plugins or other components that leverage other behavior.

#### [Demo](https://css-tricks.com/inheriting-box-sizing-probably-slightly-better-best-practice/)


### Use `all: unset` Carefully for Component Resets

When resetting an element's properties, you can reset each property individually:

```css
button {
  background: none;
  border: none;
  color: inherit;
  font: inherit;
  outline: none;
  padding: 0;
}
```

Or use the `all` shorthand with `unset`. **`all: unset` resets almost every property** (except
`unicode-bidi`, `direction`, and custom properties) — inherited props revert to inherit, others to
initial. A `<button>` becomes `display: inline` and loses its native box, so always restore layout
and focus after unsetting.

```css
button.reset {
  all: unset;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

button.reset:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: 0.15em;
}
```

> [!TIP]
> To restore the user-agent stylesheet instead of a blank slate, use `all: revert` — see
> [Reset intent: `unset` vs `revert`](#reset-intent-unset-vs-revert) in the Modern CSS section.


### Use `:not()` to Apply/Unapply Borders on Navigation

Instead of putting on the border...

```css
/* add border */
.nav li {
  border-right: 1px solid #666;
}
```

...and then taking it off the last element...

```css
/* remove border */
.nav li:last-child {
  border-right: none;
}
```

...use the `:not()` pseudo-class to only apply to the elements you want:

```css
.nav li:not(:last-child) {
  border-right: 1px solid #666;
}
```

Here, the CSS selector is read as a human would describe it.

#### [Demo](https://codepen.io/AllThingsSmitty/pen/LkymvO)


### Check if Font Is Installed Locally

You can check if a font is installed locally before fetching it remotely, which is a good performance tip, too.

```css
@font-face {
  font-family: "Dank Mono";
  src:
    /* Full name */ local("Dank Mono"), /* Postscript name */ local("Dank Mono"),
    /* Otherwise, download it! */ url("//...a.server/fonts/DankMono.woff");
}

code {
  font-family: "Dank Mono", system-ui-monospace;
}
```

H/T to Adam Argyle for sharing this protip and [demo](https://codepen.io/argyleink/pen/VwYJpgR).


### Add `line-height` to `body`

You don't need to add `line-height` to each `<p>`, `<h*>`, _et al_. separately. Instead, add it to `body`:

```css
body {
  line-height: 1.5;
}
```

This way textual elements can inherit from `body` easily.

#### [Demo](https://codepen.io/AllThingsSmitty/pen/VjbdYd)


### Set `:focus` for Form Elements

Sighted keyboard users rely on focus to determine where keyboard events go in the page. Make focus for form elements stand out and consistent than a browser's default implementation:

```css
a:focus,
button:focus,
input:focus,
select:focus,
textarea:focus {
  box-shadow: none;
  outline: #000 dotted 2px;
  outline-offset: 0.05em;
}
```

#### [Demo](https://codepen.io/AllThingsSmitty/pen/ePzoOP/)

> [!TIP]
> In modern code, prefer [`:focus-visible`](#prefer-focus-visible-over-focus) so keyboard users keep
> a clear focus ring without showing focus styles on every mouse click.


### Vertically-Center Anything

Prefer **Grid** with a dynamic viewport unit on mobile — `100vh` maps to the large viewport and can
misbehave when browser toolbars show/hide. With logical properties, use `100dvb` (dynamic viewport block).

```css
.center-page {
  min-block-size: 100dvb;
  display: grid;
  place-items: center;
}
```

Flexbox works the same way once the parent has a defined block size:

```css
html,
body {
  min-block-size: 100%;
}

body {
  align-items: center;
  display: flex;
  justify-content: center;
}
```

> [!NOTE]
> Legacy pattern: `height: 100vh` + `place-items: center` still appears in older tutorials. Prefer
> `dvh`/`dvb`/`svh`/`lvh` for full-viewport layouts on mobile — see MDN on viewport-relative lengths.

> [!TIP]
> Want to center something else? CSS-Tricks has [a nice write-up](https://css-tricks.com/centering-css-complete-guide/) on doing all of that.

#### [Demo](https://codepen.io/AllThingsSmitty/pen/GqmGqZ)


### Use `aspect-ratio` Instead of Height/Width

The `aspect-ratio` property allows you to easily size elements and maintain consistent width-to-height ratio. This is incredibly useful in responsive web design to prevent layout shift. Use `object-fit` with it to prevent disrupting the layout if the height/width values of images changes.

```css
img {
  aspect-ratio: 16 / 9; /* width / height */
  object-fit: cover;
}
```

Learn more about the `aspect-ratio` property in this [web.dev post](https://web.dev/articles/aspect-ratio).

#### [Demo](https://codepen.io/AllThingsSmitty/pen/MWxwoNx/)


### Comma-Separated Lists

Make list items look like a real, comma-separated list:

```css
ul > li:not(:last-child)::after {
  content: ",";
}
```

Use the `:not()` pseudo-class and no comma will be added to the last item.

> [!NOTE]
> This tip may not be ideal for accessibility, specifically screen readers. And copy/paste from the browser doesn't work with CSS-generated content. Proceed with caution.


### Select Items Using Negative `nth-child`

Use negative `nth-child` in CSS to select items 1 through n.

```css
li {
  display: none;
}

/* select items 1 through 3 and display them */
li:nth-child(-n + 3) {
  display: block;
}
```

Or, since you've already learned a little about [using `:not()`](#use-not-to-applyunapply-borders-on-navigation), try:

```css
/* select all items except the first 3 and display them */
li:not(:nth-child(-n + 3)) {
  display: block;
}
```

#### [Demo](https://codepen.io/AllThingsSmitty/pen/WxjKZp)


### Use SVG for Icons

There's no reason not to use SVG for icons:

```css
.logo {
  background: url("logo.svg");
}
```

SVG scales well for all resolution types and is supported in all browsers [back to IE9](http://caniuse.com/#search=svg). Ditch your .png, .jpg, or .gif-jif-whatev files.

> [!NOTE]
> If you have SVG icon-only buttons for sighted users and the SVG fails to load, this will help maintain accessibility:

```css
.no-svg .icon-only::after {
  content: attr(aria-label);
}
```


### Use the "Lobotomized Owl" Selector

It may have a strange name but using the universal selector (`*`) with the adjacent sibling selector (`+`) can provide a powerful CSS capability:

```css
* + * {
  margin-top: 1.5em;
}
```

In this example, all elements in the flow of the document that follow other elements will receive `margin-top: 1.5em`.

> [!TIP]
> For more on the "lobotomized owl" selector, read [Heydon Pickering's post](http://alistapart.com/article/axiomatic-css-and-lobotomized-owls) on _A List Apart_.

#### [Demo](https://codepen.io/AllThingsSmitty/pen/grRvWq)


### Use `max-height` for Pure CSS Sliders

Implement CSS-only sliders using `max-height` with overflow hidden:

```css
.slider {
  max-height: 200px;
  overflow-y: hidden;
  width: 300px;
}

.slider:hover {
  max-height: 600px;
  overflow-y: scroll;
}
```

The element expands to the `max-height` value on hover and the slider displays as a result of the overflow.


### Equal-Width Table Cells

Tables can be a pain to work with. Try using `table-layout: fixed` to keep cells at equal width:

```css
.calendar {
  table-layout: fixed;
}
```

Pain-free table layouts.

#### [Demo](https://codepen.io/AllThingsSmitty/pen/jALALm)


### Get Rid of Margin Hacks With Flexbox

When working with column gutters you can get rid of `nth-`, `first-`, and `last-child` hacks by using flexbox's `space-between` property:

```css
.list {
  display: flex;
  justify-content: space-between;
}

.list .person {
  flex-basis: 23%;
}
```

Now column gutters always appear evenly-spaced.


### Use Attribute Selectors with Empty Links

Display links when the `<a>` element has no text value but the `href` attribute has a link:

```css
a[href^="http"]:empty::before {
  content: attr(href);
}
```

That's really convenient.

#### [Demo](https://codepen.io/AllThingsSmitty/pen/zBzXRx)

> [!NOTE]
> This tip may not be ideal for accessibility, specifically screen readers. And copy/paste from the browser doesn't work with CSS-generated content. Proceed with caution.


### Control Specificity Better with `:is()`

The `:is()` pseudo-class is used to target multiple selectors at once, reducing redundancy and enhancing code readability. This is incredibly useful for writing large selectors in a more compact form.

```css
:is(section, article, aside, nav) :is(h1, h2, h3, h4, h5, h6) {
  color: green;
}
```

The above ruleset is equivalent to the following number selector rules...

```css
section h1,
section h2,
section h3,
section h4,
section h5,
section h6,
article h1,
article h2,
article h3,
article h4,
article h5,
article h6,
aside h1,
aside h2,
aside h3,
aside h4,
aside h5,
aside h6,
nav h1,
nav h2,
nav h3,
nav h4,
nav h5,
nav h6 {
  color: green;
}
```

#### [Demo](https://codepen.io/AllThingsSmitty/pen/rNRVxdx)


### Style "Default" Links

Add a style for "default" links:

```css
a[href]:not([class]) {
  color: #008000;
  text-decoration: underline;
}
```

Now links that are inserted via a CMS, which don't usually have a `class` attribute, will have a distinction without generically affecting the cascade.


### Intrinsic Ratio Boxes (legacy fallback)

> [!NOTE]
> **Legacy only.** Prefer [`aspect-ratio`](#use-aspect-ratio-instead-of-heightwidth) (Baseline Widely
> available) for new code. Keep this padding hack only when you must support very old browsers or
> need a pattern that predates `aspect-ratio`.

To create a box with an intrinsic ratio, apply top or bottom padding to a div:

```css
.container {
  height: 0;
  padding-bottom: 20%;
  position: relative;
}

.container div {
  border: 2px dashed #ddd;
  height: 100%;
  left: 0;
  position: absolute;
  top: 0;
  width: 100%;
}
```

Using 20% for padding makes the height of the box equal to 20% of its width. No matter the width of the viewport, the child div will keep its aspect ratio (100% / 20% = 5:1).

#### [Demo](https://codepen.io/AllThingsSmitty/pen/jALZvE)


### Style Broken Images

Make broken images more aesthetically-pleasing with a little bit of CSS:

```css
img {
  display: block;
  font-family: sans-serif;
  font-weight: 300;
  height: auto;
  line-height: 2;
  position: relative;
  text-align: center;
  width: 100%;
}
```

Now add pseudo-elements rules to display a user message and URL reference of the broken image:

```css
img::before {
  content: "We're sorry, the image below is broken :(";
  display: block;
  margin-bottom: 10px;
}

img::after {
  content: "(url: " attr(src) ")";
  display: block;
  font-size: 12px;
}
```

> [!TIP]
> Learn more about styling for this pattern in [Ire Aderinokun's post](http://bitsofco.de/styling-broken-images/).


### Use `rem` for Global Sizing; Use `em` for Local Sizing

After setting the base font size at the root (`html { font-size: 100%; }`), set the font size for textual elements to `em`:

```css
h2 {
  font-size: 2em;
}

p {
  font-size: 1em;
}
```

Then set the font-size for modules to `rem`:

```css
article {
  font-size: 1.25rem;
}

aside .module {
  font-size: 0.9rem;
}
```

Now each module becomes compartmentalized and easier to style, more maintainable, and flexible.


### Hide Autoplay Videos That Aren't Muted

This is a great trick for a custom user stylesheet. Avoid overloading a user with sound from a video that autoplays when the page is loaded. If the sound isn't muted, don't show the video:

```css
video[autoplay]:not([muted]) {
  display: none;
}
```

Once again, we're taking advantage of using the [`:not()`](#use-not-to-applyunapply-borders-on-navigation) pseudo-class.


### Use `:root` for Flexible Type

The type font size in a responsive layout should be able to adjust with each viewport. You can calculate the font size based on the viewport height and width using `:root`:

```css
:root {
  font-size: calc(1vw + 1vh + 0.5vmin);
}
```

Now you can utilize the `root em` unit based on the value calculated by `:root`:

```css
body {
  font: 1rem/1.6 sans-serif;
}
```

#### [Demo](https://codepen.io/AllThingsSmitty/pen/XKgOkR)


### Set `font-size` on Form Elements for a Better Mobile Experience

To avoid mobile browsers (iOS Safari, _et al_.) from zooming in on HTML form elements when a `<select>` drop-down is tapped, add `font-size` to the selector rule:

```css
input[type="text"],
input[type="number"],
select,
textarea {
  font-size: 16px;
}
```


### Use Pointer Events to Control Mouse Events

[Pointer events](https://developer.mozilla.org/en-US/docs/Web/CSS/pointer-events) control how pointer
input hits an element. To block clicks on a disabled-looking control:

```css
button:disabled {
  opacity: 0.5;
  pointer-events: none;
}
```

> [!WARNING]
> `pointer-events: none` blocks pointer interaction, **not all interaction**. Elements with
> `pointer-events: none` can still receive keyboard focus through Tab navigation. Do not use it as
> your only “disabled” behavior for interactive controls. Prefer the native `disabled` attribute
> where available.


### Set `display: none` on Line Breaks Used as Spacing

As [Harry Roberts pointed out](https://twitter.com/csswizardry/status/1170835532584235008), this can help prevent CMS users from using extra line breaks for spacing:

```css
br + br {
  display: none;
}
```


### Use `:empty` to Hide Empty HTML Elements

If you have HTML elements that are empty, i.e., the content has yet to be set either by a CMS or dynamically injected (e.g., `<p class="error-message"></p>`) and it's creating unwanted space on your layout, use the `:empty` pseudo-class to hide the element on the layout.

```css
:empty {
  display: none;
}
```

> [!NOTE]
> Keep in mind that elements with whitespace aren't considered empty, e.g., `<p class="error-message"> </p>`.


## Modern CSS (Baseline 2024–2026)

The tips above are evergreen. These are newer **native features that retire old hacks**. Each entry
is bucketed by [MDN Baseline](https://developer.mozilla.org/en-US/docs/Glossary/Baseline/Compatibility)
availability — confirm your project's Browserslist floor on [caniuse](https://caniuse.com) before
shipping.

> Baseline is a **browser-compatibility signal only**. It does not replace accessibility, usability,
> performance, keyboard testing, or project-specific QA.

### Shipping Modern CSS Safely

1. Pick a Baseline target or explicit Browserslist target.
2. Treat **Baseline Widely available** features as normal production CSS.
3. Treat **Baseline Newly available** features as production-ready only if your audience's browser
   floor supports them.
4. Treat **Limited availability** features as progressive enhancement only.
5. Use `@supports` for layout-changing enhancements.
6. Test accessibility, motion preferences, keyboard behavior, and contrast separately from browser
   support.

Baseline can be enforced through project tooling (Browserslist, ESLint CSS plugins) — see
[web.dev/baseline](https://web.dev/baseline).

> [!TIP]
> Gate layout-changing enhancements behind a feature query when the fallback must work:
> ```css
> @supports (anchor-name: --x) {
>   /* enhanced layout */
> }
> ```


### Baseline widely available (normal production CSS)

Safe modern defaults for current evergreen targets: `:has()`, `@container`, native CSS nesting,
`@layer`, `subgrid`, `color-mix()`, logical properties, `:focus-visible`, `clamp()`, `aspect-ratio`,
and `:is()`.

#### Select a Parent/Sibling with `:has()`

The relational pseudo-class matches an element by its descendants or following siblings — the
long-wished-for "parent selector." Replaces JS class-toggling for whole families of state.

```css
/* a card that contains an image gets a different layout */
.card:has(> img) {
  grid-template-columns: 120px 1fr;
}

/* style a field when its input is focused or invalid — no JS */
.field:has(input:focus-visible) {
  outline: 2px solid;
}
.field:has(input:user-invalid) {
  color: #b00;
}
```

#### Component-Level Responsive with Container Queries

Media queries respond to the viewport; container queries respond to the **parent's** size, so a
component adapts wherever you drop it. Set `container-type` on the wrapper, then `@container`.

```css
.wrapper {
  container-type: inline-size;
}

.card {
  grid-template-columns: 1fr;
}

@container (width > 400px) {
  .card {
    grid-template-columns: auto 1fr;
  }
}
```

#### Native CSS Nesting

Nest selectors without Sass. Use `&` to make the parent reference explicit.

```css
.card {
  padding: 1rem;

  & .title {
    font-weight: 600;
  }

  &:hover {
    background: #f6f6f6;
  }
}
```

#### Tame Specificity with `@layer`

Cascade layers declare order of precedence up front — later layers always win regardless of selector
specificity. Ends the `!important` arms race between reset, base, components, and utilities.

```css
@layer reset, base, components, utilities;

@layer base {
  a {
    color: blue;
  }
}

@layer utilities {
  .text-red {
    color: red; /* wins even though it's less specific */
  }
}
```

#### Align Nested Grids with `subgrid`

A grid item can inherit its parent's tracks with `subgrid`, so children of separate cards line up on
a shared grid — no magic numbers.

```css
.cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.card {
  display: grid;
  grid-row: span 3;
  grid-template-rows: subgrid;
}
```

#### Mix Colors with `color-mix()`

Compute tints, shades, and translucent variants in the browser — no preprocessor — and it works with
custom properties. Prefer a perceptual space like `oklab`/`oklch`.

```css
.btn {
  background: var(--brand);
}

.btn:hover {
  background: color-mix(in oklab, var(--brand) 85%, black);
}

.btn--ghost {
  background: color-mix(in srgb, var(--brand) 12%, transparent);
}
```

#### Use Logical Properties for Flow-Relative Layout

`*-inline`/`*-block` and `inset` follow the writing mode, so the same CSS mirrors correctly for RTL
and vertical text. Reach for these over `left`/`right`/`margin-left`.

```css
.box {
  margin-inline: auto;
  padding-block: 1rem;
}

.overlay {
  position: absolute;
  inset: 0; /* top/right/bottom/left: 0 */
}
```

#### Prefer `:focus-visible` over `:focus`

`:focus-visible` shows the focus ring only when the browser judges it useful (keyboard navigation),
so you keep accessibility without a ring on every mouse click. A modern upgrade to the
[`:focus` form-element tip](#set-focus-for-form-elements) above.

```css
:focus:not(:focus-visible) {
  outline: none;
}

:focus-visible {
  outline: #000 dotted 2px;
  outline-offset: 0.05em;
}
```

#### Fluid Type with `clamp()`

`clamp(MIN, PREFERRED, MAX)` scales a value with the viewport but stays within bounds — a robust,
readable replacement for the [`:root { calc(1vw + 1vh …) }` trick](#use-root-for-flexible-type)
above, which has no floor or ceiling.

```css
h1 {
  font-size: clamp(1.75rem, 1rem + 3vw, 3rem);
}

.section {
  padding-block: clamp(2rem, 5vw, 5rem);
}
```


### Baseline newly available (verify your support floor)

Production-ready only when your browser floor supports them: `text-wrap`, `light-dark()`, `@scope`,
`@starting-style`, anchor positioning, and `contrast-color()`.

#### Better Wrapping with `text-wrap`

`balance` evens out the lines of short blocks like headings; `pretty` prevents orphans and ragged
last lines in paragraphs. One line, no `<br>` babysitting.

```css
h1,
h2,
.hero-title {
  text-wrap: balance;
}

.prose p {
  text-wrap: pretty;
}
```

> [!NOTE]
> Baseline **Newly available** (2024). `pretty` degrades to normal wrapping where unsupported — safe
> progressive enhancement. Verify Firefox/Safari floors if `pretty` is required, not optional.

#### One-Declaration Theming with `light-dark()`

Return a different value per color scheme in a single declaration — once you opt the root into both
schemes. No duplicated `prefers-color-scheme` block for simple value swaps.

```css
:root {
  color-scheme: light dark;
}

body {
  background: light-dark(#fff, #111);
  color: light-dark(#111, #eee);
}
```

> [!NOTE]
> Baseline **Newly available** (2024). Solid in current Chrome/Safari/Firefox — verify your support
> floor before dropping `prefers-color-scheme` fallbacks.

#### Scope Styles with `@scope`

Limit a ruleset to a subtree — and optionally stop at an inner boundary — without specificity hacks
or BEM-style naming. Useful for component or CMS-injected markup.

```css
@scope (.card) to (.card__content) {
  img {
    border-radius: 8px; /* only cards, and not inside .card__content */
  }
}
```

> [!NOTE]
> Baseline **Newly available** (2025).

#### Flash-Free Enter Transitions with `@starting-style`

Defines the "before-open" styles an element animates **from** when it's first rendered (including
`display: none → block`, popovers, and dialogs), so entrances don't snap into place.

```css
.toast {
  transition: opacity 0.3s, translate 0.3s;
  opacity: 1;
  translate: 0 0;
}

@starting-style {
  .toast {
    opacity: 0;
    translate: 0 1rem;
  }
}
```

> [!NOTE]
> Baseline **Newly available** (2024). To transition an element that also toggles `display`, set
> `transition-behavior: allow-discrete`.

#### Tooltips & Popovers: Anchor Positioning — Limited availability

Anchor positioning is still **Limited availability** (not yet Baseline — Chromium ships it, Firefox
and Safari lag per MDN). Treat it as progressive enhancement: ship a normal positioning fallback
first, then enhance with `@supports`.

```css
.trigger {
  anchor-name: --tip;
}

.tooltip {
  position: fixed;
  position-anchor: --tip;
  position-area: top; /* sit above the trigger */
  position-try-fallbacks: flip-block; /* flip below if it would clip */
}

@supports not (anchor-name: --tip) {
  .tooltip {
    /* fallback: absolute positioning, JS coords, or static placement */
  }
}
```

> [!NOTE]
> While only Limited availability, anchor positioning still has known cross-browser bugs and missing
> pieces (web-features maintainers tracked it as effectively "beta"; Firefox shipped it later/flagged).
> The `@supports` fallback above is load-bearing, not decorative — keep a working non-anchored layout.

#### Automatic Black/White Contrast with `contrast-color()`

Picks **black or white** — whichever contrasts more with the given color — as a foreground. **Not**
the older `color-contrast()` you'll still see in blog posts.

```css
.badge {
  background: var(--brand);
  color: white; /* fallback for unsupported browsers */
}

@supports (color: contrast-color(red)) {
  .badge {
    color: contrast-color(var(--brand));
  }
}
```

> [!NOTE]
> Baseline **Newly available** (April 2026). Gate behind `@supports` for older floors.

> [!WARNING]
> Useful, but not magic: it only returns black or white, so a mid-tone background (e.g. `#2277d3`)
> can still fail WCAG AA for small text. Use it with light/dark design tokens and still test contrast.


### Limited availability (progressive enhancement only)

MDN marks these as **Limited availability** or Interop still lists them as active focus areas. Ship
a working baseline first; enhance behind `@supports`.

#### Theme Native Controls with `accent-color`

Recolor checkboxes, radios, range sliders, and progress bars to your brand in one line — keeping the
native, accessible widgets.

```css
:root {
  accent-color: rebeccapurple;
}
```

> [!NOTE]
> **Limited availability** on MDN as of 2026 — verify engine support before relying on it for brand
> theming; provide a fallback palette for unsupported browsers.

#### Scroll-Driven Animations (no scroll listeners)

Drive an animation by scroll progress (`scroll()`) or an element's visibility (`view()`) — off the
main thread, replacing `addEventListener('scroll', …)`. Interop 2026 still lists scroll-driven
animations as an active interoperability focus area.

```css
.reveal {
  animation: fade-in linear both;
  animation-timeline: view();
  animation-range: entry 0% cover 40%;
}

@keyframes fade-in {
  from {
    opacity: 0;
    translate: 0 20px;
  }
  to {
    opacity: 1;
  }
}

/* always give motion an opt-out */
@media (prefers-reduced-motion: reduce) {
  .reveal {
    animation: none;
  }
}
```

> [!NOTE]
> Gate behind `@supports (animation-timeline: view())` and ship static content as the default.

#### Auto-Sizing Inputs with `field-sizing`

`field-sizing: content` lets inputs and textareas grow with their content instead of staying a fixed
size — the autosize-textarea JS hack, in one line.

```css
textarea,
input {
  field-sizing: content;
}
```

> [!NOTE]
> **Limited availability** on MDN as of 2026. Keep a fixed `min-height` / JS autosize fallback.


### Retire / modernize older tips

Several evergreen tips above predate features that now do the job natively. The originals stay for
context; reach for these in new code. Availability is called out where it bites — the `height: auto`
animation in particular is **Chrome-only** as of 2026.

#### Drop the padding-hack ratio box → `aspect-ratio`

The [Intrinsic Ratio Boxes](#intrinsic-ratio-boxes-legacy-fallback) padding trick needs a wrapper and absolute
positioning. [`aspect-ratio`](#use-aspect-ratio-instead-of-heightwidth) (covered above) does it on one
element, no wrapper.

```css
.embed { aspect-ratio: 16 / 9; } /* replaces height: 0 + padding-bottom: 56.25% */
```

#### Smooth disclosure → animate grid rows, not `max-height`

[`max-height` sliders](#use-max-height-for-pure-css-sliders) animate against a *guessed* ceiling, so
the transition wastes time crossing the empty gap between the real height and the max. Animate
`grid-template-rows` from `0fr` to `1fr` instead — widely supported, no magic number.

```css
.disclosure {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 0.3s ease;
}
.disclosure.is-open { grid-template-rows: 1fr; }
.disclosure > * { overflow: hidden; } /* min-height: 0 so the row can collapse */
```

> [!NOTE]
> A true `height: 0 → auto` transition needs `interpolate-size: allow-keywords` (or `calc-size(auto)`),
> which is **Chrome 129+ only** as of 2026 — not Baseline. Use it as progressive enhancement; other
> browsers just snap. `transition-behavior: allow-discrete` alone will **not** interpolate `height` —
> it only governs discrete properties like `display`.

#### Even columns → `auto-fit` grid, not `space-between` + `%`

[`justify-content: space-between` with `flex-basis: 23%`](#get-rid-of-margin-hacks-with-flexbox) snaps
a partly-filled last row to the edges (e.g. 2 items in a 4-up row fly to opposite ends). An `auto-fit`
grid keeps every row aligned, complete or not.

```css
.list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}
```

#### Reset intent: `unset` vs `revert`

These aren't interchangeable — pick by what you want. [`all: unset`](#use-all-unset-carefully-for-component-resets)
gives a clean slate but sends non-inherited props to their *initial* values, so a `<button>` becomes
`display: inline` and loses its box. `all: revert` rolls back to the user-agent stylesheet — which
keeps the button's box **and** its native border/background, so it's "undo my styles," not "strip to
nothing."

```css
button { all: unset; display: inline-block; } /* clean slate, then fix the box */
button { all: revert; }                        /* restore the native button look */
```

#### Don't `local()` brand fonts

The [local-font check](#check-if-font-is-installed-locally) can match a *stale* user-installed copy
with different metrics, causing layout shift (CLS). For brand type, self-host an optimized `.woff2`
with `font-display: swap` and a metric-matching `size-adjust` descriptor; reserve `local()` for system
fonts via a `system-ui` stack.

#### Scope the owl → `.flow`

A global [`* + *`](#use-the-lobotomized-owl-selector) leaks margins into third-party widgets and grid
children. Scope it to a flow utility (and use a logical property while you're there).

```css
.flow > * + * { margin-block-start: 1.5em; }
```

#### Recolorable icons → `mask`, not `background`

[`background: url(icon.svg)`](#use-svg-for-icons) can't be recolored from CSS. For monochrome icons,
`mask` the SVG and paint with `currentColor` so it inherits text color. (Keep `background`/inline SVG
for multicolor art.)

```css
.icon {
  width: 24px;
  height: 24px;
  background-color: currentColor; /* the icon's color */
  mask: url("icon.svg") no-repeat center / contain;
}
```

#### Two quick selector upgrades

```css
/* scoped nth-child: count only .item children, ignoring other siblings */
li:nth-child(-n + 3 of .item) { display: block; }

/* zero-specificity default links — trivial to override in components later */
:where(a[href]:not([class])) {
  color: #008000;
  text-decoration: underline;
}
```



---

<!-- Provenance: derived from AllThingsSmitty/css-protips (MIT) @ commit e95123993037bbcd1bd97170cfa02087155c3690.
     The "Modern CSS (Baseline 2024–2026)" section and several in-place modernizations (all: unset reset,
     100dvh centering, pointer-events a11y note) are local additions curated from web.dev Baseline / MDN /
     Interop 2026 — not upstream. Preserve them on any re-sync of the upstream mirror. -->
