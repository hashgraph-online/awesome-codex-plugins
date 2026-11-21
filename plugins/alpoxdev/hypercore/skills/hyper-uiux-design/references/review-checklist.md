# Review Checklist

Read this reference for every review pass, once an image is back. It lists what to check in a generated screen mockup, how to record each item, and what makes an image a candidate for approval.

## Contents

1. How to Record
2. Brief Fidelity
3. Readability
4. Visual Quality
5. Generated-Image Tells
6. Accessibility
7. Set Consistency
8. Reference Independence
9. Verdict

## 1. How to Record

Open the returned image and look at it; a successful tool call is not a review. Record one row per item:

| Column | Content |
|---|---|
| Item | The check, by its id below |
| Result | `pass`, `fail`, or `not checkable in an image` |
| Label | `seen` or `computed` |
| Note | What was observed, in a few words; for a `fail`, what the next brief changes |

A `not checkable in an image` item is copied into the handoff as a requirement. It is never counted as a pass.

Section 4 is the one that decides whether the screen looks shipped. A mockup can pass every fidelity and readability item and still be a wireframe; section 4 is what catches that.

## 2. Brief Fidelity

| Id | Check |
|---|---|
| F1 | Every region in the brief is present, in the stated order, with the stated relative sizes |
| F2 | The single primary action is present, in the stated place, in the accent color |
| F3 | The components are the ones named: no extra tab bar, banner, card, or step |
| F4 | The canvas orientation and the platform frame match, with no device around it |
| F5 | The theme matches the brief's token column: background, surface, and accent read as the stated colors |
| F6 | The reported pixel size is recorded, and any difference from the requested ratio is stated in the notes |
| F7 | The status bar carries the stated content, and a selected navigation state is drawn as stated |

## 3. Readability

| Id | Check |
|---|---|
| R1 | Each stated string matches the brief character by character, including every Hangul syllable, and appears once |
| R2 | **Every text position carries real content.** No bar, block, or grey shape stands where a string, number, date, or name belongs. A bar where content belongs is a `fail`, not an abstraction |
| R3 | The hierarchy reads in order: headline, then sections, then rows, then the primary action |
| R4 | Text does not overlap, clip at an edge, or collide with an icon |
| R5 | The smallest text is still legible at the image's native size |
| R6 | Right-aligned numbers share one right edge and read as tabular |

## 4. Visual Quality

The difference between a wireframe and a shipped screen. Any `fail` here sends the screen back even when everything else passes.

| Id | Check |
|---|---|
| Q1 | The screen carries the element count its type expects ([visual-quality-recipe.md](visual-quality-recipe.md) §7): a transactional screen below 9 elements, or a content screen below 6, is under-built |
| Q2 | Every amount, count, percentage, date, and name is present and plausible, and the numbers are internally consistent: the parts add to the total, percentages sum to 100 |
| Q3 | Exactly one element is the largest, and the size ratio between the headline and the body is near 2.5 to 2.8 |
| Q4 | The accent covers roughly a tenth of the screen and appears only on the primary action, the active state, and at most one badge |
| Q5 | Icons share one style, one stroke weight, and one size per role, and each reads as the glyph it stands for |
| Q6 | Cards, fields, and rows are filled, radiused, and separated as the brief states, with hairlines where a divider belongs |
| Q7 | Secondary detail is present where the screen type expects it: a count on the section header, a caption line under each row title, a value on a navigable row |
| Q8 | Photography, when the product is visual, is the dominant weight and is composed, not a flat placeholder block |
| Q9 | The screen is full without being crowded: no large empty band where an element should be, and no element touching the frame edge |
| Q10 | Surfaces are flat colour as the tokens state, with no added texture, film grain, or noise unless the brief asked for it |

## 5. Generated-Image Tells

These are the marks that make a mockup look machine-made, and they mislead an implementer.

| Id | Check |
|---|---|
| G1 | No invented logo, brand name, mascot, or app icon |
| G2 | No decoration the tokens do not contain: gradient washes, glow, glass blur, floating blobs, stock-style illustration |
| G3 | No element the brief did not ask for: a signal cluster, a second tab bar, a social login row, a promotional banner |
| G4 | Icons sit where a real control would be, and no glyph is half-drawn or fused with a neighbour |
| G5 | Spacing is regular: equal gaps between like items, one side padding, aligned edges |
| G6 | Repeated components are identical in shape: every card, row, and field matches its siblings |
| G7 | No duplicated element, and no second screen in the same image |
| G8 | No text artifact: a repeated syllable, a doubled label, or a string running off its container |

## 6. Accessibility

| Id | Check | Label |
|---|---|---|
| A1 | Each text and background pair in the tokens meets its contrast minimum | `computed` |
| A2 | Text over a photo or gradient has a solid or scrim layer behind it | `seen` |
| A3 | State is not carried by colour alone: the selected tab has a shape, the error has an icon or text | `seen` |
| A4 | Controls are drawn large enough to plausibly meet the platform target size; the exact size is a handoff requirement | `not checkable in an image` |
| A5 | Focus, screen-reader names, and keyboard order | `not checkable in an image` |

Never sample a color from the image for A1. The ratio comes from the token values.

## 7. Set Consistency

Run these across all images of a set together, after each image passed on its own.

| Id | Check |
|---|---|
| S1 | Background, surface, and accent look the same on every screen |
| S2 | The type treatment is the same: one typeface character, the same title and body scale |
| S3 | Shared components are the same on every screen: button shape and height, field shape, card radius |
| S4 | System bars and navigation sit in the same place and style |
| S5 | A light and a dark version of one screen differ only in color |
| S6 | The sample data is coherent across the set: one person's name, one month, one running total |

A screen that drifts is regenerated with the drifting invariant restated; the anchor screen is not changed to match it.

## 8. Reference Independence

| Id | Check |
|---|---|
| I1 | The mockup cannot be mistaken for any one reference: its composition was built from the pattern summary, not traced |
| I2 | No name, logo, illustration, copy, or signature color-and-type pairing of a referenced product appears |
| I3 | The brief contains no product name, reference URL, or reference image |

## 9. Verdict

- Candidate: no `fail` in sections 2 to 8.
- Regenerate: any `fail`, while the screen has briefs left under the cap. The next brief changes one thing, chosen from the highest failing section in this order: visual quality, reference independence, brief fidelity, readability, generated-image tells, set consistency.
- Stop: the cap is reached. Keep the attempt with the fewest failing items and list them.

A candidate is not an approved mockup. Approval is the user's.

## Sources

> Checked 2026-11-15.

| Claim | Source |
|---|---|
| The review covers visual quality, generated-image tells, readability, accessibility, and consistency, with a regeneration cap | user instruction, 2026-11-15 (new skill request) |
| A bar standing in for content is a failure, and the element-count and size-ratio thresholds | this package's before-and-after experiment, `.hyper/uiux-design/quality-2026-11-15/`, 2026-11-15 |
| Contrast is computed against stated minimums, and colour is not the only means of conveying state | <https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html>, <https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html> |
| A returned image is inspected rather than trusted from the tool call, and a wrong character is fixed by regenerating | this package's image-generation skill contract, restated for screens |

### Evidence grade

`LOCAL`: the item list, the ids, the section order, and the verdict order are this package's chosen review. The element-count ranges and the 2.5-to-2.8 ratio are this package's defaults, measured on five screens, not published standards.
