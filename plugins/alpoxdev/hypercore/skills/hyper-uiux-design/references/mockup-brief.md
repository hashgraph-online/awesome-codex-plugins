# Mockup Brief

Read this reference when settling minimal tokens or writing a brief for a screen. A brief is the complete description of one screen in one theme, written so that the image skill can render it without seeing a reference.

A brief describes a finished screen, not a layout with the content left out. [visual-quality-recipe.md](visual-quality-recipe.md) owns what makes the result read as a shipped app, and this file owns the brief's structure.

## Contents

1. What a Brief Holds
2. Canvas by Platform
3. Brief Skeleton
4. Minimal Token Set
5. Light and Dark
6. Revision Briefs

## 1. What a Brief Holds

| Holds | Never holds |
|---|---|
| The screen's purpose in one line | A product, brand, or designer name |
| The platform frame and the canvas shape in words | A reference URL or a reference image |
| Token values: colors as hex, type sizes, radius, spacing | A model name or a model option |
| Regions from top to bottom, each with its own sizes, gaps, and contents inline | Real personal data |
| Every string, number, date, and name the screen shows, spelled out | Placeholders, lorem ipsum, or a bar standing in for text |
| The invented sample data with consistent totals | A request for several screens in one image |

One brief is one screen in one theme and produces one image.

Two things are required content and not decoration: the exact strings, and the sample data behind them. A brief with regions but no amounts, counts, or names is incomplete, and the image that comes back will be a wireframe.

## 2. Canvas by Platform

The frame is the logical screen the mockup represents. The canvas is the shape requested from the image skill. Describe the shape in words inside the brief, and pass the actual ratio or size only through the image skill's structured canvas value.

| Platform | Logical frame to design for | Canvas shape | Frame notes |
|---|---|---|---|
| `mobile` | 393 by 852, portrait, at a 2x scale | Tall portrait, about 9:19.5 | Status bar at the top, home indicator at the bottom, bottom navigation inside the safe area |
| `tablet` | 1024 by 1366 portrait, or 1366 by 1024 landscape | About 3:4 portrait or 4:3 landscape | State the orientation; a landscape tablet usually carries a side rail or two panes |
| `web` | 1440 by 900 desktop viewport | Landscape, about 16:10 | Show the page inside the viewport only, without browser chrome, unless the user asks for it |

- State the frame in pixels inside the brief, as a screenshot's own viewport: `393x852 logical at @2x, flat and straight on, edge to edge`. A vague ratio plus no pixel frame is what produces a tilted device on a desk.
- When the runtime offers only a few shapes, take the nearest one in the same orientation, say in the notes which shape was requested and which came back, and do not crop or resize the returned image.
- A long page is drawn as its first viewport. Further sections are separate briefs, each one viewport tall.
- Draw the screen flat and straight on, edge to edge. No device photo, no perspective, no hand, no desk, and no drop shadow around the screen, because those hide the layout.
- A narrow web layout is a `mobile` brief with the web frame notes.

## 3. Brief Skeleton

Fill every line, in this order. Lines marked invariant are repeated word for word in every brief of a set.

The brief is written as one continuous block for the image tool, not as a form with empty slots. The skeleton below is the outline an agent fills in; the compiled brief reads as prose.

```text
<Artifact and frame sentence>  [invariant]
A full-screen mobile app UI screenshot, portrait, 393x852 logical at @2x,
flat and straight on, edge to edge. The raw screenshot, not a device render.

<Register>
One or two sentences: the product, the screen's job, and the visual register
in the product's own terms, e.g. "calm, precise, information-dense but airy,
the look of a shipped finance app".

<Visual language and negatives>
"Light theme. No gradients, no glow, no glass blur, no decorative blobs,
no stock illustrations."

<Color>  [invariant per theme]
<role #hex> for each: page, surface, hairline, text primary, text secondary,
accent, accent tint, danger. One accent.

<Type>  [invariant per theme]
One typeface character with Hangul support. A scale with real numbers:
"greeting 14, section 18 bold, row title 15 semibold, body 15, caption 12,
headline amount 40 bold with tabular figures and tight tracking."

<Regions, numbered, top to bottom>
1. <region>: <components, sizes, gaps, alignment, and the actual content
   inside this region, inline>
2. ...

<Closing requirement>  [invariant]
"Every Korean string must be rendered fully and correctly, spelled right,
crisp. No placeholder bars, no blurred text, no lorem ipsum."

<Must not appear>  [invariant, extended per screen]
"brand logos or names, real app icons, watermarks, device frame, extra
screens, signal bars and wifi glyphs that were not asked for"
```

Rules for the region list:

1. Put the content in the region that shows it. `A section header with the count` is a region line; the five rows with their names, counts, amounts, and percentages are the next region's lines.
2. Give every region a size. Heights, gaps, padding, and radius as numbers. `five rows, each 64 tall with a 12 gap` renders; `a list of categories` does not.
3. Name the icon, or name the tile it sits in. `a 36x36 tinted rounded-square tile with a simple line fork-and-knife icon` renders one glyph; `simple outline icons` invents a different one each time.
4. Write every string once, in quotes, in the place it appears. Do not keep a separate unattached string list; detached strings float without structure.
5. State one primary action and say what makes it primary: size, fill, and that it is the only full-strength accent on the screen.

Checks to write beside the brief before the call:

- the regions are present in the stated order, with the stated sizes
- every string, number, date, and name in the brief is realistic and spelled out
- the numbers are internally consistent: the parts add to the total, percentages sum to 100
- each rendered string matches character by character, and appears once
- one primary action, in the accent color
- the screen has the density its type expects ([visual-quality-recipe.md](visual-quality-recipe.md) §7)
- no logo, brand name, or device frame
- the canvas orientation matches

## 4. Minimal Token Set

Use this only when the project has no design document or tokens. It is the smallest set that keeps several mockups consistent, and it is recorded as `provisional`.

| Group | Tokens | How to choose |
|---|---|---|
| Color | background, surface, border or hairline, text primary, text secondary, accent, text on accent, accent tint, danger | One accent only. Take the accent from the user's stated color when one exists; otherwise choose one and say it was chosen. Neutrals carry everything else, and the accent tint is the accent at low strength for selected states and icon tiles. |
| Type | one typeface character; a four-step scale for headline, title, body, caption; two weights | Name the character, not a licensed font, unless the project already uses one. Write real numbers, and keep the ratio between the headline and the body near 2.5 to 2.8. Body size no smaller than 16 on web and 15 on mobile in logical units. |
| Radius | one value for controls, one for cards, one for pill or tile | Three at most. |
| Spacing | one base unit and the multiples used for side padding and group gaps | A base of 4 or 8, used as multiples only. |

Rules:

- Compute the contrast of text primary, text secondary, and text on accent against their backgrounds before use, and adjust the token until each passes its minimum.
- A requirement stated by the user, such as a brand color, enters the set as given; when it fails contrast as a text color, keep it for fills and choose a passing text color, and say so.
- Do not add a second accent, a gradient, or a decorative style to the minimal set. Those belong to a visual direction, which is a different deliverable.
- Hand the provisional set over as provisional. The implementer does not treat it as the project's design system until the user accepts it.

## 5. Light and Dark

- Each theme is a separate brief and image with its own token column.
- Dark tokens are chosen, not inverted: a dark background that is not pure black, a surface one step lighter than the background, borders that stay visible, and an accent adjusted so that text on it still passes contrast.
- Between the two briefs only the Theme line and the Tokens block change. Regions, strings, and components stay identical, so the two images can be compared.
- With `both`, the light version is generated and reviewed first.

## 6. Revision Briefs

- Copy the previous brief in full.
- Change one thing and add one line at the top: `Revision <n>: <what changed and why>`.
- When the failure was a bar where content belongs, the change is to write the content, never to make the bar narrower or lighter.
- When the failure was rendered text, keep the number of rendered strings and fix the spelling or the place; cutting rendered strings is the last resort, not the first.
- When the failure was drift between screens of a set, the change is to restate the drifting invariant more exactly, not to describe the other image.

## Sources

> Checked 2026-11-15.

| Claim | Source |
|---|---|
| Mobile, tablet, and web targets, light and dark themes, tokens from the project first and a minimal set of color, type, radius, and spacing otherwise | user instruction, 2026-11-15 (new skill request) |
| Shape described in words with the actual ratio or size in a structured value, exact strings with role and place, one image per brief, shared invariants repeated across a series | this package's image-generation skill contract, restated for screens |
| Content inside the region list, a pixel viewport frame, and the prohibition on bars standing in for text | this package's before-and-after experiment, `.hyper/uiux-design/quality-2026-11-15/`, 2026-11-15 |
| Contrast minimums applied to the token set | <https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html> |

### Evidence grade

`LOCAL`: the three logical frames, the canvas shapes, the skeleton, the minimal token table, and the body-size floors are this package's chosen defaults for a mockup and are not platform requirements. A project's own frame sizes and tokens replace them. The content rule and the pixel frame are backed by this package's own comparison on one model and one token set.
