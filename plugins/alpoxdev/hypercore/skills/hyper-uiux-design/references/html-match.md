# HTML Match Stage

Read this reference after an approved or in-advance-approved mockup and before handing the screen over. It decides how the mockup becomes one HTML screen, what "visually identical" means as a test, and what sends the HTML back for another pass.

The mockup is evidence of a screen. The HTML is the screen itself, in markup, that the user can open in a browser. This stage exists because a picture is not a product surface: it cannot be tapped, resized, or read by a screen reader.

## Contents

1. What This Stage Produces
2. Hard Rules for the HTML
3. From Mockup to Markup
4. What Counts as a Match
5. Fail Signals
6. The Comparison Loop
7. Handoff Changes

## 1. What This Stage Produces

One file per screen, at `.hyper/uiux-design/<slug>/html/<screen>.html`, holding the whole screen in one document.

| Holds | Never holds |
|---|---|
| Semantic HTML with one `<main>` per screen | The mockup image, a screenshot of it, or a traced copy of it as a background |
| All CSS inline in one `<style>` block | A build step, a bundler, a framework, or an npm install |
| Every string as real text, every icon as inline SVG | Text drawn as an image, an icon font served from a CDN |
| The token block at the top of the stylesheet, as CSS custom properties | Fonts or assets fetched from a third-party host at render time |
| A fixed logical viewport declared in the brief, used as the design width | Absolute positioning for the whole layout |

The mockup file stays beside the HTML and is referenced in the notes only. It is a comparison artifact, never a page background, never a hidden `<img>` under real text.

## 2. Hard Rules for the HTML

1. **No image of the screen inside the HTML.** Embedding the mockup and drawing real text on top of it produces a page that looks right in one screenshot and is wrong in every other way. If the HTML contains the mockup, the stage has failed.
2. **One document per screen, standalone.** Opening the file from disk must render the screen with no server, no network, and no JavaScript. JavaScript is allowed only for a state the brief names (a selected period, an expanded row) and never for building the initial layout.
3. **Text is text.** Every string is a DOM text node. No string is an SVG `<text>` unless it is part of a chart's axis, and no string is baked into an icon.
4. **Icons are inline SVG, drawn from the icon rule in the brief.** One `viewBox`, one stroke width, one size per role, `stroke="currentColor"`. A geometric substitute is drawn when the mockup's glyph was invented and cannot be identified; the notes say which icons are substitutes.
5. **The token block comes first.** CSS custom properties for page, surface, hairline, text primary, text secondary, accent, accent tint, danger; then the type scale, radius, and spacing. Every value in the stylesheet reads a token, and no color or size appears twice as a literal.
6. **The layout is flow, not a picture of flow.** Flex or grid with a stated gap, one side padding token used everywhere, and section gaps from the token set. Absolute positioning is limited to a badge, an overlay, or a decorative mark.
7. **The screen is responsive in one dimension only.** The brief's logical width is the design width; the content column caps at that width and centres on wider viewports. A mobile screen is not stretched to a desktop layout, and a desktop screen does not collapse to a phone column.
8. **Accessible by construction.** Real `<button>`, `<a>`, `<input>`, and `<label>` elements, `aria-label` on an icon-only control, a visible focus ring, and a heading order that matches the visual hierarchy. Contrast comes from the tokens and is not adjusted by eye.
9. **No library look.** No utility framework classes, no default component styling, no shadow or gradient the tokens do not define.

## 3. From Mockup to Markup

Work in this order. Each step reads from the mockup and writes into the HTML, and the token table is written before the first line of markup.

1. **Copy the token table** from the mockup's brief into CSS custom properties. The brief's values are the contract; a value measured off the image is not.
2. **Write the region list as the DOM order**, top to bottom, one block element per region. Use the mockup's region list, not a guess from the picture.
3. **Set the vertical rhythm** from the brief's gaps: side padding, group gap, row height, section gap. These four numbers carry most of the resemblance.
4. **Set the type scale** from the brief: the largest element first, then section titles, then row titles, then meta. Do not invent a fifth size.
5. **Place every string** the mockup renders, in the same position, with the same emphasis. Take the strings from the mockup's copy list, not by reading the image, so a wrong syllable in the image is not copied.
6. **Draw each icon** as inline SVG at the brief's size and stroke width.
7. **Build the one primary action** last, so the accent appears exactly once at full strength.
8. **Delete anything the brief did not list.** An extra divider, badge, or caption added "for realism" is a mismatch, not a bonus.

The mockup's rendered text is never the source of copy: the brief's copy list is. When the image shows a wrong syllable, the HTML carries the correct one, and the notes record that the image and the HTML differ there on purpose.

## 4. What Counts as a Match

A match is judged on structure and rhythm, not on a pixel diff. The elements the picture cannot settle (exact spacing, font metrics, image content) are settled by the tokens and the brief.

| Band | What is compared | Pass condition |
|---|---|---|
| Frame | Viewport ratio, side padding, safe areas | The HTML presents the same ratio, the same side padding token, and no element touching the frame edge |
| Top | Status or navigation bar, title, action glyphs | The same items in the same order, one action at most, the title at the brief's size |
| Hero | Largest element, its caption, its delta or badge | The same element is the largest, at the brief's size ratio, with the same caption lines |
| Content groups | Group header, row count, row anatomy | The same number of groups and rows in the first viewport, each row with the same parts in the same order (icon tile, two-line text, trailing value) |
| Rhythm | Gaps between groups, row heights, alignment edges | Every gap matches its token; the two text columns share one left edge; the numeric column shares one right edge |
| Type | The four-step scale, weights | No extra size, and the largest-to-body ratio matches the brief |
| Colour | Accent count, surface fills, hairlines | One accent at full strength, at most one tinted surface per group, hairlines only where the brief put them |
| Bottom | Tab bar or sticky action, selected state | The same items, the same active item, active state carried by shape and colour |
| Content | Every string, amount, count, date | Every string is present, spelled correctly, and the numbers still add up |

A band with one fail sends the screen back. A pass on eight bands and a fail on rhythm is a fail, because rhythm is what makes the page read as the same screen.

## 5. Fail Signals

Any one of these is a fail even when the page looks close at a glance.

| Signal | Why it fails |
|---|---|
| The page contains the mockup image, or a crop of it | The layout is not markup; nothing below the picture is real |
| One gap value used everywhere (for example everything at 16px) | The mockup's grouping is lost; this is the most common tell of a generated page |
| A gradient, glow, drop shadow, or blur the tokens do not define | Not in the brief, and it reads as machine-made decoration |
| Every section centred, or every card the same weight | No hierarchy; the eye has nowhere to land first |
| Text set in a different size than the brief for three or more elements | The scale was eyeballed instead of read |
| Icons at mixed stroke widths or mixed sizes per role | One icon set is the point; a mixed set reads as assembled |
| Emoji used as an icon | Not an icon; renders differently on every platform |
| A placeholder string, `Lorem`, `Item`, `00,000`, or an empty box where content belongs | The mockup's content rule is broken in the deliverable |
| A rounded rectangle standing in for an illustration or a photo | Say the asset is needed; do not draw a grey block |
| More than one accent at full strength, or the accent on a non-primary element | Colour discipline is the cheapest signal of a designed screen |
| Fixed pixel heights on containers that hold text | Text overflows or clips on a different font; use min-height and padding |
| Motion, a carousel, or an animation the user did not ask for | Out of scope, and it hides a broken static state |
| Scrollbars on the page at rest, or content cut at the bottom without the mockup showing it | The viewport math is wrong |

## 6. The Comparison Loop

1. **Render and capture.** Open the HTML in a browser at the brief's logical viewport and capture a screenshot at the same scale as the mockup's native size. Record the file paths of both.
2. **Compare band by band**, in the order of §4, and write a diff list: `band — what differs — the token or brief value that fixes it`. One line per difference, no grouping.
3. **Rank the list.** Rhythm and content first, then hierarchy, then colour, then icon detail. Fix the highest item only.
4. **Fix in the HTML, not in the picture.** Change the token or the rule; never nudge a value to match a measurement taken from the image.
5. **Re-render and re-compare.** Repeat, at most three passes.
6. **Stop** when the diff list is empty, or when the cap is reached. At the cap, keep the attempt with the shortest diff list, and list every remaining difference in the notes. A screen that reaches the cap with a spacing difference is reported as that difference, not as a match.

Record for each pass: the pass number, the diff count before and after, and the one thing that changed. A pass that changed three things at once does not count as a comparison.

## 7. Handoff Changes

The handoff now carries two artifacts and says which is which.

| Part | Content |
|---|---|
| Mockup image | Evidence of layout and density only; not to be embedded, traced, or shipped |
| HTML | The screen itself, one file, opening from disk; the starting point for the real implementation |
| What the HTML is not | Not production code: no data layer, no routing, no state beyond what the brief named, no build integration |
| Token block | Copied out of the CSS custom properties, as the contract for the project's own theme |
| Remaining differences | Every band still failing after the cap, with the token that would close it |
| Icon inventory | Which icons are from the brief's named glyphs and which are geometric substitutes |

The implementer receives the tokens and the HTML as a reference implementation. The tokens win over both the picture and the HTML when they disagree.

## Sources

> Checked 2026-11-15.

| Claim | Source |
|---|---|
| The HTML stage, one standalone screen per file, no embedded mockup image, real text and inline SVG, the token block, and the comparison cap | user instruction, 2026-11-15 (approved mockup becomes HTML that matches it) |
| Region list as DOM order, the four rhythm numbers, the four-step type scale, and the single primary action | this package's own brief rules, restated for markup |
| The side padding, group gap, card grouping, row anatomy, and type-scale ranges that the match test checks | this package's synthesis of public screen listings read on 2026-11-15, stated as defaults rather than measured platform requirements; see `.hyper/uiux-design/html-2026-11-15/ref-log.md` |
| Text contrast from tokens, focus visibility, and visible state that is not carried by colour alone | <https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html>, <https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html> |
| Generated-page tells such as an undifferentiated gap value and decorative gradients | this package's own observation across the comparison passes recorded in `.hyper/uiux-design/html-2026-11-15/` |

### Evidence grade

`LOCAL` for the hard rules, the band list, the fail signals, and the three-pass cap. The craft defaults (side padding, row anatomy, type ratio) are this package's synthesis of what several public apps show in common, not a published standard. The WCAG criteria are `PRIMARY`.
