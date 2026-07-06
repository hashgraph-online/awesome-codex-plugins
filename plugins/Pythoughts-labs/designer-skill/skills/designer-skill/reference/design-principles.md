# Design Principles

The aesthetic-agnostic visual foundation. These rules hold whether the brief is brutalist, editorial, luxury, dark-tech, or consumer-warm. Concrete palettes, named token systems, and worked examples live in aesthetic-systems.md; motion, easing, hover transforms, and live-mode params live in motion-and-interaction.md. This file is the neutral baseline every aesthetic builds on.

The bar for any decision: pick from a defined set, commit to it, and apply it everywhere. Arbitrary values are the tell.

---

## Typography

Type carries most of the information on the page. Replace invisible defaults (Inter, Roboto, Arial, Open Sans, system fallback at a flat scale) with type that reflects the brand and scales with intentional contrast.

### Type scale and ratio

Five sizes cover most needs. Pick **one** ratio and commit; the common failure is too many sizes too close together (14px, 15px, 16px, 18px), which produces muddy hierarchy.

| Role | Size | Use |
|------|------|-----|
| xs | 0.75rem | Captions, legal |
| sm | 0.875rem | Secondary UI, metadata |
| base | 1rem | Body |
| lg | 1.25-1.5rem | Subheadings, lead |
| xl+ | 2-4rem | Headlines, hero |

- **Ratios:** 1.25 (major third), 1.333 (perfect fourth), 1.5 (perfect fifth). Keep **≥1.25 between steps**; a flat 1.1× scale reads as uncommitted.
- **Product UI** runs tighter: a **1.125-1.2** ratio on closely-spaced steps, on a fixed `rem` scale (no fluid `clamp()` in dense app UI; users view at consistent DPI, and a heading that shrinks in a sidebar looks worse).
- **Bolder needs drama:** 3×-5× size jumps, not 1.5×.
- **Fluid headings** use `clamp(min, preferred, max)`; bound it `max ≤ 2.5 × min`. Cap hero/display at **≤6rem (~96px)**; 8-11rem reads comically loud. Keep body text fixed even on marketing pages.

### Families and weights

- **Cap families at 3** (display + body + optional mono). More than 3 reads as indecision; more than 2-3 is almost always a mess.
- **Cap weights at 3-4** (Regular 400, Medium 500, SemiBold 600, Bold 700 is plenty). Load only the weights you use. Stop shipping only 400 + 700; intermediate weights create nuanced hierarchy.
- **Pair on a contrast axis:** serif + sans, geometric + humanist, condensed + wide. Never pair two similar-but-not-identical families (two geometric sans-serifs). One family in multiple weights beats two competing typefaces.
- **Bolder pairs extremes:** 900 with 200, not 600 with 400.
- **Emphasis stays in-family:** italic or bold of the *same* font. Injecting a random serif word into a sans headline is an amateur tell.
- **Default sans with character:** Geist, Outfit, Cabinet Grotesk, Satoshi. Inter is discouraged as a default (acceptable only for explicit neutral/Linear-style or public-sector/accessibility briefs). Serif is **very discouraged as default**; reach for it only when the brief names a serif or the aesthetic is genuinely editorial/luxury/heritage with an articulable reason. `Fraunces` and `Instrument_Serif` are banned defaults.

### Tracking, measure, line-height

- **Tracking scales inversely with size.** Negative tracking on large display; floor at **≥ -0.04em** (default -0.05 to -0.085em makes letters touch; -0.02 to -0.03em is plenty for a tight grotesque). Add **+0.05em to +0.12em** to short all-caps labels and eyebrows; capitals sit too close at default spacing.
- **Measure:** 45-75 characters for body (ideal 65-75ch). Set `max-width` in `ch` units. Data and compact UI can run denser; tables at 120ch+ are fine.
- **Line-height:** tighter for headings (1.1-1.2), looser for body (1.5-1.7). It scales inversely with line length: narrow columns want tighter leading, wide columns want more.
- **Light-on-dark loses perceived weight on three axes; fix all three:** bump line-height **+0.05 to +0.1**, add letter-spacing **+0.01 to +0.02em**, and optionally step body weight up one notch (e.g. 350 instead of 400). Body on dark sits comfortably at line-height **1.65-1.8**, measure 65-75ch.
- **Rags:** use `text-wrap: balance` on h1-h3, `text-wrap: pretty` on long prose to kill orphans. Italic display words with descenders (`y g j p q`) clip at `leading-none`; use `leading-[1.1]` minimum plus `pb-1`/`mb-1` reserve.
- **Casing:** sentence case for headers, not Title Case on every header. Vary all-caps subheaders (lowercase italics, small-caps). No all-caps body copy. Tracked uppercase is for short system markers only.
- **Always:** body ≥16px / 1rem; `rem` not `px` (respects user zoom); never disable zoom (`user-scalable=no`). Use `font-variant-numeric: tabular-nums` for data and numbers that align in columns.
- **Vertical rhythm:** line-height is the base unit for all vertical spacing. Body at line-height 1.5 on 16px (= 24px) means spacing in multiples of 24px. Paragraph rhythm: space-between **OR** first-line indent, never both.

### Hard floors (checkable, not judgment calls)

Mechanical pass/fail thresholds. Everything above is judgment; these are not.

- **Line-height ≥1.3× on any multi-line text.** 1.5-1.7 stays the body target; below 1.3 fails outright.
- **Body text never below 12px.** Below 12px is an outright fail; 14px is the minimum for body content, 16px the ideal.
- **Letter-spacing on body caps at +0.05em.** Wider tracking disrupts character groupings; wide tracking is for short uppercase labels only.
- **Never skip heading levels.** h1 → h3 with no h2 breaks the screen-reader outline.
- **No `text-align: justify` without `hyphens: auto`.** Unhyphenated justification creates rivers; default body to left-align.
- **Line length hard ceiling ~80ch.** 65-75ch stays the ideal; text wrapping beyond ~80ch fails.

---

## Spacing and rhythm

Space is the most underused design tool. Layout problems are often the root cause of an interface feeling "off" even when color and type are fine.

- **Use a 4pt base scale:** `4, 8, 12, 16, 24, 32, 48, 64, 96px`. Prefer it over 8pt; 8pt is too coarse and you will constantly want 12px between 8 and 16. **Never use values outside the scale** (no random 13px gaps). Pull every gap from the set.
- **Rhythm comes from variety, never equal spacing:** tight grouping for related elements (**8-12px** between siblings), generous separation between distinct sections (**48-96px**), varied gaps within a section (not every row needs the same gap). Marketing pages double the spacing; dense data dashboards can pack tighter. When in doubt on a marketing page, double the whitespace. **Monotony self-check:** among 10+ gaps on a page, one value covering >60% of them with ≤3 unique values total = no rhythm; rework.
- **Hard floors — checkable, not judgment calls:** text inside any bordered, outlined, or colored container gets **≥8px padding, ideally 12-16px**. Two failure shapes to catch: the element's own padding too low for its font size, and a near-zero-padding wrapper whose text children land flush against a visible boundary. Body paragraphs sit **≥16px (ideally 24-32px)** from the viewport edge, via a container or `max-width` + auto margins.
- **Bolder** uses dramatic **100-200px** gaps, not 20-40px. **Quieter** evens out extreme variations into consistent rhythm.
- Use `gap` for sibling spacing instead of margins (no margin-collapse hacks). Use `clamp()` for fluid spacing that breathes on large screens.
- **Optical vertical padding:** mathematically equal top/bottom looks bottom-heavy; bottom padding often needs to be slightly larger.

---

## Color and contrast

More color ≠ better. Strategic color beats rainbow vomit. Use OKLCH, not HSL: it is perceptually uniform, so equal lightness steps *look* equal. To build a ramp, hold chroma and hue roughly constant and vary lightness, but **reduce chroma as you approach white or black** so it does not go garish.

### Building a palette

| Role | Purpose | Shades |
|------|---------|--------|
| Primary | Brand, CTAs, key actions | 1 color, 3-5 |
| Neutral | Text, backgrounds, borders | 9-11 scale |
| Semantic | Success, error, warning, info | 4 colors, 2-3 each |
| Surface | Cards, modals, overlays | 2-3 elevation levels |

- **Choose 2-4 colors max beyond neutrals.** Skip secondary/tertiary unless you need them; most apps work with one accent. Use **exactly one** accent and lock it for the whole page (a warm-grey site does not get a blue CTA in section 7).
- **Kill pure gray.** Add chroma **0.005-0.015** to all neutrals, hued toward *this* brand's color, small enough not to read as tinted. Stick to one gray family; never mix warm and cool grays. The hue comes from the specific brand, not a "warm = friendly, cool = tech" formula. Avoid the lazy default of always tinting toward warm orange or cool blue.
- **60-30-10 by visual weight, not pixel count:** 60% neutral backgrounds/surfaces/whitespace, 30% secondary (text, borders, inactive states), 10% accent (CTAs, highlights, focus). Accents work *because* they are rare; flooding the page kills their power.
- **Accent saturation < 80%.** Desaturate so accents blend with neutrals instead of screaming. Bolder = one bold color owning ~60% plus a sharp accent; quieter = 70-85% saturation with neutral dominance. Avoid the AI purple/blue glow and the purple-to-blue gradient.
- **Gradients:** allowed when subtle and palette-matched (low-chroma tonal grades, single-hue atmospheric washes, noise-textured). Break uniform linear 45° fades with radial, noise-overlay, or mesh variants. Banned slop: rainbow/mesh blobs, purple-to-blue "AI" defaults, pink-to-orange "creator" defaults, gradient text as a premium shortcut.

### Contrast (WCAG, verify on every text element)

| Content | AA minimum | AAA target |
|---------|-----------|------------|
| Body text | 4.5:1 | 7:1 |
| Large text (≥18px, or ≥14px at weight ≥700) | 3:1 | 4.5:1 |
| UI components, icons | 3:1 | 4.5:1 |
| Placeholder text | 4.5:1 | — |

The single biggest reason AI designs feel hard to read: muted gray body text on a tinted near-white "for elegance." When close, bump the body color toward the ink end of the ramp. Dangerous combos that commonly fail: light gray on white (the #1 fail), red on green (8% of men can't distinguish), yellow on white, thin light text on images. Don't trust your eyes; test with a contrast checker. Never rely on color alone to convey information.

**Never put gray text on a colored background.** It looks washed out. Use a darker shade of the background's own hue, or a transparency of the text color.

### Dark mode

Dark mode is not inverted light mode. **Never use pure black or pure white**; use off-black or a brand-tinted near-black (`#0a0a0a`, `#121212`, oklch ~12-18% works). Depth comes from **surface lightness**, not shadow: build a 3-step surface scale where higher elevations are lighter (e.g. 15% / 20% / 25% lightness), same hue/chroma as the brand, varying only lightness. Reduce body text weight slightly and desaturate accents. Use two token layers: primitives (`--blue-500`) and semantics (`--color-primary`); for dark mode, redefine only the semantic layer. Heavy alpha use is a smell that signals an incomplete palette; define explicit overlay colors instead (exception: focus rings and interactive states).

---

## Layout and grid

- **Flexbox for 1D** (rows, nav bars, button groups, component internals). **Grid for 2D** (page structure, dashboards, data-dense interfaces). Don't default to Grid when `flex-wrap` is simpler; don't do flexbox percentage math (`w-[calc(33%-1rem)]`) where Grid is cleaner.
- **Breakpoint-free responsive grids:** `grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))`. Use container queries for components, viewport queries for page layouts.
- **Contain page width** to ~1200-1440px with auto margins; edge-to-edge content on wide screens destroys readability.
- **Asymmetry creates interest.** Break centered/symmetrical layouts with offset margins, mixed aspect ratios, or left-aligned headers over centered content. Throw out the golden ratio; try **70/30 or 80/20** splits. Use negative margins for overlap and layering. Centered hero is OK only for editorial/manifesto/launch briefs where the message is the design.
- **Cards are the lazy answer.** Use them only when elevation communicates real hierarchy; otherwise group with `border-t`, `divide-y`, or negative space. **Never nest cards inside cards.** Vary card sizes and mix with non-card content to break monotony. Allow variable card heights or masonry when content length differs; force-equalized heights look rigid. Pin CTAs to card bottoms so they form a clean horizontal line, and start feature lists at the same Y across pricing/comparison columns.
- **Bento grids:** exactly as many cells as you have content for (3 items → 3 cells; 5 → 5). No empty cell in the middle or end; re-shape the grid, never paste a blank tile. Use `grid-flow-dense` and verify col-span/row-span interlock. Give multi-cell grids real visual variation (image, palette-matched gradient, pattern, tinted background); all-text white-on-white cards read as default.
- **Vary layout families.** Each family appears at most once per page; an 8-section page uses ≥4 different families. Cap consecutive image+text zigzag at 2; the 3rd is broken.
- **Hero discipline:** headline ≤2 lines, subtext ≤20 words and ≤3-4 lines, CTAs visible without scroll. A 4-line hero headline is a font-size error, not a copy-length one. Cap hero top padding at `pt-24` (~6rem). Max 4 text elements; trust strips, taglines, pricing teasers, and logo walls move below the hero.
- **Navigation** renders on a single line at desktop (condense or hamburger if it won't fit); cap height at 80px (default 64-72px).
- **Theme lock:** one theme for the whole page; sections do not invert mid-scroll. Section-level tints within the same family are fine; flipping to a cream section between dark sections is broken. Set the theme once at the page root.
- **Touch targets** are 44×44px minimum even when the visual element is smaller; expand the hit area with padding or a pseudo-element.

### Optical alignment

Adjust only when something genuinely looks wrong, never speculatively. Text at `margin-left: 0` looks indented due to letterform whitespace; nudge `-0.05em` to optically align. Geometrically centered glyphs look off (play icons shift right, arrows shift toward their direction); icons next to text often need 1-2px adjustment. Align shared elements (titles, prices, buttons) across side-by-side items, or the layout looks broken. Standardize icons to one stroke weight.

---

## Visual hierarchy

Direct the eye with the fewest dimensions needed. Space alone is often enough; add color or size only when simpler means aren't sufficient. The strongest hierarchy combines 2-3 dimensions at once.

| Dimension | Strong | Weak |
|-----------|--------|------|
| Size | 3:1 ratio or more | <2:1 |
| Weight | Bold vs Regular | Medium vs Regular |
| Color | High contrast | Similar tones |
| Position | Top/left (primary) | Bottom/right |
| Space | Surrounded by whitespace | Crowded |

**The squint test:** blur your eyes. If you can still identify the most important element, the second, and clear groupings, the hierarchy works. The most important content should be obvious within 2 seconds. Group by proximity; create clear groupings through spacing and separation. To quiet a loud design, reduce weights (900→600, 700→500), shrink scale jumps, and lean on weight/size/space instead of color and boldness.

### Cognitive load

Humans hold ≤4 items in working memory. Cap simultaneous decision options at 4: nav ≤5 top-level, ≤4 form fields per group, 1 primary + 1-2 secondary actions, ≤4 dashboard metrics, ≤3 pricing tiers. One screen, one focus. Option bands: ≤4 is manageable, 5-7 is pushing it, 8+ and users skip, misclick, or abandon.

Three kinds of load, three treatments:

- **Intrinsic** (the task is genuinely complex): structure it with discrete steps, scaffolding, and progressive disclosure.
- **Extraneous** (the interface adds friction): eliminate ruthlessly: confusing nav, unclear labels, clutter, inconsistent patterns, unnecessary steps.
- **Germane** (effort that builds the user's mental model): this load is good; support it with consistent patterns and clear feedback.

Eight-point self-check, one point per failure (**0-1 = low load, 2-3 = moderate, 4+ = critical**): single focus per screen / chunks of ≤4 per group / visual grouping matches meaning / clear hierarchy / one decision at a time / ≤4 visible options per decision point / no memory bridges between screens / progressive disclosure for the rest.

| Violation | One-line fix |
|-----------|--------------|
| The Wall of Options | Group, default, and progressively disclose; show ≤4 at once |
| The Memory Bridge | Carry needed info forward; never make users remember it across screens |
| The Hidden Navigation | Keep primary paths visible; don't bury them behind gestures or unlabeled icons |
| The Jargon Barrier | Use the user's words, not the system's |
| The Visual Noise Floor | Strip decoration until every element earns its place |
| The Inconsistent Pattern | One interaction pattern per job, reused everywhere |
| The Multi-Task Demand | One task per screen; split parallel demands into steps |
| The Context Switch | Keep related actions in one place; don't bounce users between areas |

---

## Depth, borders, and radius

The system should read mostly flat. Depth comes from material contrast and hairlines before shadow.

- **Hairline first.** Use a 1px border or a background shift before reaching for a drop shadow. Group with `border-t` or `divide-y` instead of wrapping everything in elevated cards.
- **Shadow scale:** build a consistent `sm → md → lg → xl` and keep shadows subtle. Use elevation to reinforce hierarchy, not as decoration. All shadows imply a **single light source**; audit for inconsistent direction.
- **Tint shadows to the background hue.** No pure-black low-opacity shadows on colored or light backgrounds; a black shadow on a colored surface looks muddy and bolted-on.
- **Radius consistency.** Pick one scale and apply it everywhere: all-sharp (0), all-soft (12-16px), or all-pill (full radius on interactive). Mixed systems are allowed only under a documented rule followed everywhere (e.g. buttons full-pill, cards 16px, inputs 8px). Round buttons in a square layout is broken. When nesting, vary radius optically: tighter on inner elements, softer on outer containers.
- **Default-lean on roundness: cards top out at 12-16px.** Card, section, or input radii of 24, 28, 32, or 40px read as generated UI; full-pill radius stays at tag/button scale. Soft and high-end consumer systems deliberately override this (the precedence rule applies).
- **Glassmorphism:** go beyond `backdrop-filter: blur`. Add a 1px inner border (`border-white/10`) and a subtle inner shadow (`inset 0 1px 0 rgba(255,255,255,0.1)`) to simulate edge refraction. Provide a solid-fill fallback for `prefers-reduced-transparency`.

---

## Expensive vs cheap

These are **default-lean** verdicts for the aesthetic-neutral baseline — what to do when no aesthetic system has overridden them. A deliberately selected system *can* flip specific cells: Minimalist's canvas is literally `#FFFFFF`, Brutalist *requires* Inter Black for macro-type, Soft *requires* diffused ambient shadows. See aesthetic-systems.md (Cross-System Contradictions) for the scoped exceptions.

| ✅ Expensive | ❌ Cheap |
|-------------|---------|
| Off-black / brand-tinted near-black ground | Pure `#000000` or pure `#FFFFFF` |
| Neutrals tinted with brand chroma (0.005-0.015) | Dead pure gray; warm and cool grays mixed |
| One locked accent at <80% saturation | AI purple/blue glow; multiple competing accents |
| Subtle palette-matched gradients (radial, mesh, noise) | Even linear 45° purple-to-blue fade |
| Shadows tinted to background hue, one light source | Pure-black drop shadows, inconsistent lighting |
| Hairlines and surface contrast for depth | Blanket drop shadows on every card |
| Committed type scale, ≥1.25 between steps | Flat 1.1× scale; 14/15/16/18px muddle |
| Geist/Satoshi/Cabinet Grotesk with real weight contrast | Inter everywhere; only 400 + 700 |
| Same-family italic/bold emphasis | Random serif word dropped into a sans headline |
| Measure capped 65-75ch, generous whitespace | Edge-to-edge text, cramped equal spacing |
| Asymmetric 70/30 splits, varied layout families | Centered-over-dark hero, 6 zigzag rows, repeated cards |
| Bento cells = content count, dense interlock | Empty bento cells, nested cards |
| Cards at 12-16px radius; pill only at tag/button scale | 24-40px radii on cards, sections, inputs |
| Subtle grain/noise/texture on flat fields | Sterile flat vectors; perfectly even gradients |
| Sentence-case headers, clean rags | Title Case everywhere, orphaned last-line words |

Most of these details users never consciously notice. That is the point: in the aggregate, the unseen corrections compound into an interface people trust without knowing why. Ship beautiful defaults rather than relying on configuration, because most users never customize.
